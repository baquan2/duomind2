import json
import re
from collections import Counter
from typing import Any

from app.models.mentor import MentorIntent
from app.services.gemini_service import gemini
from app.services.market_research_service import search_market_context
from app.services.supabase_service import SupabaseService
from app.utils import mentor_logic
from app.utils.content_blueprint import (
    build_blueprint_fallback,
    build_key_points_from_briefs,
    build_section_briefs,
    build_summary_from_briefs,
)
from app.utils.helpers import build_core_title, normalize_text, normalize_topic_phrase, strip_accents
from app.utils.mentor_prompts import MENTOR_RESPONSE_PROMPT, MENTOR_RESPONSE_REWRITE_PROMPT


INTENT_PATTERNS: list[tuple[MentorIntent, tuple[str, ...]]] = [
    ("career_roles", ("vị trí", "vai trò", "nghề", "công việc", "role", "chức danh")),
    ("market_outlook", ("cơ hội", "triển vọng", "phát triển", "thu nhập", "nhu cầu", "thị trường", "jd", "tuyển dụng", "yêu cầu thị trường")),
    ("skill_gap", ("thiếu kỹ năng", "thiếu gì", "kỹ năng cần", "kiến thức nào tôi cần có", "cần có gì", "gap", "hổng kỹ năng")),
    ("learning_roadmap", ("lộ trình", "nên học gì", "học gì trước", "bắt đầu từ đâu", "roadmap", "thứ tự học", "học theo bước")),
    ("career_fit", ("phù hợp", "hợp với tôi", "nên chọn hướng nào", "nên theo hướng nào")),
]

TRACK_KEYWORDS = {
    "dev": "dev",
    "developer": "dev",
    "lập trình": "dev",
    "frontend": "dev",
    "backend": "dev",
    "fullstack": "dev",
    "web": "dev",
    "mobile": "dev",
    "software": "dev",
    "data analyst": "data",
    "business analyst": "business",
    "business analysis": "business",
    "requirement": "business",
    "user story": "business",
    "stakeholder": "business",
    "process mapping": "business",
    "nghiệp vụ": "business",
    "phân tích dữ liệu": "data",
    "sql": "data",
    "power bi": "data",
    "tableau": "data",
    "marketing": "marketing",
    "digital marketing": "marketing",
    "content": "marketing",
    "seo": "marketing",
    "product": "product",
    "product manager": "product",
}

GENERIC_MARKERS = (
    "mình chưa có phản hồi ai đầy đủ",
    "mình chưa có đủ dữ liệu",
    "mentor chưa gom đủ dữ liệu",
    "theo hướng an toàn",
    "nếu bạn hỏi cụ thể hơn",
    "mình đã hiểu câu hỏi của bạn",
    "mình đã ghi nhận mục tiêu",
    "hãy nêu rõ 3 điểm",
    "hãy cho tôi thêm",
)

SKILL_CATALOG = {
    "dev": ["JavaScript", "TypeScript", "HTML/CSS", "Git/GitHub", "API/HTTP", "SQL", "React", "Node.js"],
    "data": ["Excel", "SQL", "Python", "Power BI", "Tableau", "Statistics", "Dashboarding"],
    "business": ["Requirement analysis", "User story", "Process mapping", "Stakeholder communication", "Use case", "Acceptance criteria"],
    "marketing": ["Customer insight", "Content", "SEO", "Meta Ads", "Google Ads", "Google Analytics"],
    "product": ["User research", "Roadmapping", "Product metrics", "SQL", "A/B testing"],
    "general": ["Problem solving", "Communication", "Project work", "Portfolio"],
}

FORBIDDEN_GENERIC_PHRASES = (
    "con tuy",
    "ban co the can nhac",
    "hay cho them thong tin",
    "minh chua co du du lieu",
    "theo huong an toan",
)

MENTOR_TOPIC_STOPWORDS = {
    "la",
    "gi",
    "ve",
    "va",
    "voi",
    "nhu",
    "the",
    "nao",
    "tai",
    "sao",
    "khi",
    "can",
    "nen",
    "hoc",
    "giup",
    "cho",
    "mot",
    "nhung",
    "cua",
    "toi",
    "minh",
    "em",
    "ban",
    "hay",
}

KNOWLEDGE_QUESTION_MARKERS = (
    "la gi",
    "la nhu the nao",
    "khac nhau",
    "khac gi",
    "o diem nao",
    "phan biet",
    "so sanh",
    "giai thich",
    "ban chat",
    "co che",
    "hoat dong",
    "van hanh",
    "tai sao",
    "khi nao dung",
    "truong hop nao dung",
    "vi du",
)

PERSONAL_GUIDANCE_MARKERS = (
    "toi nen",
    "minh nen",
    "em nen",
    "phu hop voi toi",
    "hop voi toi",
    "cho toi",
    "lo trinh",
    "roadmap",
    "thieu ky nang",
    "skill gap",
    "thi truong",
    "jd",
    "tuyen dung",
    "thu nhap",
    "co hoi viec lam",
    "muc tieu cua toi",
    "ho so cua toi",
)

INTENT_RESPONSE_POLICIES: dict[MentorIntent, dict[str, Any]] = {
    "career_roles": {
        "primary_goal": "De xuat toi da 3 vai tro va chot 1 vai tro uu tien nhat.",
        "must_include": [
            "fit_reason bam profile",
            "entry_level",
            "2-4 ky nang cot loi",
            "1 buoc tiep theo trong 7 ngay",
        ],
        "avoid": ["roadmap qua dai", "qua 3 lua chon ngang nhau"],
    },
    "market_outlook": {
        "primary_goal": "Ket luan co hoi thi truong truoc, sau do moi neu tac dong den viec hoc.",
        "must_include": [
            "ket luan ngan ve nhu cau thi truong",
            "2-4 ky nang duoc nhac nhieu",
            "1 hanh dong de kiem chung hoac bat dau",
        ],
        "avoid": ["bien thanh roadmap dai", "ly thuyet chung chung"],
    },
    "skill_gap": {
        "primary_goal": "Chi ra 3 ky nang thieu quan trong nhat va thu tu bu truoc.",
        "must_include": [
            "3 skill gaps toi da",
            "ly do bam target_role/desire/challenge",
            "3 hanh dong cu the",
        ],
        "avoid": ["ban qua sau ve thi truong", "nhieu lua chon ngang nhau"],
    },
    "learning_roadmap": {
        "primary_goal": "Dua 3 buoc roadmap theo thu tu va moi buoc co dau ra cu the.",
        "must_include": [
            "thu tu hoc",
            "output moi buoc",
            "ke hoach trong 7 ngay tiep theo",
        ],
        "avoid": ["list kien thuc dai dong", "roadmap khong co output"],
    },
    "career_fit": {
        "primary_goal": "Chot 1 huong phu hop nhat truoc, chi neu them 1-2 huong phu.",
        "must_include": [
            "1 huong uu tien",
            "ly do bam profile",
            "1 buoc tiep theo de kiem chung su phu hop",
        ],
        "avoid": ["so sanh lan man", "3+ lua chon dong hang"],
    },
    "general_guidance": {
        "primary_goal": "Tra loi truc dien dung cau hoi hien tai; chi dua hanh dong khi cau hoi thuc su can.",
        "must_include": [
            "cau tra loi cot loi",
            "giai thich du de hieu",
            "vi du, phan biet, hoac luu y khi can",
        ],
        "avoid": ["coaching ep buoc", "cau tra loi an toan", "van phong rong thong tin"],
    },
}

MAX_ANSWER_WORDS = 220
MAX_STEP_WORDS = 26
MAX_FOLLOWUP_WORDS = 18

# Keep service behavior aligned with the extracted mentor logic module.
TRACK_KEYWORDS = mentor_logic.TRACK_KEYWORDS
GENERIC_MARKERS = mentor_logic.GENERIC_MARKERS
SKILL_CATALOG = mentor_logic.SKILL_CATALOG
FORBIDDEN_GENERIC_PHRASES = mentor_logic.FORBIDDEN_GENERIC_PHRASES
INTENT_RESPONSE_POLICIES = mentor_logic.INTENT_RESPONSE_POLICIES
MAX_ANSWER_WORDS = mentor_logic.MAX_ANSWER_WORDS
MAX_STEP_WORDS = mentor_logic.MAX_STEP_WORDS
MAX_FOLLOWUP_WORDS = mentor_logic.MAX_FOLLOWUP_WORDS


def _mentor_compare_subjects(message: str) -> tuple[str, str] | None:
    normalized = normalize_text(message)
    patterns = [
        r"(.+?)\s+(?:khác|khac)\s+(.+?)\s+(?:ở|o)\s+(?:điểm|diem)\s+nào\??$",
        r"so sánh\s+(.+?)\s+và\s+(.+?)$",
        r"phân biệt\s+(.+?)\s+và\s+(.+?)$",
        r"phan biet\s+(.+?)\s+va\s+(.+?)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue
        first = normalize_text(match.group(1).strip(" ?"))
        second = normalize_text(match.group(2).strip(" ?"))
        if first and second:
            return first, second
    return None


def _mentor_question_type(message: str) -> str:
    lowered = strip_accents(normalize_text(message)).lower()
    if _mentor_compare_subjects(message):
        return "comparison"
    if any(marker in lowered for marker in ("la gi", "dinh nghia", "khai niem", "ban chat")):
        return "definition"
    if any(marker in lowered for marker in ("co che", "hoat dong", "van hanh", "tai sao", "nhu the nao")):
        return "mechanism"
    return "general"


def _question_focus_terms(message: str) -> list[str]:
    normalized = strip_accents(normalize_text(message)).lower()
    tokens = re.findall(r"[0-9a-z]+", normalized)
    focus_terms: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if len(token) < 3 or token in MENTOR_TOPIC_STOPWORDS or token.isdigit():
            continue
        if token in seen:
            continue
        seen.add(token)
        focus_terms.append(token)
        if len(focus_terms) >= 8:
            break
    return focus_terms


def _looks_like_direct_knowledge_question(message: str) -> bool:
    lowered = strip_accents(normalize_text(message)).lower()
    if not lowered:
        return False
    has_knowledge_marker = any(marker in lowered for marker in KNOWLEDGE_QUESTION_MARKERS)
    if not has_knowledge_marker:
        return False
    if any(marker in lowered for marker in PERSONAL_GUIDANCE_MARKERS):
        return False
    personal_pronoun_hits = sum(1 for marker in (" toi ", " minh ", " em ") if marker in f" {lowered} ")
    return personal_pronoun_hits <= 1


def _general_guidance_requirements(message: str) -> tuple[str, str, list[str]]:
    question_type = _mentor_question_type(message)
    if question_type == "comparison":
        return (
            "Trả lời trực diện bằng cách phân biệt đúng trọng tâm câu hỏi hiện tại.",
            "direct comparison answer",
            [
                "điểm giống hoặc điểm khác cốt lõi",
                "2-3 trục so sánh rõ ràng",
                "khi nào dễ nhầm hoặc dùng sai",
            ],
        )
    if question_type == "definition":
        return (
            "Giải thích đúng khái niệm và phạm vi của chủ đề đang được hỏi.",
            "focused concept explanation",
            [
                "định nghĩa cốt lõi",
                "ranh giới hoặc điều không nên nhầm",
                "ví dụ hoặc giới hạn áp dụng",
            ],
        )
    if question_type == "mechanism":
        return (
            "Giải thích chủ đề vận hành ra sao và vì sao nó tạo ra kết quả như vậy.",
            "mechanism explanation",
            [
                "cơ chế hoặc logic vận hành",
                "luồng đầu vào -> xử lý -> đầu ra hoặc quan hệ nhân quả",
                "ví dụ hoặc điều kiện áp dụng",
            ],
        )
    return (
        "Trả lời trực diện đúng câu hỏi hiện tại của người dùng.",
        "direct answer",
        [
            "câu trả lời cốt lõi",
            "giải thích đủ để hiểu",
            "ví dụ, phân biệt, hoặc lưu ý khi cần",
        ],
    )


def _legacy_detect_mentor_intent(message: str) -> MentorIntent:
    text = strip_accents(normalize_text(message)).lower()
    if _looks_like_direct_knowledge_question(message):
        return "general_guidance"
    scores: dict[MentorIntent, int] = {
        "career_roles": 0,
        "market_outlook": 0,
        "skill_gap": 0,
        "learning_roadmap": 0,
        "career_fit": 0,
        "general_guidance": 0,
    }
    for intent, keywords in INTENT_PATTERNS:
        for keyword in keywords:
            if strip_accents(keyword).lower() in text:
                scores[intent] += 1

    if "roadmap" in text or "lo trinh" in text:
        scores["learning_roadmap"] += 2
    if "thi truong" in text or "tuyen dung" in text or "jd" in text:
        scores["market_outlook"] += 2
    if "thieu ky nang" in text or "skill gap" in text:
        scores["skill_gap"] += 2

    strongest_intent = max(scores.items(), key=lambda item: item[1])
    if strongest_intent[1] > 0:
        return strongest_intent[0]
    return "general_guidance"


def build_thread_title(message: str) -> str:
    compact = normalize_text(message).strip(" ?.!,:;")
    if not compact:
        return "Phiên mentor mới"
    return (" ".join(compact.split()[:8]).strip() or "Phiên mentor mới")[:72]


def _clip_words(text: str, max_words: int) -> str:
    words = normalize_text(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(" ,;:.") + "..."


def _normalize_answer_text(raw_text: object, max_words: int = MAX_ANSWER_WORDS) -> str:
    _ = max_words
    text = normalize_text(str(raw_text or ""))
    if not text:
        return ""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _normalize_list_of_strings(
    raw_items: object,
    limit: int,
    max_words: int = MAX_STEP_WORDS,
    *,
    clip: bool = True,
) -> list[str]:
    if not isinstance(raw_items, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        value = normalize_text(str(item or ""))
        if clip:
            value = _clip_words(value, max_words)
        if not value:
            continue
        key = strip_accents(value).lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(value)
        if len(cleaned) >= limit:
            break
    return cleaned


def _format_memory_value(value: Any) -> str:
    if isinstance(value, dict):
        parts = [f"{normalize_text(str(k))}: {normalize_text(str(v))}" for k, v in value.items() if normalize_text(str(v))]
        return "; ".join(parts)
    if isinstance(value, list):
        return ", ".join(normalize_text(str(item)) for item in value if normalize_text(str(item)))
    return normalize_text(str(value or ""))


def _track(message: str, onboarding: dict[str, Any] | None) -> str:
    message_blob = strip_accents(normalize_text(message)).lower()
    context_blob = " ".join(
        strip_accents(normalize_text(str((onboarding or {}).get(key) or ""))).lower()
        for key in ("major", "industry", "job_title", "target_role", "ai_persona")
    )
    combined = f"{message_blob} {context_blob}"
    for keyword, track in TRACK_KEYWORDS.items():
        if strip_accents(keyword).lower() in combined:
            return track
    return "general"


def build_suggested_questions(profile: dict[str, Any] | None, onboarding: dict[str, Any] | None) -> list[str]:
    onboarding = onboarding or {}
    status = normalize_text(str(onboarding.get("status") or ""))
    major = normalize_text(str(onboarding.get("major") or ""))
    industry = normalize_text(str(onboarding.get("industry") or ""))
    target_role = normalize_text(str(onboarding.get("target_role") or ""))
    desired_outcome = normalize_text(str(onboarding.get("desired_outcome") or ""))
    current_challenges = normalize_text(str(onboarding.get("current_challenges") or ""))
    daily = int(onboarding.get("daily_study_minutes") or 30)
    track = _track("", onboarding)
    questions: list[str] = []
    if target_role:
        questions += [
            f"Để tiến gần tới vai trò {target_role}, tôi nên ưu tiên học gì trong 30 ngày tới?",
            f"Với mục tiêu {target_role}, tôi đang thiếu những kỹ năng nào quan trọng nhất?",
        ]
    if desired_outcome:
        questions.append(
            f"Nếu đầu ra tôi muốn là '{desired_outcome}', mentor hãy tách giúp tôi roadmap khả thi theo từng tuần."
        )
    if current_challenges:
        questions.append(
            f"Tôi đang gặp khó khăn ở chỗ '{current_challenges}'. Mentor nên tháo gỡ thế nào trước?"
        )
    if status == "student":
        questions += [
            "Sinh viên như tôi nên học gì trước để tăng lợi thế ứng tuyển?",
            "Ngành của tôi có những vị trí thực tập và junior nào?",
        ]
    elif status == "working":
        questions += [
            "Từ vị trí hiện tại tôi có thể phát triển sang vai trò nào?",
            f"Với khoảng {daily} phút học mỗi ngày, tôi nên upskill thế nào cho hiệu quả?",
        ]
    else:
        questions += [
            "Hướng nghề nào đang phù hợp nhất với hồ sơ hiện tại của tôi?",
            "Tôi nên học gì trước để đi đúng hướng và không lan man?",
        ]
    if major:
        questions.append(f"Với nền tảng {major}, tôi nên theo hướng nghề nào để tạo lợi thế nhanh nhất?")
    if industry:
        questions.append(f"Trong ngành {industry}, thị trường đang cần những kỹ năng nào nhất?")
    if track == "dev":
        questions.append("Nếu tôi muốn theo hướng dev, tôi cần những khối kiến thức nền tảng nào?")
    if track == "data":
        questions.append("Nếu tôi muốn theo Data Analyst, tôi nên học những gì theo đúng thứ tự?")
    seen: set[str] = set()
    return [q for q in questions if not (q in seen or seen.add(q))][:6]


def _normalize_role_candidates(message: str, onboarding: dict[str, Any] | None) -> list[str]:
    mapping = {
        "dev": ["software developer", "frontend developer", "backend developer"],
        "data": ["data analyst"],
        "business": ["business analyst"],
        "marketing": ["marketing specialist", "digital marketing specialist"],
        "product": ["product analyst", "product manager"],
    }
    target_role = normalize_text(str((onboarding or {}).get("target_role") or "")).lower()
    role_candidates: list[str] = [target_role] if target_role else []
    for candidate in mapping.get(_track(message, onboarding), []):
        if candidate not in role_candidates:
            role_candidates.append(candidate)
    return role_candidates[:4]


def _looks_like_job_skill_lookup_request(message: str) -> bool:
    lowered = strip_accents(normalize_text(message)).lower()
    if not lowered:
        return False
    has_market_marker = any(
        marker in lowered
        for marker in ("tuyen dung", "jd", "thi truong", "job description", "tin tuyen dung")
    )
    has_skill_marker = any(
        marker in lowered
        for marker in ("ky nang", "skills", "yeu cau", "liet ke", "gom nhung gi", "can gi")
    )
    return has_market_marker and has_skill_marker


def _serialize_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"role": m.get("role"), "intent": m.get("intent"), "content": normalize_text(str(m.get("content") or ""))[:500]} for m in messages[-10:]]


def _serialize_sessions(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"title": s.get("title"), "type": s.get("session_type"), "tags": s.get("topic_tags") or [], "summary": normalize_text(str(s.get("summary") or ""))[:220]} for s in sessions[:6]]


def _serialize_profile(profile: dict[str, Any] | None, onboarding: dict[str, Any] | None) -> dict[str, Any]:
    onboarding = onboarding or {}
    profile = profile or {}
    return {
        "full_name": profile.get("full_name"),
        "age_range": onboarding.get("age_range"),
        "status": onboarding.get("status"),
        "education_level": onboarding.get("education_level"),
        "major": onboarding.get("major"),
        "industry": onboarding.get("industry"),
        "job_title": onboarding.get("job_title"),
        "target_role": onboarding.get("target_role"),
        "current_focus": onboarding.get("current_focus"),
        "current_challenges": onboarding.get("current_challenges"),
        "desired_outcome": onboarding.get("desired_outcome"),
        "learning_constraints": onboarding.get("learning_constraints"),
        "years_experience": onboarding.get("years_experience"),
        "learning_goals": onboarding.get("learning_goals") or [],
        "topics_of_interest": onboarding.get("topics_of_interest") or [],
        "learning_style": onboarding.get("learning_style"),
        "daily_study_minutes": onboarding.get("daily_study_minutes"),
        "ai_persona": onboarding.get("ai_persona"),
    }


def _response_style(onboarding: dict[str, Any] | None) -> dict[str, Any]:
    onboarding = onboarding or {}
    daily = int(onboarding.get("daily_study_minutes") or 30)
    depth = "gọn, ưu tiên việc nên làm trước" if daily <= 20 else "vừa phải, cân bằng giữa định hướng và hành động" if daily <= 45 else "có thể sâu hơn, đủ cho giải thích và lộ trình"
    return {
        "tone": "mentor thực dụng, nói gần người thật, không sáo rỗng",
        "output_depth": depth,
        "example_bias": "ưu tiên ví dụ theo ngành học hoặc công việc hiện tại",
        "followup_rule": "chỉ hỏi lại khi thiếu dữ kiện thật sự quan trọng",
        "learning_style_bias": normalize_text(str(onboarding.get("learning_style") or "mixed")),
        "constraint_hint": normalize_text(str(onboarding.get("learning_constraints") or "")),
    }


def _profile_digest(profile: dict[str, Any] | None, onboarding: dict[str, Any] | None, analytics: dict[str, Any] | None, memories: list[dict[str, Any]]) -> dict[str, Any]:
    onboarding = onboarding or {}
    analytics = analytics or {}
    summary: list[str] = []
    if onboarding.get("status") == "student":
        summary.append("Người dùng đang là sinh viên hoặc đang học")
    elif onboarding.get("status") == "working":
        summary.append("Người dùng đang đi làm")
    elif onboarding.get("status") == "both":
        summary.append("Người dùng vừa học vừa làm")
    if onboarding.get("target_role"):
        summary.append(f"Mục tiêu nghề nghiệp: {onboarding['target_role']}")
    for key, label in (
        ("major", "Nền tảng học tập"),
        ("industry", "Ngành nghề hiện tại"),
        ("job_title", "Vai trò hiện tại"),
        ("current_focus", "Trọng tâm hiện tại"),
        ("current_challenges", "Khó khăn lớn nhất"),
        ("desired_outcome", "Đầu ra mong muốn"),
        ("learning_constraints", "Ràng buộc học tập"),
        ("learning_style", "Phong cách học"),
        ("ai_persona", "Persona hiện tại"),
    ):
        if onboarding.get(key):
            summary.append(f"{label}: {onboarding[key]}")
    if onboarding.get("learning_goals"):
        summary.append(f"Mục tiêu học: {', '.join(onboarding['learning_goals'])}")
    if onboarding.get("daily_study_minutes"):
        summary.append(f"Quỹ thời gian học: khoảng {onboarding['daily_study_minutes']} phút mỗi ngày")
    if analytics.get("strongest_topics"):
        summary.append(f"Chủ đề mạnh: {', '.join(analytics['strongest_topics'][:3])}")
    stable_memories = [{"key": normalize_text(str(m.get('memory_key') or '')), "value": m.get("memory_value")} for m in memories[:6] if normalize_text(str(m.get("memory_key") or ""))]
    return {"profile_summary": summary, "stable_memories": stable_memories, "display_name": (profile or {}).get("full_name")}


PROFILE_CONTEXT_MEMORY_KEYS = {
    "status",
    "education_level",
    "major",
    "school_name",
    "industry",
    "job_title",
    "years_experience",
    "target_role",
    "desired_outcome",
    "current_focus",
    "current_challenges",
    "learning_constraints",
    "learning_goals",
    "topics_of_interest",
    "learning_style",
    "daily_study_minutes",
}


def _merge_onboarding_context_with_memories(
    onboarding: dict[str, Any] | None,
    memories: list[dict[str, Any]],
) -> dict[str, Any]:
    merged = dict(onboarding or {})
    for item in memories:
        memory_key = normalize_text(str(item.get("memory_key") or ""))
        if memory_key not in PROFILE_CONTEXT_MEMORY_KEYS:
            continue

        current_value = merged.get(memory_key)
        if isinstance(current_value, str):
            current_value = normalize_text(current_value)
        if current_value not in (None, "", []):
            continue

        memory_value = item.get("memory_value")
        if isinstance(memory_value, str):
            memory_value = normalize_text(memory_value)
        if memory_value in (None, "", []):
            continue

        merged[memory_key] = memory_value
    return merged


def _missing_context(onboarding: dict[str, Any] | None) -> list[str]:
    onboarding = onboarding or {}
    missing: list[str] = []
    if not onboarding.get("status"):
        missing.append("trạng thái hiện tại")
    if onboarding.get("status") in {"student", "both"} and not onboarding.get("major"):
        missing.append("chuyên ngành hoặc nền tảng học tập")
    if onboarding.get("status") in {"working", "both"} and not onboarding.get("industry"):
        missing.append("ngành nghề hiện tại")
    if not onboarding.get("target_role"):
        missing.append("mục tiêu nghề nghiệp")
    if not onboarding.get("desired_outcome"):
        missing.append("đầu ra mong muốn trong ngắn hạn")
    if not onboarding.get("current_challenges"):
        missing.append("khó khăn hiện tại")
    if not onboarding.get("learning_goals"):
        missing.append("mục tiêu học tập")
    if not onboarding.get("daily_study_minutes"):
        missing.append("quỹ thời gian học mỗi ngày")
    return missing


def _market_brief(message: str, onboarding: dict[str, Any] | None, market_signals: list[dict[str, Any]], web_research: list[dict[str, str]]) -> dict[str, Any]:
    track = _track(message, onboarding)
    catalog = SKILL_CATALOG.get(track, SKILL_CATALOG["general"])
    counts: Counter[str] = Counter()
    roles: list[str] = []
    sources: list[str] = []

    for item in market_signals:
        role = normalize_text(str(item.get("role_name") or ""))
        if role and role not in roles:
            roles.append(role)
        source = normalize_text(str(item.get("source_name") or ""))
        if source and source not in sources:
            sources.append(source)
        for field in ("skills", "tools", "soft_skills", "top_skills"):
            for raw in item.get(field) or []:
                value = strip_accents(normalize_text(str(raw))).lower()
                for skill in catalog:
                    if strip_accents(skill).lower() in value:
                        counts[skill] += 3

    blob = strip_accents(
        " ".join(
            normalize_text(" ".join([str(item.get("title") or ""), str(item.get("snippet") or ""), str(item.get("query") or "")]))
            for item in web_research
        )
    ).lower()
    for item in web_research:
        source = normalize_text(str(item.get("source_name") or ""))
        if source and source not in sources:
            sources.append(source)
        title = normalize_text(str(item.get("title") or ""))
        if title and title not in roles:
            roles.append(title[:72])
    for skill in catalog:
        token = strip_accents(skill).lower()
        if token in blob:
            counts[skill] += max(1, blob.count(token))

    top_skills = [skill for skill, _ in counts.most_common(6)] or catalog[:5]
    summary: list[str] = []
    if top_skills:
        summary.append(f"Kỹ năng nổi lên: {', '.join(top_skills[:5])}")
    if roles:
        summary.append(f"Vai trò / tín hiệu liên quan: {', '.join(roles[:3])}")
    if sources:
        summary.append(f"Nguồn tham chiếu: {', '.join(sources[:3])}")
    return {"track": track, "top_skills": top_skills[:6], "role_hints": roles[:5], "source_names": sources[:5], "summary": summary}


def _normalize_sources(raw_sources: object) -> list[dict[str, Any]]:
    if not isinstance(raw_sources, list):
        return []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw_sources[:10]:
        if not isinstance(item, dict):
            continue
        label = normalize_text(str(item.get("label") or item.get("source_name") or "Nguồn tham khảo"))
        url = normalize_text(str(item.get("url") or item.get("source_url") or ""))
        if url and url not in seen:
            seen.add(url)
            result.append({"label": label, "url": url})
    return result


def _build_profile_brief(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    analytics: dict[str, Any] | None,
    memories: list[dict[str, Any]],
) -> dict[str, Any]:
    profile_digest = _profile_digest(profile, onboarding, analytics, memories)
    onboarding = onboarding or {}
    analytics = analytics or {}
    status = normalize_text(str(onboarding.get("status") or ""))
    stable_memories: list[str] = []
    for item in memories[:5]:
        key = normalize_text(str(item.get("memory_key") or ""))
        value = _format_memory_value(item.get("memory_value"))
        if key and value:
            stable_memories.append(_clip_words(f"{key}: {value}", 16))
    return {
        "display_name": profile_digest.get("display_name") or (profile or {}).get("full_name") or "nguoi dung",
        "stage": status or "unknown",
        "status": status or "unknown",
        "education_level": normalize_text(str(onboarding.get("education_level") or "")),
        "major": normalize_text(str(onboarding.get("major") or "")),
        "school_name": normalize_text(str(onboarding.get("school_name") or "")),
        "industry": normalize_text(str(onboarding.get("industry") or "")),
        "job_title": normalize_text(str(onboarding.get("job_title") or "")),
        "years_experience": normalize_text(str(onboarding.get("years_experience") or "")),
        "target_role": normalize_text(str(onboarding.get("target_role") or "")),
        "desired_outcome": normalize_text(str(onboarding.get("desired_outcome") or "")),
        "current_focus": normalize_text(str(onboarding.get("current_focus") or "")),
        "current_challenges": normalize_text(str(onboarding.get("current_challenges") or "")),
        "learning_constraints": normalize_text(str(onboarding.get("learning_constraints") or "")),
        "daily_study_minutes": int(onboarding.get("daily_study_minutes") or 30),
        "learning_style": normalize_text(str(onboarding.get("learning_style") or "")),
        "strongest_topics": (analytics.get("strongest_topics") or [])[:3],
        "learning_goals": (onboarding.get("learning_goals") or [])[:4],
        "topics_of_interest": (onboarding.get("topics_of_interest") or [])[:4],
        "stable_memories": stable_memories,
        "profile_summary": (profile_digest.get("profile_summary") or [])[:8],
    }


def _status_label(status: str) -> str:
    cleaned = normalize_text(status)
    mapping = {
        "student": "sinh vien",
        "working": "dang di lam",
        "both": "vua hoc vua lam",
    }
    return mapping.get(cleaned, cleaned or "chua ro")


def _profile_direction_hint(onboarding: dict[str, Any] | None) -> str:
    onboarding = onboarding or {}
    target_role = normalize_text(str(onboarding.get("target_role") or ""))
    current_focus = normalize_text(str(onboarding.get("current_focus") or ""))
    industry = normalize_text(str(onboarding.get("industry") or ""))
    job_title = normalize_text(str(onboarding.get("job_title") or ""))
    major = normalize_text(str(onboarding.get("major") or ""))

    if target_role:
        return target_role
    if current_focus:
        return current_focus
    if industry and major:
        return f"{industry} (bam tren nen tang {major})"
    return industry or job_title or major


def _profile_direction_evidence(onboarding: dict[str, Any] | None) -> list[str]:
    onboarding = onboarding or {}
    evidence: list[str] = []
    target_role = normalize_text(str(onboarding.get("target_role") or ""))
    current_focus = normalize_text(str(onboarding.get("current_focus") or ""))
    desired_outcome = normalize_text(str(onboarding.get("desired_outcome") or ""))
    job_title = normalize_text(str(onboarding.get("job_title") or ""))
    industry = normalize_text(str(onboarding.get("industry") or ""))

    if target_role:
        evidence.append(f"muc tieu nghe nghiep la {target_role}")
    if current_focus:
        evidence.append(f"trong tam hien tai la {current_focus}")
    if desired_outcome:
        evidence.append(f"dau ra mong muon la {desired_outcome}")
    if not evidence and job_title:
        evidence.append(f"vai tro hien tai la {job_title}")
    if not evidence and industry:
        evidence.append(f"linh vuc hien tai la {industry}")
    return evidence[:3]


def _build_profile_lookup_fallback(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    onboarding = onboarding or {}
    requested_fields = mentor_logic.profile_lookup_requested_fields(message)
    direction = _profile_direction_hint(onboarding)
    direction_evidence = _profile_direction_evidence(onboarding)
    major = normalize_text(str(onboarding.get("major") or ""))
    school_name = normalize_text(str(onboarding.get("school_name") or ""))
    status = _status_label(str(onboarding.get("status") or ""))
    education_level = normalize_text(str(onboarding.get("education_level") or ""))
    job_title = normalize_text(str(onboarding.get("job_title") or ""))
    industry = normalize_text(str(onboarding.get("industry") or ""))

    lines: list[str] = []
    if "direction" in requested_fields:
        if direction:
            if direction_evidence:
                lines.append(
                    " ".join(
                        [
                            f"Theo ho so hien co, ban dang nghieng ve huong {direction}.",
                            f"Tin hieu chinh: {_join_readable(direction_evidence, limit=3)}.",
                        ]
                    )
                )
            else:
                lines.append(f"Theo ho so hien co, ban dang nghieng ve huong {direction}.")
        else:
            lines.append("Ho so hien tai chua chot ro huong muc tieu hoac trong tam dang theo.")
    if "major" in requested_fields:
        if major:
            lines.append(f"Nganh hoc dang co trong ho so: {major}.")
        else:
            lines.append("Ho so hien tai chua co thong tin nganh hoc.")
    if "school_name" in requested_fields:
        if school_name:
            lines.append(f"Truong dang co trong ho so: {school_name}.")
        else:
            lines.append("Ho so hien tai chua co thong tin truong hoc.")
    if "status" in requested_fields and status:
        lines.append(f"Trang thai hien tai trong ho so: {status}.")
    if "job_title" in requested_fields:
        if job_title:
            lines.append(f"Vai tro hien tai trong ho so: {job_title}.")
        else:
            lines.append("Ho so hien tai chua co thong tin vai tro hien tai.")
    if "industry" in requested_fields:
        if industry:
            lines.append(f"Linh vuc hien tai trong ho so: {industry}.")
        else:
            lines.append("Ho so hien tai chua co thong tin linh vuc hien tai.")

    if not lines:
        if direction:
            lines.append(f"Theo ho so hien co, huong ban dang theo nghieng ve {direction}.")
        else:
            lines.append("Ho so hien tai chua du thong tin de chot ro huong ban dang theo.")
        if major:
            lines.append(f"Nganh dang co trong ho so: {major}.")
        if school_name:
            lines.append(f"Truong dang co trong ho so: {school_name}.")

    context_bits = [
        f"trang thai {status}" if status and status != "chua ro" else "",
        f"bac hoc {education_level}" if education_level else "",
        f"vai tro hien tai {job_title}" if job_title else "",
    ]
    context_bits = [bit for bit in context_bits if bit]
    if context_bits:
        lines.append(f"Tom tat boi canh dang co: {', '.join(context_bits)}.")

    answer = " ".join(lines[:5])
    priority_value = direction or major or school_name or status or "Ho so hien tai"
    reason = "Cau tra loi nay doc truc tiep tu USER_PROFILE_DIGEST he thong dang co, khong suy dien vu vong."
    if direction_evidence:
        reason = (
            "Ket luan nay bam truc tiep vao "
            f"{_join_readable(direction_evidence, limit=3)} trong USER_PROFILE_DIGEST hien co."
        )
    next_action = (
        "Neu muon mentor bam sat hon nua, hay cap nhat cac field con thieu trong profile/onboarding."
        if any("chua co thong tin" in line for line in lines)
        else "Giu profile dong bo khi doi huong hoc hoac muc tieu de mentor tu van sat hon."
    )
    return {
        "intent": "general_guidance",
        "answer": answer,
        "decision_summary": {
            "headline": answer,
            "priority_label": "Doc ho so hien co",
            "priority_value": priority_value,
            "reason": reason,
            "next_action": next_action,
            "confidence_note": "Field nao chua co trong ho so duoc neu ro thay vi noi rang he thong khong truy cap duoc profile.",
        },
        "career_paths": [],
        "market_signals": [],
        "skill_gaps": [],
        "recommended_learning_steps": [],
        "suggested_followups": [
            "Ho so hien tai cua toi con thieu field nao quan trong nhat?",
            "Neu bam dung ho so nay, huong nghe nao hop nhat voi toi?",
            "Toi nen cap nhat profile the nao de mentor tu van sat hon?",
        ],
        "memory_updates": [],
        "sources": [],
    }


def _legacy_build_current_question_payload(
    message: str,
    intent: MentorIntent,
    recent_messages: list[dict[str, Any]],
    recent_sessions: list[dict[str, Any]],
    onboarding: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized_message = normalize_text(message)
    question_type = mentor_logic.mentor_question_type(normalized_message)
    comparison_targets = list(mentor_logic.mentor_compare_subjects(normalized_message) or ())
    focus_topic = mentor_logic.mentor_focus_topic(normalized_message)
    context_mode = "knowledge_first" if intent == "general_guidance" else "mentor_guidance"
    use_profile_context = mentor_logic.should_use_profile_context(intent, normalized_message)
    use_market_context = mentor_logic.should_use_market_context(intent)
    profile_grounding_required = mentor_logic.is_profile_lookup_question(normalized_message)
    requested_profile_fields = mentor_logic.profile_lookup_requested_fields(normalized_message)

    if profile_grounding_required:
        main_request = (
            "Doc USER_PROFILE_DIGEST va tra loi truc tiep theo cac field he thong dang co. "
            "Khong duoc noi rang khong truy cap duoc ho so."
        )
        deliverable_type = "profile-grounded answer"
        must_answer = [
            "tra loi truc tiep tu ho so hien co",
            "field nao chua co thi noi ro la ho so hien tai chua co",
            "khong tu choi bang ly do khong truy cap duoc profile",
        ]
    elif intent == "market_outlook":
        main_request = "Kết luận thị trường đang cần gì trước, rồi mới nối sang tác động đến việc học."
        deliverable_type = "market-first answer"
        must_answer = [
            "mức độ nhu cầu hiện tại",
            "2-4 kỹ năng đang được nhắc nhiều",
            "1 hành động kiểm chứng trong 7 ngày",
        ]
    elif intent == "skill_gap":
        main_request = "Chỉ ra 3 kỹ năng thiếu quan trọng nhất và thứ tự bù trước."
        deliverable_type = "ranked skill gaps"
        must_answer = [
            "3 skill gaps tối đa",
            "vì sao chúng quan trọng với mục tiêu hiện tại",
            "bước bù cụ thể cho từng gap",
        ]
    elif intent == "learning_roadmap":
        main_request = "Tạo roadmap theo thứ tự học, mỗi bước phải có đầu ra rõ."
        deliverable_type = "ordered roadmap"
        must_answer = [
            "thứ tự học",
            "đầu ra của từng bước",
            "việc cần làm ngay trong 7 ngày",
        ]
    elif intent in {"career_fit", "career_roles"}:
        main_request = "Chốt 1 hướng nghề ưu tiên trước, chỉ nêu thêm lựa chọn phụ khi thực sự cần."
        deliverable_type = "prioritized career recommendation"
        must_answer = [
            "1 hướng ưu tiên",
            "lý do bám hồ sơ",
            "1 bước kiểm chứng hoặc bắt đầu ngay",
        ]
    else:
        main_request = "Trả lời trực diện đúng câu hỏi hiện tại của người dùng."
        deliverable_type = "direct answer"
        must_answer = [
            "câu trả lời cốt lõi",
            "giải thích đủ để hiểu",
            "ví dụ, phân biệt, hoặc lưu ý khi cần",
        ]

    conversation_summary: list[str] = []
    for item in recent_messages[-4:]:
        role = normalize_text(str(item.get("role") or "user")) or "user"
        content = _clip_words(str(item.get("content") or ""), 18)
        if content:
            conversation_summary.append(f"{role}: {content}")
    session_summary: list[str] = []
    for item in recent_sessions[:3]:
        title = normalize_text(str(item.get("title") or ""))
        session_type = normalize_text(str(item.get("session_type") or ""))
        tags = ", ".join((item.get("topic_tags") or [])[:3])
        summary = _clip_words(" ".join(part for part in [title, session_type, tags] if part), 14)
        if summary:
            session_summary.append(summary)
    return {
        "intent": intent,
        "message": normalized_message,
        "question_type": question_type,
        "focus_topic": focus_topic,
        "comparison_targets": comparison_targets,
        "context_mode": context_mode,
        "use_profile_context": use_profile_context,
        "use_market_context": use_market_context,
        "question_type": question_type,
        "focus_topic": focus_topic,
        "comparison_targets": comparison_targets,
        "context_mode": context_mode,
        "use_profile_context": use_profile_context,
        "use_market_context": use_market_context,
        "main_request": main_request,
        "deliverable_type": deliverable_type,
        "must_answer": must_answer,
        "response_outline": must_answer,
        "response_outline": must_answer,
        "conversation_summary": conversation_summary,
        "recent_learning_signals": session_summary,
        "missing_context": _missing_context(onboarding)[:4],
        "must_avoid": [
            "trả lời thành lý thuyết dài",
            "lệch sang intent khác",
            "lặp lại bối cảnh người dùng",
        ],
    }


def _build_market_prompt_brief(
    message: str,
    onboarding: dict[str, Any] | None,
    market_signals: list[dict[str, Any]],
    web_research: list[dict[str, str]],
) -> dict[str, Any]:
    brief = _market_brief(message, onboarding, market_signals, web_research)
    evidence: list[str] = []
    for item in market_signals[:3]:
        role = normalize_text(str(item.get("role_name") or ""))
        demand_summary = normalize_text(str(item.get("demand_summary") or item.get("summary") or ""))
        if role and demand_summary:
            evidence.append(_clip_words(f"{role}: {demand_summary}", 18))
    for item in web_research[:2]:
        title = normalize_text(str(item.get("title") or ""))
        snippet = normalize_text(str(item.get("snippet") or ""))
        if title and snippet:
            evidence.append(_clip_words(f"{title}: {snippet}", 18))
    return {
        "track": brief.get("track"),
        "top_skills": (brief.get("top_skills") or [])[:4],
        "role_hints": (brief.get("role_hints") or [])[:3],
        "source_names": (brief.get("source_names") or [])[:3],
        "summary": (brief.get("summary") or [])[:3],
        "evidence": evidence[:4],
    }


def _build_response_contract(intent: MentorIntent, onboarding: dict[str, Any] | None) -> dict[str, Any]:
    policy = INTENT_RESPONSE_POLICIES.get(intent, INTENT_RESPONSE_POLICIES["general_guidance"])
    decision_rules = [
        "Chon 1 uu tien chinh duy nhat.",
        "Neu thieu du lieu, van khuyen nghi theo du lieu hien co va ghi ro 'Gia dinh dang dung: ...'.",
        "Decision_summary.reason phai bam target_role, desired_outcome, current_challenges hoac learning_constraints.",
        "Decision_summary.next_action phai lam duoc trong 7 ngay.",
        "Recommended_learning_steps toi da 3 buoc, moi buoc 1 cau.",
        "Skill_gaps phai co 2-4 ky nang cu the neu cau hoi lien quan den nang luc.",
    ]
    if intent == "general_guidance":
        decision_rules = [
            "Tra loi truc dien dung cau hoi hien tai truoc.",
            "Chi dua next action neu cau hoi thuc su can hanh dong, roadmap, skill gap, market hoac career.",
            "USER_PROFILE_DIGEST va MARKET_BRIEF chi la bo tro; neu khong lien quan thi bo qua.",
            "Decision_summary duoc phep dong vai tro tom tat cau tra loi chinh thay vi mot ke hoach hanh dong.",
            "Recommended_learning_steps va skill_gaps co the de rong neu cau hoi khong can.",
        ]
    return {
        "intent": intent,
        "primary_goal": policy["primary_goal"],
        "must_include": policy["must_include"],
        "avoid": policy["avoid"],
        "answer_limit_words": MAX_ANSWER_WORDS,
        "max_parallel_options": 3,
        "required_schema_fields": [
            "answer",
            "decision_summary",
            "career_paths",
            "market_signals",
            "skill_gaps",
            "recommended_learning_steps",
            "suggested_followups",
            "memory_updates",
            "sources",
        ],
        "decision_rules": decision_rules,
        "forbidden_generic_phrases": list(FORBIDDEN_GENERIC_PHRASES),
        "daily_study_minutes": int((onboarding or {}).get("daily_study_minutes") or 30),
    }


def _fallback_sources(market_signals: list[dict[str, Any]], web_research: list[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in market_signals[:4]:
        url = normalize_text(str(item.get("source_url") or ""))
        label = normalize_text(str(item.get("source_name") or item.get("role_name") or "Nguồn thị trường"))
        if url and url not in seen:
            seen.add(url)
            result.append({"label": label, "url": url})
    for item in web_research[:4]:
        url = normalize_text(str(item.get("url") or ""))
        label = normalize_text(str(item.get("title") or item.get("source_name") or "Nguồn web"))
        if url and url not in seen:
            seen.add(url)
            result.append({"label": label, "url": url})
    return result[:6]


def _normalize_items(raw_items: object, field_map: dict[str, str]) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []
    items: list[dict[str, Any]] = []
    for item in raw_items[:6]:
        if not isinstance(item, dict):
            continue
        cleaned: dict[str, Any] = {}
        for source_key, target_key in field_map.items():
            value = item.get(source_key)
            cleaned[target_key] = (
                _normalize_list_of_strings(value, 6, max_words=8, clip=False)
                if isinstance(value, list)
                else normalize_text(str(value or ""))
            )
        items.append(cleaned)
    return items


def _normalize_memory_updates(raw_updates: object) -> list[dict[str, Any]]:
    if not isinstance(raw_updates, list):
        return []
    allowed = {"goal", "constraint", "skill", "career_interest", "preference", "fact", "summary"}
    updates: list[dict[str, Any]] = []
    for item in raw_updates[:8]:
        if not isinstance(item, dict):
            continue
        memory_type = normalize_text(str(item.get("memory_type") or "fact"))
        memory_key = normalize_text(str(item.get("memory_key") or ""))
        if memory_type not in allowed or not memory_key:
            continue
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.8))))
        except (TypeError, ValueError):
            confidence = 0.8
        updates.append({"memory_type": memory_type, "memory_key": memory_key, "memory_value": item.get("memory_value"), "confidence": confidence})
    return updates


def _normalize_gap_level(value: object) -> str:
    level = strip_accents(normalize_text(str(value or "medium"))).lower()
    if level in {"high", "medium", "low"}:
        return level
    if level in {"cao", "rat cao"}:
        return "high"
    if level in {"thap"}:
        return "low"
    return "medium"


def _enforce_response_contract(
    result: dict[str, Any],
    intent: MentorIntent,
    onboarding: dict[str, Any] | None,
    market_signals: list[dict[str, Any]],
    web_research: list[dict[str, str]],
) -> dict[str, Any]:
    result["answer"] = _normalize_answer_text(result.get("answer"))

    career_paths: list[dict[str, Any]] = []
    for item in (result.get("career_paths") or [])[:3]:
        if not isinstance(item, dict):
            continue
        role = normalize_text(str(item.get("role") or ""))
        if not role:
            continue
        career_paths.append(
            {
                "role": normalize_text(role),
                "fit_reason": normalize_text(str(item.get("fit_reason") or "")),
                "entry_level": normalize_text(str(item.get("entry_level") or "")),
                "required_skills": _normalize_list_of_strings(
                    item.get("required_skills"),
                    4,
                    max_words=4,
                    clip=False,
                ),
                "next_step": normalize_text(str(item.get("next_step") or "")),
            }
        )
    result["career_paths"] = career_paths

    normalized_market_signals: list[dict[str, Any]] = []
    for item in (result.get("market_signals") or [])[:3]:
        if not isinstance(item, dict):
            continue
        role_name = normalize_text(str(item.get("role_name") or ""))
        if not role_name:
            continue
        normalized_market_signals.append(
            {
                "role_name": normalize_text(role_name),
                "demand_summary": normalize_text(str(item.get("demand_summary") or "")),
                "top_skills": _normalize_list_of_strings(
                    item.get("top_skills"),
                    4,
                    max_words=4,
                    clip=False,
                ),
                "source_name": normalize_text(str(item.get("source_name") or "")),
                "source_url": normalize_text(str(item.get("source_url") or "")),
            }
        )
    result["market_signals"] = normalized_market_signals or _build_market_signal_fallback(
        message,
        onboarding,
        market_signals,
        web_research,
    )

    skill_gaps: list[dict[str, Any]] = []
    for item in (result.get("skill_gaps") or [])[:4]:
        if not isinstance(item, dict):
            continue
        skill = normalize_text(str(item.get("skill") or ""))
        if not skill:
            continue
        skill_gaps.append(
            {
                "skill": normalize_text(skill),
                "gap_level": _normalize_gap_level(item.get("gap_level")),
                "why_it_matters": normalize_text(str(item.get("why_it_matters") or "")),
                "suggested_action": normalize_text(str(item.get("suggested_action") or "")),
            }
        )
    result["skill_gaps"] = skill_gaps

    result["recommended_learning_steps"] = _normalize_list_of_strings(
        result.get("recommended_learning_steps"),
        3,
        max_words=MAX_STEP_WORDS,
        clip=False,
    )
    if not result["recommended_learning_steps"]:
        result["recommended_learning_steps"] = [
            normalize_text(str(item.get("suggested_action") or ""))
            for item in result["skill_gaps"][:3]
            if normalize_text(str(item.get("suggested_action") or ""))
        ][:3]

    result["suggested_followups"] = _normalize_list_of_strings(
        result.get("suggested_followups"),
        3,
        max_words=MAX_FOLLOWUP_WORDS,
        clip=False,
    )
    result["sources"] = _normalize_sources(result.get("sources")) or _fallback_sources(market_signals, web_research)
    result = _align_result_to_target_role(result, onboarding, intent=intent)
    result["decision_summary"] = _build_decision_summary(result, onboarding, intent=intent)

    if intent == "market_outlook":
        result["recommended_learning_steps"] = result["recommended_learning_steps"][:2] or [
            "Kiểm chứng 5 JD gần nhất cho vai trò mục tiêu.",
            "Đối chiếu bộ kỹ năng của bạn với nhóm kỹ năng đang được nhắc nhiều.",
        ]
    return result


def _align_result_to_target_role(
    result: dict[str, Any],
    onboarding: dict[str, Any] | None,
    *,
    intent: MentorIntent = "career_fit",
) -> dict[str, Any]:
    onboarding = onboarding or {}
    if intent == "general_guidance":
        return result
    target_role = strip_accents(normalize_text(str(onboarding.get("target_role") or ""))).lower()
    if "business analyst" not in target_role:
        return result

    if not result.get("career_paths"):
        result["career_paths"] = [
            {
                "role": "Business Analyst",
                "fit_reason": "Phù hợp với mục tiêu hiện tại cần tư duy business, requirement và giao tiếp stakeholder.",
                "entry_level": "Intern / Fresher / Junior",
                "required_skills": [
                    "Requirement analysis",
                    "Process mapping",
                    "Stakeholder communication",
                    "Documentation",
                ],
                "next_step": "Hoàn thành 1 case study gồm problem, user story, process flow và acceptance criteria.",
            }
        ]
    if not result.get("skill_gaps"):
        result["skill_gaps"] = [
            {
                "skill": "Requirement analysis",
                "gap_level": "high",
                "why_it_matters": "Đây là kỹ năng lõi để biến nhu cầu business thành yêu cầu rõ ràng.",
                "suggested_action": "Viết 1 bộ user story và acceptance criteria cho một bài toán đơn giản.",
            },
            {
                "skill": "Process mapping",
                "gap_level": "high",
                "why_it_matters": "BA cần nhìn được luồng nghiệp vụ hiện tại và luồng đề xuất sau cải tiến.",
                "suggested_action": "Vẽ 1 process flow AS-IS/TO-BE cho cùng một tình huống thực tế.",
            },
            {
                "skill": "Stakeholder communication",
                "gap_level": "medium",
                "why_it_matters": "BA không chỉ viết tài liệu mà còn phải khai thác và làm rõ nhu cầu từ nhiều phía.",
                "suggested_action": "Luyện 5-7 câu hỏi khai thác yêu cầu và gắn chúng vào case study của bạn.",
            },
        ]
    if not result.get("recommended_learning_steps"):
        result["recommended_learning_steps"] = [
            "Tuần 1: học requirement analysis và viết user story cho một tình huống thực tế.",
            "Tuần 2: vẽ process flow AS-IS/TO-BE và giải thích được logic nghiệp vụ.",
            "Trong 7 ngày tới: hoàn thành 1 tài liệu ngắn gồm problem, user story và acceptance criteria.",
        ]
    if not result.get("suggested_followups"):
        result["suggested_followups"] = [
            "Business Analyst mới bắt đầu nên học user story trước hay process mapping trước?",
            "Một portfolio BA đầu tiên nên gồm những artefact nào?",
            "SQL cho BA nên học đến mức nào trong giai đoạn nền tảng?",
        ]
    return result


def _fallback_market_signals(web_research: list[dict[str, str]]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for item in web_research[:3]:
        title = normalize_text(str(item.get("title") or ""))
        snippet = normalize_text(str(item.get("snippet") or ""))
        if not title or not snippet:
            continue
        signals.append(
            {
                "role_name": title[:72],
                "demand_summary": snippet[:240],
                "top_skills": [],
                "source_name": normalize_text(str(item.get("source_name") or "")),
                "source_url": normalize_text(str(item.get("url") or "")),
            }
        )
    return signals


def _legacy_prune_result_for_intent(result: dict[str, Any], intent: MentorIntent) -> dict[str, Any]:
    pruned = dict(result)
    if intent == "market_outlook":
        pruned["career_paths"] = []
        pruned["skill_gaps"] = []
        pruned["recommended_learning_steps"] = (pruned.get("recommended_learning_steps") or [])[:2]
    elif intent == "skill_gap":
        pruned["career_paths"] = []
        pruned["market_signals"] = []
        pruned["skill_gaps"] = (pruned.get("skill_gaps") or [])[:3]
        pruned["recommended_learning_steps"] = (pruned.get("recommended_learning_steps") or [])[:3]
    elif intent == "learning_roadmap":
        pruned["career_paths"] = []
        pruned["market_signals"] = []
        pruned["skill_gaps"] = []
        pruned["recommended_learning_steps"] = (pruned.get("recommended_learning_steps") or [])[:3]
    elif intent in {"career_fit", "career_roles"}:
        pruned["career_paths"] = (pruned.get("career_paths") or [])[:3]
        pruned["market_signals"] = []
        pruned["skill_gaps"] = (pruned.get("skill_gaps") or [])[:3]
        pruned["recommended_learning_steps"] = (pruned.get("recommended_learning_steps") or [])[:3]
    return pruned


def _answer_matches_intent(
    answer: str,
    intent: MentorIntent,
    result: dict[str, Any] | None,
) -> bool:
    text = strip_accents(normalize_text(answer)).lower()
    if not text:
        return False

    if intent == "market_outlook":
        return (
            any(token in text for token in ("thi truong", "nhu cau", "tuyen dung", "jd"))
            and len((result or {}).get("market_signals") or []) >= 1
        )
    if intent == "skill_gap":
        gap_names = [
            strip_accents(normalize_text(str(item.get("skill") or ""))).lower()
            for item in ((result or {}).get("skill_gaps") or [])
            if normalize_text(str(item.get("skill") or ""))
        ]
        return len(gap_names) >= 2 and any(gap in text for gap in gap_names[:2])
    if intent == "learning_roadmap":
        return len((result or {}).get("recommended_learning_steps") or []) >= 3 and any(
            token in text for token in ("buoc", "tuan", "thu tu", "roadmap", "lo trinh")
        )
    if intent in {"career_fit", "career_roles"}:
        roles = [
            strip_accents(normalize_text(str(item.get("role") or ""))).lower()
            for item in ((result or {}).get("career_paths") or [])
            if normalize_text(str(item.get("role") or ""))
        ]
        return len(roles) >= 1 and any(role in text for role in roles[:2])
    return True


def _should_replace_answer_with_structured_fallback(
    answer: str,
    intent: MentorIntent,
    result: dict[str, Any] | None,
) -> bool:
    normalized = normalize_text(answer)
    if not normalized:
        return True
    lowered = strip_accents(normalized).lower()
    if normalized.endswith("...") or normalized.endswith("…"):
        return True
    if any(marker in lowered for marker in GENERIC_MARKERS):
        return True
    if any(phrase in lowered for phrase in FORBIDDEN_GENERIC_PHRASES):
        return True
    if intent != "general_guidance" and len(normalized.split()) < 16:
        return True
    if result and not _answer_matches_intent(normalized, intent, result):
        return True
    return False


def _legacy_build_decision_summary_v1(
    result: dict[str, Any],
    onboarding: dict[str, Any] | None,
    *,
    intent: MentorIntent = "general_guidance",
) -> dict[str, str]:
    onboarding = onboarding or {}
    raw_summary = result.get("decision_summary") if isinstance(result.get("decision_summary"), dict) else {}
    if intent == "general_guidance":
        answer = normalize_text(str(result.get("answer") or ""))
        first_sentence = normalize_text(re.split(r"(?<=[.!?])\s+", answer, maxsplit=1)[0]) if answer else ""
        headline = first_sentence or "Câu trả lời đã được chốt theo đúng câu hỏi hiện tại."
        priority_value = _first_text(
            raw_summary.get("priority_value"),
            first_sentence,
            normalize_text(str(onboarding.get("target_role") or "")),
            "Trọng tâm kiến thức",
        )
        reason = _first_text(
            raw_summary.get("reason"),
            "Câu trả lời này ưu tiên bám thẳng vào câu hỏi hiện tại thay vì kéo sang tư vấn nghề nghiệp.",
        )
        next_action = _first_text(
            raw_summary.get("next_action"),
            "Đối chiếu thêm một ví dụ hoặc trường hợp ngược để kiểm tra ranh giới áp dụng.",
        )
        return {
            "headline": _prefer_summary_field(raw_summary.get("headline"), headline),
            "priority_label": _prefer_summary_field(raw_summary.get("priority_label"), "Trọng tâm câu trả lời"),
            "priority_value": _prefer_summary_field(raw_summary.get("priority_value"), priority_value),
            "reason": _prefer_summary_field(raw_summary.get("reason"), reason),
            "next_action": _prefer_summary_field(raw_summary.get("next_action"), next_action),
            "confidence_note": _prefer_summary_field(
                raw_summary.get("confidence_note"),
                "Câu trả lời này ưu tiên bám câu hỏi hiện tại hơn là hồ sơ học tập.",
            ),
        }

    return _legacy_build_decision_summary_v2(result, onboarding)


def _legacy_low_signal_v1(
    answer: str,
    message: str,
    onboarding: dict[str, Any] | None,
    result: dict[str, Any] | None = None,
) -> bool:
    text = strip_accents(normalize_text(answer)).lower()
    if not text:
        return True
    intent = detect_mentor_intent(message)
    if any(marker in text for marker in GENERIC_MARKERS):
        return True
    if any(phrase in text for phrase in FORBIDDEN_GENERIC_PHRASES):
        return True
    if mentor_logic.is_profile_lookup_question(message) and mentor_logic.answer_denies_profile_access(answer):
        return True
    if mentor_logic.is_profile_lookup_question(message) and mentor_logic.answer_denies_profile_access(answer):
        return True
    track = _track(message, onboarding)
    if (
        track != "general"
        and intent in {"market_outlook", "skill_gap", "learning_roadmap", "career_fit", "career_roles"}
        and not any(strip_accents(skill).lower() in text for skill in SKILL_CATALOG[track][:6])
    ):
        if len(text.split()) < 90:
            return True
    question = strip_accents(normalize_text(message)).lower()
    if (
        intent in {"skill_gap", "learning_roadmap", "career_fit", "career_roles"}
        and any(token in question for token in ("hoc gi", "can gi", "ky nang", "lo trinh"))
        and len(text.split()) < 70
    ):
        return True
    if len(text.split()) > MAX_ANSWER_WORDS + 20:
        return True
    if result:
        if not result.get("decision_summary"):
            return True
        if intent == "general_guidance":
            return len(text.split()) < 24 or not _answer_matches_intent(answer, intent, result)
        if intent == "market_outlook" and len(result.get("market_signals") or []) < 1:
            return True
        if intent == "skill_gap":
            if len(result.get("skill_gaps") or []) < 2:
                return True
            if len(result.get("recommended_learning_steps") or []) < 1:
                return True
        if intent == "learning_roadmap" and len(result.get("recommended_learning_steps") or []) < 3:
            return True
        if intent in {"career_fit", "career_roles"} and len(result.get("career_paths") or []) < 1:
            return True
        if (
            intent in {"skill_gap", "learning_roadmap"}
            and any(token in question for token in ("ky nang", "skill", "lo trinh", "roadmap"))
            and len(result.get("skill_gaps") or []) < 2
        ):
            return True
        if track != "general" and intent in {"skill_gap", "learning_roadmap", "career_fit", "career_roles"}:
            concrete_skills = {
                strip_accents(normalize_text(str(item.get("skill") or ""))).lower()
                for item in (result.get("skill_gaps") or [])
                if normalize_text(str(item.get("skill") or ""))
            }
            if len(concrete_skills) < 2:
                return True
        if not _answer_matches_intent(answer, intent, result):
            return True
    return False


def _merge(primary: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    merged = dict(primary)
    for key in ("career_paths", "market_signals", "skill_gaps", "recommended_learning_steps", "suggested_followups", "sources"):
        if not merged.get(key):
            merged[key] = fallback.get(key, [])
    if not merged.get("answer"):
        merged["answer"] = fallback.get("answer", "")
    if not merged.get("decision_summary"):
        merged["decision_summary"] = fallback.get("decision_summary")
    return merged


def _legacy_build_decision_summary_v2(result: dict[str, Any], onboarding: dict[str, Any] | None) -> dict[str, str]:
    onboarding = onboarding or {}
    raw_summary = result.get("decision_summary") if isinstance(result.get("decision_summary"), dict) else {}
    target_role = normalize_text(
        str(
            onboarding.get("target_role")
            or (result.get("career_paths") or [{}])[0].get("role")
            or "vai trò mục tiêu hiện tại"
        )
    )
    desired_outcome = normalize_text(str(onboarding.get("desired_outcome") or ""))
    current_challenges = normalize_text(str(onboarding.get("current_challenges") or ""))
    current_focus = normalize_text(str(onboarding.get("current_focus") or ""))
    learning_constraints = normalize_text(str(onboarding.get("learning_constraints") or ""))
    daily = int(onboarding.get("daily_study_minutes") or 30)

    top_gap = normalize_text(
        str(
            ((result.get("skill_gaps") or [{}])[0].get("skill"))
            or ((result.get("recommended_learning_steps") or [""])[0])
            or "khối kỹ năng ưu tiên"
        )
    )
    next_action = normalize_text(
        str(
            ((result.get("skill_gaps") or [{}])[0].get("suggested_action"))
            or ((result.get("recommended_learning_steps") or [""])[0])
            or "Mở roadmap và thực hiện bước học tiếp theo"
        )
    )

    if desired_outcome:
        headline = f"Ưu tiên {top_gap} để tiến gần mục tiêu {desired_outcome}."
    else:
        headline = f"Ưu tiên {top_gap} để tiến gần vai trò {target_role}."

    reason_parts: list[str] = []
    if current_focus:
        reason_parts.append(f"Bạn đang tập trung vào {current_focus}")
    if current_challenges:
        reason_parts.append(f"Nút thắt hiện tại là {current_challenges}")
    if learning_constraints:
        reason_parts.append(f"Cần giữ đúng ràng buộc {learning_constraints}")
    if not reason_parts:
        reason_parts.append(f"Quỹ học hiện tại là khoảng {daily} phút mỗi ngày")

    context_count = sum(
        1
        for value in (
            onboarding.get("target_role"),
            onboarding.get("desired_outcome"),
            onboarding.get("current_focus"),
            onboarding.get("current_challenges"),
            onboarding.get("learning_constraints"),
        )
        if normalize_text(str(value or ""))
    )
    confidence_note = (
        "Đã bám đủ bối cảnh mục tiêu, đầu ra và ràng buộc học tập."
        if context_count >= 4
        else "Nên bổ sung hồ sơ thêm một chút để mentor khóa ưu tiên sát hơn."
    )

    return {
        "headline": normalize_text(str(raw_summary.get("headline") or headline)),
        "priority_label": normalize_text(
            str(raw_summary.get("priority_label") or f"Gấp ưu tiên cho {target_role}")
        ),
        "priority_value": normalize_text(str(raw_summary.get("priority_value") or top_gap)),
        "reason": normalize_text(str(raw_summary.get("reason") or ". ".join(reason_parts) + ".")),
        "next_action": normalize_text(str(raw_summary.get("next_action") or next_action)),
        "confidence_note": normalize_text(str(raw_summary.get("confidence_note") or confidence_note)),
    }
def _build_prompt_profile_brief(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    analytics: dict[str, Any] | None,
    memories: list[dict[str, Any]],
    intent: MentorIntent,
) -> dict[str, Any]:
    profile_brief = _build_profile_brief(profile, onboarding, analytics, memories)
    if intent != "general_guidance":
        return profile_brief
    return {
        "display_name": profile_brief.get("display_name"),
        "target_role": profile_brief.get("target_role"),
        "current_focus": profile_brief.get("current_focus"),
        "desired_outcome": profile_brief.get("desired_outcome"),
        "learning_constraints": profile_brief.get("learning_constraints"),
        "context_usage": "optional_only_when_it_improves_example_or_clarity",
    }


def _build_prompt_market_brief(
    message: str,
    onboarding: dict[str, Any] | None,
    market_signals: list[dict[str, Any]],
    web_research: list[dict[str, str]],
    intent: MentorIntent,
) -> dict[str, Any]:
    if intent == "general_guidance":
        return {
            "context_usage": "ignore_for_objective_knowledge_questions",
            "track": "",
            "top_skills": [],
            "role_hints": [],
            "source_names": [],
            "summary": [],
            "evidence": [],
        }
    return _build_market_prompt_brief(message, onboarding, market_signals, web_research)


def _build_prompt_current_question(
    message: str,
    intent: MentorIntent,
    recent_messages: list[dict[str, Any]],
    recent_sessions: list[dict[str, Any]],
    onboarding: dict[str, Any] | None,
) -> dict[str, Any]:
    current_question = _build_current_question_payload(
        message,
        intent,
        recent_messages,
        recent_sessions,
        onboarding,
    )
    current_question["question_type"] = current_question.get("question_type") or mentor_logic.mentor_question_type(message)
    current_question["focus_topic"] = current_question.get("focus_topic") or mentor_logic.mentor_focus_topic(message)
    current_question["comparison_targets"] = current_question.get("comparison_targets") or list(
        mentor_logic.mentor_compare_subjects(message) or ()
    )
    current_question["context_mode"] = current_question.get("context_mode") or (
        "knowledge_first" if intent == "general_guidance" else "mentor_guidance"
    )
    if current_question.get("use_profile_context") is None:
        current_question["use_profile_context"] = mentor_logic.should_use_profile_context(intent, message)
    if current_question.get("use_market_context") is None:
        current_question["use_market_context"] = mentor_logic.should_use_market_context(intent)
    if current_question.get("profile_grounding_required") is None:
        current_question["profile_grounding_required"] = mentor_logic.is_profile_lookup_question(message)
    if not current_question.get("requested_profile_fields"):
        current_question["requested_profile_fields"] = mentor_logic.profile_lookup_requested_fields(message)
    current_question["response_outline"] = current_question.get("response_outline") or current_question.get(
        "must_answer"
    ) or []
    return current_question


def build_mentor_prompt(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    analytics: dict[str, Any] | None,
    recent_sessions: list[dict[str, Any]],
    memories: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    market_signals: list[dict[str, Any]],
    web_research: list[dict[str, str]],
    intent: MentorIntent,
    message: str,
) -> str:
    current_question = _build_prompt_current_question(message, intent, messages, recent_sessions, onboarding)
    if current_question.get("profile_grounding_required"):
        profile_brief = _build_profile_brief(profile, onboarding, analytics, memories)
    else:
        profile_brief = _build_prompt_profile_brief(profile, onboarding, analytics, memories, intent)
    market_brief = _build_prompt_market_brief(message, onboarding, market_signals, web_research, intent)
    response_contract = _build_response_contract(intent, onboarding)
    return MENTOR_RESPONSE_PROMPT.format(
        profile_brief_json=json.dumps(profile_brief, ensure_ascii=False, indent=2),
        current_question_json=json.dumps(current_question, ensure_ascii=False, indent=2),
        market_brief_json=json.dumps(market_brief, ensure_ascii=False, indent=2),
        response_contract_json=json.dumps(response_contract, ensure_ascii=False, indent=2),
    )


def _build_rewrite_prompt(
    message: str,
    intent: MentorIntent,
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    analytics: dict[str, Any] | None,
    recent_sessions: list[dict[str, Any]],
    recent_messages: list[dict[str, Any]],
    memories: list[dict[str, Any]],
    market_signals: list[dict[str, Any]],
    web_research: list[dict[str, str]],
    draft_answer: str,
) -> str:
    current_question = _build_prompt_current_question(
        message,
        intent,
        recent_messages,
        recent_sessions,
        onboarding,
    )
    if current_question.get("profile_grounding_required"):
        profile_brief = _build_profile_brief(profile, onboarding, analytics, memories)
    else:
        profile_brief = _build_prompt_profile_brief(profile, onboarding, analytics, memories, intent)
    market_brief = _build_prompt_market_brief(message, onboarding, market_signals, web_research, intent)
    response_contract = _build_response_contract(intent, onboarding)
    return MENTOR_RESPONSE_REWRITE_PROMPT.format(
        profile_brief_json=json.dumps(profile_brief, ensure_ascii=False, indent=2),
        current_question_json=json.dumps(current_question, ensure_ascii=False, indent=2),
        market_brief_json=json.dumps(market_brief, ensure_ascii=False, indent=2),
        response_contract_json=json.dumps(response_contract, ensure_ascii=False, indent=2),
        draft_answer=draft_answer,
    )


def _build_personalized_fallback_base(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    intent: MentorIntent,
    message: str,
    market_signals: list[dict[str, Any]] | None = None,
    web_research: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    onboarding = onboarding or {}
    market_signals = market_signals or []
    web_research = web_research or []
    status = normalize_text(str(onboarding.get("status") or ""))
    major = normalize_text(str(onboarding.get("major") or ""))
    industry = normalize_text(str(onboarding.get("industry") or ""))
    job_title = normalize_text(str(onboarding.get("job_title") or ""))
    desired_outcome = normalize_text(str(onboarding.get("desired_outcome") or ""))
    current_focus = normalize_text(str(onboarding.get("current_focus") or ""))
    current_challenges = normalize_text(str(onboarding.get("current_challenges") or ""))
    learning_constraints = normalize_text(str(onboarding.get("learning_constraints") or ""))
    daily = int(onboarding.get("daily_study_minutes") or 30)
    track = _track(message, onboarding)
    market_brief = _market_brief(message, onboarding, market_signals, web_research)
    top_skills = market_brief["top_skills"][:5]
    source_names = market_brief["source_names"][:3]
    source_hint = f" Theo các tín hiệu mình quét được từ {', '.join(source_names)}, nhóm kỹ năng nổi lên là {', '.join(top_skills[:4])}." if source_names else ""
    outcome_hint = f" Đầu ra bạn đang muốn đạt là: {desired_outcome}." if desired_outcome else ""
    challenge_hint = f" Khó khăn nổi bật hiện tại là: {current_challenges}." if current_challenges else ""
    constraint_hint = f" Mentor cần giữ đúng ràng buộc này khi đề xuất lộ trình: {learning_constraints}." if learning_constraints else ""
    context_bits = [bit for bit in [("bạn đang là sinh viên" if status == "student" else "bạn đang đi làm" if status == "working" else "bạn vừa học vừa làm" if status == "both" else ""), f"nền tảng {major}" if major else "", f"ngành {industry}" if industry else "", f"vai trò hiện tại {job_title}" if job_title else ""] if bit]
    prefix = f"Với việc {', '.join(context_bits)}, " if context_bits else ""

    if track == "dev":
        answer = (
            f"{prefix}nếu bạn đi theo hướng dev thì nên học theo 4 khối kiến thức, không học dàn trải.\n\n"
            f"- Khối 1: nền tảng lập trình và tư duy giải quyết vấn đề, ưu tiên một ngôn ngữ chính như JavaScript hoặc Python.\n"
            f"- Khối 2: web fundamentals gồm HTML/CSS, JavaScript, Git/GitHub và cách làm việc với API.\n"
            f"- Khối 3: một nhánh đủ sâu để tạo đầu ra, thường nên bắt đầu bằng frontend với React nếu bạn muốn thấy sản phẩm nhanh.\n"
            f"- Khối 4: project thật, vì nhà tuyển dụng nhìn vào khả năng build sản phẩm chứ không chỉ nhìn khóa học đã xem.{source_hint}{outcome_hint}{challenge_hint}{constraint_hint}\n\n"
            f"Với quỹ thời gian khoảng {daily} phút mỗi ngày, hợp lý nhất là chia phần lớn thời gian cho code và project. Trong 6-8 tuần đầu, mục tiêu nên là làm được 2 project nhỏ có Git, form, gọi API và deploy được.{f' Trọng tâm bạn đang theo là {current_focus}.' if current_focus else ''}"
        )
        steps = [
            "Tuần 1-2: học chắc JavaScript hoặc Python và Git/GitHub.",
            "Tuần 3-4: học HTML/CSS, DOM và cách gọi API cơ bản.",
            "Tuần 5-8: làm 2 project nhỏ rồi mới học framework như React hoặc Next.js.",
        ]
        followups = [
            "Nếu tôi ưu tiên frontend trước, stack nào vừa đủ mạnh mà không quá nặng?",
            "Portfolio dev đầu tiên của tôi nên gồm những project nào?",
            f"Với {daily} phút mỗi ngày, tôi nên chia lịch học dev theo tuần ra sao?",
        ]
    elif track == "business":
        answer = (
            f"{prefix}neu ban theo Business Analyst thi uu tien dung thu tu: hieu business -> viet requirement -> mo hinh hoa quy trinh -> giao tiep voi stakeholder. "
            f"Khong nen lao ngay vao qua nhieu cong cu ky thuat neu nen tang BA chua chac.{source_hint}{outcome_hint}{challenge_hint}{constraint_hint}\n\n"
            f"- Buoc dau la requirement analysis va user story de biet cach bien nhu cau thanh tai lieu ro rang.\n"
            f"- Sau do hoc process mapping, flow, use case va cac cach mo ta nghiep vu de tranh hoc ly thuyet roi rac.\n"
            f"- Tiep theo la stakeholder communication va documentation vi day la phan BA dung hang ngay.\n"
            f"- SQL nen hoc o muc co ban de doc du lieu va ho tro phan tich, nhung khong phai diem bat dau duy nhat.\n\n"
            f"Voi {daily} phut moi ngay, dau ra hop ly trong 2 tuan dau la 1 bo user story, 1 process flow va 1 requirement note cho mot bai toan don gian.{f' Trong tam ban dang theo la {current_focus}.' if current_focus else ''}"
        )
        steps = [
            "Tuần 1: học requirement analysis và viết user story cho một tình huống thực tế.",
            "Tuần 2: vẽ process flow AS-IS/TO-BE cho cùng bài toán và giải thích được logic.",
            "Trong 7 ngày tới: hoàn thành 1 tài liệu ngắn gồm problem, user story và acceptance criteria.",
        ]
        followups = [
            "Business Analyst mới bắt đầu nên học user story trước hay process mapping trước?",
            "Một portfolio BA đầu tiên nên gồm những artefact nào để dễ chứng minh năng lực?",
            "SQL cho BA nên học đến mức nào trong giai đoạn nền tảng?",
        ]
    elif track == "data":
        answer = (
            f"{prefix}nếu bạn theo Data Analyst thì đừng bắt đầu từ quá nhiều công cụ. Hãy đi theo chuỗi: xử lý dữ liệu -> phân tích -> trực quan hóa -> kể chuyện bằng dữ liệu.\n\n"
            f"- Bước đầu là Excel hoặc Google Sheets để làm sạch dữ liệu và hiểu cấu trúc bảng.\n"
            f"- Sau đó học SQL thật chắc vì đây là kỹ năng gần như bắt buộc cho hầu hết vị trí data đầu vào.\n"
            f"- Tiếp theo là Power BI hoặc Tableau để biến dữ liệu thành dashboard có insight.\n"
            f"- Cuối cùng là tư duy business: đọc số để đưa ra đề xuất chứ không chỉ trình bày biểu đồ.{source_hint}{outcome_hint}{challenge_hint}{constraint_hint}\n\n"
            f"Nếu học đều {daily} phút mỗi ngày, bạn nên ưu tiên đầu ra là 1 dashboard hoàn chỉnh từ dữ liệu thật và 1 case viết insight rõ ràng.{f' Trọng tâm bạn đang theo là {current_focus}.' if current_focus else ''}"
        )
        steps = [
            "Tuần 1-2: làm sạch dữ liệu và thao tác thành thạo trên Excel hoặc Google Sheets.",
            "Tuần 3-4: học SQL theo hướng query thật, join, group và filter.",
            "Tuần 5-8: dựng dashboard Power BI/Tableau và viết insight từ dữ liệu.",
        ]
        followups = [
            "Nếu tôi theo Data Analyst, tôi nên học SQL đến mức nào trước khi làm dashboard?",
            "Portfolio data nên có những project nào để dễ xin intern hoặc junior?",
            "Tôi nên học Excel trước hay Power BI trước?",
        ]
    else:
        answer = (
            f"{prefix}hướng đi tốt nhất lúc này là chọn một nhánh nghề đủ rõ, rồi học theo thứ tự từ nền tảng -> đầu ra -> tối ưu, thay vì ôm quá nhiều thứ một lúc.\n\n"
            f"- Trước hết, hãy bám vào nhóm kỹ năng tạo đầu ra gần nhất với mục tiêu nghề nghiệp của bạn.\n"
            f"- Sau đó ưu tiên 3 nhóm năng lực: nền tảng chuyên môn, công cụ làm việc và một project hoặc sản phẩm có thể đem ra chứng minh.\n"
            f"- Cuối cùng mới mở rộng sang kỹ năng phụ hoặc các nhánh sâu hơn.{source_hint}{outcome_hint}{challenge_hint}{constraint_hint}\n\n"
            f"Nếu bạn đang phân vân giữa nhiều hướng, tiêu chí chọn nên là: hướng nào hợp nền tảng hiện có, tạo được đầu ra trong 1-3 tháng và có tín hiệu tuyển dụng rõ."
        )
        steps = [
            "Chốt một vai trò hoặc một nhánh nghề rõ ràng trong ngắn hạn.",
            "Liệt kê 3-5 kỹ năng nền tảng bắt buộc của nhánh đó rồi học theo thứ tự ưu tiên.",
            "Tạo một đầu ra thật như project, portfolio hoặc case study để chứng minh năng lực.",
        ]
        followups = [
            "Nếu bám đúng hồ sơ hiện tại của tôi, hướng nào dễ tạo lợi thế nhất?",
            "Tôi nên học phần nền tảng nào trước trong 6 tuần đầu?",
            "Đầu ra đầu tiên của tôi nên là project, portfolio hay case study?",
        ]
    if track == "dev":
        role_paths = [{"role": "Frontend Developer", "fit_reason": "Dễ tạo đầu ra nhanh qua project web.", "entry_level": "Intern / Junior", "required_skills": ["JavaScript", "HTML/CSS", "React", "Git"], "next_step": "Làm 2-3 project web nhỏ rồi tối ưu dần lên React + API."}]
    elif track == "business":
        role_paths = [{"role": "Business Analyst", "fit_reason": "Phù hợp với hướng đi cần tư duy business, requirement và giao tiếp stakeholder.", "entry_level": "Intern / Fresher / Junior", "required_skills": ["Requirement analysis", "Process mapping", "Stakeholder communication", "Documentation"], "next_step": "Hoàn thành 1 case study gồm problem, user story, process flow và acceptance criteria."}]
    elif track == "data":
        role_paths = [{"role": "Data Analyst", "fit_reason": "Có đầu ra rõ qua dashboard và case business.", "entry_level": "Intern / Junior", "required_skills": ["Excel", "SQL", "Power BI/Tableau"], "next_step": "Làm 1 dashboard hoàn chỉnh từ dữ liệu thật."}]
    else:
        role_paths = []
    skill_gaps = [{"skill": skill, "gap_level": "high" if index < 2 else "medium", "why_it_matters": "Đây là nhóm năng lực xuất hiện lặp lại trong tín hiệu nghề nghiệp.", "suggested_action": f"Ưu tiên học và tạo đầu ra nhỏ để chứng minh được {skill}."} for index, skill in enumerate((top_skills or SKILL_CATALOG.get(track, SKILL_CATALOG["general"]))[:4])]
    if intent == "market_outlook":
        role_hint = normalize_text(str(onboarding.get("target_role") or (role_paths[0]["role"] if role_paths else "")))
        if top_skills:
            market_headline = (
                f"Nhu cầu thị trường cho hướng {role_hint or 'bạn đang hỏi'} hiện đang xoay quanh "
                f"các nhóm kỹ năng {', '.join(top_skills[:3])}."
            )
        else:
            market_headline = (
                f"Thị trường của hướng {role_hint or 'bạn đang hỏi'} hiện chưa nghiêng về một kỹ năng đơn lẻ, "
                "mà đang ưu tiên bộ kỹ năng nền tảng đi kèm đầu ra thực hành."
            )
        answer = (
            f"{market_headline}{source_hint} "
            f"{'Đầu ra bạn đang muốn đạt là: ' + desired_outcome + '. ' if desired_outcome else ''}"
            "Trọng tâm lúc này là kiểm chứng JD gần nhất để chốt đúng kỹ năng thị trường đang gọi tên nhiều nhất."
        ).strip()
        steps = [
            "Trong 7 ngày tới, đối chiếu 5-7 JD gần nhất để chốt 3 nhóm kỹ năng bị nhắc lặp lại nhiều nhất.",
            "So hồ sơ hiện tại với 3 nhóm kỹ năng đó và ghi rõ phần nào đã có, phần nào còn thiếu.",
        ]
        followups = [
            "Với tín hiệu thị trường hiện tại, tôi nên ưu tiên kỹ năng nào trước?",
            "JD của vai trò mục tiêu đang nhắc lại công cụ hay đầu ra nào nhiều nhất?",
            "Từ tín hiệu này, tôi nên chỉnh roadmap học như thế nào?",
        ]
    elif intent == "skill_gap":
        prioritized_gaps = skill_gaps[:3]
        gap_names = ", ".join(item["skill"] for item in prioritized_gaps if item.get("skill"))
        answer = (
            f"Ba khoảng trống nên bù trước của bạn là {gap_names}. "
            f"Thứ tự này bám vào mục tiêu {onboarding.get('target_role') or 'hiện tại'} và tín hiệu kỹ năng đang lặp lại trên thị trường."
            f"{challenge_hint}{constraint_hint}"
        ).strip()
        steps = [item["suggested_action"] for item in prioritized_gaps if item.get("suggested_action")][:3]
        followups = [
            "Tôi nên bù skill nào trước để tạo đầu ra nhanh nhất?",
            "Mỗi skill gap này nên học đến mức nào là đủ cho giai đoạn hiện tại?",
            "Tôi nên làm project nào để chứng minh ba skill gap này?",
        ]
    elif intent == "learning_roadmap":
        answer = (
            f"Roadmap phù hợp lúc này là đi theo thứ tự nền tảng -> đầu ra thực hành -> tối ưu theo tín hiệu thị trường, "
            f"không học dàn trải song song quá nhiều mảng.{outcome_hint}{constraint_hint}"
        ).strip()
        steps = steps[:3]
        followups = [
            "Bước 1 của roadmap này nên học những gì trước?",
            "Đầu ra nào đủ tốt để chuyển sang bước 2?",
            "Với quỹ thời gian hiện tại, tôi nên chia roadmap theo tuần ra sao?",
        ]
    elif intent in {"career_fit", "career_roles"} and role_paths:
        answer = (
            f"Hướng nên ưu tiên trước là {role_paths[0]['role']}. "
            f"Lý do là hướng này bám sát hồ sơ hiện tại hơn và cho phép tạo đầu ra thực hành rõ hơn trong giai đoạn ngắn hạn."
            f"{outcome_hint}{challenge_hint}"
        ).strip()
        steps = steps[:3]

    fallback_result = {
        "intent": intent,
        "answer": answer,
        "career_paths": role_paths,
        "market_signals": _build_market_signal_fallback(
            message,
            onboarding,
            market_signals,
            web_research,
        ),
        "skill_gaps": skill_gaps,
        "recommended_learning_steps": steps,
        "suggested_followups": followups,
        "memory_updates": [],
        "sources": _fallback_sources(market_signals, web_research),
    }
    fallback_result = _enforce_response_contract(
        fallback_result,
        intent,
        onboarding,
        market_signals,
        web_research,
    )
    synthesized_answer = _compose_structured_answer(fallback_result, intent, onboarding)
    if synthesized_answer:
        fallback_result["answer"] = synthesized_answer
    return _prune_result_for_intent(fallback_result, intent)


_legacy_build_personalized_fallback = _build_personalized_fallback_base

def _first_text(*values: object) -> str:
    for value in values:
        text = normalize_text(str(value or ""))
        if text:
            return text
    return ""


def _join_readable(items: list[str], limit: int = 3) -> str:
    cleaned = [normalize_text(item) for item in items if normalize_text(item)]
    picked = cleaned[:limit]
    if not picked:
        return ""
    if len(picked) == 1:
        return picked[0]
    if len(picked) == 2:
        return f"{picked[0]} và {picked[1]}"
    return f"{', '.join(picked[:-1])} và {picked[-1]}"


def _priority_value_from_step(step: str) -> str:
    cleaned = normalize_text(step)
    if not cleaned:
        return "Bước 1"
    return " ".join(cleaned.split()[:8]).strip(" ,;:.") or "Bước 1"


def _prefer_summary_field(raw_value: object, fallback_value: str) -> str:
    raw = normalize_text(str(raw_value or ""))
    if not raw or raw.endswith("...") or raw.endswith("â€¦"):
        return fallback_value
    lowered = strip_accents(raw).lower()
    if any(marker in lowered for marker in GENERIC_MARKERS) or any(
        phrase in lowered for phrase in FORBIDDEN_GENERIC_PHRASES
    ):
        return fallback_value
    return raw


def detect_mentor_intent(message: str) -> MentorIntent:
    return mentor_logic.detect_mentor_intent(message)


def _mentor_focus_topic(message: str) -> str:
    return mentor_logic.mentor_focus_topic(message)


def _should_use_profile_context(intent: MentorIntent, message: str) -> bool:
    return mentor_logic.should_use_profile_context(intent, message)


def _should_use_market_context(intent: MentorIntent) -> bool:
    return mentor_logic.should_use_market_context(intent)


def _build_general_guidance_followups(
    message: str,
    focus_topic: str,
    compare_subjects: tuple[str, str] | None,
) -> list[str]:
    return mentor_logic.build_general_guidance_followups(message, focus_topic, compare_subjects)


def _build_current_question_payload(
    message: str,
    intent: MentorIntent,
    recent_messages: list[dict[str, Any]],
    recent_sessions: list[dict[str, Any]],
    onboarding: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized_message = normalize_text(message)
    question_type = mentor_logic.mentor_question_type(normalized_message)
    comparison_targets = list(mentor_logic.mentor_compare_subjects(normalized_message) or ())
    focus_topic = mentor_logic.mentor_focus_topic(normalized_message)
    context_mode = "knowledge_first" if intent == "general_guidance" else "mentor_guidance"
    use_profile_context = mentor_logic.should_use_profile_context(intent, normalized_message)
    use_market_context = mentor_logic.should_use_market_context(intent)
    profile_grounding_required = mentor_logic.is_profile_lookup_question(normalized_message)
    requested_profile_fields = mentor_logic.profile_lookup_requested_fields(normalized_message)

    if profile_grounding_required:
        main_request = (
            "Doc USER_PROFILE_DIGEST va tra loi truc tiep theo cac field he thong dang co. "
            "Khong duoc noi rang khong truy cap duoc ho so."
        )
        deliverable_type = "profile-grounded answer"
        must_answer = [
            "tra loi truc tiep tu ho so hien co",
            "field nao chua co thi noi ro la ho so hien tai chua co",
            "khong tu choi bang ly do khong truy cap duoc profile",
        ]
    elif intent == "market_outlook":
        main_request = "Kết luận thị trường đang cần gì trước, rồi mới nối sang tác động đến việc học."
        deliverable_type = "market-first answer"
        must_answer = [
            "mức độ nhu cầu hiện tại",
            "2-4 kỹ năng đang được nhắc nhiều",
            "1 hành động kiểm chứng trong 7 ngày",
        ]
    elif intent == "skill_gap":
        main_request = "Chỉ ra 3 kỹ năng thiếu quan trọng nhất và thứ tự bù trước."
        deliverable_type = "ranked skill gaps"
        must_answer = [
            "3 skill gaps tối đa",
            "vì sao chúng quan trọng với mục tiêu hiện tại",
            "bước bù cụ thể cho từng gap",
        ]
    elif intent == "learning_roadmap":
        main_request = "Tạo roadmap theo thứ tự học, mỗi bước phải có đầu ra rõ."
        deliverable_type = "ordered roadmap"
        must_answer = [
            "thứ tự học",
            "đầu ra của từng bước",
            "việc cần làm ngay trong 7 ngày",
        ]
    elif intent in {"career_fit", "career_roles"}:
        main_request = "Chốt 1 hướng nghề ưu tiên trước, chỉ nêu thêm lựa chọn phụ khi thực sự cần."
        deliverable_type = "prioritized career recommendation"
        must_answer = [
            "1 hướng ưu tiên",
            "lý do bám hồ sơ",
            "1 bước kiểm chứng hoặc bắt đầu ngay",
        ]
    else:
        main_request, deliverable_type, must_answer = mentor_logic.general_guidance_requirements(
            normalized_message
        )

    conversation_summary: list[str] = []
    for item in recent_messages[-4:]:
        role = normalize_text(str(item.get("role") or "user")) or "user"
        content = _clip_words(str(item.get("content") or ""), 18)
        if content:
            conversation_summary.append(f"{role}: {content}")

    session_summary: list[str] = []
    for item in recent_sessions[:3]:
        title = normalize_text(str(item.get("title") or ""))
        session_type = normalize_text(str(item.get("session_type") or ""))
        tags = ", ".join((item.get("topic_tags") or [])[:3])
        summary = _clip_words(" ".join(part for part in [title, session_type, tags] if part), 14)
        if summary:
            session_summary.append(summary)

    return {
        "intent": intent,
        "message": normalized_message,
        "main_request": main_request,
        "deliverable_type": deliverable_type,
        "must_answer": must_answer,
        "question_type": question_type,
        "focus_topic": focus_topic,
        "comparison_targets": comparison_targets,
        "context_mode": context_mode,
        "use_profile_context": use_profile_context,
        "use_market_context": use_market_context,
        "profile_grounding_required": profile_grounding_required,
        "requested_profile_fields": requested_profile_fields,
        "conversation_summary": conversation_summary,
        "recent_learning_signals": session_summary,
        "missing_context": _missing_context(onboarding)[:4],
        "must_avoid": [
            "trả lời thành lý thuyết dài",
            "lệch sang intent khác",
            "lặp lại bối cảnh người dùng",
        ],
    }


def _general_guidance_answer_matches_question(answer: str, message: str) -> bool:
    return mentor_logic.general_guidance_answer_matches_question(answer, message)


def _build_general_guidance_fallback(
    onboarding: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    onboarding = onboarding or {}
    question_type = mentor_logic.mentor_question_type(message)
    compare_subjects = list(mentor_logic.mentor_compare_subjects(message) or ())
    focus_topic = mentor_logic.mentor_focus_topic(message)
    blueprint = build_blueprint_fallback(
        title=focus_topic,
        question_type=question_type,
        learner_context={
            "target_role": normalize_text(str(onboarding.get("target_role") or "")),
            "current_focus": normalize_text(str(onboarding.get("current_focus") or "")),
        },
        comparison_targets=compare_subjects,
    )

    answer_parts = [normalize_text(blueprint.get("core_definition", ""))]
    if question_type == "comparison":
        answer_parts.append(normalize_text(blueprint.get("components", "")))
        answer_parts.append(normalize_text(blueprint.get("misconceptions", "")))
    elif question_type == "mechanism":
        answer_parts.append(normalize_text(blueprint.get("mechanism", "")))
        answer_parts.append(normalize_text(blueprint.get("conditions_and_limits", "")))
    else:
        answer_parts.append(normalize_text(blueprint.get("mechanism", "")))
        answer_parts.append(
            normalize_text(
                blueprint.get("application", "")
                or blueprint.get("conditions_and_limits", "")
                or blueprint.get("misconceptions", "")
            )
        )
    answer = " ".join(part for part in answer_parts if part)

    if compare_subjects:
        priority_value = f"{compare_subjects[0]} và {compare_subjects[1]}"
        followups = [
            f"Khi nào dễ nhầm giữa {compare_subjects[0]} và {compare_subjects[1]} trong thực tế?",
            f"Nếu đặt {compare_subjects[0]} và {compare_subjects[1]} trong cùng một dự án, đầu ra của mỗi bên khác nhau ở đâu?",
            f"Có khái niệm nào gần với {compare_subjects[0]} và {compare_subjects[1]} nhưng dễ bị đồng nhất sai không?",
        ]
    else:
        priority_value = focus_topic
        followups = [
            f"Cơ chế vận hành của {priority_value} nhìn theo đầu vào -> xử lý -> đầu ra ra sao?",
            f"{priority_value} dễ bị hiểu sai với khái niệm nào gần giống?",
            f"Khi nào nên dùng và khi nào không nên dùng {priority_value}?",
        ]

    return {
        "intent": "general_guidance",
        "answer": answer,
        "decision_summary": {
            "headline": normalize_text(blueprint.get("core_definition", "") or answer),
            "priority_label": "Trọng tâm câu trả lời",
            "priority_value": priority_value,
            "reason": normalize_text(
                blueprint.get("scope_boundary", "")
                or blueprint.get("decision_value", "")
                or "Câu trả lời ưu tiên bám thẳng vào câu hỏi hiện tại."
            ),
            "next_action": normalize_text(
                blueprint.get("related_concepts", "")
                or blueprint.get("conditions_and_limits", "")
                or f"Đối chiếu thêm một ví dụ trái ngược để kiểm tra ranh giới áp dụng của {priority_value}."
            ),
            "confidence_note": "Câu trả lời này ưu tiên bám câu hỏi hiện tại hơn là hồ sơ học tập.",
        },
        "career_paths": [],
        "market_signals": [],
        "skill_gaps": [],
        "recommended_learning_steps": [],
        "suggested_followups": followups[:3],
        "memory_updates": [],
        "sources": [],
    }


def _build_market_signal_fallback(
    message: str,
    onboarding: dict[str, Any] | None,
    market_signals: list[dict[str, Any]],
    web_research: list[dict[str, str]],
) -> list[dict[str, Any]]:
    if market_signals:
        signals: list[dict[str, Any]] = []
        for item in market_signals[:3]:
            role_name = normalize_text(str(item.get("role_name") or item.get("title") or ""))
            if not role_name:
                continue
            top_skills = _normalize_list_of_strings(
                item.get("top_skills") or item.get("skills") or item.get("tools") or [],
                5,
                max_words=4,
                clip=False,
            )
            signals.append(
                {
                    "role_name": role_name,
                    "demand_summary": normalize_text(str(item.get("demand_summary") or item.get("summary") or "")),
                    "top_skills": top_skills,
                    "source_name": normalize_text(str(item.get("source_name") or "")),
                    "source_url": normalize_text(str(item.get("source_url") or "")),
                }
            )
        if signals:
            return signals

    brief = _market_brief(message, onboarding, market_signals, web_research)
    top_skills = (brief.get("top_skills") or [])[:5]
    role_hint = normalize_text(
        str((onboarding or {}).get("target_role") or (brief.get("role_hints") or [""])[0] or "")
    )
    fallback_signals: list[dict[str, Any]] = []
    for item in web_research[:3]:
        role_name = role_hint or normalize_text(str(item.get("title") or "")) or "Tin hieu tuyen dung"
        demand_summary = normalize_text(str(item.get("snippet") or "")) or normalize_text(str(item.get("title") or ""))
        fallback_signals.append(
            {
                "role_name": role_name,
                "demand_summary": demand_summary,
                "top_skills": top_skills[:4],
                "source_name": normalize_text(str(item.get("source_name") or "")),
                "source_url": normalize_text(str(item.get("url") or "")),
            }
        )
    if fallback_signals:
        return fallback_signals

    if role_hint or top_skills:
        return [
            {
                "role_name": role_hint or "Vai tro dang tim",
                "demand_summary": "Chua lay duoc JD cu the, nhung he thong da tong hop duoc nhom ky nang lap lai nhieu nhat.",
                "top_skills": top_skills[:4],
                "source_name": "",
                "source_url": "",
            }
        ]
    return []


def _build_direct_market_lookup_result(
    onboarding: dict[str, Any] | None,
    message: str,
    market_signals: list[dict[str, Any]],
    web_research: list[dict[str, str]],
) -> dict[str, Any]:
    brief = _market_brief(message, onboarding, market_signals, web_research)
    top_skills = (brief.get("top_skills") or [])[:5]
    sources = _fallback_sources(market_signals, web_research)
    normalized_market_signals = _build_market_signal_fallback(
        message,
        onboarding,
        market_signals,
        web_research,
    )
    role_hint = normalize_text(
        str(
            (onboarding or {}).get("target_role")
            or (normalized_market_signals[0]["role_name"] if normalized_market_signals else "")
            or "vai tro ban dang hoi"
        )
    )
    skills_text = ", ".join(top_skills[:4]) if top_skills else "chua rut duoc nhom ky nang ro rang"
    source_text = ", ".join(item["label"] for item in sources[:3] if item.get("label"))

    answer_parts = [
        f"Neu bam vao tin hieu tuyen dung cho {role_hint}, nhom ky nang dang noi len nhat la: {skills_text}.",
    ]
    if source_text:
        answer_parts.append(f"Toi dang dua tren cac nguon nhu {source_text}.")
    if normalized_market_signals:
        demand_summary = normalize_text(str(normalized_market_signals[0].get("demand_summary") or ""))
        if demand_summary:
            answer_parts.append(demand_summary)
    answer_parts.append(
        "Neu muc tieu cua ban la doc JD de chot thu tu hoc, hay uu tien 2 nhom ky nang lap lai nhieu nhat truoc."
    )
    answer = " ".join(answer_parts)

    result = {
        "intent": "market_outlook",
        "answer": answer,
        "career_paths": [],
        "market_signals": normalized_market_signals,
        "skill_gaps": [
            {
                "skill": skill,
                "gap_level": "high" if index < 2 else "medium",
                "why_it_matters": "Ky nang nay dang lap lai trong cac tin hieu tuyen dung he thong quet duoc.",
                "suggested_action": f"Doc 5-7 JD gan nhat va danh dau xem {skill} duoc nhac o phan yeu cau nao.",
            }
            for index, skill in enumerate(top_skills[:4])
        ],
        "recommended_learning_steps": [
            "Chot 5-7 JD gan nhat cua vai tro muc tieu va danh dau nhung ky nang bi lap lai nhieu nhat.",
            "So bang ky nang dang co voi 3 nhom ky nang lap lai do de biet phan nao da co, phan nao con thieu.",
        ],
        "suggested_followups": [],
        "memory_updates": [],
        "sources": sources,
    }
    result["decision_summary"] = _build_decision_summary(
        result,
        onboarding,
        intent="market_outlook",
    )
    return _prune_result_for_intent(
        _enforce_response_contract(result, "market_outlook", onboarding, market_signals, web_research),
        "market_outlook",
    )


def _build_general_guidance_text_prompt(message: str) -> str:
    question_type = mentor_logic.mentor_question_type(message)
    answer_shape = (
        "Nếu là câu hỏi so sánh, hãy nêu ngay các trục khác biệt cốt lõi rồi mới giải thích."
        if question_type == "comparison"
        else "Nếu là câu hỏi cơ chế, hãy đi theo luồng đầu vào -> xử lý -> đầu ra hoặc nguyên nhân -> hệ quả."
        if question_type == "mechanism"
        else "Nếu là câu hỏi định nghĩa, hãy nêu định nghĩa, phạm vi và điều dễ nhầm."
        if question_type == "definition"
        else "Hãy trả lời trực diện câu hỏi trước, rồi mới thêm ví dụ hoặc lưu ý khi cần."
    )
    return (
        "Bạn là trợ lý tri thức chất lượng cao của DUO MIND.\n"
        "Hãy trả lời câu hỏi sau bằng tiếng Việt, như một LLM chuyên môn: ngắn gọn nhưng sâu, rõ và có giá trị học thật.\n"
        "Không hỏi ngược lại, không coaching, không nói meta, không lặp lại câu hỏi, không dùng câu rỗng.\n"
        f"{answer_shape}\n"
        "Yêu cầu:\n"
        "- Mở đầu bằng câu trả lời cốt lõi.\n"
        "- Có giải thích bản chất hoặc logic vận hành khi phù hợp.\n"
        "- Có ví dụ, giới hạn, hoặc hiểu lầm phổ biến khi nó làm câu trả lời rõ hơn.\n"
        "- Tối đa 220 từ.\n\n"
        f"Câu hỏi: {normalize_text(message)}"
    )


def _build_direct_knowledge_prompt(
    message: str,
    onboarding: dict[str, Any] | None,
) -> str:
    onboarding = onboarding or {}
    question_type = mentor_logic.mentor_question_type(message)
    focus_topic = mentor_logic.mentor_focus_topic(message)
    comparison_targets = list(mentor_logic.mentor_compare_subjects(message) or ())
    learner_context = {
        "target_role": normalize_text(str(onboarding.get("target_role") or "")),
        "current_focus": normalize_text(str(onboarding.get("current_focus") or "")),
    }
    blueprint = build_blueprint_fallback(
        title=focus_topic,
        question_type=question_type,
        learner_context=learner_context,
        comparison_targets=comparison_targets,
    )
    section_briefs = build_section_briefs(
        blueprint,
        title=focus_topic,
        question_type=question_type,
        mode="explore",
        main_question=message,
        focus_topic=focus_topic,
        comparison_targets=comparison_targets,
    )
    summary = build_summary_from_briefs(section_briefs, key="overview")
    key_points = build_key_points_from_briefs(section_briefs)
    answer_shape = (
        "Neu la so sanh, mo dau bang diem khac cot loi, sau do tach 2-3 truc so sanh ro rang."
        if question_type == "comparison"
        else "Neu la co che, di theo logic dau vao -> xu ly -> dau ra hoac nguyen nhan -> he qua."
        if question_type == "mechanism"
        else "Neu la dinh nghia, phai chot dinh nghia, pham vi va dieu de nham."
        if question_type == "definition"
        else "Tra loi truc dien cau hoi, sau do bo sung logic, vi du hoac gioi han neu can."
    )
    return (
        "Ban la DUO MIND Knowledge Mentor, mot tro ly giai thich thong minh va dung trong tam.\n"
        "Muc tieu duy nhat: tra loi cho dung cau hoi hien tai cua nguoi hoc. Khong coaching, khong meta, khong nhac den profile neu cau hoi khong can.\n"
        "Phai viet nhu mot nguoi thuc su hieu ban chat van de, khong duoc viet an toan, khong noi rong thong tin, khong lap y.\n\n"
        f"QUESTION_TYPE: {question_type}\n"
        f"FOCUS_TOPIC: {focus_topic}\n"
        f"COMPARISON_TARGETS: {json.dumps(comparison_targets, ensure_ascii=False)}\n"
        f"SUGGESTED_SUMMARY: {summary}\n"
        f"SUGGESTED_KEY_POINTS: {json.dumps(key_points, ensure_ascii=False)}\n"
        f"KNOWLEDGE_BLUEPRINT: {json.dumps(blueprint, ensure_ascii=False)}\n\n"
        "RULES:\n"
        "- Mo dau bang cau tra loi cot loi cho dung cau hoi.\n"
        f"- {answer_shape}\n"
        "- Chi dua vao phan kien thuc can thiet nhat; khong bien cau tra loi thanh bai viet dai.\n"
        "- Neu dung vi du, vi du phai lam ro ban chat chu khong chi minh hoa qua loa.\n"
        "- Neu co dieu kien, gioi han, hay nham lan pho bien thi neu ngan gon, dung luc.\n"
        "- Tuyet doi khong viet kieu: 'con tuy', 'hay cho them thong tin', 'toi khong co du du lieu' neu van tra loi duoc.\n"
        "- Toi da 190 tu.\n\n"
        f"CAU_HOI: {normalize_text(message)}"
    )


async def _generate_direct_knowledge_result(
    onboarding: dict[str, Any] | None,
    message: str,
) -> dict[str, Any]:
    fallback_result = _build_general_guidance_fallback(onboarding, message)
    try:
        answer = _normalize_answer_text(
            await gemini.generate_text(
                _build_direct_knowledge_prompt(message, onboarding),
                precise=True,
            )
        )
    except Exception:
        return fallback_result

    if not answer or not _general_guidance_answer_matches_question(answer, message):
        return fallback_result
    if _low_signal(answer, message, onboarding):
        return fallback_result

    result = dict(fallback_result)
    result["answer"] = answer
    result["decision_summary"] = _build_decision_summary(
        result,
        onboarding,
        intent="general_guidance",
    )
    result = _enforce_response_contract(result, "general_guidance", onboarding, [], [])
    return _prune_result_for_intent(result, "general_guidance")


def _prune_result_for_intent(result: dict[str, Any], intent: MentorIntent) -> dict[str, Any]:
    pruned = dict(result)
    if intent == "general_guidance":
        pruned["career_paths"] = []
        pruned["market_signals"] = []
        pruned["skill_gaps"] = []
        pruned["recommended_learning_steps"] = []
        return pruned
    if intent == "market_outlook":
        pruned["career_paths"] = []
        pruned["skill_gaps"] = []
        pruned["recommended_learning_steps"] = (pruned.get("recommended_learning_steps") or [])[:2]
    elif intent == "skill_gap":
        pruned["career_paths"] = []
        pruned["market_signals"] = []
        pruned["skill_gaps"] = (pruned.get("skill_gaps") or [])[:3]
        pruned["recommended_learning_steps"] = (pruned.get("recommended_learning_steps") or [])[:3]
    elif intent == "learning_roadmap":
        pruned["career_paths"] = []
        pruned["market_signals"] = []
        pruned["skill_gaps"] = []
        pruned["recommended_learning_steps"] = (pruned.get("recommended_learning_steps") or [])[:3]
    elif intent in {"career_fit", "career_roles"}:
        pruned["career_paths"] = (pruned.get("career_paths") or [])[:3]
        pruned["market_signals"] = []
        pruned["skill_gaps"] = (pruned.get("skill_gaps") or [])[:3]
        pruned["recommended_learning_steps"] = (pruned.get("recommended_learning_steps") or [])[:3]
    return pruned


def build_personalized_fallback(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    intent: MentorIntent,
    message: str,
    market_signals: list[dict[str, Any]] | None = None,
    web_research: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    if intent == "general_guidance":
        if mentor_logic.is_profile_lookup_question(message):
            fallback_result = _build_profile_lookup_fallback(profile, onboarding, message)
        else:
            fallback_result = _build_general_guidance_fallback(onboarding, message)
        fallback_result = _enforce_response_contract(
            fallback_result,
            intent,
            onboarding,
            market_signals or [],
            web_research or [],
        )
        return _prune_result_for_intent(fallback_result, intent)

    return _legacy_build_personalized_fallback(
        profile,
        onboarding,
        intent,
        message,
        market_signals,
        web_research,
    )


def _compose_structured_answer(
    result: dict[str, Any],
    intent: MentorIntent,
    onboarding: dict[str, Any] | None,
) -> str:
    onboarding = onboarding or {}
    target_role = _first_text(
        onboarding.get("target_role"),
        ((result.get("career_paths") or [{}])[0]).get("role"),
        ((result.get("market_signals") or [{}])[0]).get("role_name"),
        "hướng bạn đang hỏi",
    )
    desired_outcome = _first_text(onboarding.get("desired_outcome"))
    top_step = _first_text(*((result.get("recommended_learning_steps") or [])[:1]))
    top_gap = _first_text(*[item.get("skill") for item in (result.get("skill_gaps") or [])[:1]])
    top_gap_action = _first_text(
        *[item.get("suggested_action") for item in (result.get("skill_gaps") or [])[:1]],
        top_step,
    )

    if intent == "market_outlook":
        top_skills = _join_readable(
            [
                *[
                    skill
                    for signal in (result.get("market_signals") or [])[:2]
                    for skill in (signal.get("top_skills") or [])[:3]
                ],
                *[
                    normalize_text(str(item.get("skill") or ""))
                    for item in (result.get("skill_gaps") or [])[:2]
                ],
            ],
            limit=4,
        )
        demand_summary = _first_text(
            *[item.get("demand_summary") for item in (result.get("market_signals") or [])[:1]]
        )
        answer_parts = [
            f"Kết luận nhanh: thị trường cho hướng {target_role} hiện đang ưu tiên {top_skills or 'bộ kỹ năng nền tảng gắn với đầu ra thực hành'}.",
        ]
        if demand_summary:
            answer_parts.append(demand_summary)
        if desired_outcome:
            answer_parts.append(f"Điều này bám trực tiếp với đầu ra bạn muốn là {desired_outcome}.")
        if top_step:
            answer_parts.append(f"Việc nên làm ngay trong 7 ngày tới là {top_step}.")
        return " ".join(answer_parts)

    if intent == "skill_gap":
        prioritized_gaps = [
            normalize_text(str(item.get("skill") or ""))
            for item in (result.get("skill_gaps") or [])[:3]
            if normalize_text(str(item.get("skill") or ""))
        ]
        gap_text = _join_readable(prioritized_gaps, limit=3) or top_gap or "khối kỹ năng nền tảng"
        why_it_matters = _first_text(
            *[item.get("why_it_matters") for item in (result.get("skill_gaps") or [])[:1]]
        )
        answer_parts = [f"Ba kỹ năng nên bù trước là {gap_text}."]
        if why_it_matters:
            answer_parts.append(why_it_matters)
        if desired_outcome:
            answer_parts.append(f"Thứ tự này được chốt để tiến gần hơn tới mục tiêu {desired_outcome}.")
        if top_gap_action:
            answer_parts.append(f"Bắt đầu ngay bằng việc {top_gap_action}.")
        return " ".join(answer_parts)

    if intent == "learning_roadmap":
        steps = [
            normalize_text(str(item))
            for item in (result.get("recommended_learning_steps") or [])[:3]
            if normalize_text(str(item))
        ]
        if not steps:
            steps = [
                normalize_text(str(item.get("suggested_action") or ""))
                for item in (result.get("skill_gaps") or [])[:3]
                if normalize_text(str(item.get("suggested_action") or ""))
            ]
        answer_parts = [f"Lộ trình nên đi theo đúng thứ tự để tiến tới {target_role}."]
        if desired_outcome:
            answer_parts.append(f"Mục tiêu đầu ra đang bám là {desired_outcome}.")
        if steps:
            answer_parts.append(" ".join(f"Bước {index + 1}: {step}." for index, step in enumerate(steps[:3])))
        return " ".join(answer_parts)

    if intent in {"career_fit", "career_roles"}:
        primary_path = (result.get("career_paths") or [{}])[0]
        role = _first_text(primary_path.get("role"), target_role)
        fit_reason = _first_text(primary_path.get("fit_reason"))
        required_skills = _join_readable(primary_path.get("required_skills") or [], limit=4)
        next_step = _first_text(primary_path.get("next_step"), top_step)
        answer_parts = [f"Hướng nên ưu tiên trước là {role}."]
        if fit_reason:
            answer_parts.append(fit_reason)
        if required_skills:
            answer_parts.append(f"Nhóm năng lực nên tập trung là {required_skills}.")
        if next_step:
            answer_parts.append(f"Bước kiểm chứng ngay là {next_step}.")
        return " ".join(answer_parts)

    focus_value = _first_text(top_gap, _priority_value_from_step(top_step), target_role, "ưu tiên hiện tại")
    answer_parts = [f"Ưu tiên nên chốt lúc này là {focus_value}."]
    if desired_outcome:
        answer_parts.append(f"Trục này bám trực tiếp với đầu ra {desired_outcome}.")
    if top_step:
        answer_parts.append(f"Việc nên làm tiếp là {top_step}.")
    return " ".join(answer_parts)


def _build_decision_summary_with_learning_context(
    result: dict[str, Any],
    onboarding: dict[str, Any] | None,
    *,
    intent: MentorIntent = "general_guidance",
) -> dict[str, str]:
    onboarding = onboarding or {}
    raw_summary = result.get("decision_summary") if isinstance(result.get("decision_summary"), dict) else {}
    target_role = normalize_text(
        str(
            onboarding.get("target_role")
            or (result.get("career_paths") or [{}])[0].get("role")
            or "vai trò mục tiêu hiện tại"
        )
    )
    desired_outcome = normalize_text(str(onboarding.get("desired_outcome") or ""))
    current_challenges = normalize_text(str(onboarding.get("current_challenges") or ""))
    current_focus = normalize_text(str(onboarding.get("current_focus") or ""))
    learning_constraints = normalize_text(str(onboarding.get("learning_constraints") or ""))
    daily = int(onboarding.get("daily_study_minutes") or 30)
    top_gap = normalize_text(
        str(
            ((result.get("skill_gaps") or [{}])[0].get("skill"))
            or ((result.get("recommended_learning_steps") or [""])[0])
            or "khối kỹ năng ưu tiên"
        )
    )
    next_action = normalize_text(
        str(
            ((result.get("skill_gaps") or [{}])[0].get("suggested_action"))
            or ((result.get("recommended_learning_steps") or [""])[0])
            or "Mở roadmap và thực hiện bước học tiếp theo"
        )
    )
    top_role = _first_text(((result.get("career_paths") or [{}])[0]).get("role"), target_role)
    top_role_reason = _first_text(((result.get("career_paths") or [{}])[0]).get("fit_reason"))
    top_signal_reason = _first_text(((result.get("market_signals") or [{}])[0]).get("demand_summary"))
    market_skills = _join_readable(
        [
            skill
            for signal in (result.get("market_signals") or [])[:2]
            for skill in (signal.get("top_skills") or [])[:3]
        ],
        limit=4,
    )

    if intent == "market_outlook":
        priority_value = market_skills or top_gap or target_role
        headline = f"Thị trường hiện đang ưu tiên {priority_value} cho hướng {target_role}."
        priority_label = f"Tín hiệu thị trường cho {target_role}"
        reason_seed = top_signal_reason or "Bạn nên bám nhóm kỹ năng đang được nhắc lặp lại thay vì học dàn trải."
    elif intent == "skill_gap":
        priority_value = top_gap
        headline = f"Ưu tiên bù {priority_value} trước khi mở rộng sang nhóm kỹ năng khác."
        priority_label = f"Khoảng trống cần bù cho {target_role}"
        reason_seed = _first_text(
            ((result.get("skill_gaps") or [{}])[0]).get("why_it_matters"),
            f"Đây là điểm nghẽn ảnh hưởng trực tiếp đến tiến độ tiến gần vai trò {target_role}.",
        )
    elif intent == "learning_roadmap":
        priority_value = _priority_value_from_step(next_action)
        headline = f"Bắt đầu roadmap từ {priority_value.lower()} rồi mới mở rộng sang bước tiếp theo."
        priority_label = "Bước học cần bắt đầu"
        reason_seed = f"Thứ tự này giúp giữ đúng quỹ học {daily} phút mỗi ngày và tránh học lan man."
    elif intent in {"career_fit", "career_roles"}:
        priority_value = top_role
        headline = f"Hướng nên ưu tiên trước là {top_role}."
        priority_label = "Hướng nghề nên ưu tiên"
        reason_seed = top_role_reason or "Hướng này đang khớp hơn với bối cảnh hiện tại của bạn."
    elif desired_outcome:
        priority_value = top_gap
        headline = f"Ưu tiên {top_gap} để tiến gần mục tiêu {desired_outcome}."
        priority_label = f"Gấp ưu tiên cho {target_role}"
        reason_seed = ""
    else:
        priority_value = top_gap
        headline = f"Ưu tiên {top_gap} để tiến gần vai trò {target_role}."
        priority_label = f"Gấp ưu tiên cho {target_role}"
        reason_seed = ""

    reason_parts: list[str] = []
    if reason_seed:
        reason_parts.append(reason_seed)
    if current_focus:
        reason_parts.append(f"Bạn đang tập trung vào {current_focus}")
    if current_challenges:
        reason_parts.append(f"Nút thắt hiện tại là {current_challenges}")
    if learning_constraints:
        reason_parts.append(f"Cần giữ đúng ràng buộc {learning_constraints}")
    if not reason_parts:
        reason_parts.append(f"Quỹ học hiện tại là khoảng {daily} phút mỗi ngày")

    context_count = sum(
        1
        for value in (
            onboarding.get("target_role"),
            onboarding.get("desired_outcome"),
            onboarding.get("current_focus"),
            onboarding.get("current_challenges"),
            onboarding.get("learning_constraints"),
        )
        if normalize_text(str(value or ""))
    )
    confidence_note = (
        "Đã bám đủ bối cảnh mục tiêu, đầu ra và ràng buộc học tập."
        if context_count >= 4
        else "Nên bổ sung hồ sơ thêm một chút để mentor khóa ưu tiên sát hơn."
    )

    return {
        "headline": _prefer_summary_field(raw_summary.get("headline"), headline),
        "priority_label": _prefer_summary_field(raw_summary.get("priority_label"), priority_label),
        "priority_value": _prefer_summary_field(raw_summary.get("priority_value"), priority_value),
        "reason": _prefer_summary_field(raw_summary.get("reason"), ". ".join(reason_parts) + "."),
        "next_action": _prefer_summary_field(raw_summary.get("next_action"), next_action),
        "confidence_note": _prefer_summary_field(
            raw_summary.get("confidence_note"),
            confidence_note,
        ),
    }


def _low_signal_with_learning_context(
    answer: str,
    message: str,
    onboarding: dict[str, Any] | None,
    result: dict[str, Any] | None = None,
) -> bool:
    text = strip_accents(normalize_text(answer)).lower()
    if not text:
        return True
    intent = detect_mentor_intent(message)
    if any(marker in text for marker in GENERIC_MARKERS):
        return True
    if any(phrase in text for phrase in FORBIDDEN_GENERIC_PHRASES):
        return True
    if len(text.split()) > MAX_ANSWER_WORDS + 20:
        return True

    track = _track(message, onboarding)
    if (
        track != "general"
        and intent in {"market_outlook", "skill_gap", "learning_roadmap", "career_fit", "career_roles"}
    ):
        if not any(strip_accents(skill).lower() in text for skill in SKILL_CATALOG[track][:6]) and len(text.split()) < 60:
            return True

    if result:
        steps = result.get("recommended_learning_steps") or []
        market_signals = result.get("market_signals") or []
        skill_gaps = result.get("skill_gaps") or []
        career_paths = result.get("career_paths") or []
        if not result.get("decision_summary"):
            return True
        if intent == "general_guidance":
            if len(text.split()) < 24:
                return True
        elif intent == "market_outlook":
            if len(market_signals) < 1 or len(steps) < 1:
                return True
        elif intent == "skill_gap":
            if len(skill_gaps) < 2 or len(steps) < 2:
                return True
        elif intent == "learning_roadmap":
            if len(steps) < 3:
                return True
        elif intent in {"career_fit", "career_roles"}:
            if len(career_paths) < 1:
                return True
        if not _answer_matches_intent(answer, intent, result):
            return True
    return False


def _normalize_response(
    raw_result: dict[str, Any],
    intent: MentorIntent,
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
    market_signals: list[dict[str, Any]],
    web_research: list[dict[str, str]],
) -> dict[str, Any]:
    normalized = {
        "intent": intent,
        "answer": _normalize_answer_text(raw_result.get("answer")),
        "decision_summary": raw_result.get("decision_summary") if isinstance(raw_result.get("decision_summary"), dict) else None,
        "career_paths": _normalize_items(raw_result.get("career_paths"), {"role": "role", "fit_reason": "fit_reason", "entry_level": "entry_level", "required_skills": "required_skills", "next_step": "next_step"}),
        "market_signals": _normalize_items(raw_result.get("market_signals"), {"role_name": "role_name", "demand_summary": "demand_summary", "top_skills": "top_skills", "source_name": "source_name", "source_url": "source_url"}),
        "skill_gaps": _normalize_items(raw_result.get("skill_gaps"), {"skill": "skill", "gap_level": "gap_level", "why_it_matters": "why_it_matters", "suggested_action": "suggested_action"}),
        "recommended_learning_steps": _normalize_list_of_strings(raw_result.get("recommended_learning_steps"), 6, clip=False),
        "suggested_followups": _normalize_list_of_strings(raw_result.get("suggested_followups"), 5, clip=False),
        "memory_updates": _normalize_memory_updates(raw_result.get("memory_updates")),
        "sources": _normalize_sources(raw_result.get("sources")),
    }
    if not normalized["sources"]:
        normalized["sources"] = _fallback_sources(market_signals, web_research)
    if not normalized["market_signals"]:
        normalized["market_signals"] = _fallback_market_signals(web_research)
    fallback = build_personalized_fallback(profile, onboarding, intent, message, market_signals, web_research)
    normalized = _merge(normalized, fallback)
    normalized = _enforce_response_contract(normalized, intent, onboarding, market_signals, web_research)
    synthesized_answer = _compose_structured_answer(normalized, intent, onboarding)
    if synthesized_answer and _should_replace_answer_with_structured_fallback(
        normalized.get("answer", ""),
        intent,
        normalized,
    ):
        normalized["answer"] = synthesized_answer
    if _low_signal(normalized["answer"], message, onboarding, normalized):
        normalized["answer"] = fallback["answer"]
        normalized["career_paths"] = fallback["career_paths"]
        normalized["skill_gaps"] = fallback["skill_gaps"]
        normalized["recommended_learning_steps"] = fallback["recommended_learning_steps"]
        normalized["suggested_followups"] = fallback["suggested_followups"]
        if fallback.get("market_signals"):
            normalized["market_signals"] = fallback["market_signals"]
        if fallback.get("sources"):
            normalized["sources"] = fallback["sources"]
        normalized["decision_summary"] = fallback["decision_summary"]
        normalized = _enforce_response_contract(normalized, intent, onboarding, market_signals, web_research)
        synthesized_answer = _compose_structured_answer(normalized, intent, onboarding)
        if synthesized_answer and _should_replace_answer_with_structured_fallback(
            normalized.get("answer", ""),
            intent,
            normalized,
        ):
            normalized["answer"] = synthesized_answer
    return _prune_result_for_intent(normalized, intent)


async def _legacy_generate_mentor_response(
    svc: SupabaseService,
    user_id: str,
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
    recent_messages: list[dict[str, Any]],
) -> dict[str, Any]:
    intent = detect_mentor_intent(message)
    recent_sessions = svc.get_all_sessions_for_analytics(user_id)[:8]
    analytics = svc.get_latest_analytics_report(user_id)
    memories = svc.get_mentor_memory(user_id, limit=24)

    if intent == "general_guidance":
        market_signals: list[dict[str, Any]] = []
        web_research: list[dict[str, str]] = []
        salvaged = await _salvage_general_guidance_result(
            profile,
            onboarding,
            message,
            market_signals,
            web_research,
        )
        if salvaged and not _low_signal(salvaged["answer"], message, onboarding, salvaged):
            return salvaged
    else:
        role_candidates = _normalize_role_candidates(message, onboarding)
        industry = normalize_text(str((onboarding or {}).get("industry") or ""))
        market_signals = svc.get_market_signals(industry=industry or None, roles=role_candidates or None)
        web_research = await search_market_context(message=message, onboarding=onboarding, intent=intent)

    prompt = build_mentor_prompt(profile, onboarding, analytics, recent_sessions, memories, recent_messages, market_signals, web_research, intent, message)
    raw_result = await gemini.generate_json(prompt)
    result = _normalize_response(raw_result, intent, profile, onboarding, message, market_signals, web_research)

    if _low_signal(result["answer"], message, onboarding, result):
        rewrite_prompt = _build_rewrite_prompt(
            message,
            intent,
            profile,
            onboarding,
            analytics,
            recent_sessions,
            recent_messages,
            memories,
            market_signals,
            web_research,
            json.dumps(result, ensure_ascii=False, indent=2),
        )
        try:
            rewritten_raw = await gemini.generate_json(rewrite_prompt)
            rewritten_result = _normalize_response(rewritten_raw, intent, profile, onboarding, message, market_signals, web_research)
            if not _low_signal(rewritten_result["answer"], message, onboarding, rewritten_result):
                result = rewritten_result
        except Exception:
            pass

    if _low_signal(result["answer"], message, onboarding, result):
        result = build_personalized_fallback(profile, onboarding, intent, message, market_signals, web_research)

    return result


def _legacy_build_decision_summary_v3(
    result: dict[str, Any],
    onboarding: dict[str, Any] | None,
    *,
    intent: MentorIntent = "general_guidance",
) -> dict[str, str]:
    onboarding = onboarding or {}
    raw_summary = result.get("decision_summary") if isinstance(result.get("decision_summary"), dict) else {}
    target_role = normalize_text(
        str(
            onboarding.get("target_role")
            or (result.get("career_paths") or [{}])[0].get("role")
            or "vai trò mục tiêu hiện tại"
        )
    )
    desired_outcome = normalize_text(str(onboarding.get("desired_outcome") or ""))
    current_challenges = normalize_text(str(onboarding.get("current_challenges") or ""))
    current_focus = normalize_text(str(onboarding.get("current_focus") or ""))
    learning_constraints = normalize_text(str(onboarding.get("learning_constraints") or ""))
    daily = int(onboarding.get("daily_study_minutes") or 30)
    top_gap = normalize_text(
        str(
            ((result.get("skill_gaps") or [{}])[0].get("skill"))
            or ((result.get("recommended_learning_steps") or [""])[0])
            or "khối kỹ năng ưu tiên"
        )
    )
    next_action = normalize_text(
        str(
            ((result.get("skill_gaps") or [{}])[0].get("suggested_action"))
            or ((result.get("recommended_learning_steps") or [""])[0])
            or "Mở roadmap và thực hiện bước học tiếp theo"
        )
    )
    top_role = _first_text(((result.get("career_paths") or [{}])[0]).get("role"), target_role)
    top_role_reason = _first_text(((result.get("career_paths") or [{}])[0]).get("fit_reason"))
    top_signal_reason = _first_text(((result.get("market_signals") or [{}])[0]).get("demand_summary"))
    market_skills = _join_readable(
        [
            skill
            for signal in (result.get("market_signals") or [])[:2]
            for skill in (signal.get("top_skills") or [])[:3]
        ],
        limit=4,
    )

    if intent == "general_guidance":
        answer = normalize_text(str(result.get("answer") or ""))
        first_sentence = normalize_text(re.split(r"(?<=[.!?])\s+", answer, maxsplit=1)[0]) if answer else ""
        return {
            "headline": _prefer_summary_field(
                raw_summary.get("headline"),
                first_sentence or "Câu trả lời đã được chốt theo đúng câu hỏi hiện tại.",
            ),
            "priority_label": _prefer_summary_field(raw_summary.get("priority_label"), "Trọng tâm câu trả lời"),
            "priority_value": _prefer_summary_field(
                raw_summary.get("priority_value"),
                _first_text(first_sentence, target_role, "Trọng tâm kiến thức"),
            ),
            "reason": _prefer_summary_field(
                raw_summary.get("reason"),
                "Câu trả lời này ưu tiên bám thẳng vào câu hỏi hiện tại thay vì kéo sang tư vấn nghề nghiệp.",
            ),
            "next_action": _prefer_summary_field(
                raw_summary.get("next_action"),
                "Đối chiếu thêm một ví dụ hoặc trường hợp ngược để kiểm tra ranh giới áp dụng.",
            ),
            "confidence_note": _prefer_summary_field(
                raw_summary.get("confidence_note"),
                "Câu trả lời này ưu tiên bám câu hỏi hiện tại hơn là hồ sơ học tập.",
            ),
        }

    if intent == "market_outlook":
        priority_value = market_skills or top_gap or target_role
        headline = f"Thị trường hiện đang ưu tiên {priority_value} cho hướng {target_role}."
        priority_label = f"Tín hiệu thị trường cho {target_role}"
        reason_seed = top_signal_reason or "Bạn nên bám nhóm kỹ năng đang được nhắc lặp lại thay vì học dàn trải."
    elif intent == "skill_gap":
        priority_value = top_gap
        headline = f"Ưu tiên bù {priority_value} trước khi mở rộng sang nhóm kỹ năng khác."
        priority_label = f"Khoảng trống cần bù cho {target_role}"
        reason_seed = _first_text(
            ((result.get("skill_gaps") or [{}])[0]).get("why_it_matters"),
            f"Đây là điểm nghẽn ảnh hưởng trực tiếp đến tiến độ tiến gần vai trò {target_role}.",
        )
    elif intent == "learning_roadmap":
        priority_value = _priority_value_from_step(next_action)
        headline = f"Bắt đầu roadmap từ {priority_value.lower()} rồi mới mở rộng sang bước tiếp theo."
        priority_label = "Bước học cần bắt đầu"
        reason_seed = f"Thứ tự này giúp giữ đúng quỹ học {daily} phút mỗi ngày và tránh học lan man."
    elif intent in {"career_fit", "career_roles"}:
        priority_value = top_role
        headline = f"Hướng nên ưu tiên trước là {top_role}."
        priority_label = "Hướng nghề nên ưu tiên"
        reason_seed = top_role_reason or "Hướng này đang khớp hơn với bối cảnh hiện tại của bạn."
    elif desired_outcome:
        priority_value = top_gap
        headline = f"Ưu tiên {top_gap} để tiến gần mục tiêu {desired_outcome}."
        priority_label = f"Gấp ưu tiên cho {target_role}"
        reason_seed = ""
    else:
        priority_value = top_gap
        headline = f"Ưu tiên {top_gap} để tiến gần vai trò {target_role}."
        priority_label = f"Gấp ưu tiên cho {target_role}"
        reason_seed = ""

    reason_parts: list[str] = []
    if reason_seed:
        reason_parts.append(reason_seed)
    if current_focus:
        reason_parts.append(f"Bạn đang tập trung vào {current_focus}")
    if current_challenges:
        reason_parts.append(f"Nút thắt hiện tại là {current_challenges}")
    if learning_constraints:
        reason_parts.append(f"Cần giữ đúng ràng buộc {learning_constraints}")
    if not reason_parts:
        reason_parts.append(f"Quỹ học hiện tại là khoảng {daily} phút mỗi ngày")

    context_count = sum(
        1
        for value in (
            onboarding.get("target_role"),
            onboarding.get("desired_outcome"),
            onboarding.get("current_focus"),
            onboarding.get("current_challenges"),
            onboarding.get("learning_constraints"),
        )
        if normalize_text(str(value or ""))
    )
    confidence_note = (
        "Đã bám đủ bối cảnh mục tiêu, đầu ra và ràng buộc học tập."
        if context_count >= 4
        else "Nên bổ sung hồ sơ thêm một chút để mentor khóa ưu tiên sát hơn."
    )

    return {
        "headline": _prefer_summary_field(raw_summary.get("headline"), headline),
        "priority_label": _prefer_summary_field(raw_summary.get("priority_label"), priority_label),
        "priority_value": _prefer_summary_field(raw_summary.get("priority_value"), priority_value),
        "reason": _prefer_summary_field(raw_summary.get("reason"), ". ".join(reason_parts) + "."),
        "next_action": _prefer_summary_field(raw_summary.get("next_action"), next_action),
        "confidence_note": _prefer_summary_field(raw_summary.get("confidence_note"), confidence_note),
    }


def _build_decision_summary(
    result: dict[str, Any],
    onboarding: dict[str, Any] | None,
    *,
    intent: MentorIntent = "general_guidance",
) -> dict[str, str]:
    if intent != "general_guidance":
        return _build_decision_summary_with_learning_context(result, onboarding, intent=intent)

    raw_summary = result.get("decision_summary") if isinstance(result.get("decision_summary"), dict) else {}
    answer = normalize_text(str(result.get("answer") or ""))
    first_sentence = normalize_text(re.split(r"(?<=[.!?])\s+", answer, maxsplit=1)[0]) if answer else ""
    priority_value = _first_text(
        raw_summary.get("priority_value"),
        first_sentence,
        normalize_text(str((onboarding or {}).get("target_role") or "")),
        "Trọng tâm kiến thức",
    )
    return {
        "headline": _prefer_summary_field(
            raw_summary.get("headline"),
            first_sentence or "Câu trả lời đã được chốt theo đúng câu hỏi hiện tại.",
        ),
        "priority_label": _prefer_summary_field(raw_summary.get("priority_label"), "Trọng tâm câu trả lời"),
        "priority_value": _prefer_summary_field(raw_summary.get("priority_value"), priority_value),
        "reason": _prefer_summary_field(
            raw_summary.get("reason"),
            "Câu trả lời này ưu tiên bám thẳng vào câu hỏi hiện tại thay vì kéo sang tư vấn nghề nghiệp.",
        ),
        "next_action": _prefer_summary_field(
            raw_summary.get("next_action"),
            "Đối chiếu thêm một ví dụ hoặc trường hợp ngược để kiểm tra ranh giới áp dụng.",
        ),
        "confidence_note": _prefer_summary_field(
            raw_summary.get("confidence_note"),
            "Câu trả lời này ưu tiên bám câu hỏi hiện tại hơn là hồ sơ học tập.",
        ),
    }


def _low_signal(
    answer: str,
    message: str,
    onboarding: dict[str, Any] | None,
    result: dict[str, Any] | None = None,
) -> bool:
    intent = detect_mentor_intent(message)
    if intent != "general_guidance":
        return _low_signal_with_learning_context(answer, message, onboarding, result)

    text = strip_accents(normalize_text(answer)).lower()
    if not text:
        return True
    if mentor_logic.is_profile_lookup_question(message) and mentor_logic.answer_denies_profile_access(answer):
        return True
    if any(marker in text for marker in GENERIC_MARKERS):
        return True
    if any(phrase in text for phrase in FORBIDDEN_GENERIC_PHRASES):
        return True
    if normalize_text(answer).endswith("...") or normalize_text(answer).endswith("…"):
        return True
    if len(text.split()) < 20 or len(text.split()) > MAX_ANSWER_WORDS + 20:
        return True
    if not _general_guidance_answer_matches_question(answer, message):
        return True
    if result and not result.get("decision_summary"):
        return True
    return False


async def _salvage_general_guidance_result(
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
    market_signals: list[dict[str, Any]],
    web_research: list[dict[str, str]],
) -> dict[str, Any] | None:
    if mentor_logic.is_profile_lookup_question(message):
        return None
    try:
        answer = _normalize_answer_text(
            await gemini.generate_text(
                _build_general_guidance_text_prompt(message),
                precise=True,
            )
        )
    except Exception:
        return None

    if _low_signal(answer, message, onboarding):
        return None

    result = build_personalized_fallback(
        profile,
        onboarding,
        "general_guidance",
        message,
        market_signals,
        web_research,
    )
    result["answer"] = answer
    result["decision_summary"] = _build_decision_summary(
        result,
        onboarding,
        intent="general_guidance",
    )
    return _prune_result_for_intent(result, "general_guidance")


async def generate_mentor_response(
    svc: SupabaseService,
    user_id: str,
    profile: dict[str, Any] | None,
    onboarding: dict[str, Any] | None,
    message: str,
    recent_messages: list[dict[str, Any]],
) -> dict[str, Any]:
    intent = detect_mentor_intent(message)
    recent_sessions = svc.get_all_sessions_for_analytics(user_id)[:8]
    analytics = svc.get_latest_analytics_report(user_id)
    memories = svc.get_mentor_memory(user_id, limit=24)
    merged_onboarding = _merge_onboarding_context_with_memories(onboarding, memories)
    is_direct_knowledge = mentor_logic.looks_like_direct_knowledge_question(message) or (
        intent == "general_guidance"
        and mentor_logic.mentor_question_type(message) in {"definition", "comparison", "mechanism"}
        and not mentor_logic.should_use_profile_context(intent, message)
    )
    if mentor_logic.is_profile_lookup_question(message):
        return _build_profile_lookup_fallback(profile, merged_onboarding, message)
    if intent == "general_guidance" and is_direct_knowledge:
        return await _generate_direct_knowledge_result(merged_onboarding, message)
    if intent == "general_guidance":
        market_signals: list[dict[str, Any]] = []
        web_research: list[dict[str, str]] = []
        salvaged = await _salvage_general_guidance_result(
            profile,
            merged_onboarding,
            message,
            market_signals,
            web_research,
        )
        if salvaged and not _low_signal(salvaged["answer"], message, merged_onboarding, salvaged):
            return salvaged
    else:
        role_candidates = _normalize_role_candidates(message, merged_onboarding)
        industry = normalize_text(str((merged_onboarding or {}).get("industry") or ""))
        market_signals = svc.get_market_signals(industry=industry or None, roles=role_candidates or None)
        web_research = await search_market_context(message=message, onboarding=merged_onboarding, intent=intent)
        if intent == "market_outlook" and _looks_like_job_skill_lookup_request(message):
            return _build_direct_market_lookup_result(
                merged_onboarding,
                message,
                market_signals,
                web_research,
            )

    prompt = build_mentor_prompt(
        profile,
        merged_onboarding,
        analytics,
        recent_sessions,
        memories,
        recent_messages,
        market_signals,
        web_research,
        intent,
        message,
    )
    raw_result = await gemini.generate_json(prompt)
    result = _normalize_response(
        raw_result,
        intent,
        profile,
        merged_onboarding,
        message,
        market_signals,
        web_research,
    )

    if intent == "general_guidance" and _low_signal(result["answer"], message, merged_onboarding, result):
        salvaged = await _salvage_general_guidance_result(
            profile,
            merged_onboarding,
            message,
            market_signals,
            web_research,
        )
        if salvaged and not _low_signal(salvaged["answer"], message, merged_onboarding, salvaged):
            result = salvaged

    if _low_signal(result["answer"], message, merged_onboarding, result):
        rewrite_prompt = _build_rewrite_prompt(
            message,
            intent,
            profile,
            merged_onboarding,
            analytics,
            recent_sessions,
            recent_messages,
            memories,
            market_signals,
            web_research,
            json.dumps(result, ensure_ascii=False, indent=2),
        )
        try:
            rewritten_raw = await gemini.generate_json(rewrite_prompt)
            rewritten_result = _normalize_response(
                rewritten_raw,
                intent,
                profile,
                merged_onboarding,
                message,
                market_signals,
                web_research,
            )
            if not _low_signal(rewritten_result["answer"], message, merged_onboarding, rewritten_result):
                result = rewritten_result
        except Exception:
            pass

    if intent == "general_guidance" and _low_signal(result["answer"], message, merged_onboarding, result):
        salvaged = await _salvage_general_guidance_result(
            profile,
            merged_onboarding,
            message,
            market_signals,
            web_research,
        )
        if salvaged and not _low_signal(salvaged["answer"], message, merged_onboarding, salvaged):
            result = salvaged

    if _low_signal(result["answer"], message, merged_onboarding, result):
        result = build_personalized_fallback(
            profile,
            merged_onboarding,
            intent,
            message,
            market_signals,
            web_research,
        )

    return result

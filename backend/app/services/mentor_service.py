import json
import re
from collections import Counter
from typing import Any

from app.models.mentor import MentorIntent
from app.services.gemini_service import gemini
from app.services.market_research_service import search_market_context
from app.services.supabase_service import SupabaseService
from app.utils.helpers import get_user_context, normalize_text, strip_accents
from app.utils.mentor_prompts import MENTOR_RESPONSE_PROMPT, MENTOR_RESPONSE_REWRITE_PROMPT


INTENT_PATTERNS: list[tuple[MentorIntent, tuple[str, ...]]] = [
    ("career_roles", ("vị trí", "vai trò", "nghề", "công việc", "role", "chức danh")),
    ("market_outlook", ("cơ hội", "triển vọng", "phát triển", "thu nhập", "nhu cầu", "thị trường")),
    ("skill_gap", ("thiếu kỹ năng", "thiếu gì", "kỹ năng cần", "kiến thức nào tôi cần có", "cần có gì")),
    ("learning_roadmap", ("lộ trình", "nên học gì", "học gì trước", "bắt đầu từ đâu", "roadmap")),
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
    "business analyst": "data",
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
    "marketing": ["Customer insight", "Content", "SEO", "Meta Ads", "Google Ads", "Google Analytics"],
    "product": ["User research", "Roadmapping", "Product metrics", "SQL", "A/B testing"],
    "general": ["Problem solving", "Communication", "Project work", "Portfolio"],
}


def detect_mentor_intent(message: str) -> MentorIntent:
    text = strip_accents(normalize_text(message)).lower()
    for intent, keywords in INTENT_PATTERNS:
        if any(strip_accents(keyword).lower() in text for keyword in keywords):
            return intent
    return "general_guidance"


def build_thread_title(message: str) -> str:
    compact = normalize_text(message).strip(" ?.!,:;")
    if not compact:
        return "Phiên mentor mới"
    return (" ".join(compact.split()[:8]).strip() or "Phiên mentor mới")[:72]


def _track(message: str, onboarding: dict[str, Any] | None) -> str:
    message_blob = strip_accents(normalize_text(message)).lower()
    context_blob = " ".join(
        strip_accents(normalize_text(str((onboarding or {}).get(key) or ""))).lower()
        for key in ("major", "industry", "job_title", "ai_persona")
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
    daily = int(onboarding.get("daily_study_minutes") or 30)
    track = _track("", onboarding)
    questions: list[str] = []
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
        "data": ["data analyst", "business analyst"],
        "marketing": ["marketing specialist", "digital marketing specialist"],
        "product": ["product analyst", "product manager"],
    }
    return mapping.get(_track(message, onboarding), [])[:4]


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
    for key, label in (("major", "Nền tảng học tập"), ("industry", "Ngành nghề hiện tại"), ("job_title", "Vai trò hiện tại"), ("learning_style", "Phong cách học"), ("ai_persona", "Persona hiện tại")):
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


def _missing_context(onboarding: dict[str, Any] | None) -> list[str]:
    onboarding = onboarding or {}
    missing: list[str] = []
    if not onboarding.get("status"):
        missing.append("trạng thái hiện tại")
    if onboarding.get("status") in {"student", "both"} and not onboarding.get("major"):
        missing.append("chuyên ngành hoặc nền tảng học tập")
    if onboarding.get("status") in {"working", "both"} and not onboarding.get("industry"):
        missing.append("ngành nghề hiện tại")
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
            cleaned[target_key] = _normalize_list_of_strings(value, 6) if isinstance(value, list) else normalize_text(str(value or ""))
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


def _low_signal(answer: str, message: str, onboarding: dict[str, Any] | None) -> bool:
    text = strip_accents(normalize_text(answer)).lower()
    if not text:
        return True
    if any(marker in text for marker in GENERIC_MARKERS):
        return True
    track = _track(message, onboarding)
    if track != "general" and not any(strip_accents(skill).lower() in text for skill in SKILL_CATALOG[track][:6]):
        if len(text.split()) < 90:
            return True
    question = strip_accents(normalize_text(message)).lower()
    if any(token in question for token in ("hoc gi", "can gi", "ky nang", "lo trinh")) and len(text.split()) < 70:
        return True
    return False


def _merge(primary: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    merged = dict(primary)
    for key in ("career_paths", "market_signals", "skill_gaps", "recommended_learning_steps", "suggested_followups", "sources"):
        if not merged.get(key):
            merged[key] = fallback.get(key, [])
    if not merged.get("answer"):
        merged["answer"] = fallback.get("answer", "")
    return merged


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
    context_payload = {**get_user_context(onboarding), "analytics": analytics or {}, "raw_onboarding": onboarding or {}}
    profile_digest = _profile_digest(profile, onboarding, analytics, memories)
    market_brief = _market_brief(message, onboarding, market_signals, web_research)
    return MENTOR_RESPONSE_PROMPT.format(
        profile_json=json.dumps(_serialize_profile(profile, onboarding), ensure_ascii=False, indent=2),
        profile_digest=json.dumps(profile_digest, ensure_ascii=False, indent=2),
        user_context_json=json.dumps(context_payload, ensure_ascii=False, indent=2),
        learning_history_json=json.dumps(_serialize_sessions(recent_sessions), ensure_ascii=False, indent=2),
        memory_json=json.dumps(memories[:20], ensure_ascii=False, indent=2),
        conversation_json=json.dumps(_serialize_messages(messages), ensure_ascii=False, indent=2),
        market_json=json.dumps(market_signals[:8], ensure_ascii=False, indent=2),
        market_brief_json=json.dumps(market_brief, ensure_ascii=False, indent=2),
        web_research_json=json.dumps(web_research[:6], ensure_ascii=False, indent=2),
        missing_context_json=json.dumps(_missing_context(onboarding), ensure_ascii=False, indent=2),
        response_style_json=json.dumps(_response_style(onboarding), ensure_ascii=False, indent=2),
        intent=intent,
        message=normalize_text(message),
    )


def _build_rewrite_prompt(
    message: str,
    intent: MentorIntent,
    onboarding: dict[str, Any] | None,
    profile_digest: dict[str, Any],
    market_brief: dict[str, Any],
    web_research: list[dict[str, str]],
    draft_answer: str,
) -> str:
    return MENTOR_RESPONSE_REWRITE_PROMPT.format(
        profile_digest=json.dumps(profile_digest, ensure_ascii=False, indent=2),
        response_style_json=json.dumps(_response_style(onboarding), ensure_ascii=False, indent=2),
        intent=intent,
        market_brief_json=json.dumps(market_brief, ensure_ascii=False, indent=2),
        web_research_json=json.dumps(web_research[:6], ensure_ascii=False, indent=2),
        message=normalize_text(message),
        draft_answer=draft_answer,
    )


def build_personalized_fallback(
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
    daily = int(onboarding.get("daily_study_minutes") or 30)
    track = _track(message, onboarding)
    market_brief = _market_brief(message, onboarding, market_signals, web_research)
    top_skills = market_brief["top_skills"][:5]
    source_names = market_brief["source_names"][:3]
    source_hint = f" Theo các tín hiệu mình quét được từ {', '.join(source_names)}, nhóm kỹ năng nổi lên là {', '.join(top_skills[:4])}." if source_names else ""
    context_bits = [bit for bit in [("bạn đang là sinh viên" if status == "student" else "bạn đang đi làm" if status == "working" else "bạn vừa học vừa làm" if status == "both" else ""), f"nền tảng {major}" if major else "", f"ngành {industry}" if industry else "", f"vai trò hiện tại {job_title}" if job_title else ""] if bit]
    prefix = f"Với việc {', '.join(context_bits)}, " if context_bits else ""

    if track == "dev":
        answer = (
            f"{prefix}nếu bạn đi theo hướng dev thì nên học theo 4 khối kiến thức, không học dàn trải.\n\n"
            f"- Khối 1: nền tảng lập trình và tư duy giải quyết vấn đề, ưu tiên một ngôn ngữ chính như JavaScript hoặc Python.\n"
            f"- Khối 2: web fundamentals gồm HTML/CSS, JavaScript, Git/GitHub và cách làm việc với API.\n"
            f"- Khối 3: một nhánh đủ sâu để tạo đầu ra, thường nên bắt đầu bằng frontend với React nếu bạn muốn thấy sản phẩm nhanh.\n"
            f"- Khối 4: project thật, vì nhà tuyển dụng nhìn vào khả năng build sản phẩm chứ không chỉ nhìn khóa học đã xem.{source_hint}\n\n"
            f"Với quỹ thời gian khoảng {daily} phút mỗi ngày, hợp lý nhất là chia phần lớn thời gian cho code và project. Trong 6-8 tuần đầu, mục tiêu nên là làm được 2 project nhỏ có Git, form, gọi API và deploy được."
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
    elif track == "data":
        answer = (
            f"{prefix}nếu bạn theo Data Analyst thì đừng bắt đầu từ quá nhiều công cụ. Hãy đi theo chuỗi: xử lý dữ liệu -> phân tích -> trực quan hóa -> kể chuyện bằng dữ liệu.\n\n"
            f"- Bước đầu là Excel hoặc Google Sheets để làm sạch dữ liệu và hiểu cấu trúc bảng.\n"
            f"- Sau đó học SQL thật chắc vì đây là kỹ năng gần như bắt buộc cho hầu hết vị trí data đầu vào.\n"
            f"- Tiếp theo là Power BI hoặc Tableau để biến dữ liệu thành dashboard có insight.\n"
            f"- Cuối cùng là tư duy business: đọc số để đưa ra đề xuất chứ không chỉ trình bày biểu đồ.{source_hint}\n\n"
            f"Nếu học đều {daily} phút mỗi ngày, bạn nên ưu tiên đầu ra là 1 dashboard hoàn chỉnh từ dữ liệu thật và 1 case viết insight rõ ràng."
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
            f"- Cuối cùng mới mở rộng sang kỹ năng phụ hoặc các nhánh sâu hơn.{source_hint}\n\n"
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
    role_paths = [{"role": "Frontend Developer", "fit_reason": "Dễ tạo đầu ra nhanh qua project web.", "entry_level": "Intern / Junior", "required_skills": ["JavaScript", "HTML/CSS", "React", "Git"], "next_step": "Làm 2-3 project web nhỏ rồi tối ưu dần lên React + API."}] if track == "dev" else [{"role": "Data Analyst", "fit_reason": "Có đầu ra rõ qua dashboard và case business.", "entry_level": "Intern / Junior", "required_skills": ["Excel", "SQL", "Power BI/Tableau"], "next_step": "Làm 1 dashboard hoàn chỉnh từ dữ liệu thật."}] if track == "data" else []
    skill_gaps = [{"skill": skill, "gap_level": "high" if index < 2 else "medium", "why_it_matters": "Đây là nhóm năng lực xuất hiện lặp lại trong tín hiệu nghề nghiệp.", "suggested_action": f"Ưu tiên học và tạo đầu ra nhỏ để chứng minh được {skill}."} for index, skill in enumerate((top_skills or SKILL_CATALOG.get(track, SKILL_CATALOG["general"]))[:4])]
    return {"intent": intent, "answer": answer, "career_paths": role_paths, "market_signals": _fallback_market_signals(web_research), "skill_gaps": skill_gaps, "recommended_learning_steps": steps, "suggested_followups": followups, "memory_updates": [], "sources": _fallback_sources(market_signals, web_research)}


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
        "career_paths": _normalize_items(raw_result.get("career_paths"), {"role": "role", "fit_reason": "fit_reason", "entry_level": "entry_level", "required_skills": "required_skills", "next_step": "next_step"}),
        "market_signals": _normalize_items(raw_result.get("market_signals"), {"role_name": "role_name", "demand_summary": "demand_summary", "top_skills": "top_skills", "source_name": "source_name", "source_url": "source_url"}),
        "skill_gaps": _normalize_items(raw_result.get("skill_gaps"), {"skill": "skill", "gap_level": "gap_level", "why_it_matters": "why_it_matters", "suggested_action": "suggested_action"}),
        "recommended_learning_steps": _normalize_list_of_strings(raw_result.get("recommended_learning_steps"), 6),
        "suggested_followups": _normalize_list_of_strings(raw_result.get("suggested_followups"), 5),
        "memory_updates": _normalize_memory_updates(raw_result.get("memory_updates")),
        "sources": _normalize_sources(raw_result.get("sources")),
    }
    if not normalized["sources"]:
        normalized["sources"] = _fallback_sources(market_signals, web_research)
    if not normalized["market_signals"]:
        normalized["market_signals"] = _fallback_market_signals(web_research)
    fallback = build_personalized_fallback(profile, onboarding, intent, message, market_signals, web_research)
    normalized = _merge(normalized, fallback)
    if _low_signal(normalized["answer"], message, onboarding):
        normalized["answer"] = fallback["answer"]
        normalized["recommended_learning_steps"] = fallback["recommended_learning_steps"]
        normalized["suggested_followups"] = fallback["suggested_followups"]
        if fallback.get("market_signals"):
            normalized["market_signals"] = fallback["market_signals"]
        if fallback.get("sources"):
            normalized["sources"] = fallback["sources"]
    return normalized


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
    role_candidates = _normalize_role_candidates(message, onboarding)
    industry = normalize_text(str((onboarding or {}).get("industry") or ""))
    market_signals = svc.get_market_signals(industry=industry or None, roles=role_candidates or None)
    web_research = await search_market_context(message=message, onboarding=onboarding, intent=intent)

    prompt = build_mentor_prompt(profile, onboarding, analytics, recent_sessions, memories, recent_messages, market_signals, web_research, intent, message)
    raw_result = await gemini.generate_json(prompt)
    result = _normalize_response(raw_result, intent, profile, onboarding, message, market_signals, web_research)

    if _low_signal(result["answer"], message, onboarding):
        rewrite_prompt = _build_rewrite_prompt(message, intent, onboarding, _profile_digest(profile, onboarding, analytics, memories), _market_brief(message, onboarding, market_signals, web_research), web_research, result["answer"])
        try:
            rewritten_raw = await gemini.generate_json(rewrite_prompt)
            rewritten_result = _normalize_response(rewritten_raw, intent, profile, onboarding, message, market_signals, web_research)
            if not _low_signal(rewritten_result["answer"], message, onboarding):
                result = rewritten_result
        except Exception:
            pass

    if _low_signal(result["answer"], message, onboarding):
        result = build_personalized_fallback(profile, onboarding, intent, message, market_signals, web_research)

    return result

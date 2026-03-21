from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.models.user import OnboardingData, OnboardingResponse
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.core_ai_prompts import ONBOARDING_CLASSIFY_CORE_PROMPT
from app.utils.helpers import build_learner_profile


router = APIRouter()


ROLE_TOPIC_HINTS: dict[str, list[str]] = {
    "frontend developer": ["HTML/CSS", "JavaScript", "React", "Git/GitHub", "UI project"],
    "backend developer": ["API design", "Database", "Python/Node.js", "Authentication", "Deployment"],
    "full-stack developer": ["JavaScript", "Frontend", "Backend", "Database", "Full-flow project"],
    "data analyst": ["Excel/Sheets", "SQL", "Dashboard", "Data cleaning", "Business insight"],
    "business analyst": [
        "Requirement analysis",
        "Process mapping",
        "Documentation",
        "Stakeholder communication",
        "SQL cơ bản",
    ],
    "digital marketing specialist": ["Content", "SEO", "Social media", "Analytics", "Campaign planning"],
    "performance marketing specialist": ["Meta Ads", "Google Ads", "Tracking", "Funnel", "Optimization"],
    "product manager": ["User research", "Roadmap", "Product metrics", "Prioritization", "Cross-team execution"],
}

ROLE_KEYWORD_HINTS: list[tuple[tuple[str, ...], list[str]]] = [
    (("frontend", "react", "ui"), ["HTML/CSS", "JavaScript", "React", "UI implementation", "Responsive layout"]),
    (("backend", "api", "server"), ["API design", "Database", "Authentication", "Business logic", "Deployment"]),
    (("full-stack", "fullstack"), ["Frontend", "Backend", "Database", "API integration", "Full-flow project"]),
    (("data", "analyst", "analytics", "bi"), ["Excel/Sheets", "SQL", "Dashboard", "Data cleaning", "Business insight"]),
    (("marketing", "content", "seo"), ["Content", "SEO", "Social media", "Analytics", "Campaign planning"]),
    (("performance", "ads", "paid media"), ["Meta Ads", "Google Ads", "Tracking", "Funnel", "Optimization"]),
    (("product", "pm"), ["User research", "Roadmap", "Prioritization", "Product metrics", "Stakeholder alignment"]),
    (("designer", "design", "ux", "ui/ux"), ["UX research", "Wireframe", "Visual design", "Figma", "Design system"]),
    (("teacher", "giao vien", "trainer", "giang vien"), ["Lesson planning", "Instruction design", "Assessment", "Feedback", "Classroom practice"]),
    (("qa", "tester", "quality assurance"), ["Test case", "Bug reporting", "Regression testing", "Automation basics", "Product thinking"]),
]

GENERIC_TOPIC_MARKERS = {
    "technology",
    "science",
    "history",
    "business",
    "language",
    "health",
    "finance",
    "arts",
    "general",
    "general knowledge",
    "study skills",
}

OPTIONAL_ONBOARDING_FIELDS = {
    "target_role",
    "current_focus",
    "current_challenges",
    "desired_outcome",
    "learning_constraints",
    "ai_persona",
    "ai_persona_description",
    "ai_recommended_topics",
}

LOW_SIGNAL_ONBOARDING_PATTERNS = (
    "ai tạm thời chưa phân loại",
    "ai tam thoi chua phan loai",
    "dùng hồ sơ cơ bản",
    "dung ho so co ban",
    "general learner",
    "knowledge seeker",
    "needs clear guidance",
)


def _build_onboarding_prompt(data: OnboardingData) -> str:
    learner_profile = build_learner_profile(data.model_dump(mode="json"))
    return ONBOARDING_CLASSIFY_CORE_PROMPT.format(learner_profile=learner_profile)


def _normalize_topic_text(topic: str) -> str:
    return " ".join(str(topic).strip().lower().split())


def _normalize_sentence(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _looks_generic_topic(topic: str) -> bool:
    normalized = _normalize_topic_text(topic)
    if not normalized:
        return True
    if normalized in GENERIC_TOPIC_MARKERS:
        return True
    return normalized in {"topic", "learning", "knowledge", "career", "skills"}


def _role_hint_topics(target_role: str | None) -> list[str]:
    normalized = _normalize_sentence(target_role).lower()
    if not normalized:
        return []

    direct_match = ROLE_TOPIC_HINTS.get(normalized)
    if direct_match:
        return direct_match

    for keywords, topics in ROLE_KEYWORD_HINTS:
        if any(keyword in normalized for keyword in keywords):
            return topics

    return []


def _merge_topic_candidates(*topic_groups: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []

    for topics in topic_groups:
        for topic in topics:
            cleaned = _normalize_sentence(topic)
            if not cleaned or _looks_generic_topic(cleaned):
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(cleaned)
            if len(merged) >= 5:
                return merged

    return merged


def _build_persona_name(data: OnboardingData, ai_result: dict | None = None) -> str:
    ai_result = ai_result or {}
    raw_persona = _normalize_sentence(str(ai_result.get("persona_name") or ai_result.get("persona") or ""))
    target_role = _normalize_sentence(data.target_role)

    if target_role:
        lowered = target_role.lower()
        if data.status == "student":
            return f"Sinh viên đang xây nền tảng để theo đuổi {target_role}"
        if data.status == "working":
            if any(keyword in lowered for keyword in ("analyst", "developer", "manager", "specialist", "engineer", "designer")):
                return f"Người đi làm đang chuyển hướng sang {target_role}"
            return f"Người đi làm đang phát triển theo hướng {target_role}"
        if data.status == "both":
            return f"Người học vừa học vừa làm hướng tới {target_role}"
        return f"Người học đang hướng tới {target_role}"

    if raw_persona and not any(pattern in raw_persona.lower() for pattern in LOW_SIGNAL_ONBOARDING_PATTERNS):
        return raw_persona

    if data.status == "student":
        return "Người học đang xây nền tảng nghề nghiệp"
    if data.status == "working":
        return "Người đi làm đang nâng cấp kỹ năng"
    if data.status == "both":
        return "Người học vừa học vừa làm"
    return "Người học đang tự định hướng"


def _build_teaching_strategy(data: OnboardingData, ai_result: dict | None = None) -> str:
    ai_result = ai_result or {}
    personalization = ai_result.get("personalization_rules")
    explanation_style = ""
    pacing = ""

    if isinstance(personalization, dict):
        explanation_style = _normalize_sentence(str(personalization.get("explanation_style") or ""))
        pacing = _normalize_sentence(str(personalization.get("pacing") or ""))

    style_map = {
        "visual": "ưu tiên sơ đồ, ví dụ trực quan và bản tóm tắt ngắn",
        "reading": "ưu tiên giải thích có cấu trúc, thuật ngữ rõ ràng và ghi chú cô đọng",
        "practice": "ưu tiên ví dụ thực hành, bài tập ngắn và đầu ra cụ thể",
        "mixed": "kết hợp giải thích ngắn, ví dụ gần thực tế và bước thực hành nhỏ",
    }
    base_style = style_map.get(data.learning_style, style_map["mixed"])

    if explanation_style and pacing:
        return f"{base_style}; đồng thời giữ cách giải thích {explanation_style.lower()} và nhịp học {pacing.lower()}"
    if explanation_style:
        return f"{base_style}; đồng thời giữ cách giải thích {explanation_style.lower()}"
    return base_style


def _build_persona_description(
    data: OnboardingData,
    recommended_topics: list[str],
    ai_result: dict | None = None,
) -> str:
    target_role = _normalize_sentence(data.target_role)
    desired_outcome = _normalize_sentence(data.desired_outcome)
    current_focus = _normalize_sentence(data.current_focus)
    current_challenges = _normalize_sentence(data.current_challenges)
    learning_constraints = _normalize_sentence(data.learning_constraints)
    study_minutes = data.daily_study_minutes or 30

    direction_clause = f"theo đuổi mục tiêu {target_role}" if target_role else "xác định hướng học phù hợp"
    sentence_1_parts = [f"Người học hiện đang {direction_clause}."]
    if current_focus:
        sentence_1_parts.append(f"Trọng tâm hiện tại là {current_focus}.")
    if desired_outcome:
        sentence_1_parts.append(f"Đầu ra mong muốn trước mắt là {desired_outcome}.")

    sentence_2_parts: list[str] = []
    if current_challenges:
        sentence_2_parts.append(f"Khó khăn chính là {current_challenges}.")
    if learning_constraints:
        sentence_2_parts.append(f"Ràng buộc cần tính tới: {learning_constraints}.")
    else:
        sentence_2_parts.append(f"Quỹ học hiện tại khoảng {study_minutes} phút mỗi ngày.")

    teaching_strategy = _build_teaching_strategy(data, ai_result)
    topic_clause = ", ".join(recommended_topics[:3]) if recommended_topics else "khối kiến thức cốt lõi"
    sentence_3 = (
        f"DUO MIND nên ưu tiên cách dạy {teaching_strategy}, bắt đầu từ {topic_clause}, "
        "rồi mới mở rộng sang ví dụ và bài tập ứng dụng sát mục tiêu."
    )

    description_parts = [
        " ".join(sentence_1_parts).strip(),
        " ".join(sentence_2_parts).strip(),
        sentence_3.strip(),
    ]
    return " ".join(part for part in description_parts if part)


def _is_low_signal_persona(persona: str, description: str, data: OnboardingData) -> bool:
    combined = f"{persona} {description}".lower()
    if any(pattern in combined for pattern in LOW_SIGNAL_ONBOARDING_PATTERNS):
        return True
    if data.target_role and data.target_role.lower() not in combined:
        return True
    return len(description.split()) < 18


def _normalize_ai_payload(result: dict, data: OnboardingData) -> tuple[str, str, list[str]]:
    raw_topics = result.get("recommended_topics") or []
    ai_topics = [str(topic).strip() for topic in raw_topics if str(topic).strip()] if isinstance(raw_topics, list) else []
    role_hint_topics = _role_hint_topics(data.target_role)
    interest_topics = [str(topic).strip() for topic in data.topics_of_interest if str(topic).strip()]

    normalized_topics = _merge_topic_candidates(ai_topics, role_hint_topics, interest_topics)
    if not normalized_topics:
        normalized_topics = [
            "Tư duy học có cấu trúc",
            "Khái niệm cốt lõi",
            "Ví dụ ứng dụng",
            "Luyện tập ngắn",
            "Ôn tập có phản hồi",
        ]

    persona = _build_persona_name(data, result)
    description = _build_persona_description(data, normalized_topics[:5], result)
    if _is_low_signal_persona(persona, description, data):
        persona = _build_persona_name(data)
        description = _build_persona_description(data, normalized_topics[:5], None)

    return persona, description, normalized_topics[:5]


def _fallback_onboarding_payload(data: OnboardingData) -> tuple[str, str, list[str]]:
    recommended_topics = _merge_topic_candidates(
        [str(topic).strip() for topic in data.topics_of_interest if str(topic).strip()],
        _role_hint_topics(data.target_role),
    )
    if not recommended_topics:
        recommended_topics = [
            "Tư duy hệ thống",
            "Khái niệm cốt lõi",
            "Ví dụ ứng dụng",
            "Luyện tập ngắn",
            "Ôn tập có cấu trúc",
        ]

    persona = _build_persona_name(data)
    description = _build_persona_description(data, recommended_topics[:5], None)
    return persona, description, recommended_topics[:5]


def _sync_onboarding_context_memories(
    svc: SupabaseService,
    user_id: str,
    payload: dict,
) -> None:
    memory_specs = [
        ("profile", "age_range", payload.get("age_range"), 0.75),
        ("profile", "status", payload.get("status"), 0.75),
        ("profile", "education_level", payload.get("education_level"), 0.74),
        ("profile", "major", payload.get("major"), 0.72),
        ("profile", "school_name", payload.get("school_name"), 0.68),
        ("profile", "industry", payload.get("industry"), 0.72),
        ("profile", "job_title", payload.get("job_title"), 0.72),
        ("profile", "years_experience", payload.get("years_experience"), 0.74),
        ("goal", "target_role", payload.get("target_role"), 0.95),
        ("goal", "desired_outcome", payload.get("desired_outcome"), 0.92),
        ("summary", "current_focus", payload.get("current_focus"), 0.84),
        ("constraint", "current_challenges", payload.get("current_challenges"), 0.88),
        ("constraint", "learning_constraints", payload.get("learning_constraints"), 0.86),
        ("goal", "learning_goals", payload.get("learning_goals"), 0.88),
        ("goal", "topics_of_interest", payload.get("topics_of_interest"), 0.84),
        ("preference", "learning_style", payload.get("learning_style"), 0.80),
        ("preference", "daily_study_minutes", payload.get("daily_study_minutes"), 0.82),
        ("summary", "ai_persona", payload.get("ai_persona"), 0.90),
        ("summary", "ai_persona_description", payload.get("ai_persona_description"), 0.88),
        ("goal", "ai_recommended_topics", payload.get("ai_recommended_topics"), 0.86),
    ]

    for memory_type, memory_key, memory_value, confidence in memory_specs:
        if isinstance(memory_value, str):
            memory_value = memory_value.strip()
        if isinstance(memory_value, list):
            memory_value = [item for item in memory_value if item not in (None, "")]
        if memory_value in (None, "", []):
            continue
        try:
            svc.upsert_mentor_memory(
                user_id=user_id,
                memory_type=memory_type,
                memory_key=memory_key,
                memory_value=memory_value,
                confidence=confidence,
            )
        except Exception as exc:
            print(f"[onboarding] Failed to sync mentor memory {memory_key}: {exc}")


def _build_db_error_detail(exc: Exception) -> str:
    raw_message = str(exc).strip()
    lowered = raw_message.lower()

    if "user_onboarding" in lowered and "does not exist" in lowered:
        return (
            "Bảng public.user_onboarding chưa tồn tại hoặc chưa được khởi tạo đúng. "
            f"Chi tiết kỹ thuật: {raw_message}"
        )

    if "profiles" in lowered and "does not exist" in lowered:
        return (
            "Bảng public.profiles chưa tồn tại hoặc chưa được khởi tạo đúng. "
            f"Chi tiết kỹ thuật: {raw_message}"
        )

    if "column" in lowered and "does not exist" in lowered:
        return (
            "Schema onboarding hiện chưa đủ cột mà DUO MIND đang dùng. "
            "Hãy chạy file ensure_onboarding_core rồi thử lại. "
            f"Chi tiết kỹ thuật: {raw_message}"
        )

    if "violates foreign key constraint" in lowered:
        return (
            "Ràng buộc khóa ngoại giữa profiles và user_onboarding đang chưa đồng bộ. "
            f"Chi tiết kỹ thuật: {raw_message}"
        )

    return f"Không thể lưu onboarding vào database lúc này. Chi tiết kỹ thuật: {raw_message}"


def _extract_missing_schema_column(exc: Exception, table_name: str) -> str | None:
    raw_message = str(exc)
    pattern = rf"Could not find the '([^']+)' column of '{table_name}' in the schema cache"
    import re

    match = re.search(pattern, raw_message)
    if not match:
        return None
    return match.group(1)


def _persist_onboarding_with_schema_fallback(
    svc: SupabaseService,
    user_id: str,
    payload: dict,
) -> tuple[dict | None, list[str]]:
    safe_payload = dict(payload)
    dropped_columns: list[str] = []

    while True:
        try:
            result = svc.upsert_onboarding(user_id, safe_payload)
            return result, dropped_columns
        except Exception as exc:
            missing_column = _extract_missing_schema_column(exc, "user_onboarding")
            if not missing_column or missing_column not in OPTIONAL_ONBOARDING_FIELDS:
                raise
            if missing_column not in safe_payload:
                raise
            dropped_columns.append(missing_column)
            safe_payload.pop(missing_column, None)
            print(
                f"[onboarding] Missing schema column '{missing_column}' in user_onboarding. "
                "Dropping field and retrying."
            )


@router.post("/submit", response_model=OnboardingResponse)
async def submit_onboarding(
    data: OnboardingData,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> OnboardingResponse:
    svc = SupabaseService(supabase)

    try:
        svc.ensure_profile(
            current_user["id"],
            email=current_user.get("email"),
            full_name=current_user.get("full_name"),
            avatar_url=current_user.get("avatar_url"),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_build_db_error_detail(exc),
        ) from exc

    try:
        ai_result = await gemini.generate_json(_build_onboarding_prompt(data))
        ai_persona, ai_description, ai_topics = _normalize_ai_payload(ai_result, data)
    except Exception as exc:
        print(f"[onboarding] Gemini classification failed: {exc}")
        ai_persona, ai_description, ai_topics = _fallback_onboarding_payload(data)

    payload = {
        **data.model_dump(mode="json"),
        "ai_persona": ai_persona,
        "ai_persona_description": ai_description,
        "ai_recommended_topics": ai_topics,
    }

    try:
        _, dropped_columns = _persist_onboarding_with_schema_fallback(svc, current_user["id"], payload)
        if dropped_columns:
            print(
                "[onboarding] Completed with reduced payload because DB schema is missing columns: "
                + ", ".join(dropped_columns)
            )
        _sync_onboarding_context_memories(svc, current_user["id"], payload)
        svc.set_onboarded(current_user["id"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_build_db_error_detail(exc),
        ) from exc

    return OnboardingResponse(
        success=True,
        ai_persona=ai_persona,
        ai_persona_description=ai_description,
        ai_recommended_topics=ai_topics,
    )


@router.get("/me")
async def get_my_onboarding(
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict | None:
    svc = SupabaseService(supabase)
    return svc.get_onboarding(current_user["id"])

from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.models.user import OnboardingData, OnboardingResponse
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.prompts import ONBOARDING_CLASSIFY_PROMPT


router = APIRouter()


def _build_onboarding_prompt(data: OnboardingData) -> str:
    payload = data.model_dump(mode="json")
    return ONBOARDING_CLASSIFY_PROMPT.format(**payload)


def _normalize_ai_payload(result: dict) -> tuple[str, str, list[str]]:
    persona = str(result.get("persona") or "general_learner").strip()
    description = str(
        result.get("description") or "Nguoi hoc dang trong giai doan xay dung nen tang."
    ).strip()

    topics = result.get("recommended_topics") or []
    if not isinstance(topics, list):
        topics = []
    normalized_topics = [str(topic).strip() for topic in topics if str(topic).strip()]
    if not normalized_topics:
        normalized_topics = ["Tu duy hoc tap", "Tom tat kien thuc", "Tu danh gia"]

    return persona, description, normalized_topics[:5]


def _fallback_onboarding_payload(data: OnboardingData) -> tuple[str, str, list[str]]:
    if data.status == "student":
        if data.education_level in {"university", "postgrad"}:
            persona = "university_student"
        elif data.education_level == "high_school":
            persona = "high_school_student"
        else:
            persona = "student_learner"
    elif data.status == "working":
        persona = "working_professional"
    elif data.status == "both":
        persona = "working_student"
    else:
        persona = "self_directed_learner"

    recommended_topics = data.topics_of_interest[:5]
    if not recommended_topics:
        recommended_topics = ["technology", "science", "business"]

    goals = ", ".join(data.learning_goals[:2]) or "mo rong kien thuc"
    description = (
        "Gemini tam thoi khong phan tich duoc, nen he thong da dung co che fallback "
        f"dua tren profile co ban. DUO MIND se uu tien noi dung phu hop voi muc tieu {goals}."
    )

    return persona, description, recommended_topics


@router.post("/submit", response_model=OnboardingResponse)
async def submit_onboarding(
    data: OnboardingData,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> OnboardingResponse:
    svc = SupabaseService(supabase)
    svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )

    try:
        ai_result = await gemini.generate_json(_build_onboarding_prompt(data))
        ai_persona, ai_description, ai_topics = _normalize_ai_payload(ai_result)
    except Exception as exc:
        print(f"[onboarding] Gemini classification failed: {exc}")
        ai_persona, ai_description, ai_topics = _fallback_onboarding_payload(data)
    payload = {
        **data.model_dump(mode="json"),
        "ai_persona": ai_persona,
        "ai_persona_description": ai_description,
        "ai_recommended_topics": ai_topics,
    }

    svc.upsert_onboarding(current_user["id"], payload)
    svc.set_onboarded(current_user["id"])

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

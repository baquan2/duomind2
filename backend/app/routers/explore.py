from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.models.analysis import ExploreRequest, ExploreResult
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.fallbacks import (
    build_basic_infographic,
    build_basic_mindmap,
    build_explore_fallback,
)
from app.utils.helpers import get_user_context, normalize_topic_tags
from app.utils.prompts import (
    EXPLORE_TOPIC_PROMPT,
    INFOGRAPHIC_GENERATE_PROMPT,
    MINDMAP_GENERATE_PROMPT,
)


router = APIRouter()


@router.post("/", response_model=ExploreResult)
async def explore_topic(
    request: ExploreRequest,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> ExploreResult:
    svc = SupabaseService(supabase)
    start_time = perf_counter()
    svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )

    onboarding = svc.get_onboarding(current_user["id"])
    prompt_context = get_user_context(onboarding)

    try:
        ai_result = await gemini.generate_json(
            EXPLORE_TOPIC_PROMPT.format(
                prompt=request.prompt,
                language=request.language,
                **prompt_context,
            )
        )
    except Exception as exc:
        print(f"[explore] Topic exploration failed, using fallback: {exc}")
        ai_result = build_explore_fallback(request.prompt)

    title = str(ai_result.get("title") or "Khám phá chủ đề").strip()
    summary = str(ai_result.get("summary") or "").strip()
    key_points = [
        str(point).strip()
        for point in (ai_result.get("key_points") or [])
        if str(point).strip()
    ]

    try:
        infographic_data = await gemini.generate_json(
            INFOGRAPHIC_GENERATE_PROMPT.format(
                title=title,
                summary=summary,
                key_points="\n".join(key_points),
            )
        )
    except Exception as exc:
        print(f"[explore] Infographic generation failed, using fallback: {exc}")
        infographic_data = build_basic_infographic(title, summary, key_points)

    try:
        mindmap_data = await gemini.generate_json(
            MINDMAP_GENERATE_PROMPT.format(
                content=summary + "\n" + "\n".join(key_points),
                title=title,
            )
        )
    except Exception as exc:
        print(f"[explore] Mind map generation failed, using fallback: {exc}")
        mindmap_data = build_basic_mindmap(title, key_points)

    topic_tags = normalize_topic_tags(ai_result.get("topic_tags"), title or request.prompt)

    session = svc.create_session(
        current_user["id"],
        {
            "session_type": "explore",
            "title": title,
            "user_input": request.prompt,
            "topic_tags": topic_tags,
            "summary": summary,
            "key_points": key_points,
            "infographic_data": infographic_data,
            "mindmap_data": mindmap_data,
            "language": request.language,
            "duration_ms": int((perf_counter() - start_time) * 1000),
        },
    )
    if not session or not session.get("id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lưu phiên khám phá.",
        )

    return ExploreResult(
        session_id=session["id"],
        title=title,
        summary=summary,
        key_points=key_points,
        infographic_data=infographic_data,
        topic_tags=topic_tags,
        mindmap_data=mindmap_data,
    )

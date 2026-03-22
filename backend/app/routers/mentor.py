from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.models.mentor import (
    MentorChatResponse,
    MentorMessageItem,
    MentorMessageRequest,
    MentorSuggestedQuestionsResponse,
    MentorThreadCreateRequest,
    MentorThreadDetail,
    MentorThreadSummary,
)
from app.services.mentor_service import (
    build_personalized_fallback,
    build_suggested_questions,
    build_thread_title,
    detect_mentor_intent,
    generate_mentor_response,
)
from app.services.supabase_service import SupabaseService
from app.utils.helpers import normalize_text


router = APIRouter()


def _map_thread(thread: dict) -> MentorThreadSummary:
    return MentorThreadSummary(
        id=str(thread.get("id")),
        title=str(thread.get("title") or "Phiên mentor"),
        status=str(thread.get("status") or "active"),
        last_message_at=thread.get("last_message_at"),
        created_at=thread.get("created_at"),
        updated_at=thread.get("updated_at"),
    )


def _map_message(message: dict) -> MentorMessageItem:
    return MentorMessageItem(
        id=str(message.get("id")),
        thread_id=str(message.get("thread_id")),
        role=str(message.get("role") or "assistant"),
        intent=message.get("intent"),
        content=str(message.get("content") or ""),
        answer_mode=message.get("answer_mode"),
        response_data=message.get("response_data"),
        sources=message.get("sources") or [],
        related_materials=message.get("related_materials") or [],
        request_payload=message.get("request_payload"),
        context_snapshot=message.get("context_snapshot"),
        generation_trace=message.get("generation_trace"),
        created_at=message.get("created_at"),
    )


@router.get("/threads", response_model=list[MentorThreadSummary])
async def get_threads(
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> list[MentorThreadSummary]:
    svc = SupabaseService(supabase)
    threads = svc.get_mentor_threads(current_user["id"])
    return [_map_thread(thread) for thread in threads]


@router.post("/threads", response_model=MentorThreadSummary)
async def create_thread(
    request: MentorThreadCreateRequest,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> MentorThreadSummary:
    svc = SupabaseService(supabase)
    svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )

    title = normalize_text(request.title or "") or "Phiên mentor mới"
    thread = svc.create_mentor_thread(current_user["id"], title)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo phiên mentor.",
        )

    return _map_thread(thread)


@router.get("/threads/{thread_id}", response_model=MentorThreadDetail)
async def get_thread_detail(
    thread_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> MentorThreadDetail:
    svc = SupabaseService(supabase)
    thread = svc.get_mentor_thread(thread_id, current_user["id"])
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy phiên mentor.",
        )

    messages = svc.get_mentor_messages(thread_id, current_user["id"])
    return MentorThreadDetail(
        thread=_map_thread(thread),
        messages=[_map_message(message) for message in messages],
    )


@router.get("/suggested-questions", response_model=MentorSuggestedQuestionsResponse)
async def get_suggested_questions(
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> MentorSuggestedQuestionsResponse:
    svc = SupabaseService(supabase)
    profile = svc.get_profile(current_user["id"])
    onboarding = svc.get_onboarding(current_user["id"])
    return MentorSuggestedQuestionsResponse(
        questions=build_suggested_questions(profile, onboarding)
    )


@router.post("/chat", response_model=MentorChatResponse)
async def mentor_chat(
    request: MentorMessageRequest,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> MentorChatResponse:
    svc = SupabaseService(supabase)
    profile = svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )
    onboarding = svc.get_onboarding(current_user["id"])

    if request.thread_id:
        thread = svc.get_mentor_thread(request.thread_id, current_user["id"])
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy phiên mentor.",
            )
    else:
        title = build_thread_title(request.message)
        thread = svc.create_mentor_thread(current_user["id"], title)

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể khởi tạo phiên mentor.",
        )

    thread_id = str(thread["id"])
    existing_messages = svc.get_mentor_messages(thread_id, current_user["id"], limit=30)

    user_message = svc.create_mentor_message(
        thread_id=thread_id,
        user_id=current_user["id"],
        role="user",
        content=request.message,
        request_payload={
            "normalized_message": normalize_text(request.message),
        },
    )
    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lưu câu hỏi mentor.",
        )

    try:
        mentor_result = await generate_mentor_response(
            svc=svc,
            user_id=current_user["id"],
            profile=profile,
            onboarding=onboarding,
            message=request.message,
            recent_messages=existing_messages + [user_message],
        )
    except Exception as exc:
        print(f"[mentor] Mentor response failed: {exc}")
        mentor_result = build_personalized_fallback(
            profile=profile,
            onboarding=onboarding,
            intent=detect_mentor_intent(request.message),
            message=request.message,
            recent_messages=existing_messages + [user_message],
        )

    try:
        assistant_message = svc.create_mentor_message(
            thread_id=thread_id,
            user_id=current_user["id"],
            role="assistant",
            content=mentor_result["answer"],
            intent=mentor_result["intent"],
            response_data=mentor_result,
            sources=mentor_result["sources"],
            related_materials=mentor_result.get("related_materials"),
            answer_mode=mentor_result.get("answer_mode"),
            request_payload=mentor_result.get("request_payload"),
            context_snapshot=mentor_result.get("context_snapshot"),
            generation_trace=mentor_result.get("generation_trace"),
            memory_updates=mentor_result.get("memory_updates"),
        )
    except Exception as exc:
        print(f"[mentor] Failed to persist rich assistant message: {exc}")
        assistant_message = svc.create_mentor_message(
            thread_id=thread_id,
            user_id=current_user["id"],
            role="assistant",
            content=mentor_result["answer"],
            intent=mentor_result["intent"],
            response_data=mentor_result,
            sources=mentor_result["sources"],
        )

    if not assistant_message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lưu phản hồi mentor.",
        )

    for memory_update in mentor_result.get("memory_updates", []):
        try:
            svc.upsert_mentor_memory(
                user_id=current_user["id"],
                memory_type=str(memory_update["memory_type"]),
                memory_key=str(memory_update["memory_key"]),
                memory_value=memory_update["memory_value"],
                confidence=float(memory_update.get("confidence", 0.8)),
                source_thread_id=thread_id,
            )
        except Exception as exc:
            print(
                "[mentor] Failed to persist memory update "
                f"{memory_update.get('memory_key')}: {exc}"
            )

    try:
        messages = svc.get_mentor_messages(thread_id, current_user["id"], limit=50)
    except Exception as exc:
        print(f"[mentor] Failed to reload messages after reply: {exc}")
        messages = existing_messages + [user_message, assistant_message]

    return MentorChatResponse(
        thread_id=thread_id,
        thread_title=str(thread.get("title") or "Phiên mentor"),
        message_id=str(assistant_message["id"]),
        intent=mentor_result["intent"],
        answer=mentor_result["answer"],
        answer_mode=mentor_result.get("answer_mode"),
        career_paths=mentor_result["career_paths"],
        market_signals=mentor_result["market_signals"],
        skill_gaps=mentor_result["skill_gaps"],
        decision_summary=mentor_result.get("decision_summary"),
        recommended_learning_steps=mentor_result["recommended_learning_steps"],
        suggested_followups=mentor_result["suggested_followups"],
        sources=mentor_result["sources"],
        related_materials=mentor_result.get("related_materials") or [],
        request_payload=mentor_result.get("request_payload"),
        context_snapshot=mentor_result.get("context_snapshot"),
        generation_trace=mentor_result.get("generation_trace"),
        save_metadata=assistant_message.get("_save_metadata"),
        messages=[_map_message(message) for message in messages],
    )

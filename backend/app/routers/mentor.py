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


def _prepend_target_role_questions(
    questions: list[str],
    onboarding: dict | None,
) -> list[str]:
    target_role = normalize_text(str((onboarding or {}).get("target_role") or ""))
    if not target_role:
        return questions

    priority_questions = [
        f"Để tiến gần tới vai trò {target_role}, tôi nên ưu tiên học gì trong 30 ngày tới?",
        f"Với mục tiêu {target_role}, tôi đang thiếu những kỹ năng nào quan trọng nhất?",
    ]

    merged: list[str] = []
    seen: set[str] = set()
    for question in priority_questions + questions:
        cleaned = normalize_text(question)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            merged.append(question)
        if len(merged) >= 6:
            break
    return merged


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
        response_data=message.get("response_data"),
        sources=message.get("sources") or [],
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
        questions=_prepend_target_role_questions(build_suggested_questions(profile, onboarding), onboarding)
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
    thread = None

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
        content=normalize_text(request.message),
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
        )
    except Exception as exc:
        print(f"[mentor] Failed to persist rich assistant message: {exc}")
        try:
            assistant_message = svc.create_mentor_message(
                thread_id=thread_id,
                user_id=current_user["id"],
                role="assistant",
                content=mentor_result["answer"],
                intent=mentor_result["intent"],
                response_data=None,
                sources=[],
            )
        except Exception as fallback_exc:
            print(f"[mentor] Failed to persist lean assistant message: {fallback_exc}")
            assistant_message = {
                "id": "__assistant_fallback__",
                "thread_id": thread_id,
                "role": "assistant",
                "intent": mentor_result["intent"],
                "content": mentor_result["answer"],
                "response_data": mentor_result,
                "sources": mentor_result["sources"],
                "created_at": None,
            }
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
        career_paths=mentor_result["career_paths"],
        market_signals=mentor_result["market_signals"],
        skill_gaps=mentor_result["skill_gaps"],
        decision_summary=mentor_result.get("decision_summary"),
        recommended_learning_steps=mentor_result["recommended_learning_steps"],
        suggested_followups=mentor_result["suggested_followups"],
        sources=mentor_result["sources"],
        messages=[_map_message(message) for message in messages],
    )

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.services.supabase_service import SupabaseService


router = APIRouter()


def _hydrate_quiz_question(question: dict[str, Any]) -> dict[str, Any]:
    payload = dict(question)
    if payload.get("question_type") != "open":
        return payload

    metadata = payload.get("options")
    if isinstance(metadata, dict):
        payload["thinking_hints"] = metadata.get("thinking_hints") or []
        payload["sample_answer_points"] = metadata.get("sample_answer_points") or []
    else:
        payload["thinking_hints"] = []
        payload["sample_answer_points"] = []
    payload["options"] = None
    return payload


@router.get("/sessions")
async def get_history(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    session_type: str | None = Query(default=None),
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict[str, Any]:
    svc = SupabaseService(supabase)
    sessions = svc.get_sessions(current_user["id"], limit, offset)
    if session_type:
        sessions = [item for item in sessions if item.get("session_type") == session_type]
    return {"sessions": sessions, "total": len(sessions)}


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict[str, Any]:
    svc = SupabaseService(supabase)
    session = svc.get_session_detail(session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=404, detail="Khong tim thay phien hoc.")

    quiz_questions = [_hydrate_quiz_question(q) for q in svc.get_quiz_questions(session_id)]
    return {"session": session, "quiz_questions": quiz_questions}


@router.patch("/sessions/{session_id}/bookmark")
async def toggle_bookmark(
    session_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict[str, bool]:
    svc = SupabaseService(supabase)
    session = svc.get_session_detail(session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=404, detail="Khong tim thay phien hoc.")

    new_value = not bool(session.get("is_bookmarked", False))
    svc.db.table("learning_sessions").update({"is_bookmarked": new_value}).eq(
        "id", session_id
    ).execute()
    return {"is_bookmarked": new_value}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict[str, bool]:
    svc = SupabaseService(supabase)
    session = svc.get_session_detail(session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=404, detail="Khong tim thay phien hoc.")

    svc.db.table("learning_sessions").delete().eq("id", session_id).eq(
        "user_id", current_user["id"]
    ).execute()
    return {"success": True}

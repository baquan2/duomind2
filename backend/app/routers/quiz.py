from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.fallbacks import build_open_feedback_fallback, build_quiz_fallback
from app.utils.helpers import get_user_context
from app.utils.prompts import (
    OPEN_ANSWER_FEEDBACK_PROMPT,
    OPEN_QUESTIONS_PROMPT,
    QUIZ_GENERATE_PROMPT,
)


router = APIRouter()


class QuizGenerateRequest(BaseModel):
    session_id: str
    num_questions: int = Field(default=5, ge=1, le=10)
    include_open: bool = True


class QuizAnswerPayload(BaseModel):
    question_id: str
    user_answer: str


class QuizSubmitRequest(BaseModel):
    session_id: str
    answers: list[QuizAnswerPayload]


class OpenAnswerRequest(BaseModel):
    question_id: str
    user_answer: str
    language: str = "vi"


def _hydrate_question(question: dict[str, Any]) -> dict[str, Any]:
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


def _sanitize_question_for_client(question: dict[str, Any]) -> dict[str, Any]:
    payload = _hydrate_question(question)
    if payload.get("question_type") == "multiple_choice":
        payload.pop("correct_answer", None)
    return payload


def _normalize_critical_thinking_score(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return None
    return None


def _normalize_question_for_storage(
    question: dict[str, Any],
    fallback_order_index: int,
) -> dict[str, Any]:
    question_type = str(question.get("question_type") or "multiple_choice").strip()
    base_payload: dict[str, Any] = {
        "order_index": question.get("order_index", fallback_order_index),
        "question_type": question_type,
        "question_text": str(question.get("question_text") or "").strip(),
        "difficulty": str(question.get("difficulty") or "medium").strip(),
        "explanation": str(question.get("explanation") or "").strip(),
    }

    if question_type == "open":
        base_payload["options"] = {
            "thinking_hints": question.get("thinking_hints") or [],
            "sample_answer_points": question.get("sample_answer_points") or [],
        }
        base_payload["correct_answer"] = None
        return base_payload

    base_payload["options"] = question.get("options") or []
    base_payload["correct_answer"] = question.get("correct_answer")
    return base_payload


@router.post("/generate")
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict[str, list[dict[str, Any]]]:
    svc = SupabaseService(supabase)
    svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )
    session = svc.get_session_detail(request.session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên học.")

    existing_questions = svc.get_quiz_questions(request.session_id)
    if existing_questions:
        return {"questions": [_sanitize_question_for_client(q) for q in existing_questions]}

    onboarding = svc.get_onboarding(current_user["id"])
    prompt_context = get_user_context(onboarding)
    content = (session.get("user_input") or "") + "\n" + (session.get("summary") or "")

    try:
        mcq_result = await gemini.generate_json(
            QUIZ_GENERATE_PROMPT.format(
                content=content,
                summary=session.get("summary", ""),
                num_questions=request.num_questions,
                language=session.get("language", "vi"),
                **prompt_context,
            )
        )
        questions = mcq_result.get("questions") or []

        if request.include_open:
            open_result = await gemini.generate_json(
                OPEN_QUESTIONS_PROMPT.format(
                    title=session.get("title", ""),
                    summary=session.get("summary", ""),
                    language=session.get("language", "vi"),
                    **prompt_context,
                )
            )
            questions.extend(open_result.get("questions") or [])
    except Exception as exc:
        print(f"[quiz] Quiz generation failed, using fallback: {exc}")
        questions = build_quiz_fallback(
            str(session.get("title") or "Chủ đề"),
            str(session.get("summary") or ""),
            [str(point) for point in (session.get("key_points") or []) if str(point)],
            request.num_questions,
        )

    prepared_questions = [
        _normalize_question_for_storage(question, index)
        for index, question in enumerate(questions)
        if isinstance(question, dict)
    ]
    saved_questions = svc.save_quiz_questions(
        request.session_id,
        current_user["id"],
        prepared_questions,
    )
    return {"questions": [_sanitize_question_for_client(q) for q in saved_questions]}


@router.get("/{session_id}")
async def get_quiz(
    session_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict[str, list[dict[str, Any]]]:
    svc = SupabaseService(supabase)
    session = svc.get_session_detail(session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên học.")

    questions = svc.get_quiz_questions(session_id)
    response_questions = [_sanitize_question_for_client(question) for question in questions]
    return {"questions": response_questions}


@router.post("/submit")
async def submit_quiz(
    request: QuizSubmitRequest,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict[str, Any]:
    svc = SupabaseService(supabase)
    svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )
    session = svc.get_session_detail(request.session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên học.")

    all_questions = svc.get_quiz_questions(request.session_id)
    mcq_questions = {
        question["id"]: question
        for question in all_questions
        if question.get("question_type") == "multiple_choice"
    }

    results: list[dict[str, Any]] = []
    correct = 0
    for answer in request.answers:
        question = mcq_questions.get(answer.question_id)
        if not question:
            continue
        is_correct = answer.user_answer == question.get("correct_answer")
        if is_correct:
            correct += 1
        results.append(
            {
                "question_id": answer.question_id,
                "user_answer": answer.user_answer,
                "correct_answer": question.get("correct_answer"),
                "is_correct": is_correct,
                "explanation": question.get("explanation", ""),
            }
        )

    total = len(mcq_questions)
    percentage = round((correct / total) * 100, 2) if total > 0 else 0
    attempt = svc.save_quiz_attempt(
        current_user["id"],
        request.session_id,
        {
            "answers": results,
            "score": correct,
            "total": total,
            "percentage": percentage,
        },
    )
    if not attempt or not attempt.get("id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lưu kết quả quiz.",
        )

    return {
        "attempt_id": attempt["id"],
        "score": correct,
        "total": total,
        "percentage": percentage,
        "results": results,
    }


@router.post("/open-feedback")
async def get_open_feedback(
    request: OpenAnswerRequest,
    current_user: dict[str, str | None] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict[str, Any]:
    svc = SupabaseService(supabase)
    svc.ensure_profile(
        current_user["id"],
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        avatar_url=current_user.get("avatar_url"),
    )
    question = svc.get_quiz_question(request.question_id, current_user["id"])
    if not question:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi.")

    metadata = question.get("options")
    sample_points = []
    if isinstance(metadata, dict):
        sample_points = metadata.get("sample_answer_points") or []

    try:
        feedback = await gemini.generate_json(
            OPEN_ANSWER_FEEDBACK_PROMPT.format(
                question=question.get("question_text", ""),
                sample_points="\n".join(sample_points),
                user_answer=request.user_answer,
                language=request.language,
            )
        )
    except Exception as exc:
        print(f"[quiz] Open-answer feedback failed, using fallback: {exc}")
        feedback = build_open_feedback_fallback(request.user_answer)

    critical_score = _normalize_critical_thinking_score(
        feedback.get("critical_thinking_score")
    )
    svc.save_open_question_response(
        current_user["id"],
        request.question_id,
        {
            "user_response": request.user_answer,
            "ai_feedback": feedback.get("ai_feedback"),
            "critical_thinking_score": critical_score,
        },
    )
    if critical_score is not None:
        feedback["critical_thinking_score"] = critical_score
    return feedback

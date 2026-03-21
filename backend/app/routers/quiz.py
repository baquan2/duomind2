import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.fallbacks import (
    build_open_feedback_fallback,
    build_targeted_quiz_fallback_v2,
)
from app.utils.helpers import extract_keywords_from_text, normalize_text, strip_accents
from app.utils.prompts import (
    OPEN_ANSWER_FEEDBACK_PROMPT,
    OPEN_QUESTIONS_PROMPT,
    QUIZ_GENERATE_PROMPT,
)


router = APIRouter()
# Legacy phrases kept for traceability; clean normalized phrases below are the active ones.
GENERIC_MCQ_PHRASES_LEGACY = (
    "pháº§n 1",
    "pháº§n 2",
    "pháº§n 3",
    "Ã½ nÃ o phÃ¹ há»£p nháº¥t",
    "ná»™i dung chÃ­nh cá»§a pháº§n",
    "chá»§ Ä‘á» trÃªn",
)

GENERIC_OPEN_PHRASES_LEGACY = (
    "theo báº¡n",
    "báº¡n sáº½ báº¯t Ä‘áº§u tá»« Ä‘Ã¢u",
    "báº¡n nghÄ© gÃ¬",
)


GENERIC_MCQ_PHRASES = (
    "phan 1",
    "phan 2",
    "phan 3",
    "y nao phu hop nhat",
    "noi dung chinh cua phan",
    "chu de tren",
)

GENERIC_OPEN_PHRASES = (
    "theo ban",
    "ban se bat dau tu dau",
    "ban nghi gi",
)


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


def _build_quiz_material(session: dict[str, Any]) -> dict[str, Any]:
    infographic_data = session.get("infographic_data")
    detailed_sections = {}
    if isinstance(infographic_data, dict):
        detailed_sections = infographic_data.get("detailed_sections") or {}

    normalized_sections: list[dict[str, str]] = []
    if isinstance(detailed_sections, dict):
        for key in (
            "core_concept",
            "mechanism",
            "components_and_relationships",
            "persona_based_example",
            "real_world_applications",
            "common_misconceptions",
            "next_step_self_study",
        ):
            section = detailed_sections.get(key)
            if not isinstance(section, dict):
                continue
            title = str(section.get("title") or "").strip()
            content = str(section.get("content") or "").strip()
            if not title and not content:
                continue
            normalized_sections.append(
                {
                    "title": title,
                    "content": content[:320],
                }
            )

    corrections_raw = session.get("corrections") or []
    normalized_corrections: list[dict[str, str]] = []
    if isinstance(corrections_raw, list):
        for item in corrections_raw[:4]:
            if not isinstance(item, dict):
                continue
            original = str(item.get("original") or "").strip()
            correction = str(item.get("correction") or "").strip()
            explanation = str(item.get("explanation") or "").strip()
            if not original and not correction:
                continue
            normalized_corrections.append(
                {
                    "original": original,
                    "correction": correction,
                    "explanation": explanation[:220],
                }
            )

    key_points_raw = session.get("key_points") or []
    key_points = [
        str(item).strip()
        for item in key_points_raw[:6]
        if str(item).strip()
    ]

    return {
        "title": str(session.get("title") or "").strip(),
        "summary": str(session.get("summary") or "").strip(),
        "key_points": key_points,
        "corrections": normalized_corrections,
        "detailed_sections": normalized_sections,
    }


def _build_quiz_focus_keywords(quiz_material: dict[str, Any]) -> list[str]:
    text_parts = [
        str(quiz_material.get("title") or ""),
        str(quiz_material.get("summary") or ""),
        " ".join(str(item) for item in quiz_material.get("key_points") or []),
        " ".join(
            " ".join(str(section.get(key) or "") for key in ("title", "content"))
            for section in quiz_material.get("detailed_sections") or []
            if isinstance(section, dict)
        ),
        " ".join(
            " ".join(str(item.get(key) or "") for key in ("original", "correction", "explanation"))
            for item in quiz_material.get("corrections") or []
            if isinstance(item, dict)
        ),
    ]
    return extract_keywords_from_text(" ".join(text_parts), limit=10)


def _keyword_overlap(text: str, keywords: list[str]) -> int:
    lowered = strip_accents(normalize_text(text)).lower()
    return sum(1 for keyword in keywords if keyword and keyword in lowered)


def _mcq_question_is_weak(question: dict[str, Any], focus_keywords: list[str]) -> bool:
    question_text = normalize_text(str(question.get("question_text") or ""))
    lowered_question = strip_accents(question_text).lower()
    options = question.get("options") or []
    correct_answer = str(question.get("correct_answer") or "").strip()
    explanation = normalize_text(str(question.get("explanation") or ""))

    if len(question_text) < 18:
        return True
    if any(phrase in lowered_question for phrase in GENERIC_MCQ_PHRASES):
        return True
    if _keyword_overlap(question_text, focus_keywords) == 0:
        return True
    if not isinstance(options, list) or len(options) != 4:
        return True
    if correct_answer not in {"A", "B", "C", "D"}:
        return True
    option_texts = [normalize_text(str(option.get("text") or "")) for option in options if isinstance(option, dict)]
    if len(option_texts) != 4 or len({text.lower() for text in option_texts if text}) != 4:
        return True
    if any(len(text) < 4 for text in option_texts):
        return True
    if len(explanation) < 18:
        return True
    return False


def _open_question_is_weak(question: dict[str, Any], focus_keywords: list[str]) -> bool:
    question_text = normalize_text(str(question.get("question_text") or ""))
    lowered_question = strip_accents(question_text).lower()
    hints = question.get("thinking_hints") or []
    sample_points = question.get("sample_answer_points") or []

    if len(question_text) < 18:
        return True
    if any(phrase in lowered_question for phrase in GENERIC_OPEN_PHRASES) and _keyword_overlap(question_text, focus_keywords) < 2:
        return True
    if _keyword_overlap(question_text, focus_keywords) == 0:
        return True
    if not isinstance(hints, list) or len([hint for hint in hints if normalize_text(str(hint))]) < 2:
        return True
    if not isinstance(sample_points, list) or len([point for point in sample_points if normalize_text(str(point))]) < 2:
        return True
    return False


def _quiz_questions_need_fallback(
    questions: list[dict[str, Any]],
    quiz_material: dict[str, Any],
    num_questions: int,
    include_open: bool,
) -> bool:
    focus_keywords = _build_quiz_focus_keywords(quiz_material)
    mcq_questions = [
        question
        for question in questions
        if isinstance(question, dict) and question.get("question_type") == "multiple_choice"
    ]
    open_questions = [
        question
        for question in questions
        if isinstance(question, dict) and question.get("question_type") == "open"
    ]

    if len(mcq_questions) < num_questions:
        return True
    if sum(1 for question in mcq_questions if _mcq_question_is_weak(question, focus_keywords)) >= max(1, len(mcq_questions) // 2):
        return True
    if include_open:
        if len(open_questions) < 2:
            return True
        if any(_open_question_is_weak(question, focus_keywords) for question in open_questions):
            return True

    return False


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

    quiz_material = _build_quiz_material(session)
    fallback_title = str(session.get("title") or "Chu de")
    session["title"] = fallback_title

    try:
        mcq_result = await gemini.generate_json(
            QUIZ_GENERATE_PROMPT.format(
                title=session.get("title", ""),
                material_json=json.dumps(quiz_material, ensure_ascii=False, indent=2),
                num_questions=request.num_questions,
                language=session.get("language", "vi"),
            )
        )
        questions = mcq_result.get("questions") or []

        if request.include_open:
            open_result = await gemini.generate_json(
                OPEN_QUESTIONS_PROMPT.format(
                    title=session.get("title", ""),
                    material_json=json.dumps(quiz_material, ensure_ascii=False, indent=2),
                    language=session.get("language", "vi"),
                )
            )
            questions.extend(open_result.get("questions") or [])
        if _quiz_questions_need_fallback(
            [question for question in questions if isinstance(question, dict)],
            quiz_material,
            request.num_questions,
            request.include_open,
        ):
            questions = build_targeted_quiz_fallback_v2(
                str(session.get("title") or "Chá»§ Ä‘á»"),
                str(session.get("summary") or ""),
                [str(point) for point in (session.get("key_points") or []) if str(point)],
                request.num_questions,
                quiz_material=quiz_material,
            )
    except Exception as exc:
        print(f"[quiz] Quiz generation failed, using fallback: {exc}")
        questions = build_targeted_quiz_fallback_v2(
            str(session.get("title") or "Chủ đề"),
            str(session.get("summary") or ""),
            [str(point) for point in (session.get("key_points") or []) if str(point)],
            request.num_questions,
            quiz_material=quiz_material,
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

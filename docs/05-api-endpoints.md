# 05 — API Endpoints (FastAPI Routers)

## Mục tiêu
Implement tất cả routers còn lại: analyze, explore, mindmap, quiz, history, analytics.

---

## `app/routers/analyze.py`

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_supabase
from app.models.analysis import AnalyzeRequest, AnalyzeResult
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.prompts import ANALYZE_CONTENT_PROMPT, MINDMAP_GENERATE_PROMPT
from app.utils.helpers import truncate_content, get_user_context
import time

router = APIRouter()

@router.post("/", response_model=AnalyzeResult)
async def analyze_content(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    start_time = time.time()

    # Lấy context người dùng
    onboarding = svc.get_onboarding(current_user["id"])
    ctx = get_user_context(onboarding)

    # Gọi Gemini phân tích
    content = truncate_content(request.content)
    prompt = ANALYZE_CONTENT_PROMPT.format(
        content=content,
        language=request.language,
        **ctx
    )
    ai_result = await gemini.generate_json(prompt)

    # Tạo mind map song song
    mindmap_prompt = MINDMAP_GENERATE_PROMPT.format(
        content=content,
        title=ai_result["title"]
    )
    mindmap_data = await gemini.generate_json(mindmap_prompt)

    duration_ms = int((time.time() - start_time) * 1000)

    # Lưu session
    session = svc.create_session(current_user["id"], {
        "session_type": "analyze",
        "title": ai_result["title"],
        "user_input": request.content,
        "topic_tags": ai_result.get("topic_tags", []),
        "accuracy_score": ai_result.get("accuracy_score"),
        "accuracy_assessment": ai_result.get("accuracy_assessment"),
        "summary": ai_result["summary"],
        "key_points": ai_result.get("key_points", []),
        "corrections": ai_result.get("corrections", []),
        "mindmap_data": mindmap_data,
        "language": request.language,
        "duration_ms": duration_ms,
    })

    return AnalyzeResult(
        session_id=session["id"],
        title=ai_result["title"],
        accuracy_score=ai_result.get("accuracy_score", 0),
        accuracy_assessment=ai_result.get("accuracy_assessment", "unverifiable"),
        summary=ai_result["summary"],
        key_points=ai_result.get("key_points", []),
        corrections=ai_result.get("corrections", []),
        topic_tags=ai_result.get("topic_tags", []),
    )
```

---

## `app/routers/explore.py`

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_supabase
from app.models.analysis import ExploreRequest, ExploreResult
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.prompts import (
    EXPLORE_TOPIC_PROMPT, MINDMAP_GENERATE_PROMPT, INFOGRAPHIC_GENERATE_PROMPT
)
from app.utils.helpers import get_user_context
import time

router = APIRouter()

@router.post("/", response_model=ExploreResult)
async def explore_topic(
    request: ExploreRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    start_time = time.time()

    onboarding = svc.get_onboarding(current_user["id"])
    ctx = get_user_context(onboarding)

    # Gọi Gemini tìm hiểu chủ đề
    prompt = EXPLORE_TOPIC_PROMPT.format(
        prompt=request.prompt,
        language=request.language,
        **ctx
    )
    ai_result = await gemini.generate_json(prompt)

    # Tạo infographic
    infographic_prompt = INFOGRAPHIC_GENERATE_PROMPT.format(
        title=ai_result["title"],
        summary=ai_result["summary"],
        key_points="\n".join(ai_result.get("key_points", []))
    )
    infographic_data = await gemini.generate_json(infographic_prompt)

    # Tạo mind map
    mindmap_prompt = MINDMAP_GENERATE_PROMPT.format(
        content=ai_result["summary"] + "\n" + "\n".join(ai_result.get("key_points", [])),
        title=ai_result["title"]
    )
    mindmap_data = await gemini.generate_json(mindmap_prompt)

    duration_ms = int((time.time() - start_time) * 1000)

    session = svc.create_session(current_user["id"], {
        "session_type": "explore",
        "title": ai_result["title"],
        "user_input": request.prompt,
        "topic_tags": ai_result.get("topic_tags", []),
        "summary": ai_result["summary"],
        "key_points": ai_result.get("key_points", []),
        "infographic_data": infographic_data,
        "mindmap_data": mindmap_data,
        "language": request.language,
        "duration_ms": duration_ms,
    })

    return ExploreResult(
        session_id=session["id"],
        title=ai_result["title"],
        summary=ai_result["summary"],
        key_points=ai_result.get("key_points", []),
        infographic_data=infographic_data,
        topic_tags=ai_result.get("topic_tags", []),
    )
```

---

## `app/routers/quiz.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from app.dependencies import get_current_user, get_supabase
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.prompts import (
    QUIZ_GENERATE_PROMPT, OPEN_QUESTIONS_PROMPT, OPEN_ANSWER_FEEDBACK_PROMPT
)
from app.utils.helpers import get_user_context

router = APIRouter()

class QuizGenerateRequest(BaseModel):
    session_id: str
    num_questions: int = 5
    include_open: bool = True

class QuizSubmitRequest(BaseModel):
    session_id: str
    answers: List[dict]

class OpenAnswerRequest(BaseModel):
    question_id: str
    user_answer: str
    language: str = "vi"

@router.post("/generate")
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    session = svc.get_session_detail(request.session_id, current_user["id"])
    if not session:
        raise HTTPException(404, "Session not found")

    onboarding = svc.get_onboarding(current_user["id"])
    ctx = get_user_context(onboarding)

    content = session.get("user_input", "") + "\n" + (session.get("summary") or "")

    # Tạo trắc nghiệm
    mcq_prompt = QUIZ_GENERATE_PROMPT.format(
        content=content,
        summary=session.get("summary", ""),
        num_questions=request.num_questions,
        language=session.get("language", "vi"),
        **ctx
    )
    mcq_result = await gemini.generate_json(mcq_prompt)
    questions = mcq_result.get("questions", [])

    # Tạo câu hỏi mở
    if request.include_open:
        open_prompt = OPEN_QUESTIONS_PROMPT.format(
            title=session.get("title", ""),
            summary=session.get("summary", ""),
            language=session.get("language", "vi"),
            **ctx
        )
        open_result = await gemini.generate_json(open_prompt)
        questions.extend(open_result.get("questions", []))

    # Lưu vào DB
    saved = svc.save_quiz_questions(request.session_id, current_user["id"], questions)
    return {"questions": saved}

@router.get("/{session_id}")
async def get_quiz(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    questions = svc.get_quiz_questions(session_id)
    # Ẩn correct_answer khi trả về client
    for q in questions:
        if q.get("question_type") == "multiple_choice":
            q.pop("correct_answer", None)
    return {"questions": questions}

@router.post("/submit")
async def submit_quiz(
    request: QuizSubmitRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    all_questions = svc.get_quiz_questions(request.session_id)

    # Chấm điểm trắc nghiệm
    mcq_questions = {q["id"]: q for q in all_questions if q["question_type"] == "multiple_choice"}
    results = []
    correct = 0

    for answer in request.answers:
        qid = answer.get("question_id")
        q = mcq_questions.get(qid)
        if q:
            is_correct = answer.get("user_answer") == q.get("correct_answer")
            if is_correct:
                correct += 1
            results.append({
                "question_id": qid,
                "user_answer": answer.get("user_answer"),
                "correct_answer": q.get("correct_answer"),
                "is_correct": is_correct,
                "explanation": q.get("explanation", "")
            })

    total = len(mcq_questions)
    percentage = round((correct / total * 100), 2) if total > 0 else 0

    attempt = svc.save_quiz_attempt(current_user["id"], request.session_id, {
        "answers": results,
        "score": correct,
        "total": total,
        "percentage": percentage
    })

    return {"attempt_id": attempt["id"], "score": correct, "total": total, "percentage": percentage, "results": results}

@router.post("/open-feedback")
async def get_open_feedback(
    request: OpenAnswerRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    questions = svc.db.table("quiz_questions").select("*").eq("id", request.question_id).eq("user_id", current_user["id"]).single().execute()
    if not questions.data:
        raise HTTPException(404, "Question not found")

    q = questions.data
    prompt = OPEN_ANSWER_FEEDBACK_PROMPT.format(
        question=q["question_text"],
        sample_points="\n".join(q.get("sample_answer_points") or []),
        user_answer=request.user_answer,
        language=request.language
    )
    feedback = await gemini.generate_json(prompt)

    # Lưu response
    svc.db.table("open_question_responses").insert({
        "user_id": current_user["id"],
        "question_id": request.question_id,
        "user_response": request.user_answer,
        "ai_feedback": feedback.get("ai_feedback"),
        "critical_thinking_score": feedback.get("critical_thinking_score")
    }).execute()

    return feedback
```

---

## `app/routers/history.py`

```python
from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_user, get_supabase
from app.services.supabase_service import SupabaseService

router = APIRouter()

@router.get("/sessions")
async def get_history(
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0),
    session_type: str = Query(default=None),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    sessions = svc.get_sessions(current_user["id"], limit, offset)
    if session_type:
        sessions = [s for s in sessions if s["session_type"] == session_type]
    return {"sessions": sessions, "total": len(sessions)}

@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    session = svc.get_session_detail(session_id, current_user["id"])
    if not session:
        from fastapi import HTTPException
        raise HTTPException(404, "Session not found")
    quiz_questions = svc.get_quiz_questions(session_id)
    return {"session": session, "quiz_questions": quiz_questions}

@router.patch("/sessions/{session_id}/bookmark")
async def toggle_bookmark(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    session = svc.get_session_detail(session_id, current_user["id"])
    if not session:
        from fastapi import HTTPException
        raise HTTPException(404, "Session not found")
    new_val = not session.get("is_bookmarked", False)
    svc.db.table("learning_sessions").update({"is_bookmarked": new_val}).eq("id", session_id).execute()
    return {"is_bookmarked": new_val}
```

---

## `app/routers/analytics.py`

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_supabase
from app.services.gemini_service import gemini
from app.services.supabase_service import SupabaseService
from app.utils.prompts import KNOWLEDGE_ANALYTICS_PROMPT
import json

router = APIRouter()

@router.get("/knowledge-report")
async def get_knowledge_report(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    sessions = svc.get_all_sessions_for_analytics(current_user["id"])
    onboarding = svc.get_onboarding(current_user["id"])
    profile = svc.get_profile(current_user["id"])

    # Lấy quiz stats
    attempts = svc.db.table("quiz_attempts").select("percentage").eq("user_id", current_user["id"]).execute()
    attempt_list = attempts.data or []
    avg_score = sum(a["percentage"] for a in attempt_list) / len(attempt_list) if attempt_list else 0

    # Tóm tắt sessions để không vượt context
    sessions_summary = json.dumps([{
        "title": s["title"],
        "type": s["session_type"],
        "tags": s.get("topic_tags", []),
        "date": s["created_at"][:10]
    } for s in sessions[:50]])  # max 50 sessions

    prompt = KNOWLEDGE_ANALYTICS_PROMPT.format(
        user_persona=onboarding.get("ai_persona", "general") if onboarding else "general",
        member_since=profile.get("created_at", "")[:10] if profile else "",
        sessions_summary=sessions_summary,
        total_quizzes=len(attempt_list),
        avg_quiz_score=round(avg_score, 1)
    )

    ai_report = await gemini.generate_json(prompt)

    # Lưu báo cáo
    svc.save_analytics_report(current_user["id"], {
        "report_period": "all_time",
        "total_sessions": len(sessions),
        "topics_covered": list(set(tag for s in sessions for tag in s.get("topic_tags", []))),
        "strongest_topics": ai_report.get("strongest_topics", []),
        "weakest_topics": ai_report.get("weakest_topics", []),
        "ai_summary": ai_report.get("ai_summary"),
        "ai_recommendations": ai_report.get("ai_recommendations", []),
        "learning_pattern": ai_report.get("learning_pattern"),
        "knowledge_depth": ai_report.get("knowledge_depth"),
        "avg_quiz_score": avg_score,
        "total_quizzes": len(attempt_list),
    })

    return {**ai_report, "total_sessions": len(sessions), "total_quizzes": len(attempt_list)}
```

---

## API Endpoints Tổng hợp

| Method | Path | Mô tả |
|---|---|---|
| GET | /health | Health check |
| GET | /api/auth/me | Lấy profile hiện tại |
| GET | /api/auth/onboarding-status | Kiểm tra đã onboard chưa |
| POST | /api/onboarding/submit | Gửi data onboarding |
| GET | /api/onboarding/me | Lấy thông tin onboarding |
| POST | /api/analyze/ | Phân tích nội dung |
| POST | /api/explore/ | Tìm hiểu chủ đề |
| POST | /api/quiz/generate | Tạo quiz cho session |
| GET | /api/quiz/{session_id} | Lấy câu hỏi quiz |
| POST | /api/quiz/submit | Nộp bài quiz |
| POST | /api/quiz/open-feedback | AI đánh giá câu tự luận |
| GET | /api/history/sessions | Lịch sử học |
| GET | /api/history/sessions/{id} | Chi tiết 1 session |
| PATCH | /api/history/sessions/{id}/bookmark | Bookmark session |
| GET | /api/analytics/knowledge-report | Báo cáo kiến thức AI |

---

## ✅ Checklist Bước 05

- [ ] `routers/analyze.py` — POST /api/analyze/ hoạt động
- [ ] `routers/explore.py` — POST /api/explore/ hoạt động
- [ ] `routers/quiz.py` — generate, get, submit, open-feedback
- [ ] `routers/history.py` — get sessions, detail, bookmark
- [ ] `routers/analytics.py` — knowledge report
- [ ] `app/main.py` đã include tất cả routers
- [ ] Test toàn bộ endpoints với Postman/Swagger UI (`/docs`)

---

## ➡️ Bước Tiếp theo
Đọc `06-frontend-setup.md` để setup Next.js.

---

## 🤖 Codex Prompt

```
Tạo các file router trong backend/app/routers/ theo code trong 05-api-endpoints.md:
- analyze.py, explore.py, quiz.py, history.py, analytics.py

Cập nhật app/main.py để include tất cả routers mới.
Sau đó chạy uvicorn và mở http://localhost:8000/docs để verify tất cả endpoints hiển thị.
```

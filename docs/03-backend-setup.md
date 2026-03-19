# 03 — Backend Setup (FastAPI + Supabase + Gemini)

## Mục tiêu
Hoàn thiện backend skeleton: auth middleware, Supabase client, Gemini client, dependencies.

---

## `app/dependencies.py` — Auth Middleware

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.config import settings

security = HTTPBearer()

def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase)
) -> dict:
    """Verify Supabase JWT token và trả về user data."""
    token = credentials.credentials
    try:
        response = supabase.auth.get_user(token)
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": response.user.id, "email": response.user.email}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
```

---

## `app/services/gemini_service.py` — Gemini Client

```python
import google.generativeai as genai
import json
import re
from app.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiService:
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
        )
        self.model_json = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0.3,  # Thấp hơn cho output JSON chính xác
                "top_p": 0.95,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",  # Force JSON output
            }
        )

    async def generate_text(self, prompt: str) -> str:
        """Generate text thông thường."""
        response = self.model.generate_content(prompt)
        return response.text

    async def generate_json(self, prompt: str) -> dict:
        """Generate JSON có cấu trúc."""
        response = self.model_json.generate_content(prompt)
        text = response.text
        # Fallback: strip markdown code blocks nếu có
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        return json.loads(text.strip())

gemini = GeminiService()
```

---

## `app/services/supabase_service.py` — DB Operations

```python
from supabase import Client
from typing import Optional, List
import uuid

class SupabaseService:
    def __init__(self, client: Client):
        self.db = client

    # --- Profiles ---
    def get_profile(self, user_id: str) -> Optional[dict]:
        result = self.db.table("profiles").select("*").eq("id", user_id).single().execute()
        return result.data

    def update_profile(self, user_id: str, data: dict) -> dict:
        result = self.db.table("profiles").update(data).eq("id", user_id).execute()
        return result.data[0]

    def set_onboarded(self, user_id: str) -> None:
        self.db.table("profiles").update({"is_onboarded": True}).eq("id", user_id).execute()

    # --- Onboarding ---
    def get_onboarding(self, user_id: str) -> Optional[dict]:
        result = self.db.table("user_onboarding").select("*").eq("user_id", user_id).execute()
        return result.data[0] if result.data else None

    def upsert_onboarding(self, user_id: str, data: dict) -> dict:
        payload = {"user_id": user_id, **data}
        result = self.db.table("user_onboarding").upsert(payload, on_conflict="user_id").execute()
        return result.data[0]

    # --- Learning Sessions ---
    def create_session(self, user_id: str, data: dict) -> dict:
        payload = {"user_id": user_id, **data}
        result = self.db.table("learning_sessions").insert(payload).execute()
        return result.data[0]

    def get_sessions(self, user_id: str, limit: int = 20, offset: int = 0) -> List[dict]:
        result = (self.db.table("learning_sessions")
            .select("id,title,session_type,topic_tags,accuracy_score,created_at,is_bookmarked")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute())
        return result.data

    def get_session_detail(self, session_id: str, user_id: str) -> Optional[dict]:
        result = (self.db.table("learning_sessions")
            .select("*")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .single()
            .execute())
        return result.data

    # --- Quiz ---
    def save_quiz_questions(self, session_id: str, user_id: str, questions: list) -> list:
        payload = [{"session_id": session_id, "user_id": user_id, **q} for q in questions]
        result = self.db.table("quiz_questions").insert(payload).execute()
        return result.data

    def get_quiz_questions(self, session_id: str) -> List[dict]:
        result = (self.db.table("quiz_questions")
            .select("*")
            .eq("session_id", session_id)
            .order("order_index")
            .execute())
        return result.data

    def save_quiz_attempt(self, user_id: str, session_id: str, data: dict) -> dict:
        payload = {"user_id": user_id, "session_id": session_id, **data}
        result = self.db.table("quiz_attempts").insert(payload).execute()
        return result.data[0]

    # --- Analytics ---
    def get_all_sessions_for_analytics(self, user_id: str) -> List[dict]:
        result = (self.db.table("learning_sessions")
            .select("title,session_type,topic_tags,accuracy_score,created_at,summary")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute())
        return result.data

    def save_analytics_report(self, user_id: str, data: dict) -> dict:
        payload = {"user_id": user_id, **data}
        result = self.db.table("knowledge_analytics").insert(payload).execute()
        return result.data[0]
```

---

## `app/models/user.py`

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserProfile(BaseModel):
    id: str
    email: Optional[str]
    full_name: Optional[str]
    is_onboarded: bool
    created_at: datetime

class OnboardingData(BaseModel):
    age_range: str
    status: str
    education_level: Optional[str] = None
    major: Optional[str] = None
    school_name: Optional[str] = None
    industry: Optional[str] = None
    job_title: Optional[str] = None
    years_experience: Optional[int] = None
    learning_goals: List[str] = []
    topics_of_interest: List[str] = []
    learning_style: str = "mixed"
    daily_study_minutes: int = 30

class OnboardingResponse(BaseModel):
    success: bool
    ai_persona: str
    ai_persona_description: str
    ai_recommended_topics: List[str]
```

---

## `app/models/analysis.py`

```python
from pydantic import BaseModel
from typing import Optional, List

class AnalyzeRequest(BaseModel):
    content: str            # Nội dung người dùng nhập
    language: str = "vi"   # Ngôn ngữ: 'vi' hoặc 'en'

class Correction(BaseModel):
    original: str
    correction: str
    explanation: str

class AnalyzeResult(BaseModel):
    session_id: str
    title: str
    accuracy_score: int         # 0-100
    accuracy_assessment: str    # high/medium/low/unverifiable
    summary: str
    key_points: List[str]
    corrections: List[Correction]
    topic_tags: List[str]

class ExploreRequest(BaseModel):
    prompt: str
    language: str = "vi"

class ExploreResult(BaseModel):
    session_id: str
    title: str
    summary: str
    key_points: List[str]
    infographic_data: dict
    topic_tags: List[str]
```

---

## `app/routers/auth.py`

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_supabase
from app.services.supabase_service import SupabaseService

router = APIRouter()

@router.get("/me")
async def get_me(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    profile = svc.get_profile(current_user["id"])
    return profile

@router.get("/onboarding-status")
async def onboarding_status(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    profile = svc.get_profile(current_user["id"])
    return {"is_onboarded": profile.get("is_onboarded", False) if profile else False}
```

---

## `app/routers/onboarding.py`

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, get_supabase
from app.models.user import OnboardingData, OnboardingResponse
from app.services.supabase_service import SupabaseService
from app.services.gemini_service import gemini
from app.utils.prompts import ONBOARDING_CLASSIFY_PROMPT

router = APIRouter()

@router.post("/submit", response_model=OnboardingResponse)
async def submit_onboarding(
    data: OnboardingData,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)

    # Gọi Gemini phân loại người dùng
    prompt = ONBOARDING_CLASSIFY_PROMPT.format(**data.model_dump())
    ai_result = await gemini.generate_json(prompt)

    # Lưu vào DB
    full_data = {
        **data.model_dump(),
        "ai_persona": ai_result["persona"],
        "ai_persona_description": ai_result["description"],
        "ai_recommended_topics": ai_result["recommended_topics"],
    }
    svc.upsert_onboarding(current_user["id"], full_data)
    svc.set_onboarded(current_user["id"])

    return OnboardingResponse(
        success=True,
        ai_persona=ai_result["persona"],
        ai_persona_description=ai_result["description"],
        ai_recommended_topics=ai_result["recommended_topics"]
    )

@router.get("/me")
async def get_my_onboarding(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    svc = SupabaseService(supabase)
    return svc.get_onboarding(current_user["id"])
```

---

## ✅ Checklist Bước 03

- [ ] `dependencies.py` — auth middleware hoạt động
- [ ] `gemini_service.py` — test generate_text và generate_json
- [ ] `supabase_service.py` — tất cả methods đã implement
- [ ] `models/` — UserProfile, OnboardingData, AnalyzeRequest, ExploreRequest
- [ ] `routers/auth.py` — GET /api/auth/me trả về profile
- [ ] `routers/onboarding.py` — POST /api/onboarding/submit hoạt động
- [ ] Test với Postman: POST /api/onboarding/submit với Bearer token

---

## ➡️ Bước Tiếp theo
Đọc `04-ai-prompts-engine.md` để xây dựng toàn bộ prompt templates.

---

## 🤖 Codex Prompt

```
Trong thư mục backend/app/, tạo các file sau theo đúng code trong 03-backend-setup.md:
1. dependencies.py (auth middleware)
2. services/gemini_service.py (Gemini client)
3. services/supabase_service.py (DB operations)
4. models/user.py, models/analysis.py
5. routers/auth.py, routers/onboarding.py

Sau đó test:
- curl http://localhost:8000/api/auth/me với Bearer token → trả về profile
- Đảm bảo không có import errors
```

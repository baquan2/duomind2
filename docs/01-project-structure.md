# 01 — Cấu trúc Thư mục & Khởi tạo Dự án

## Mục tiêu
Tạo monorepo `duomind/` với backend FastAPI và frontend Next.js, đầy đủ cấu trúc cho toàn bộ tính năng.

---

## Cấu trúc Thư mục Đầy đủ

```
duomind/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Settings từ .env
│   │   ├── dependencies.py          # Auth dependency, Supabase client
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py              # UserProfile, OnboardingData
│   │   │   ├── session.py           # LearningSession, SessionType
│   │   │   ├── analysis.py          # AnalysisRequest, AnalysisResult
│   │   │   ├── explore.py           # ExploreRequest, ExploreResult
│   │   │   ├── mindmap.py           # MindMapNode, MindMapEdge
│   │   │   └── quiz.py              # QuizQuestion, QuizAttempt
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # GET /me, POST /sync-profile
│   │   │   ├── onboarding.py        # POST /submit, GET /status
│   │   │   ├── analyze.py           # POST /analyze (ANALYZE mode)
│   │   │   ├── explore.py           # POST /explore (EXPLORE mode)
│   │   │   ├── mindmap.py           # POST /generate, GET /{session_id}
│   │   │   ├── quiz.py              # POST /generate, POST /submit-attempt
│   │   │   ├── history.py           # GET /sessions, GET /sessions/{id}
│   │   │   └── analytics.py         # GET /knowledge-report
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── gemini_service.py    # Tất cả calls đến Gemini API
│   │   │   ├── supabase_service.py  # Tất cả DB operations
│   │   │   ├── analysis_service.py  # Logic xử lý ANALYZE mode
│   │   │   ├── explore_service.py   # Logic xử lý EXPLORE mode
│   │   │   └── session_service.py   # Tạo/lưu learning sessions
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── prompts.py           # Tất cả Gemini prompt templates
│   │       └── helpers.py           # Parse JSON, sanitize, etc.
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_analyze.py
│   │   └── test_explore.py
│   ├── .env                         # (KHÔNG commit — chỉ local)
│   ├── .env.example
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx               # Root layout (font, providers)
│   │   ├── page.tsx                 # Landing page (redirect nếu đã login)
│   │   ├── globals.css
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── signup/
│   │   │       └── page.tsx
│   │   └── (app)/                   # Protected: cần đăng nhập
│   │       ├── layout.tsx           # App shell: Sidebar + Header
│   │       ├── onboarding/
│   │       │   └── page.tsx         # Wizard 4 bước
│   │       ├── dashboard/
│   │       │   └── page.tsx         # Trang chủ sau login
│   │       ├── analyze/
│   │       │   └── page.tsx         # ANALYZE mode
│   │       ├── explore/
│   │       │   └── page.tsx         # EXPLORE mode
│   │       ├── history/
│   │       │   ├── page.tsx         # Danh sách sessions
│   │       │   └── [id]/
│   │       │       └── page.tsx     # Chi tiết 1 session
│   │       └── profile/
│   │           └── page.tsx
│   ├── components/
│   │   ├── ui/                      # shadcn/ui components (tự generate)
│   │   ├── providers/
│   │   │   ├── QueryProvider.tsx    # TanStack Query
│   │   │   └── AuthProvider.tsx     # Supabase auth state
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── MobileNav.tsx
│   │   ├── onboarding/
│   │   │   ├── OnboardingWizard.tsx # Container wizard
│   │   │   ├── StepIndicator.tsx
│   │   │   └── steps/
│   │   │       ├── Step1Basic.tsx   # Tuổi + học/làm
│   │   │       ├── Step2Details.tsx # Ngành + chuyên ngành
│   │   │       ├── Step3Goals.tsx   # Mục tiêu học tập
│   │   │       └── Step4Confirm.tsx # Xác nhận + AI classify
│   │   ├── analyze/
│   │   │   ├── ContentInput.tsx     # Textarea + file upload
│   │   │   ├── AnalysisResult.tsx   # Container kết quả
│   │   │   ├── AccuracyBadge.tsx    # Score độ chính xác
│   │   │   └── SummaryCard.tsx      # Tóm tắt AI
│   │   ├── explore/
│   │   │   ├── PromptInput.tsx      # Input tìm hiểu
│   │   │   ├── ExploreResult.tsx    # Container kết quả
│   │   │   └── Infographic.tsx      # Renderer infographic từ JSON
│   │   ├── mindmap/
│   │   │   ├── MindMapViewer.tsx    # ReactFlow wrapper
│   │   │   ├── CustomNode.tsx       # Node tùy chỉnh
│   │   │   └── mindmap.types.ts
│   │   ├── quiz/
│   │   │   ├── QuizContainer.tsx
│   │   │   ├── MultipleChoice.tsx
│   │   │   ├── OpenQuestion.tsx     # Câu hỏi tự luận
│   │   │   └── QuizResult.tsx
│   │   └── history/
│   │       ├── SessionList.tsx
│   │       ├── SessionCard.tsx
│   │       └── KnowledgeReport.tsx  # AI tổng hợp
│   ├── lib/
│   │   ├── supabase/
│   │   │   ├── client.ts            # Browser client
│   │   │   └── server.ts            # Server client (RSC)
│   │   ├── api/
│   │   │   ├── client.ts            # Axios instance + interceptors
│   │   │   ├── analyze.ts           # API calls cho analyze
│   │   │   ├── explore.ts
│   │   │   ├── quiz.ts
│   │   │   └── history.ts
│   │   └── utils.ts
│   ├── hooks/
│   │   ├── useUser.ts
│   │   ├── useAnalysis.ts
│   │   ├── useExplore.ts
│   │   └── useHistory.ts
│   ├── store/
│   │   ├── userStore.ts             # Zustand: user + onboarding state
│   │   └── sessionStore.ts          # Zustand: current session state
│   ├── types/
│   │   └── index.ts                 # Tất cả TypeScript types
│   ├── .env.local                   # (KHÔNG commit)
│   ├── .env.local.example
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── package.json
│
├── .github/
│   └── workflows/
│       ├── backend-test.yml
│       └── frontend-test.yml
├── .gitignore
└── README.md
```

---

## Lệnh Khởi tạo

### Bước 1: Tạo repo

```bash
mkdir duomind && cd duomind
git init
echo "# DUO MIND" > README.md
```

### Bước 2: Setup Backend

```bash
mkdir -p backend/app/{models,routers,services,utils}
mkdir -p backend/tests
cd backend

python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

pip install \
  fastapi==0.111.0 \
  uvicorn[standard]==0.30.0 \
  supabase==2.5.0 \
  google-generativeai==0.7.2 \
  python-dotenv==1.0.1 \
  pydantic-settings==2.3.4 \
  httpx==0.27.0 \
  python-multipart==0.0.9 \
  pytest==8.2.2 \
  pytest-asyncio==0.23.7

pip freeze > requirements.txt

# Tạo các file __init__.py
touch app/__init__.py
touch app/models/__init__.py
touch app/routers/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py
touch tests/__init__.py

cd ..
```

### Bước 3: Setup Frontend

```bash
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"

cd frontend

npm install \
  @supabase/supabase-js \
  @supabase/ssr \
  @xyflow/react \
  zustand \
  @tanstack/react-query \
  framer-motion \
  axios \
  lucide-react \
  clsx \
  tailwind-merge \
  class-variance-authority

# shadcn/ui init
npx shadcn-ui@latest init
# Chọn: Default, Slate, CSS variables: yes

# Cài shadcn components cần dùng
npx shadcn-ui@latest add button card input textarea badge
npx shadcn-ui@latest add progress tabs dialog tooltip
npx shadcn-ui@latest add select checkbox radio-group
npx shadcn-ui@latest add skeleton alert separator

cd ..
```

---

## File Cấu hình Quan trọng

### `backend/.env.example`
```env
# Supabase
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Gemini
GEMINI_API_KEY=AIza...

# App
SECRET_KEY=change_this_to_random_32_char_string
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
```

### `frontend/.env.local.example`
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### `backend/app/config.py`
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    GEMINI_API_KEY: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### `backend/app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, onboarding, analyze, explore, mindmap, quiz, history, analytics

app = FastAPI(
    title="DUO MIND API",
    description="AI-powered knowledge analysis & education platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,       prefix="/api/auth",       tags=["auth"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(analyze.router,    prefix="/api/analyze",    tags=["analyze"])
app.include_router(explore.router,    prefix="/api/explore",    tags=["explore"])
app.include_router(mindmap.router,    prefix="/api/mindmap",    tags=["mindmap"])
app.include_router(quiz.router,       prefix="/api/quiz",       tags=["quiz"])
app.include_router(history.router,    prefix="/api/history",    tags=["history"])
app.include_router(analytics.router,  prefix="/api/analytics",  tags=["analytics"])

@app.get("/health")
async def health():
    return {"status": "healthy", "app": "DUO MIND API"}
```

### `backend/railway.toml`
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
```

### `backend/Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `.gitignore`
```
# Python
backend/venv/
backend/.env
backend/__pycache__/
backend/**/__pycache__/
backend/*.pyc

# Node
frontend/node_modules/
frontend/.next/
frontend/.env.local

# General
.DS_Store
*.log
```

---

## ✅ Checklist Bước 01

- [ ] `duomind/` repo khởi tạo với git
- [ ] `backend/` có đầy đủ thư mục, venv đã activate, packages đã cài
- [ ] `requirements.txt` đã generate
- [ ] `frontend/` đã create-next-app, packages đã cài, shadcn init
- [ ] Cả hai `.env.example` đã tạo, copy thành `.env` / `.env.local` với giá trị thật
- [ ] `uvicorn app.main:app --reload` chạy được tại `http://localhost:8000/health`
- [ ] `npm run dev` chạy được tại `http://localhost:3000`

---

## ➡️ Bước Tiếp theo
Đọc `02-database-schema.md` để setup Supabase.

---

## 🤖 Codex Prompt

```
Tôi đang build DUO MIND - nền tảng học tập AI. Hãy thực hiện các bước sau:

1. Tạo cấu trúc thư mục theo spec trong file này
2. Tạo Python virtual environment trong backend/ và cài tất cả packages trong requirements
3. Chạy create-next-app cho frontend với TypeScript, Tailwind, App Router
4. Cài tất cả npm packages được liệt kê
5. Init shadcn/ui và cài các components: button, card, input, textarea, badge, progress, tabs, dialog, tooltip, select, checkbox, radio-group, skeleton, alert, separator
6. Tạo tất cả file config: config.py, main.py, railway.toml, Dockerfile, .env.example, .gitignore
7. Test: uvicorn app.main:app --reload → phải trả về {"status":"healthy"} tại /health
```

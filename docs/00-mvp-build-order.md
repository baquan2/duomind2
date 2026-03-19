# 00 — MVP Build Order (Đọc file này TRƯỚC)

> Dựa trên thứ tự ưu tiên đã xác nhận:
> **1. Onboarding → 2. Explore → 3. Analyze → 4. History/Analytics**

---

## 🗺️ Sơ đồ Build theo Priority

```
SPRINT 1 — Foundation (Không thể skip)
├── 01-project-structure   → Tạo repo, cài packages
├── 02-database-schema     → Supabase tables + RLS
├── 03-backend-setup       → FastAPI core + auth
└── 06-frontend-setup      → Next.js + routing + auth pages

SPRINT 2 — Priority 1: Onboarding (Tính năng đầu tiên cần chạy được)
└── 07-onboarding-flow     → Wizard 4 bước + AI classify persona
    Phụ thuộc: 04-ai-prompts-engine (chỉ cần ONBOARDING_CLASSIFY_PROMPT)

SPRINT 3 — Priority 2: EXPLORE (Tính năng cốt lõi thứ hai)
├── 04-ai-prompts-engine   → Tất cả prompts (EXPLORE, MINDMAP, INFOGRAPHIC, QUIZ)
├── 05-api-endpoints       → Chỉ router explore.py + quiz.py trước
└── 09-explore-feature     → UI: PromptInput + Infographic + MindMap + Quiz

SPRINT 4 — Priority 3: ANALYZE
├── 05-api-endpoints       → Router analyze.py
└── 08-analyze-feature     → UI: ContentInput + AccuracyBadge + SummaryCard

SPRINT 5 — Priority 4: History + Analytics + Deploy
├── 10-quiz-history-deploy → History UI + KnowledgeReport
└── Deploy Vercel + Railway
```

---

## ⚡ Thứ tự File Codex Chạy (Copy theo đúng thứ tự này)

```
Bước 1:  01-project-structure.md     → Setup repo
Bước 2:  02-database-schema.md       → Supabase SQL
Bước 3:  03-backend-setup.md         → FastAPI skeleton
Bước 4:  06-frontend-setup.md        → Next.js skeleton + auth
Bước 5:  04-ai-prompts-engine.md     → Prompts (chỉ cần ONBOARDING trước)
Bước 6:  07-onboarding-flow.md       ★ MILESTONE 1: Onboarding chạy được
Bước 7:  04-ai-prompts-engine.md     → Thêm EXPLORE + MINDMAP + INFOGRAPHIC + QUIZ prompts
Bước 8:  05-api-endpoints.md         → explore.py + quiz.py routers
Bước 9:  09-explore-feature.md       ★ MILESTONE 2: Explore + Mind Map + Quiz chạy được
Bước 10: 05-api-endpoints.md         → analyze.py router
Bước 11: 08-analyze-feature.md       ★ MILESTONE 3: Analyze chạy được
Bước 12: 10-quiz-history-deploy.md   ★ MILESTONE 4: History + Deploy
```

---

## 🎯 Milestone Kiểm tra

### ✅ Milestone 1 — Onboarding
- Đăng ký tài khoản mới
- Tự redirect → `/onboarding`
- Wizard 4 bước hoàn chỉnh
- AI trả về persona (vd: `university_tech_student`)
- `is_onboarded = true` trong Supabase
- Redirect → `/dashboard`

### ✅ Milestone 2 — Explore
- Vào `/explore`
- Nhập: *"Blockchain là gì?"*
- Xem kết quả: Summary + Infographic + Mind Map
- Tab Quiz: làm trắc nghiệm + câu hỏi tự luận
- AI feedback câu tự luận hoạt động

### ✅ Milestone 3 — Analyze
- Vào `/analyze`
- Paste 1 đoạn văn bản
- Xem: Accuracy Score + Tóm tắt + Đính chính
- Mind Map của nội dung đó
- Quiz từ nội dung đã nhập

### ✅ Milestone 4 — History & Deploy
- `/history` hiển thị tất cả sessions đã học
- Nhấn "Báo cáo AI" → KnowledgeReport hiện ra
- Frontend chạy trên Vercel
- Backend chạy trên Railway
- Test end-to-end trên production URL

---

## 🔑 Biến Môi Trường Cần Chuẩn bị Trước

Trước khi bắt đầu Bước 1, chuẩn bị sẵn các keys sau:

| Key | Lấy ở đâu |
|---|---|
| `SUPABASE_URL` | Supabase Dashboard → Settings → API |
| `SUPABASE_ANON_KEY` | Supabase Dashboard → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Dashboard → Settings → API |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| `SECRET_KEY` | Random 32 chars: `openssl rand -hex 16` |

---

## ⚠️ Lưu ý Quan trọng cho Codex

1. **Luôn chạy backend trước khi test frontend** — frontend gọi API backend
2. **Chạy SQL Supabase theo đúng thứ tự Block 1→8** — có foreign key dependencies
3. **File `.env` và `.env.local` KHÔNG commit lên git** — đã có trong `.gitignore`
4. **Sau mỗi Milestone, test thủ công** trước khi chuyển sang sprint tiếp theo
5. **CORS**: `FRONTEND_URL` trong Railway phải khớp chính xác với Vercel URL (kể cả `https://`)

---

## 📐 Tech Stack Cuối cùng

```
Frontend: Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui
          + ReactFlow (mind map) + Framer Motion + Zustand + TanStack Query
          Deploy: Vercel

Backend:  FastAPI (Python 3.11) + Supabase (PostgreSQL + Auth + Storage)
          + Gemini 1.5 Pro API
          Deploy: Railway

Database: Supabase (7 bảng: profiles, user_onboarding, learning_sessions,
          quiz_questions, quiz_attempts, open_question_responses, knowledge_analytics)
```

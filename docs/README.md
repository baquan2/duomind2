# DUO MIND — Hệ thống Đối chiếu & Giáo dục Thông minh
> Tài liệu kế hoạch phát triển — đọc theo thứ tự số file

---

## 🎯 Tổng quan Sản phẩm

**DUO MIND** là nền tảng học tập AI-powered với hai chế độ chính:

| Chế độ | Mô tả |
|---|---|
| **ANALYZE** | Người dùng nhập nội dung → AI kiểm tra độ chính xác, tóm tắt, mind map, quiz |
| **EXPLORE** | Người dùng nhập prompt tự nhiên → AI tìm kiếm, tóm tắt, infographic, quiz |

**Tính năng nổi bật:**
- Onboarding thông minh → AI phân loại đối tượng học (tuổi, ngành, mục tiêu)
- Mind map động (ReactFlow) + Infographic (Gemini JSON → React render)
- Trắc nghiệm tự động + câu hỏi tư duy phản biện
- Lịch sử học bài + AI tổng hợp kiến thức người học

---

## 🛠️ Tech Stack Đã Xác nhận

### Backend
| Thành phần | Công nghệ |
|---|---|
| Framework | **FastAPI (Python 3.11+)** |
| Database + Auth | **Supabase (PostgreSQL + Supabase Auth)** |
| AI Engine | **Gemini 1.5 Pro API (google-generativeai)** |
| File Storage | **Supabase Storage** |
| Deploy | **Railway** |

### Frontend
| Thành phần | Công nghệ |
|---|---|
| Framework | **Next.js 14 (App Router, TypeScript)** |
| Styling | **Tailwind CSS + shadcn/ui** |
| Mind Map | **React Flow (@xyflow/react)** |
| Infographic | **Gemini JSON → custom React renderer** |
| State | **Zustand** |
| Data Fetching | **TanStack Query v5** |
| Animations | **Framer Motion** |
| Deploy | **Vercel** |

---

## 📁 Danh sách File Kế hoạch

```
README.md                    ← File này (tổng quan + hướng dẫn)
01-project-structure.md      ← Cấu trúc thư mục + lệnh khởi tạo
02-database-schema.md        ← Supabase schema + RLS + triggers
03-backend-setup.md          ← FastAPI config + auth middleware + Gemini client
04-ai-prompts-engine.md      ← Toàn bộ prompt templates cho Gemini
05-api-endpoints.md          ← REST API endpoints đầy đủ có request/response mẫu
06-frontend-setup.md         ← Next.js layout + Supabase auth + routing
07-onboarding-flow.md        ← Wizard onboarding 4 bước + AI phân loại
08-analyze-feature.md        ← Tính năng ANALYZE (phân tích nội dung người dùng nhập)
09-explore-feature.md        ← Tính năng EXPLORE (tìm hiểu chủ đề qua prompt)
10-mindmap-infographic.md    ← Mind map ReactFlow + Infographic renderer
11-quiz-openquestion.md      ← Trắc nghiệm + câu hỏi tự luận tư duy phản biện
12-history-analytics.md      ← Lịch sử học + AI tổng hợp kiến thức
13-deployment.md             ← Deploy Vercel + Railway + biến môi trường
```

---

## ✅ Quyết định Đã Xác nhận

| Hạng mục | Lựa chọn |
|---|---|
| Frontend framework | **Next.js 14 (App Router)** |
| Infographic | **Gemini JSON → React render** (không cần image API) |
| Mind map | **ReactFlow động** |
| Deploy | **Vercel** (frontend) + **Railway** (backend) |
| MVP Priority | **1. Onboarding → 2. Explore → 3. Analyze → 4. History** |

---

## 🗺️ Lộ trình MVP (4 tuần — theo Priority)

```
Tuần 1 — Foundation
  ├── 01: Setup repo + cấu trúc thư mục
  ├── 02: Supabase schema + RLS (7 bảng)
  ├── 03: FastAPI skeleton + auth middleware
  └── 06: Next.js skeleton + Supabase auth

Tuần 2 — ★ Priority 1: Onboarding
  ├── 04: Gemini prompts (bắt đầu với ONBOARDING prompt)
  └── 07: Wizard 4 bước + AI classify persona
      → MILESTONE 1: Đăng ký → Onboard → AI persona → Dashboard

Tuần 3 — ★ Priority 2: Explore + Priority 3: Analyze
  ├── 04: Bổ sung EXPLORE + MINDMAP + INFOGRAPHIC + QUIZ prompts
  ├── 05: API endpoints (explore, analyze, quiz)
  ├── 09: EXPLORE feature (Infographic + Mind Map + Quiz)
  └── 08: ANALYZE feature (Accuracy + Tóm tắt + Đính chính)
      → MILESTONE 2 & 3: Cả hai tính năng chạy được

Tuần 4 — ★ Priority 4: History + Deploy
  ├── 10: Lịch sử học + AI KnowledgeReport
  └── Deploy: Vercel (frontend) + Railway (backend)
      → MILESTONE 4: Production live
```

---

## 📖 Hướng Dẫn Dùng với Codex

> Cuối mỗi file có phần **"🤖 Codex Prompt"** — copy nguyên vào Codex để thực thi.

**⚡ Đọc `00-mvp-build-order.md` TRƯỚC** — file này cho biết thứ tự chính xác cần thực hiện theo priority đã chọn.

**Thứ tự thực hiện:** `00 → 01 → 02 → 03 → 06 → 04 → 07 → [Milestone 1] → 04 → 05 → 09 → 08 → [Milestone 2&3] → 10 → [Deploy]`

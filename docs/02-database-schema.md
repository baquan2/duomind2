# 02 — Database Schema (Supabase)

## Mục tiêu
Tạo toàn bộ bảng, trigger, RLS policies và indexes trong Supabase SQL Editor.

---

## Thứ tự Chạy SQL

Chạy lần lượt từng block trong **Supabase Dashboard → SQL Editor → New Query**.

---

## Block 1: Bảng `profiles`

```sql
-- Mở rộng auth.users, tự tạo khi user đăng ký
CREATE TABLE public.profiles (
    id            UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email         TEXT,
    full_name     TEXT,
    avatar_url    TEXT,
    is_onboarded  BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger: tự tạo profile khi có user mới
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Trigger: cập nhật updated_at tự động
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
```

---

## Block 2: Bảng `user_onboarding`

```sql
CREATE TABLE public.user_onboarding (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id       UUID REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE NOT NULL,

    -- Thông tin cơ bản (Step 1)
    age_range     TEXT CHECK (age_range IN ('under_18','18_24','25_34','35_44','45_plus')),
    status        TEXT CHECK (status IN ('student','working','both','other')),

    -- Chi tiết học sinh/sinh viên (Step 2a)
    education_level  TEXT CHECK (education_level IN ('high_school','college','university','postgrad','other')),
    major            TEXT,
    school_name      TEXT,

    -- Chi tiết đi làm (Step 2b)
    industry         TEXT,
    job_title        TEXT,
    years_experience INTEGER CHECK (years_experience >= 0),

    -- Mục tiêu & sở thích (Step 3)
    learning_goals      TEXT[] DEFAULT '{}',
    -- Giá trị: 'exam_prep','skill_upgrade','general_knowledge','research','career_change','hobby'
    topics_of_interest  TEXT[] DEFAULT '{}',
    -- Giá trị: 'technology','science','history','business','language','arts','health','law','finance'
    learning_style      TEXT CHECK (learning_style IN ('visual','reading','practice','mixed')),
    daily_study_minutes INTEGER DEFAULT 30,

    -- AI phân loại tự động (Step 4 — do backend fill)
    ai_persona              TEXT,
    -- Ví dụ: 'high_school_stem', 'university_tech', 'professional_business'
    ai_persona_description  TEXT,
    ai_recommended_topics   TEXT[] DEFAULT '{}',

    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER user_onboarding_updated_at
    BEFORE UPDATE ON public.user_onboarding
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
```

---

## Block 3: Bảng `learning_sessions`

```sql
CREATE TABLE public.learning_sessions (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id      UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,

    -- Loại session
    session_type TEXT CHECK (session_type IN ('analyze','explore')) NOT NULL,
    title        TEXT NOT NULL,          -- AI tự generate từ nội dung
    topic_tags   TEXT[] DEFAULT '{}',    -- Tags chủ đề cho filtering

    -- Input người dùng
    user_input   TEXT NOT NULL,          -- Nội dung nhập hoặc prompt

    -- Output AI
    accuracy_score      INTEGER,         -- Chỉ dùng cho 'analyze' mode (0-100)
    accuracy_assessment TEXT,            -- 'high'|'medium'|'low'|'unverifiable'
    summary             TEXT,            -- Tóm tắt AI
    key_points          JSONB DEFAULT '[]',  -- Mảng string điểm chính
    corrections         JSONB DEFAULT '[]',  -- Chỉ analyze: [{point, correction, source}]
    infographic_data    JSONB,           -- JSON để render infographic (explore mode)
    mindmap_data        JSONB,           -- {nodes: [...], edges: [...]}

    -- Metadata
    language    TEXT DEFAULT 'vi',       -- Ngôn ngữ nội dung
    duration_ms INTEGER,                 -- Thời gian AI xử lý
    is_bookmarked BOOLEAN DEFAULT FALSE,

    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER learning_sessions_updated_at
    BEFORE UPDATE ON public.learning_sessions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- Index cho query nhanh
CREATE INDEX idx_sessions_user_id ON public.learning_sessions(user_id);
CREATE INDEX idx_sessions_type ON public.learning_sessions(session_type);
CREATE INDEX idx_sessions_created ON public.learning_sessions(created_at DESC);
CREATE INDEX idx_sessions_tags ON public.learning_sessions USING gin(topic_tags);
```

---

## Block 4: Bảng `quiz_questions` & `quiz_attempts`

```sql
-- Câu hỏi quiz (gắn với session)
CREATE TABLE public.quiz_questions (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id  UUID REFERENCES public.learning_sessions(id) ON DELETE CASCADE NOT NULL,
    user_id     UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,

    -- Nội dung câu hỏi
    question_type   TEXT CHECK (question_type IN ('multiple_choice','open')) NOT NULL,
    question_text   TEXT NOT NULL,
    options         JSONB,              -- [{id:'A', text:'...'}, ...] chỉ cho multiple_choice
    correct_answer  TEXT,              -- 'A'|'B'|'C'|'D' hoặc null cho open
    explanation     TEXT,              -- Giải thích đáp án
    difficulty      TEXT CHECK (difficulty IN ('easy','medium','hard')) DEFAULT 'medium',

    order_index     INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_quiz_session ON public.quiz_questions(session_id);

-- Lượt làm quiz của người dùng
CREATE TABLE public.quiz_attempts (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id     UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    session_id  UUID REFERENCES public.learning_sessions(id) ON DELETE CASCADE NOT NULL,

    -- Kết quả
    answers     JSONB NOT NULL DEFAULT '[]',
    -- Format: [{question_id, user_answer, is_correct, time_spent_sec}]
    score       INTEGER,        -- Số câu đúng
    total       INTEGER,        -- Tổng số câu
    percentage  NUMERIC(5,2),

    completed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_attempts_user ON public.quiz_attempts(user_id);
CREATE INDEX idx_attempts_session ON public.quiz_attempts(session_id);
```

---

## Block 5: Bảng `open_question_responses`

```sql
CREATE TABLE public.open_question_responses (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id      UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    question_id  UUID REFERENCES public.quiz_questions(id) ON DELETE CASCADE NOT NULL,

    -- Câu trả lời
    user_response       TEXT NOT NULL,
    ai_feedback         TEXT,           -- AI đánh giá câu trả lời
    critical_thinking_score INTEGER,   -- 0-10: điểm tư duy phản biện

    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Block 6: Bảng `knowledge_analytics`

```sql
-- AI tổng hợp kiến thức người học (generate theo yêu cầu)
CREATE TABLE public.knowledge_analytics (
    id       UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id  UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,

    -- Phân tích tổng hợp
    report_period       TEXT,           -- 'all_time'|'last_7_days'|'last_30_days'
    total_sessions      INTEGER DEFAULT 0,
    topics_covered      TEXT[] DEFAULT '{}',
    strongest_topics    TEXT[] DEFAULT '{}',
    weakest_topics      TEXT[] DEFAULT '{}',

    -- AI insights
    ai_summary          TEXT,           -- Tóm tắt tổng thể
    ai_recommendations  TEXT[],         -- Gợi ý học tiếp theo
    learning_pattern    TEXT,           -- 'consistent'|'sporadic'|'intensive'|'new'
    knowledge_depth     TEXT,           -- 'surface'|'intermediate'|'deep'

    -- Quiz performance
    avg_quiz_score      NUMERIC(5,2),
    total_quizzes       INTEGER DEFAULT 0,

    generated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analytics_user ON public.knowledge_analytics(user_id);
```

---

## Block 7: Row Level Security (RLS)

```sql
-- Bật RLS trên tất cả bảng
ALTER TABLE public.profiles              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_onboarding       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_sessions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quiz_questions        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quiz_attempts         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.open_question_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_analytics   ENABLE ROW LEVEL SECURITY;

-- profiles: user chỉ đọc/sửa profile của mình
CREATE POLICY "profiles_select_own"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "profiles_update_own"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- user_onboarding: user chỉ thao tác data của mình
CREATE POLICY "onboarding_all_own"
    ON public.user_onboarding FOR ALL
    USING (auth.uid() = user_id);

-- learning_sessions: user chỉ thao tác sessions của mình
CREATE POLICY "sessions_all_own"
    ON public.learning_sessions FOR ALL
    USING (auth.uid() = user_id);

-- quiz_questions: user chỉ đọc quiz gắn với session của mình
CREATE POLICY "quiz_questions_own"
    ON public.quiz_questions FOR ALL
    USING (auth.uid() = user_id);

-- quiz_attempts: user chỉ thao tác attempts của mình
CREATE POLICY "quiz_attempts_own"
    ON public.quiz_attempts FOR ALL
    USING (auth.uid() = user_id);

-- open_question_responses
CREATE POLICY "open_responses_own"
    ON public.open_question_responses FOR ALL
    USING (auth.uid() = user_id);

-- knowledge_analytics
CREATE POLICY "analytics_own"
    ON public.knowledge_analytics FOR ALL
    USING (auth.uid() = user_id);
```

---

## Block 8: Supabase Auth Config

Vào **Supabase Dashboard → Authentication → Providers**:

1. **Email**: Enable, disable "Confirm email" cho dev
2. **Google OAuth** (tùy chọn):
   - Tạo Google Cloud project
   - Lấy Client ID + Secret
   - Redirect URL: `https://xxxx.supabase.co/auth/v1/callback`

---

## ✅ Checklist Bước 02

- [ ] Chạy Block 1 → Bảng `profiles` + triggers
- [ ] Chạy Block 2 → Bảng `user_onboarding`
- [ ] Chạy Block 3 → Bảng `learning_sessions` + indexes
- [ ] Chạy Block 4 → Bảng `quiz_questions` + `quiz_attempts`
- [ ] Chạy Block 5 → Bảng `open_question_responses`
- [ ] Chạy Block 6 → Bảng `knowledge_analytics`
- [ ] Chạy Block 7 → RLS policies
- [ ] Verify trong **Table Editor**: thấy đủ 7 bảng
- [ ] Verify trigger: tạo thử 1 user → profile tự tạo

---

## ➡️ Bước Tiếp theo
Đọc `03-backend-setup.md` để config FastAPI + Supabase client + auth middleware.

---

## 🤖 Codex Prompt

```
Trong Supabase SQL Editor, hãy chạy lần lượt từng block SQL trong file 02-database-schema.md.
Sau khi xong, kiểm tra Table Editor để xác nhận đủ 7 bảng:
profiles, user_onboarding, learning_sessions, quiz_questions, quiz_attempts,
open_question_responses, knowledge_analytics.
Kiểm tra RLS đã bật trên tất cả bảng.
```

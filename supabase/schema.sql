-- DUO MIND Supabase schema
-- Source of truth: docs/02-database-schema.md
-- Run in Supabase SQL Editor in the documented order.

-- Block 1: profiles
CREATE TABLE public.profiles (
    id            UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email         TEXT,
    full_name     TEXT,
    avatar_url    TEXT,
    is_onboarded  BOOLEAN DEFAULT FALSE,
    has_seen_intro_tour BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

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

-- Block 2: user_onboarding
CREATE TABLE public.user_onboarding (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id       UUID REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE NOT NULL,
    age_range     TEXT CHECK (age_range IN ('under_18','18_24','25_34','35_44','45_plus')),
    status        TEXT CHECK (status IN ('student','working','both','other')),
    education_level  TEXT CHECK (education_level IN ('high_school','college','university','postgrad','other')),
    major            TEXT,
    school_name      TEXT,
    industry         TEXT,
    job_title        TEXT,
    years_experience INTEGER CHECK (years_experience >= 0),
    learning_goals      TEXT[] DEFAULT '{}',
    topics_of_interest  TEXT[] DEFAULT '{}',
    learning_style      TEXT CHECK (learning_style IN ('visual','reading','practice','mixed')),
    daily_study_minutes INTEGER DEFAULT 30,
    ai_persona              TEXT,
    ai_persona_description  TEXT,
    ai_recommended_topics   TEXT[] DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER user_onboarding_updated_at
    BEFORE UPDATE ON public.user_onboarding
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- Block 3: learning_sessions
CREATE TABLE public.learning_sessions (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id      UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    session_type TEXT CHECK (session_type IN ('analyze','explore')) NOT NULL,
    title        TEXT NOT NULL,
    topic_tags   TEXT[] DEFAULT '{}',
    user_input   TEXT NOT NULL,
    accuracy_score      INTEGER,
    accuracy_assessment TEXT,
    summary             TEXT,
    key_points          JSONB DEFAULT '[]',
    corrections         JSONB DEFAULT '[]',
    infographic_data    JSONB,
    mindmap_data        JSONB,
    language    TEXT DEFAULT 'vi',
    duration_ms INTEGER,
    is_bookmarked BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER learning_sessions_updated_at
    BEFORE UPDATE ON public.learning_sessions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE INDEX idx_sessions_user_id ON public.learning_sessions(user_id);
CREATE INDEX idx_sessions_type ON public.learning_sessions(session_type);
CREATE INDEX idx_sessions_created ON public.learning_sessions(created_at DESC);
CREATE INDEX idx_sessions_tags ON public.learning_sessions USING gin(topic_tags);

-- Block 4: quiz_questions and quiz_attempts
CREATE TABLE public.quiz_questions (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id  UUID REFERENCES public.learning_sessions(id) ON DELETE CASCADE NOT NULL,
    user_id     UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    question_type   TEXT CHECK (question_type IN ('multiple_choice','open')) NOT NULL,
    question_text   TEXT NOT NULL,
    options         JSONB,
    correct_answer  TEXT,
    explanation     TEXT,
    difficulty      TEXT CHECK (difficulty IN ('easy','medium','hard')) DEFAULT 'medium',
    order_index     INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_quiz_session ON public.quiz_questions(session_id);

CREATE TABLE public.quiz_attempts (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id     UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    session_id  UUID REFERENCES public.learning_sessions(id) ON DELETE CASCADE NOT NULL,
    answers     JSONB NOT NULL DEFAULT '[]',
    score       INTEGER,
    total       INTEGER,
    percentage  NUMERIC(5,2),
    completed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_attempts_user ON public.quiz_attempts(user_id);
CREATE INDEX idx_attempts_session ON public.quiz_attempts(session_id);

-- Block 5: open_question_responses
CREATE TABLE public.open_question_responses (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id      UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    question_id  UUID REFERENCES public.quiz_questions(id) ON DELETE CASCADE NOT NULL,
    user_response       TEXT NOT NULL,
    ai_feedback         TEXT,
    critical_thinking_score INTEGER,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Block 6: knowledge_analytics
CREATE TABLE public.knowledge_analytics (
    id       UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id  UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    report_period       TEXT,
    total_sessions      INTEGER DEFAULT 0,
    topics_covered      TEXT[] DEFAULT '{}',
    strongest_topics    TEXT[] DEFAULT '{}',
    weakest_topics      TEXT[] DEFAULT '{}',
    ai_summary          TEXT,
    ai_recommendations  TEXT[],
    learning_pattern    TEXT,
    knowledge_depth     TEXT,
    avg_quiz_score      NUMERIC(5,2),
    total_quizzes       INTEGER DEFAULT 0,
    generated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analytics_user ON public.knowledge_analytics(user_id);

-- Block 7: mentor
CREATE TABLE public.mentor_threads (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    title           TEXT NOT NULL,
    status          TEXT DEFAULT 'active' CHECK (status IN ('active','archived')),
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER mentor_threads_updated_at
    BEFORE UPDATE ON public.mentor_threads
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE INDEX idx_mentor_threads_user ON public.mentor_threads(user_id);
CREATE INDEX idx_mentor_threads_last_message ON public.mentor_threads(last_message_at DESC);

CREATE TABLE public.mentor_messages (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    thread_id     UUID REFERENCES public.mentor_threads(id) ON DELETE CASCADE NOT NULL,
    user_id       UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    role          TEXT CHECK (role IN ('user','assistant','system')) NOT NULL,
    intent        TEXT,
    content       TEXT NOT NULL,
    response_data JSONB,
    sources       JSONB DEFAULT '[]',
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_mentor_messages_thread ON public.mentor_messages(thread_id, created_at);

CREATE TABLE public.mentor_memory (
    id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id          UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    memory_type      TEXT CHECK (
        memory_type IN ('goal','constraint','skill','career_interest','preference','fact','summary')
    ) NOT NULL,
    memory_key       TEXT NOT NULL,
    memory_value     JSONB NOT NULL,
    confidence       NUMERIC(3,2) DEFAULT 0.80,
    source_thread_id UUID REFERENCES public.mentor_threads(id) ON DELETE SET NULL,
    updated_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, memory_type, memory_key)
);

CREATE TRIGGER mentor_memory_updated_at
    BEFORE UPDATE ON public.mentor_memory
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE INDEX idx_mentor_memory_user ON public.mentor_memory(user_id);
CREATE INDEX idx_mentor_memory_key ON public.mentor_memory(user_id, memory_key);

CREATE TABLE public.job_market_signals (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    industry     TEXT,
    role_name    TEXT NOT NULL,
    seniority    TEXT,
    location     TEXT,
    skills       TEXT[] DEFAULT '{}',
    tools        TEXT[] DEFAULT '{}',
    soft_skills  TEXT[] DEFAULT '{}',
    salary_min   NUMERIC,
    salary_max   NUMERIC,
    demand_score NUMERIC(5,2),
    source_name  TEXT,
    source_url   TEXT,
    captured_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_market_role ON public.job_market_signals(role_name);
CREATE INDEX idx_market_industry ON public.job_market_signals(industry);
CREATE INDEX idx_market_skills ON public.job_market_signals USING gin(skills);

-- Block 8: RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_onboarding ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quiz_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.open_question_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_market_signals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_own"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "profiles_update_own"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "onboarding_all_own"
    ON public.user_onboarding FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "sessions_all_own"
    ON public.learning_sessions FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "quiz_questions_own"
    ON public.quiz_questions FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "quiz_attempts_own"
    ON public.quiz_attempts FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "open_responses_own"
    ON public.open_question_responses FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "analytics_own"
    ON public.knowledge_analytics FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "mentor_threads_own"
    ON public.mentor_threads FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "mentor_messages_own"
    ON public.mentor_messages FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "mentor_memory_own"
    ON public.mentor_memory FOR ALL
    USING (auth.uid() = user_id);

-- Block 9 from docs is a dashboard configuration step, not SQL:
-- Authentication -> Providers -> Email enable
-- For local dev, disable confirm email if needed.

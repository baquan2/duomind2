-- DUO MIND Mentor MVP
-- Run this file in Supabase SQL Editor before testing /mentor

CREATE TABLE IF NOT EXISTS public.mentor_threads (
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

CREATE INDEX IF NOT EXISTS idx_mentor_threads_user ON public.mentor_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_threads_last_message ON public.mentor_threads(last_message_at DESC);

CREATE TABLE IF NOT EXISTS public.mentor_messages (
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

CREATE INDEX IF NOT EXISTS idx_mentor_messages_thread ON public.mentor_messages(thread_id, created_at);

CREATE TABLE IF NOT EXISTS public.mentor_memory (
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

CREATE INDEX IF NOT EXISTS idx_mentor_memory_user ON public.mentor_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_memory_key ON public.mentor_memory(user_id, memory_key);

CREATE TABLE IF NOT EXISTS public.job_market_signals (
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

CREATE INDEX IF NOT EXISTS idx_market_role ON public.job_market_signals(role_name);
CREATE INDEX IF NOT EXISTS idx_market_industry ON public.job_market_signals(industry);
CREATE INDEX IF NOT EXISTS idx_market_skills ON public.job_market_signals USING gin(skills);

ALTER TABLE public.mentor_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_market_signals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "mentor_threads_own" ON public.mentor_threads;
CREATE POLICY "mentor_threads_own"
    ON public.mentor_threads FOR ALL
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "mentor_messages_own" ON public.mentor_messages;
CREATE POLICY "mentor_messages_own"
    ON public.mentor_messages FOR ALL
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "mentor_memory_own" ON public.mentor_memory;
CREATE POLICY "mentor_memory_own"
    ON public.mentor_memory FOR ALL
    USING (auth.uid() = user_id);

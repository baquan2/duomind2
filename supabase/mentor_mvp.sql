-- DUO MIND Mentor Core
-- Safe to run on a fresh or partially initialized database.
-- If public.profiles does not exist yet, run schema.sql or restore_profiles_table first.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF to_regclass('public.profiles') IS NULL THEN
        RAISE EXCEPTION 'Missing base table public.profiles. Run schema.sql or 2026-03-20_restore_profiles_table.sql first.';
    END IF;
END $$;

CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS public.mentor_threads (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    title           TEXT NOT NULL,
    status          TEXT DEFAULT 'active' CHECK (status IN ('active','archived')),
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.mentor_threads
    ADD COLUMN IF NOT EXISTS title TEXT,
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS last_message_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE public.mentor_threads
    DROP CONSTRAINT IF EXISTS mentor_threads_status_check;

ALTER TABLE public.mentor_threads
    ADD CONSTRAINT mentor_threads_status_check
    CHECK (status IN ('active','archived'));

DROP TRIGGER IF EXISTS mentor_threads_updated_at ON public.mentor_threads;
CREATE TRIGGER mentor_threads_updated_at
    BEFORE UPDATE ON public.mentor_threads
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TABLE IF NOT EXISTS public.mentor_messages (
    id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    thread_id        UUID REFERENCES public.mentor_threads(id) ON DELETE CASCADE NOT NULL,
    user_id          UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    role             TEXT CHECK (role IN ('user','assistant','system')) NOT NULL,
    intent           TEXT,
    answer_mode      TEXT CHECK (answer_mode IN ('knowledge_first','mentor_guidance')),
    content          TEXT NOT NULL,
    response_data    JSONB,
    sources          JSONB DEFAULT '[]'::jsonb,
    request_payload  JSONB DEFAULT '{}'::jsonb,
    context_snapshot JSONB DEFAULT '{}'::jsonb,
    generation_trace JSONB DEFAULT '{}'::jsonb,
    memory_updates   JSONB DEFAULT '[]'::jsonb,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.mentor_messages
    ADD COLUMN IF NOT EXISTS intent TEXT,
    ADD COLUMN IF NOT EXISTS answer_mode TEXT,
    ADD COLUMN IF NOT EXISTS response_data JSONB,
    ADD COLUMN IF NOT EXISTS sources JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS request_payload JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS context_snapshot JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS generation_trace JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS memory_updates JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE public.mentor_messages
    DROP CONSTRAINT IF EXISTS mentor_messages_role_check;

ALTER TABLE public.mentor_messages
    ADD CONSTRAINT mentor_messages_role_check
    CHECK (role IN ('user','assistant','system'));

ALTER TABLE public.mentor_messages
    DROP CONSTRAINT IF EXISTS mentor_messages_answer_mode_check;

ALTER TABLE public.mentor_messages
    ADD CONSTRAINT mentor_messages_answer_mode_check
    CHECK (answer_mode IN ('knowledge_first','mentor_guidance'));

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

ALTER TABLE public.mentor_memory
    ADD COLUMN IF NOT EXISTS memory_type TEXT,
    ADD COLUMN IF NOT EXISTS memory_key TEXT,
    ADD COLUMN IF NOT EXISTS memory_value JSONB,
    ADD COLUMN IF NOT EXISTS confidence NUMERIC(3,2) DEFAULT 0.80,
    ADD COLUMN IF NOT EXISTS source_thread_id UUID,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE public.mentor_memory
    DROP CONSTRAINT IF EXISTS mentor_memory_memory_type_check;

ALTER TABLE public.mentor_memory
    ADD CONSTRAINT mentor_memory_memory_type_check
    CHECK (memory_type IN ('goal','constraint','skill','career_interest','preference','fact','summary'));

DROP TRIGGER IF EXISTS mentor_memory_updated_at ON public.mentor_memory;
CREATE TRIGGER mentor_memory_updated_at
    BEFORE UPDATE ON public.mentor_memory
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

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

ALTER TABLE public.job_market_signals
    ADD COLUMN IF NOT EXISTS industry TEXT,
    ADD COLUMN IF NOT EXISTS role_name TEXT,
    ADD COLUMN IF NOT EXISTS seniority TEXT,
    ADD COLUMN IF NOT EXISTS location TEXT,
    ADD COLUMN IF NOT EXISTS skills TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS tools TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS soft_skills TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS salary_min NUMERIC,
    ADD COLUMN IF NOT EXISTS salary_max NUMERIC,
    ADD COLUMN IF NOT EXISTS demand_score NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS source_name TEXT,
    ADD COLUMN IF NOT EXISTS source_url TEXT,
    ADD COLUMN IF NOT EXISTS captured_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_mentor_threads_user ON public.mentor_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_threads_last_message ON public.mentor_threads(last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_mentor_messages_thread ON public.mentor_messages(thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_mentor_memory_user ON public.mentor_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_memory_key ON public.mentor_memory(user_id, memory_key);
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

NOTIFY pgrst, 'reload schema';

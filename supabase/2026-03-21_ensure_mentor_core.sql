-- Safe bootstrap for mentor core tables on an existing DUO MIND database.
-- Run this only if /mentor or /profile complains about missing mentor tables.

DO $$
BEGIN
    IF to_regclass('public.profiles') IS NULL THEN
        RAISE EXCEPTION 'Missing base table public.profiles. Restore profiles first before running mentor core bootstrap.';
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.mentor_threads (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    title           TEXT NOT NULL,
    status          TEXT DEFAULT 'active' CHECK (status IN ('active','archived')),
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.mentor_messages (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    thread_id     UUID REFERENCES public.mentor_threads(id) ON DELETE CASCADE NOT NULL,
    user_id       UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    role          TEXT CHECK (role IN ('user','assistant','system')) NOT NULL,
    intent        TEXT,
    content       TEXT NOT NULL,
    response_data JSONB,
    sources       JSONB DEFAULT '[]'::jsonb,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

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

DO $$
BEGIN
    IF to_regprocedure('public.update_updated_at()') IS NOT NULL THEN
        DROP TRIGGER IF EXISTS mentor_threads_updated_at ON public.mentor_threads;
        CREATE TRIGGER mentor_threads_updated_at
            BEFORE UPDATE ON public.mentor_threads
            FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

        DROP TRIGGER IF EXISTS mentor_memory_updated_at ON public.mentor_memory;
        CREATE TRIGGER mentor_memory_updated_at
            BEFORE UPDATE ON public.mentor_memory
            FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_mentor_threads_user ON public.mentor_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_threads_last_message ON public.mentor_threads(last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_mentor_messages_thread ON public.mentor_messages(thread_id, created_at);
CREATE INDEX IF NOT EXISTS idx_mentor_memory_user ON public.mentor_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_mentor_memory_key ON public.mentor_memory(user_id, memory_key);

ALTER TABLE public.mentor_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_memory ENABLE ROW LEVEL SECURITY;

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

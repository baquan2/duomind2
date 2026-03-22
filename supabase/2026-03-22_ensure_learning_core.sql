-- Safe repair for learning_sessions on a partially initialized database.
-- Run this if analyze/explore/history fails because public.learning_sessions is missing or outdated.

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

CREATE TABLE IF NOT EXISTS public.learning_sessions (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id           UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    session_type      TEXT CHECK (session_type IN ('analyze','explore')) NOT NULL,
    session_subtype   TEXT CHECK (session_subtype IN ('overview','deep_dive','critique')),
    title             TEXT NOT NULL,
    topic_tags        TEXT[] DEFAULT '{}',
    user_input        TEXT NOT NULL,
    accuracy_score    INTEGER,
    accuracy_assessment TEXT,
    summary           TEXT,
    key_points        JSONB DEFAULT '[]'::jsonb,
    corrections       JSONB DEFAULT '[]'::jsonb,
    infographic_data  JSONB,
    mindmap_data      JSONB,
    sources           JSONB DEFAULT '[]'::jsonb,
    request_payload   JSONB DEFAULT '{}'::jsonb,
    context_snapshot  JSONB DEFAULT '{}'::jsonb,
    generation_trace  JSONB DEFAULT '{}'::jsonb,
    language          TEXT DEFAULT 'vi',
    duration_ms       INTEGER,
    is_bookmarked     BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.learning_sessions
    ADD COLUMN IF NOT EXISTS session_subtype TEXT,
    ADD COLUMN IF NOT EXISTS topic_tags TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS accuracy_score INTEGER,
    ADD COLUMN IF NOT EXISTS accuracy_assessment TEXT,
    ADD COLUMN IF NOT EXISTS summary TEXT,
    ADD COLUMN IF NOT EXISTS key_points JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS corrections JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS infographic_data JSONB,
    ADD COLUMN IF NOT EXISTS mindmap_data JSONB,
    ADD COLUMN IF NOT EXISTS sources JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS request_payload JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS context_snapshot JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS generation_trace JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'vi',
    ADD COLUMN IF NOT EXISTS duration_ms INTEGER,
    ADD COLUMN IF NOT EXISTS is_bookmarked BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE public.learning_sessions
    DROP CONSTRAINT IF EXISTS learning_sessions_session_type_check;

ALTER TABLE public.learning_sessions
    ADD CONSTRAINT learning_sessions_session_type_check
    CHECK (session_type IN ('analyze','explore'));

ALTER TABLE public.learning_sessions
    DROP CONSTRAINT IF EXISTS learning_sessions_session_subtype_check;

ALTER TABLE public.learning_sessions
    ADD CONSTRAINT learning_sessions_session_subtype_check
    CHECK (session_subtype IN ('overview','deep_dive','critique'));

DROP TRIGGER IF EXISTS learning_sessions_updated_at ON public.learning_sessions;
CREATE TRIGGER learning_sessions_updated_at
    BEFORE UPDATE ON public.learning_sessions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON public.learning_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_type ON public.learning_sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON public.learning_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_tags ON public.learning_sessions USING gin(topic_tags);

ALTER TABLE public.learning_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "sessions_all_own" ON public.learning_sessions;
CREATE POLICY "sessions_all_own"
    ON public.learning_sessions FOR ALL
    USING (auth.uid() = user_id);

NOTIFY pgrst, 'reload schema';

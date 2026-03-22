-- Safe migration for AI trace fields.
-- This file is idempotent and skips blocks whose base tables are not present yet.

DO $$
BEGIN
    IF to_regclass('public.learning_sessions') IS NULL THEN
        RAISE NOTICE 'Skipping learning_sessions trace fields because public.learning_sessions does not exist yet.';
    ELSE
        ALTER TABLE public.learning_sessions
            ADD COLUMN IF NOT EXISTS session_subtype TEXT,
            ADD COLUMN IF NOT EXISTS request_payload JSONB DEFAULT '{}'::jsonb,
            ADD COLUMN IF NOT EXISTS context_snapshot JSONB DEFAULT '{}'::jsonb,
            ADD COLUMN IF NOT EXISTS generation_trace JSONB DEFAULT '{}'::jsonb;

        ALTER TABLE public.learning_sessions
            DROP CONSTRAINT IF EXISTS learning_sessions_session_subtype_check;

        ALTER TABLE public.learning_sessions
            ADD CONSTRAINT learning_sessions_session_subtype_check
            CHECK (session_subtype IN ('overview','deep_dive','critique'));
    END IF;
END $$;

DO $$
BEGIN
    IF to_regclass('public.mentor_messages') IS NULL THEN
        RAISE NOTICE 'Skipping mentor_messages trace fields because public.mentor_messages does not exist yet.';
    ELSE
        ALTER TABLE public.mentor_messages
            ADD COLUMN IF NOT EXISTS answer_mode TEXT,
            ADD COLUMN IF NOT EXISTS request_payload JSONB DEFAULT '{}'::jsonb,
            ADD COLUMN IF NOT EXISTS context_snapshot JSONB DEFAULT '{}'::jsonb,
            ADD COLUMN IF NOT EXISTS generation_trace JSONB DEFAULT '{}'::jsonb,
            ADD COLUMN IF NOT EXISTS memory_updates JSONB DEFAULT '[]'::jsonb;

        ALTER TABLE public.mentor_messages
            DROP CONSTRAINT IF EXISTS mentor_messages_answer_mode_check;

        ALTER TABLE public.mentor_messages
            ADD CONSTRAINT mentor_messages_answer_mode_check
            CHECK (answer_mode IN ('knowledge_first','mentor_guidance'));
    END IF;
END $$;

NOTIFY pgrst, 'reload schema';

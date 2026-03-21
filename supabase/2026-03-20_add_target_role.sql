DO $$
BEGIN
    IF to_regclass('public.profiles') IS NULL THEN
        RAISE EXCEPTION 'Missing base table public.profiles. Run Block 1 in supabase/schema.sql first.';
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.user_onboarding (
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
    target_role      TEXT,
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

ALTER TABLE public.user_onboarding
ADD COLUMN IF NOT EXISTS target_role TEXT;

DO $$
BEGIN
    IF to_regprocedure('public.update_updated_at()') IS NOT NULL
    AND NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'user_onboarding_updated_at'
          AND tgrelid = 'public.user_onboarding'::regclass
    ) THEN
        EXECUTE '
            CREATE TRIGGER user_onboarding_updated_at
            BEFORE UPDATE ON public.user_onboarding
            FOR EACH ROW EXECUTE FUNCTION public.update_updated_at()
        ';
    END IF;
END $$;

ALTER TABLE public.user_onboarding ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'user_onboarding'
          AND policyname = 'onboarding_all_own'
    ) THEN
        EXECUTE '
            CREATE POLICY "onboarding_all_own"
            ON public.user_onboarding FOR ALL
            USING (auth.uid() = user_id)
        ';
    END IF;
END $$;

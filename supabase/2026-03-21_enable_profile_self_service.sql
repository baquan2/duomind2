-- Ensure the profile page can read and update the learner context that drives
-- AI guidance, mentor personalization, and roadmap suggestions.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT,
    full_name TEXT,
    avatar_url TEXT,
    is_onboarded BOOLEAN DEFAULT FALSE,
    has_seen_intro_tour BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS email TEXT,
    ADD COLUMN IF NOT EXISTS full_name TEXT,
    ADD COLUMN IF NOT EXISTS avatar_url TEXT,
    ADD COLUMN IF NOT EXISTS is_onboarded BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS has_seen_intro_tour BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    )
    ON CONFLICT (id) DO UPDATE
    SET
        email = EXCLUDED.email,
        full_name = COALESCE(NULLIF(EXCLUDED.full_name, ''), public.profiles.full_name),
        avatar_url = COALESCE(NULLIF(EXCLUDED.avatar_url, ''), public.profiles.avatar_url),
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

DROP TRIGGER IF EXISTS profiles_updated_at ON public.profiles;
CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TABLE IF NOT EXISTS public.user_onboarding (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE NOT NULL,
    age_range TEXT,
    status TEXT,
    education_level TEXT,
    major TEXT,
    school_name TEXT,
    industry TEXT,
    job_title TEXT,
    years_experience INTEGER CHECK (years_experience >= 0),
    target_role TEXT,
    current_focus TEXT,
    current_challenges TEXT,
    desired_outcome TEXT,
    learning_constraints TEXT,
    learning_goals TEXT[] DEFAULT '{}'::TEXT[],
    topics_of_interest TEXT[] DEFAULT '{}'::TEXT[],
    learning_style TEXT,
    daily_study_minutes INTEGER DEFAULT 30,
    ai_persona TEXT,
    ai_persona_description TEXT,
    ai_recommended_topics TEXT[] DEFAULT '{}'::TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.user_onboarding
    ADD COLUMN IF NOT EXISTS age_range TEXT,
    ADD COLUMN IF NOT EXISTS status TEXT,
    ADD COLUMN IF NOT EXISTS education_level TEXT,
    ADD COLUMN IF NOT EXISTS major TEXT,
    ADD COLUMN IF NOT EXISTS school_name TEXT,
    ADD COLUMN IF NOT EXISTS industry TEXT,
    ADD COLUMN IF NOT EXISTS job_title TEXT,
    ADD COLUMN IF NOT EXISTS years_experience INTEGER,
    ADD COLUMN IF NOT EXISTS target_role TEXT,
    ADD COLUMN IF NOT EXISTS current_focus TEXT,
    ADD COLUMN IF NOT EXISTS current_challenges TEXT,
    ADD COLUMN IF NOT EXISTS desired_outcome TEXT,
    ADD COLUMN IF NOT EXISTS learning_constraints TEXT,
    ADD COLUMN IF NOT EXISTS learning_goals TEXT[] DEFAULT '{}'::TEXT[],
    ADD COLUMN IF NOT EXISTS topics_of_interest TEXT[] DEFAULT '{}'::TEXT[],
    ADD COLUMN IF NOT EXISTS learning_style TEXT,
    ADD COLUMN IF NOT EXISTS daily_study_minutes INTEGER DEFAULT 30,
    ADD COLUMN IF NOT EXISTS ai_persona TEXT,
    ADD COLUMN IF NOT EXISTS ai_persona_description TEXT,
    ADD COLUMN IF NOT EXISTS ai_recommended_topics TEXT[] DEFAULT '{}'::TEXT[],
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE public.user_onboarding
    ALTER COLUMN learning_goals SET DEFAULT '{}'::TEXT[],
    ALTER COLUMN topics_of_interest SET DEFAULT '{}'::TEXT[],
    ALTER COLUMN ai_recommended_topics SET DEFAULT '{}'::TEXT[],
    ALTER COLUMN daily_study_minutes SET DEFAULT 30;

DROP TRIGGER IF EXISTS user_onboarding_updated_at ON public.user_onboarding;
CREATE TRIGGER user_onboarding_updated_at
    BEFORE UPDATE ON public.user_onboarding
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

INSERT INTO public.profiles (id, email, full_name, avatar_url)
SELECT
    u.id,
    u.email,
    u.raw_user_meta_data->>'full_name',
    u.raw_user_meta_data->>'avatar_url'
FROM auth.users AS u
LEFT JOIN public.profiles AS p ON p.id = u.id
WHERE p.id IS NULL;

INSERT INTO public.user_onboarding (
    user_id,
    learning_goals,
    topics_of_interest,
    daily_study_minutes
)
SELECT
    p.id,
    '{}'::TEXT[],
    '{}'::TEXT[],
    30
FROM public.profiles AS p
LEFT JOIN public.user_onboarding AS o ON o.user_id = p.id
WHERE o.user_id IS NULL;

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_onboarding ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "profiles_select_own" ON public.profiles;
DROP POLICY IF EXISTS "profiles_insert_own" ON public.profiles;
DROP POLICY IF EXISTS "profiles_update_own" ON public.profiles;

CREATE POLICY "profiles_select_own"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "profiles_insert_own"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "profiles_update_own"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "onboarding_all_own" ON public.user_onboarding;
DROP POLICY IF EXISTS "user_onboarding_own" ON public.user_onboarding;
DROP POLICY IF EXISTS "onboarding_select_own" ON public.user_onboarding;
DROP POLICY IF EXISTS "onboarding_insert_own" ON public.user_onboarding;
DROP POLICY IF EXISTS "onboarding_update_own" ON public.user_onboarding;

CREATE POLICY "onboarding_select_own"
    ON public.user_onboarding FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "onboarding_insert_own"
    ON public.user_onboarding FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "onboarding_update_own"
    ON public.user_onboarding FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

NOTIFY pgrst, 'reload schema';

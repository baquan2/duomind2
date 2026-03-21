DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'user_onboarding'
    ) THEN
        RAISE EXCEPTION 'public.user_onboarding does not exist. Run base schema or the onboarding bootstrap migration first.';
    END IF;
END $$;

ALTER TABLE public.user_onboarding
    ADD COLUMN IF NOT EXISTS current_focus TEXT,
    ADD COLUMN IF NOT EXISTS current_challenges TEXT,
    ADD COLUMN IF NOT EXISTS desired_outcome TEXT,
    ADD COLUMN IF NOT EXISTS learning_constraints TEXT;

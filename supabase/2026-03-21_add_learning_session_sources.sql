ALTER TABLE public.learning_sessions
ADD COLUMN IF NOT EXISTS sources JSONB DEFAULT '[]'::jsonb;

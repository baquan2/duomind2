-- Backfill missing profiles from auth.users
-- Use this once if some users were created before the trigger existed.

INSERT INTO public.profiles (id, email, full_name, avatar_url)
SELECT
    u.id,
    u.email,
    u.raw_user_meta_data->>'full_name',
    u.raw_user_meta_data->>'avatar_url'
FROM auth.users AS u
LEFT JOIN public.profiles AS p
    ON p.id = u.id
WHERE p.id IS NULL;

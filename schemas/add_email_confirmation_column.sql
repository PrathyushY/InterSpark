-- Add email_confirmed column to profiles table
-- Run this SQL in your Supabase SQL Editor

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN DEFAULT FALSE;

-- Update existing users to have email_confirmed = true (assuming they're already verified)
-- You can remove this line if you want existing users to re-verify their emails
UPDATE public.profiles
SET email_confirmed = TRUE
WHERE email_confirmed IS NULL;

-- Add comment for documentation
COMMENT
ON COLUMN public.profiles.email_confirmed IS 'Tracks whether user has confirmed their email address';

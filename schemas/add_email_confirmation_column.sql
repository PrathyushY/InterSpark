-- Add email_confirmed column to profiles table
-- Run this SQL in your Supabase SQL Editor

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN DEFAULT TRUE;

-- Update existing users to have email_confirmed = true (assuming they're already verified)
-- This allows existing users to continue using the app without needing to reverify
UPDATE public.profiles
SET email_confirmed = TRUE
WHERE email_confirmed IS NULL;

-- Create an index for faster queries on email confirmation status
CREATE INDEX IF NOT EXISTS idx_profiles_email_confirmed 
ON public.profiles(email_confirmed);

-- Add comment for documentation
COMMENT ON COLUMN public.profiles.email_confirmed IS 'Tracks whether user has confirmed their email address';

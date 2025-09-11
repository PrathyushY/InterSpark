-- Add skills_needed column to opportunities table
-- This column will store skills as a JSON array
ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS skills_needed JSONB DEFAULT '[]'::jsonb;

-- Add category column if it doesn't exist
ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS category VARCHAR(100);

-- Update the status constraint to include 'draft'
ALTER TABLE public.opportunities 
DROP CONSTRAINT IF EXISTS opportunities_status_check;

ALTER TABLE public.opportunities 
ADD CONSTRAINT opportunities_status_check 
CHECK (status IN ('active', 'inactive', 'expired', 'draft'));

-- Add index for better query performance on skills
CREATE INDEX IF NOT EXISTS opportunities_skills_needed_idx ON public.opportunities USING GIN (skills_needed);
CREATE INDEX IF NOT EXISTS opportunities_category_idx ON public.opportunities(category);

-- Update existing opportunities to have empty skills array if null
UPDATE public.opportunities 
SET skills_needed = '[]'::jsonb 
WHERE skills_needed IS NULL;

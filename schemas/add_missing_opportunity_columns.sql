-- Add missing columns to opportunities table
-- Run this SQL in your Supabase SQL Editor

-- Add image column for banner images
ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS image VARCHAR(500);

-- Add category column if it doesn't exist
ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS category VARCHAR(100);

-- Add type-specific columns for different opportunity types
ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS eligibility_criteria TEXT,
ADD COLUMN IF NOT EXISTS age_range VARCHAR(50),
ADD COLUMN IF NOT EXISTS prerequisite_skills TEXT,
ADD COLUMN IF NOT EXISTS award_amount VARCHAR(255),
ADD COLUMN IF NOT EXISTS program_dates VARCHAR(255),
ADD COLUMN IF NOT EXISTS mentor_info TEXT,
ADD COLUMN IF NOT EXISTS research_field VARCHAR(255),
ADD COLUMN IF NOT EXISTS commitment_level VARCHAR(255),
ADD COLUMN IF NOT EXISTS application_materials TEXT,
ADD COLUMN IF NOT EXISTS selection_process TEXT,
ADD COLUMN IF NOT EXISTS skills_needed JSONB;

-- Update the type check constraint to include new opportunity types
ALTER TABLE public.opportunities 
DROP CONSTRAINT IF EXISTS opportunities_type_check;

ALTER TABLE public.opportunities 
ADD CONSTRAINT opportunities_type_check 
CHECK (type IN (
    'Internship', 'Volunteer', 'Full-time', 'Part-time', 'Job', 
    'Summer Camp', 'Research Opportunity', 'Summer Program', 
    'Scholarship', 'Competition', 'Workshop', 'Mentorship'
));

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS opportunities_category_idx ON public.opportunities(category);
CREATE INDEX IF NOT EXISTS opportunities_type_updated_idx ON public.opportunities(type);

-- Add comments for documentation
COMMENT ON COLUMN public.opportunities.image IS 'URL to banner image in Supabase Storage';
COMMENT ON COLUMN public.opportunities.category IS 'Opportunity category (Technology, Healthcare, etc.)';
COMMENT ON COLUMN public.opportunities.skills_needed IS 'JSON array of required skills';
COMMENT ON COLUMN public.opportunities.eligibility_criteria IS 'Specific eligibility requirements for scholarships/competitions';
COMMENT ON COLUMN public.opportunities.age_range IS 'Age range for camps/workshops';
COMMENT ON COLUMN public.opportunities.prerequisite_skills IS 'Required background knowledge for research opportunities';
COMMENT ON COLUMN public.opportunities.award_amount IS 'Award amount for scholarships/competitions';
COMMENT ON COLUMN public.opportunities.program_dates IS 'Specific dates for camps/workshops';
COMMENT ON COLUMN public.opportunities.mentor_info IS 'Information about mentors for mentorship opportunities';
COMMENT ON COLUMN public.opportunities.research_field IS 'Research field for research opportunities';
COMMENT ON COLUMN public.opportunities.commitment_level IS 'Time commitment for work-based opportunities';
COMMENT ON COLUMN public.opportunities.application_materials IS 'Required application materials';
COMMENT ON COLUMN public.opportunities.selection_process IS 'Description of selection process';
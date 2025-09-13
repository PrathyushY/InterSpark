-- Update opportunities table to support new opportunity types and fields
-- Run this after the existing schema

-- First, remove the old type constraint
ALTER TABLE public.opportunities 
DROP CONSTRAINT IF EXISTS opportunities_type_check;

-- Add the new type constraint with all the new types
ALTER TABLE public.opportunities 
ADD CONSTRAINT opportunities_type_check 
CHECK (type IN (
    'Internship', 
    'Volunteer', 
    'Job', 
    'Summer Camp', 
    'Research Opportunity', 
    'Summer Program', 
    'Scholarship', 
    'Competition', 
    'Workshop', 
    'Mentorship', 
    'Full-time', 
    'Part-time'
));

-- Add new columns for specific opportunity types
ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS eligibility_criteria TEXT; -- For scholarships, competitions, etc.

ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS age_range VARCHAR(50); -- For summer camps, workshops

ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS prerequisite_skills TEXT; -- For research opportunities, advanced programs

ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS award_amount VARCHAR(100); -- For scholarships, competitions

ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS program_dates VARCHAR(200); -- For summer programs, camps

ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS mentor_info TEXT; -- For mentorship opportunities

ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS research_field VARCHAR(100); -- For research opportunities

ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS commitment_level VARCHAR(100); -- Hours per week, full-time equivalent

ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS application_materials TEXT; -- What students need to submit

ALTER TABLE public.opportunities 
ADD COLUMN IF NOT EXISTS selection_process TEXT; -- How candidates are selected

-- Add indexes for the new columns
CREATE INDEX IF NOT EXISTS opportunities_eligibility_criteria_idx ON public.opportunities(eligibility_criteria);
CREATE INDEX IF NOT EXISTS opportunities_age_range_idx ON public.opportunities(age_range);
CREATE INDEX IF NOT EXISTS opportunities_research_field_idx ON public.opportunities(research_field);
CREATE INDEX IF NOT EXISTS opportunities_commitment_level_idx ON public.opportunities(commitment_level);

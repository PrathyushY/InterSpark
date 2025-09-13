-- InterSpark Database Schema for Supabase
-- Run these SQL commands in your Supabase SQL Editor

-- Enable Row Level Security
ALTER
DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

-- Create profiles table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.profiles
(
    id
    UUID
    REFERENCES
    auth
    .
    users
(
    id
) ON DELETE CASCADE PRIMARY KEY,
    email VARCHAR
(
    255
) UNIQUE NOT NULL,
    name VARCHAR
(
    255
) NOT NULL,
    phone VARCHAR
(
    20
),
    location VARCHAR
(
    255
),
    user_type VARCHAR
(
    20
) NOT NULL CHECK
(
    user_type
    IN
(
    'student',
    'organization'
)),
    profile_image VARCHAR
(
    500
), -- URL to profile image in storage

-- Student-specific fields
    school VARCHAR
(
    255
),
    grade VARCHAR
(
    50
),
    skills TEXT,
    bio TEXT,
    github_url VARCHAR
(
    500
),
    linkedin_url VARCHAR
(
    500
),
    portfolio_url VARCHAR
(
    500
),

    -- Organization-specific fields
    organization_name VARCHAR
(
    255
),
    industry VARCHAR
(
    255
),
    organization_size VARCHAR
(
    50
),
    description TEXT,
    website VARCHAR
(
    500
),

    created_at TIMESTAMP
  WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP
  WITH TIME ZONE DEFAULT NOW()
    );

-- Create opportunities table
CREATE TABLE IF NOT EXISTS public.opportunities
(
    id
    BIGSERIAL
    PRIMARY
    KEY,
    title
    VARCHAR
(
    255
) NOT NULL,
    company_id UUID REFERENCES public.profiles
(
    id
) ON DELETE CASCADE,
    location VARCHAR
(
    255
),
    type VARCHAR
(
    50
) CHECK
(
    type
    IN
(
    'Internship',
    'Volunteer',
    'Full-time',
    'Part-time'
)),
    requirements TEXT,
    compensation VARCHAR
(
    255
),
    duration VARCHAR
(
    100
),
    application_deadline DATE,
    description TEXT,
    status VARCHAR
(
    20
) DEFAULT 'active' CHECK
(
    status
    IN
(
    'active',
    'inactive',
    'expired'
)),
    created_at TIMESTAMP
  WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP
  WITH TIME ZONE DEFAULT NOW()
    );

-- Create applications table (for future use)
CREATE TABLE IF NOT EXISTS public.applications
(
    id
    BIGSERIAL
    PRIMARY
    KEY,
    student_id
    UUID
    REFERENCES
    public
    .
    profiles
(
    id
) ON DELETE CASCADE,
    opportunity_id BIGINT REFERENCES public.opportunities
(
    id
)
  ON DELETE CASCADE,
    status VARCHAR
(
    20
) DEFAULT 'pending' CHECK
(
    status
    IN
(
    'pending',
    'accepted',
    'rejected',
    'withdrawn'
)),
    cover_letter TEXT,
    applied_at TIMESTAMP
  WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP
  WITH TIME ZONE DEFAULT NOW(),
    UNIQUE
(
    student_id,
    opportunity_id
)
    );

-- Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles
CREATE
POLICY "Public profiles are viewable by everyone"
ON public.profiles FOR
SELECT
    USING (true);

CREATE
POLICY "Users can insert their own profile"
ON public.profiles FOR INSERT 
WITH CHECK (auth.uid() = id);

CREATE
POLICY "Users can update their own profile"
ON public.profiles FOR
UPDATE
    USING (auth.uid() = id);

-- RLS Policies for opportunities
CREATE
POLICY "Opportunities are viewable by everyone"
ON public.opportunities FOR
SELECT
    USING (true);

CREATE
POLICY "Companies can insert opportunities"
ON public.opportunities FOR INSERT 
WITH CHECK (
    auth.uid() = company_id AND 
    EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE id = auth.uid() AND user_type = 'organization'
    )
);

CREATE
POLICY "Companies can update their own opportunities"
ON public.opportunities FOR
UPDATE
    USING (auth.uid() = company_id);

CREATE
POLICY "Companies can delete their own opportunities"
ON public.opportunities FOR DELETE
USING (auth.uid() = company_id);

-- RLS Policies for applications
CREATE
POLICY "Students can view their own applications"
ON public.applications FOR
SELECT
    USING (auth.uid() = student_id);

CREATE
POLICY "Companies can view applications for their opportunities"
ON public.applications FOR
SELECT
    USING (
    EXISTS (
    SELECT 1 FROM public.opportunities
    WHERE id = opportunity_id AND company_id = auth.uid()
    )
    );

CREATE
POLICY "Students can insert their own applications"
ON public.applications FOR INSERT 
WITH CHECK (
    auth.uid() = student_id AND 
    EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE id = auth.uid() AND user_type = 'student'
    )
);

CREATE
POLICY "Students can update their own applications"
ON public.applications FOR
UPDATE
    USING (auth.uid() = student_id);

-- Functions
CREATE
OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
INSERT INTO public.profiles (id, email, name, user_type)
VALUES (NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data ->>'name', 'New User'),
        COALESCE(NEW.raw_user_meta_data ->>'user_type', 'student'));
RETURN NEW;
END;
$$
LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user creation
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT
    ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update updated_at timestamp
CREATE
OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at
= NOW();
RETURN NEW;
END;
$$
LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE
    ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER opportunities_updated_at
    BEFORE UPDATE
    ON public.opportunities
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER applications_updated_at
    BEFORE UPDATE
    ON public.applications
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS profiles_user_type_idx ON public.profiles(user_type);
CREATE INDEX IF NOT EXISTS profiles_email_idx ON public.profiles(email);
CREATE INDEX IF NOT EXISTS opportunities_company_id_idx ON public.opportunities(company_id);
CREATE INDEX IF NOT EXISTS opportunities_type_idx ON public.opportunities(type);
CREATE INDEX IF NOT EXISTS opportunities_status_idx ON public.opportunities(status);
CREATE INDEX IF NOT EXISTS applications_student_id_idx ON public.applications(student_id);
CREATE INDEX IF NOT EXISTS applications_opportunity_id_idx ON public.applications(opportunity_id);
CREATE INDEX IF NOT EXISTS applications_status_idx ON public.applications(status);

-- Create saved profiles table
CREATE TABLE IF NOT EXISTS public.saved_profiles
(
    id
    BIGSERIAL
    PRIMARY
    KEY,
    user_id
    UUID
    REFERENCES
    public
    .
    profiles
(
    id
) ON DELETE CASCADE,
    profile_id UUID REFERENCES public.profiles
(
    id
)
  ON DELETE CASCADE,
    created_at TIMESTAMP
  WITH TIME ZONE DEFAULT NOW(),
    UNIQUE
(
    user_id,
    profile_id
)
    );

-- Create saved opportunities table
CREATE TABLE IF NOT EXISTS public.saved_opportunities
(
    id
    BIGSERIAL
    PRIMARY
    KEY,
    user_id
    UUID
    REFERENCES
    public
    .
    profiles
(
    id
) ON DELETE CASCADE,
    opportunity_id BIGINT REFERENCES public.opportunities
(
    id
)
  ON DELETE CASCADE,
    created_at TIMESTAMP
  WITH TIME ZONE DEFAULT NOW(),
    UNIQUE
(
    user_id,
    opportunity_id
)
    );

-- Enable RLS on saved tables
ALTER TABLE public.saved_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_opportunities ENABLE ROW LEVEL SECURITY;

-- RLS Policies for saved profiles
CREATE
POLICY "Users can view their own saved profiles"
ON public.saved_profiles FOR
SELECT
    USING (auth.uid() = user_id);

CREATE
POLICY "Users can save profiles"
ON public.saved_profiles FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE
POLICY "Users can unsave their own saved profiles"
ON public.saved_profiles FOR DELETE
USING (auth.uid() = user_id);

-- RLS Policies for saved opportunities
CREATE
POLICY "Users can view their own saved opportunities"
ON public.saved_opportunities FOR
SELECT
    USING (auth.uid() = user_id);

CREATE
POLICY "Users can save opportunities"
ON public.saved_opportunities FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE
POLICY "Users can unsave their own saved opportunities"
ON public.saved_opportunities FOR DELETE
USING (auth.uid() = user_id);

-- Indexes for saved tables
CREATE INDEX IF NOT EXISTS saved_profiles_user_id_idx ON public.saved_profiles(user_id);
CREATE INDEX IF NOT EXISTS saved_profiles_profile_id_idx ON public.saved_profiles(profile_id);
CREATE INDEX IF NOT EXISTS saved_opportunities_user_id_idx ON public.saved_opportunities(user_id);
CREATE INDEX IF NOT EXISTS saved_opportunities_opportunity_id_idx ON public.saved_opportunities(opportunity_id);

-- Create saved_opportunities table
CREATE TABLE IF NOT EXISTS saved_opportunities
(
    id
    SERIAL
    PRIMARY
    KEY,
    user_id
    UUID
    REFERENCES
    auth
    .
    users
(
    id
) ON DELETE CASCADE,
    opportunity_id INTEGER REFERENCES opportunities
(
    id
)
  ON DELETE CASCADE,
    created_at TIMESTAMP
  WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE
(
    user_id,
    opportunity_id
)
    );

-- Create saved_profiles table  
CREATE TABLE IF NOT EXISTS saved_profiles
(
    id
    SERIAL
    PRIMARY
    KEY,
    user_id
    UUID
    REFERENCES
    auth
    .
    users
(
    id
) ON DELETE CASCADE,
    profile_id UUID REFERENCES profiles
(
    id
)
  ON DELETE CASCADE,
    created_at TIMESTAMP
  WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE
(
    user_id,
    profile_id
)
    );

-- Enable RLS
ALTER TABLE saved_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies for saved_opportunities
CREATE
POLICY "Users can view their own saved opportunities"
ON saved_opportunities FOR
SELECT
    USING (auth.uid() = user_id);

CREATE
POLICY "Users can insert their own saved opportunities"
ON saved_opportunities FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE
POLICY "Users can delete their own saved opportunities"
ON saved_opportunities FOR DELETE
USING (auth.uid() = user_id);

-- RLS Policies for saved_profiles
CREATE
POLICY "Users can view their own saved profiles"
ON saved_profiles FOR
SELECT
    USING (auth.uid() = user_id);

CREATE
POLICY "Users can insert their own saved profiles"
ON saved_profiles FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE
POLICY "Users can delete their own saved profiles"
ON saved_profiles FOR DELETE
USING (auth.uid() = user_id);

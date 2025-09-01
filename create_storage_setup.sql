-- Storage setup for profile pictures
-- Run this in your Supabase SQL Editor

-- Create the profile-pictures bucket (public bucket for easy access)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'profile-pictures',
    'profile-pictures', 
    true, -- Public bucket for easy image serving
    5242880, -- 5MB limit per file
    ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/gif']::text[]
) ON CONFLICT (id) DO NOTHING;

-- RLS Policies for storage.objects (profile-pictures bucket)

-- Allow authenticated users to upload their own profile pictures
CREATE POLICY "Allow authenticated users to upload profile pictures" 
ON storage.objects 
FOR INSERT 
TO authenticated 
WITH CHECK (
    bucket_id = 'profile-pictures' 
    AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
);

-- Allow users to view all profile pictures (public bucket)
CREATE POLICY "Allow public viewing of profile pictures" 
ON storage.objects 
FOR SELECT 
USING (bucket_id = 'profile-pictures');

-- Allow authenticated users to update/replace their own profile pictures
CREATE POLICY "Allow users to update own profile pictures" 
ON storage.objects 
FOR UPDATE 
TO authenticated 
USING (
    bucket_id = 'profile-pictures' 
    AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
);

-- Allow authenticated users to delete their own profile pictures
CREATE POLICY "Allow users to delete own profile pictures" 
ON storage.objects 
FOR DELETE 
TO authenticated 
USING (
    bucket_id = 'profile-pictures' 
    AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
);

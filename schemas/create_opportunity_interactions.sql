-- InterSpark User Interactions Schema
-- Tracks user interactions with opportunities for personalized ranking
-- Run these SQL commands in your Supabase SQL Editor

-- =============================================================================
-- DATA RETENTION POLICY
-- =============================================================================
-- To prevent unbounded growth, we implement the following retention rules:
-- 
-- | Interaction Type | Retention Period | Rationale |
-- |-----------------|------------------|-----------|
-- | view            | 30 days          | Only recent views affect relevance |
-- | click           | 30 days          | Recent engagement signal |
-- | share           | 30 days          | Recent engagement signal |
-- | dismiss         | 180 days         | Kept longer - explicit user preference |
--
-- Cleanup runs automatically via scheduled function (pg_cron or external trigger)
-- =============================================================================

-- Create opportunity_interactions table
-- Tracks views, dismissals, and other interaction signals
CREATE TABLE IF NOT EXISTS public.opportunity_interactions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    opportunity_id BIGINT REFERENCES public.opportunities(id) ON DELETE CASCADE,
    interaction_type VARCHAR(20) NOT NULL CHECK (
        interaction_type IN ('view', 'dismiss', 'click', 'share')
    ),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Allow multiple views but only one dismiss per user/opportunity
    UNIQUE (user_id, opportunity_id, interaction_type)
);

-- Enable Row Level Security
ALTER TABLE public.opportunity_interactions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for opportunity_interactions (drop first to make idempotent)
DROP POLICY IF EXISTS "Users can view their own interactions" ON public.opportunity_interactions;
CREATE POLICY "Users can view their own interactions"
ON public.opportunity_interactions FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create their own interactions" ON public.opportunity_interactions;
CREATE POLICY "Users can create their own interactions"
ON public.opportunity_interactions FOR INSERT 
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own interactions" ON public.opportunity_interactions;
CREATE POLICY "Users can delete their own interactions"
ON public.opportunity_interactions FOR DELETE
USING (auth.uid() = user_id);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS opportunity_interactions_user_id_idx 
    ON public.opportunity_interactions(user_id);
CREATE INDEX IF NOT EXISTS opportunity_interactions_opportunity_id_idx 
    ON public.opportunity_interactions(opportunity_id);
CREATE INDEX IF NOT EXISTS opportunity_interactions_type_idx 
    ON public.opportunity_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS opportunity_interactions_user_type_idx 
    ON public.opportunity_interactions(user_id, interaction_type);
-- Index for efficient cleanup queries
CREATE INDEX IF NOT EXISTS opportunity_interactions_created_at_idx 
    ON public.opportunity_interactions(created_at);
CREATE INDEX IF NOT EXISTS opportunity_interactions_cleanup_idx 
    ON public.opportunity_interactions(interaction_type, created_at);

-- =============================================================================
-- AUTOMATIC DATA CLEANUP FUNCTION
-- =============================================================================
-- This function deletes old interaction records based on retention policy.
-- Should be called periodically (daily recommended) via:
--   1. Supabase pg_cron extension (if enabled)
--   2. External cron job calling this function
--   3. Application-level scheduled task

CREATE OR REPLACE FUNCTION public.cleanup_old_interactions()
RETURNS JSON AS $$
DECLARE
    views_deleted INTEGER;
    clicks_deleted INTEGER;
    shares_deleted INTEGER;
    dismisses_deleted INTEGER;
    total_deleted INTEGER;
BEGIN
    -- Delete views older than 30 days
    DELETE FROM public.opportunity_interactions
    WHERE interaction_type = 'view'
      AND created_at < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS views_deleted = ROW_COUNT;
    
    -- Delete clicks older than 30 days
    DELETE FROM public.opportunity_interactions
    WHERE interaction_type = 'click'
      AND created_at < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS clicks_deleted = ROW_COUNT;
    
    -- Delete shares older than 30 days
    DELETE FROM public.opportunity_interactions
    WHERE interaction_type = 'share'
      AND created_at < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS shares_deleted = ROW_COUNT;
    
    -- Delete dismisses older than 180 days (6 months)
    -- Kept longer since this is explicit user preference
    DELETE FROM public.opportunity_interactions
    WHERE interaction_type = 'dismiss'
      AND created_at < NOW() - INTERVAL '180 days';
    GET DIAGNOSTICS dismisses_deleted = ROW_COUNT;
    
    total_deleted := views_deleted + clicks_deleted + shares_deleted + dismisses_deleted;
    
    -- Log the cleanup operation
    RAISE NOTICE 'Interaction cleanup completed: % views, % clicks, % shares, % dismisses deleted (% total)',
        views_deleted, clicks_deleted, shares_deleted, dismisses_deleted, total_deleted;
    
    RETURN json_build_object(
        'success', true,
        'deleted', json_build_object(
            'views', views_deleted,
            'clicks', clicks_deleted,
            'shares', shares_deleted,
            'dismisses', dismisses_deleted,
            'total', total_deleted
        ),
        'timestamp', NOW()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute to service role (for scheduled jobs)
GRANT EXECUTE ON FUNCTION public.cleanup_old_interactions TO service_role;

-- =============================================================================
-- OPTIONAL: Automatic scheduling with pg_cron (if extension is enabled)
-- =============================================================================
-- Uncomment the following lines if you have pg_cron enabled in Supabase:
--
-- SELECT cron.schedule(
--     'cleanup-opportunity-interactions',  -- job name
--     '0 3 * * *',                          -- run daily at 3 AM UTC
--     $$SELECT public.cleanup_old_interactions()$$
-- );

-- =============================================================================
-- STORAGE ESTIMATION & MONITORING
-- =============================================================================
-- View to monitor table size and estimate growth

CREATE OR REPLACE VIEW public.interaction_stats AS
SELECT 
    interaction_type,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as last_7_days,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as last_30_days
FROM public.opportunity_interactions
GROUP BY interaction_type
UNION ALL
SELECT 
    'TOTAL' as interaction_type,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as last_7_days,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as last_30_days
FROM public.opportunity_interactions;

-- =============================================================================

-- Function to upsert interaction (update timestamp if exists, insert if not)
CREATE OR REPLACE FUNCTION public.upsert_opportunity_interaction(
    p_user_id UUID,
    p_opportunity_id BIGINT,
    p_interaction_type VARCHAR(20)
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO public.opportunity_interactions (user_id, opportunity_id, interaction_type)
    VALUES (p_user_id, p_opportunity_id, p_interaction_type)
    ON CONFLICT (user_id, opportunity_id, interaction_type) 
    DO UPDATE SET created_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.upsert_opportunity_interaction TO authenticated;

-- View to get user's dismissed opportunities
CREATE OR REPLACE VIEW public.user_dismissed_opportunities AS
SELECT 
    user_id,
    opportunity_id,
    created_at as dismissed_at
FROM public.opportunity_interactions
WHERE interaction_type = 'dismiss';

-- View to get user's recently viewed opportunities (last 30 days)
CREATE OR REPLACE VIEW public.user_viewed_opportunities AS
SELECT 
    user_id,
    opportunity_id,
    MAX(created_at) as last_viewed_at,
    COUNT(*) as view_count
FROM public.opportunity_interactions
WHERE interaction_type = 'view'
    AND created_at > NOW() - INTERVAL '30 days'
GROUP BY user_id, opportunity_id;

-- Comment explaining the schema
COMMENT ON TABLE public.opportunity_interactions IS 
'Tracks user interactions with opportunities for personalized ranking. 
Interaction types:
- view: User viewed the opportunity details
- dismiss: User explicitly dismissed/hid the opportunity
- click: User clicked on external apply link
- share: User shared the opportunity';

# InterSpark Personalized Opportunity Ranking System

## Overview

This document describes the personalized opportunity ranking system that sorts opportunities by relevance for each user. The system powers both the **Opportunities page** and the **"Suggested For You"** section on the **Dashboard**.

## How Relevance is Calculated

### Scoring Components

The relevance score (0-1) is computed using five weighted components:

| Component | Weight | Description |
|-----------|--------|-------------|
| **Skill Match** | 40% | Overlap between user's skills and opportunity's required skills |
| **Bio Similarity** | 25% | Semantic similarity between user bio and opportunity description |
| **Tag/Interest Match** | 15% | Category and type alignment with user interests |
| **Recency** | 10% | Newer opportunities get slight boost (14-day half-life decay) |
| **Interactions** | 10% | User behavior signals (saved, viewed, dismissed, applied) |

### Detailed Component Explanations

#### 1. Skill Match Score (40%)

Compares user skills against opportunity requirements using two methods:

- **Exact Match**: Full credit (1.0) for identical skill names
- **Semantic Match**: Partial credit (0.3-0.7) for semantically similar skills using sentence embeddings

Example: If opportunity requires "Machine Learning" and user has "Deep Learning", semantic similarity captures this relationship.

**Why 40%?** Skills are the strongest indicator of qualification and fit. Users with matching skills are most likely to succeed in the role.

#### 2. Bio Similarity Score (25%)

Uses sentence embeddings to measure semantic similarity between:
- User's bio/description
- Opportunity description

This captures alignment in:
- Career interests
- Domain expertise  
- Project types
- Values and motivations

**Why 25%?** The bio contains rich context about what users are looking for beyond just skills.

#### 3. Tag/Interest Match Score (15%)

Matches opportunity metadata against inferred user interests:
- Opportunity type (Internship, Volunteer, etc.)
- Category (Technology, Healthcare, etc.)
- User's skill-derived interests

**Why 15%?** Provides additional signal for preference alignment without over-weighting.

#### 4. Recency Score (10%)

Implements exponential decay to favor newer opportunities:

```
score = 0.5^(days_old / 14)
```

- Brand new opportunity: 1.0
- 14 days old: 0.5
- 28 days old: 0.25
- Minimum: 0.1 (never fully penalizes old opportunities)

**Why 10%?** Balances freshness without overwhelming relevance signals.

#### 5. Interaction Score (10%)

Incorporates user behavior signals:

| Signal | Effect |
|--------|--------|
| Saved | +0.3 boost |
| Viewed | +0.1 boost |
| Applied | Excluded from results |
| Dismissed | -0.5 penalty (or excluded) |

**Why 10%?** Leverages implicit feedback to personalize without over-fitting to recent behavior.

## Technical Implementation

### Semantic Similarity (Embeddings)

The system uses **sentence-transformers** with the `all-MiniLM-L6-v2` model:

- Lightweight (~80MB)
- Fast inference
- Good balance of speed and quality
- Produces 384-dimensional embeddings

**Fallback**: If sentence-transformers is unavailable, falls back to keyword-based Jaccard similarity.

### Caching Strategy

1. **Embedding Cache**: LRU cache (1000 entries) for computed embeddings
2. **Score Cache**: TTL-based cache (30 minutes) for user-opportunity scores
3. **Lazy Loading**: Model loads only on first use to minimize startup time

### Database Schema

New `opportunity_interactions` table tracks:
- `view`: User viewed opportunity details
- `dismiss`: User explicitly dismissed/hid opportunity
- `click`: User clicked external apply link
- `share`: User shared opportunity

### Data Retention Policy

To prevent unbounded database growth, interaction data is automatically cleaned up:

| Interaction Type | Retention Period | Rationale |
|-----------------|------------------|-----------|
| `view` | 30 days | Only recent views affect relevance |
| `click` | 30 days | Recent engagement signal |
| `share` | 30 days | Recent engagement signal |
| `dismiss` | 180 days | Kept longer - explicit user preference |

**Cleanup Methods:**
1. **Database Function**: `cleanup_old_interactions()` - callable via Supabase RPC
2. **pg_cron** (optional): Schedule daily automatic cleanup at 3 AM UTC
3. **Application**: Call `supabase_service.cleanup_old_interactions()` from a scheduled task

**Storage Estimation:**
- Each interaction record: ~100 bytes
- 1000 active users × 50 views/month = 50,000 records = ~5 MB/month
- With 30-day retention: max ~5 MB for views at steady state

**Monitoring:**
- Use `interaction_stats` view to monitor table growth
- Call `supabase_service.get_interaction_stats()` to check counts

## Usage in Application

### Dashboard (Suggested For You)

```python
relevance_service.get_suggested_opportunities(
    user_profile=profile,
    opportunities=all_opportunities,
    saved_ids=saved_ids,
    applied_ids=applied_ids,
    dismissed_ids=dismissed_ids,
    limit=6
)
```

- Shows top 6 personalized suggestions
- Excludes applied and dismissed opportunities
- Shows "Great match" / "Good match" badges

### Opportunities Page

```python
relevance_service.rank_opportunities(
    user_profile=profile,
    opportunities=filtered_opportunities,
    saved_ids=saved_ids,
    viewed_ids=viewed_ids,
    applied_ids=applied_ids,
    dismissed_ids=dismissed_ids
)
```

- Default sort: relevance
- Alternatives: recent, deadline
- Shows all opportunities (doesn't exclude applied/dismissed)
- Match indicator badges on cards

## Setup Requirements

### Dependencies

Add to `requirements.txt`:
```
sentence-transformers>=2.2.0
numpy>=1.24.0
```

### Database Migration

Run the SQL in `schemas/create_opportunity_interactions.sql` to create:
- `opportunity_interactions` table
- RLS policies
- Indexes
- Utility views

## Performance Considerations

1. **First Load**: Model loading takes ~2-5 seconds on first use
2. **Subsequent Calls**: Cached embeddings make scoring very fast (<100ms for 100 opportunities)
3. **Memory**: ~100MB for model + ~50MB for caches
4. **Scaling**: For large datasets, consider precomputing embeddings batch

## Extending the System

### Adding New Signals

1. Add new interaction type in schema
2. Update `record_opportunity_interaction()` 
3. Modify `_compute_interaction_score()` with new weights

### Adjusting Weights

Modify class constants in `RelevanceService`:
```python
WEIGHT_SKILL_MATCH = 0.40
WEIGHT_BIO_SIMILARITY = 0.25
WEIGHT_TAG_MATCH = 0.15
WEIGHT_RECENCY = 0.10
WEIGHT_INTERACTIONS = 0.10
```

### Alternative Models

Change the embedding model in initialization:
```python
RelevanceService(model_name="all-mpnet-base-v2")  # Higher quality
RelevanceService(model_name="paraphrase-MiniLM-L3-v2")  # Faster
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dismiss_opportunity/<id>` | POST | Mark opportunity as not interested |
| `/undismiss_opportunity/<id>` | POST | Restore dismissed opportunity |
| `/opportunity/<id>` | GET | View details (auto-records view) |

## Monitoring

The system logs:
- Model loading status
- Number of suggestions generated per user
- Relevance sorting application status
- Interaction recording events

Check logs for `relevance_service` and `app` loggers.

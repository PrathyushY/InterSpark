# Talent Search Relevance Ranking System

## Overview

The Talent Search feature now includes intelligent relevance-based ranking that shows you the most compatible connections first. This system analyzes profile similarity and compatibility to surface people you're most likely to want to connect with.

## How It Works

### Scoring Components

When you view Talent Search results, the system computes a relevance score (0-1) between your profile and each candidate profile using these weighted factors:

1. **Skill Overlap & Complementarity (35%)**
   - **Overlap (60%)**: Shared skills indicate collaboration potential
   - **Complementarity (40%)**: Related but different skills suggest learning opportunities
   - Uses semantic matching to find related skills (e.g., "React" and "React Native")

2. **Bio Similarity (30%)**
   - Semantic analysis of your bio vs candidate's bio
   - Looks for similar interests, experiences, and goals
   - Uses sentence embeddings for deeper understanding beyond keywords

3. **Interest Overlap (20%)**
   - Matches between your interests/skills and theirs
   - Includes both exact and semantic matches
   - Helps find people with aligned passions

4. **Experience Compatibility (15%)**
   - Grade/year proximity (same or adjacent years score higher)
   - School matching (same school = strong connection signal)
   - Considers experience level for peer vs mentor matching

### Match Quality Indicators

Results include visual badges:
- **🌟 Great Match** (>70% score): Highly compatible profiles with strong alignment
- **✓ Good Match** (>50% score): Compatible profiles worth exploring

## User Interface

### Sort Options

The Talent Search page includes a sort dropdown with three options:

1. **Relevance** (default): Sorts by compatibility score
2. **Most Recent**: Newest profiles first
3. **Name (A-Z)**: Alphabetical by first name

### How to Use

1. Navigate to Talent Search
2. Apply any filters (skills, grade, school, location)
3. Select "Relevance" from the Sort dropdown
4. Profiles will be ordered by compatibility with your profile
5. Look for match badges to identify strongest connections

## Technical Implementation

### Files Modified

- **`relevance_service.py`**: Added people ranking methods
  - `compute_people_relevance_score()`: Main scoring function
  - `rank_people()`: Sorts candidate profiles by relevance
  - `_compute_skill_overlap_score()`: Skill matching logic
  - `_compute_bio_similarity_people()`: Bio comparison
  - `_compute_interest_overlap_score()`: Interest matching
  - `_compute_experience_compatibility_score()`: Experience/grade compatibility

- **`app.py`**: Updated talent_search route
  - Added `sort_by` parameter handling
  - Loads viewer profile for relevance scoring
  - Calls `rank_people()` when sort_by='relevance'
  - Falls back gracefully if viewer profile unavailable

- **`templates/talent_search.html`**: Enhanced UI
  - Added sort dropdown with three options
  - Added match quality badges to profile cards
  - Results count display

- **`static/js/talent_search.js`**: Client-side sorting
  - Handles sort dropdown changes
  - Preserves filters when changing sort order
  - Resets to page 1 on sort change

### Graceful Degradation

The system works even with limited data:

- **No embeddings available**: Falls back to keyword-based matching
- **No viewer profile**: Returns candidates in default order
- **Minimal profile data**: Uses available fields, defaults to neutral scores
- **Self-exclusion**: Your own profile is automatically filtered out

### Performance Considerations

- **Caching**: Embeddings are cached to avoid recomputation
- **Lazy loading**: Embedding model loads only when needed
- **Efficient computation**: Similarity calculations optimized with NumPy
- **Pagination**: Only computes scores for displayed results

## Requirements

### Required Python Packages

Install these for optimal performance:

```bash
pip install sentence-transformers numpy
```

Already in `requirements.txt`:
- `sentence-transformers>=2.2.0`
- `numpy>=1.24.0`

### Fallback Behavior

If packages aren't installed:
- System falls back to keyword-based matching
- Jaccard similarity for text comparison
- Exact skill matching only
- Still provides useful results, just less sophisticated

## Scoring Examples

### Example 1: High Match (0.82)
**Your Profile:**
- Skills: Python, React, Machine Learning
- Bio: "Interested in AI and web development. Looking for hackathon teammates."
- Grade: 11th
- School: Lincoln High

**Candidate Profile:**
- Skills: Python, JavaScript, TensorFlow
- Bio: "Passionate about ML and full-stack development. Love building AI projects."
- Grade: 11th
- School: Lincoln High

**Score Breakdown:**
- Skill overlap: 0.85 (Python match, ML/TensorFlow semantic match)
- Bio similarity: 0.88 (AI, development, projects align)
- Interest overlap: 0.80 (ML, web dev)
- Experience: 1.0 (same grade + same school)
- **Total: 0.82** → Great Match ⭐

### Example 2: Medium Match (0.58)
**Your Profile:**
- Skills: Java, Spring Boot, SQL
- Bio: "Backend developer interested in cloud computing."
- Grade: 12th
- School: Washington High

**Candidate Profile:**
- Skills: React, Node.js, MongoDB
- Bio: "Frontend engineer exploring full-stack development."
- Grade: 11th
- School: Jefferson High

**Score Breakdown:**
- Skill overlap: 0.35 (complementary but different stacks)
- Bio similarity: 0.62 (both developers, some overlap)
- Interest overlap: 0.45 (different specializations)
- Experience: 0.60 (adjacent grades, different schools)
- **Total: 0.58** → Good Match ✓

### Example 3: Low Match (0.28)
**Your Profile:**
- Skills: Robotics, C++, Arduino
- Bio: "Building autonomous robots for competitions."
- Grade: 9th

**Candidate Profile:**
- Skills: Graphic Design, Photoshop, Illustrator
- Bio: "Creating digital art and UI designs."
- Grade: 12th

**Score Breakdown:**
- Skill overlap: 0.10 (no overlap, different domains)
- Bio similarity: 0.25 (both creative but different areas)
- Interest overlap: 0.15 (minimal)
- Experience: 0.40 (3-year gap)
- **Total: 0.28** → No badge (low match)

## Best Practices

### For Best Results

1. **Complete Your Profile**
   - Add detailed bio describing interests and goals
   - List all relevant skills
   - Keep profile information up-to-date

2. **Use Filters First**
   - Apply skill/school/grade filters before relevance sorting
   - This gives relevance scoring a better starting set

3. **Interpret Scores Contextually**
   - High scores suggest strong alignment, not perfect matches
   - Explore "Good Match" profiles too—complementary skills can be valuable
   - No badge doesn't mean incompatible, just less obvious overlap

### For Organizations

When searching as an organization:
- Relevance sorting is less applicable (organizations don't have skills/bio)
- Falls back to default ordering
- Consider using filters instead

## Comparison with Opportunity Ranking

| Feature | Opportunity Ranking | People Ranking |
|---------|-------------------|----------------|
| **Primary use** | Finding relevant opportunities | Finding compatible connections |
| **Interaction tracking** | Yes (views, applies, dismisses) | No (static profile comparison) |
| **Recency factor** | Yes (newer = better) | No (profile age irrelevant) |
| **Skill matching** | Exact match focus | Overlap + complementarity |
| **Experience factor** | Minimal | Grade/school compatibility |
| **Weights** | Skill 40%, Bio 25%, Tags 15% | Skill 35%, Bio 30%, Interest 20% |

## Future Enhancements

Potential improvements for future iterations:

1. **Interaction Tracking**: Track profile views, messages sent
2. **Collaborative Filtering**: "Users similar to you also connected with..."
3. **Role-Based Matching**: Optimize for mentor/mentee vs peer matching
4. **Project Compatibility**: Match based on past projects/competitions
5. **Availability Signals**: Factor in active status, response rate
6. **Network Effects**: Boost profiles with mutual connections

## Monitoring & Debugging

### Check if Embeddings are Working

In Python console:
```python
from relevance_service import get_relevance_service
service = get_relevance_service()
print(service._model_loaded)  # True if embeddings available
```

### Test Relevance Scoring

```python
from relevance_service import get_relevance_service
from supabase_config import SupabaseService

service = get_relevance_service()
supabase = SupabaseService()

viewer = supabase.get_student_profile("viewer-user-id")
candidate = supabase.get_student_profile("candidate-user-id")

score = service.compute_people_relevance_score(viewer, candidate)
print(f"Total Score: {score['total_score']:.2f}")
print(f"Components: {score['components']}")
```

### Common Issues

**Problem**: All scores are the same
- **Cause**: Embeddings not loaded, using fallback methods
- **Fix**: Install `sentence-transformers` and `numpy`

**Problem**: Relevance sort doesn't work
- **Cause**: Viewer profile not loaded
- **Fix**: Ensure user is logged in with complete profile

**Problem**: Scores seem random
- **Cause**: Minimal profile data (empty bios, few skills)
- **Fix**: Encourage users to complete profiles

## API Reference

### `compute_people_relevance_score(viewer_profile, candidate_profile)`

Computes relevance between two profiles.

**Parameters:**
- `viewer_profile` (dict): Profile of person viewing talent search
- `candidate_profile` (dict): Profile being evaluated

**Returns:**
```python
{
    'total_score': 0.72,
    'components': {
        'skill_overlap': 0.68,
        'bio_similarity': 0.75,
        'interest_overlap': 0.80,
        'experience_compatibility': 0.65
    },
    'should_exclude': False
}
```

### `rank_people(viewer_profile, candidates, limit=None)`

Ranks a list of candidate profiles by relevance.

**Parameters:**
- `viewer_profile` (dict): Profile of viewer
- `candidates` (list): List of candidate profiles
- `limit` (int, optional): Maximum results to return

**Returns:**
- Sorted list of candidates with `relevance_score` and `score_components` added

---

**Last Updated**: January 9, 2026

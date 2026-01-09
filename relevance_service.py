"""
Relevance Service for InterSpark - Personalized Opportunity Ranking System

This module provides semantic similarity-based opportunity ranking for users.
It computes relevance scores between user profiles and opportunities using:
1. Skill overlap (exact + semantic matching)
2. Bio/description semantic similarity using sentence embeddings
3. Interest/tag matching
4. Recency and interaction signal boosts

The scoring is reusable across the Opportunities page and Dashboard suggestions.
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from functools import lru_cache
import os

logger = logging.getLogger(__name__)

# Try to import sentence-transformers for embeddings
# Falls back to simpler methods if not available
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np

    EMBEDDINGS_AVAILABLE = True
    logger.info("Sentence transformers loaded successfully")
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning(
        "sentence-transformers not available. Using fallback similarity methods."
    )
    np = None


class RelevanceService:
    """
    Service for computing relevance scores between users and opportunities.

    Scoring Components and Weights:
    - Skill Match (40%): Exact and semantic skill overlap
    - Bio Similarity (25%): Semantic similarity between user bio and opportunity description
    - Interest/Tag Match (15%): Category and tag alignment
    - Recency Boost (10%): Newer opportunities get slight boost
    - Interaction Signals (10%): Saved/viewed boost, applied/dismissed penalty

    These weights can be adjusted based on empirical performance.
    """

    # Scoring weights - sum to 1.0
    WEIGHT_SKILL_MATCH = 0.40
    WEIGHT_BIO_SIMILARITY = 0.25
    WEIGHT_TAG_MATCH = 0.15
    WEIGHT_RECENCY = 0.10
    WEIGHT_INTERACTIONS = 0.10

    # Cache settings
    EMBEDDING_CACHE_SIZE = 1000
    SCORE_CACHE_TTL_MINUTES = 30

    # Recency decay parameters
    RECENCY_HALF_LIFE_DAYS = 14  # Score halves every 14 days

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the relevance service.

        Args:
            model_name: The sentence-transformer model to use for embeddings.
                       'all-MiniLM-L6-v2' is a good balance of speed and quality.
        """
        self.model = None
        self.model_name = model_name
        self._embedding_cache: Dict[str, Any] = {}
        self._score_cache: Dict[str, Tuple[float, datetime]] = {}

        if EMBEDDINGS_AVAILABLE:
            try:
                # Lazy load model on first use to improve startup time
                self._model_loaded = False
            except Exception as e:
                logger.error(f"Failed to initialize embedding model: {e}")
                self._model_loaded = False

    def _ensure_model_loaded(self):
        """Lazy load the embedding model."""
        if not EMBEDDINGS_AVAILABLE:
            return False

        if not self._model_loaded:
            try:
                logger.info(f"Loading sentence transformer model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                self._model_loaded = True
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self._model_loaded = False

        return self._model_loaded

    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for text content."""
        return hashlib.md5(text.encode()).hexdigest()

    def _get_embedding(self, text: str) -> Optional[Any]:
        """
        Get embedding for text, using cache if available.

        Args:
            text: Text to embed

        Returns:
            Numpy array of embeddings or None if unavailable
        """
        if not text or not self._ensure_model_loaded():
            return None

        cache_key = self._get_cache_key(text)

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)

            # Manage cache size
            if len(self._embedding_cache) >= self.EMBEDDING_CACHE_SIZE:
                # Remove oldest entries (simple FIFO)
                keys_to_remove = list(self._embedding_cache.keys())[:100]
                for key in keys_to_remove:
                    del self._embedding_cache[key]

            self._embedding_cache[cache_key] = embedding
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def _cosine_similarity(self, vec1: Any, vec2: Any) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score between 0 and 1
        """
        if vec1 is None or vec2 is None or np is None:
            return 0.0

        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            # Normalize to 0-1 range (cosine similarity is -1 to 1)
            return (similarity + 1) / 2

        except Exception as e:
            logger.error(f"Error computing cosine similarity: {e}")
            return 0.0

    def _parse_skills(self, skills_data: Any) -> List[str]:
        """
        Parse skills from various formats (JSON string, list, comma-separated).

        Args:
            skills_data: Skills in any supported format

        Returns:
            List of skill strings, normalized to lowercase
        """
        if not skills_data:
            return []

        if isinstance(skills_data, list):
            return [
                s.lower().strip()
                for s in skills_data
                if isinstance(s, str) and s.strip()
            ]

        if isinstance(skills_data, str):
            # Try JSON parse
            try:
                loaded = json.loads(skills_data)
                if isinstance(loaded, list):
                    return [
                        s.lower().strip()
                        for s in loaded
                        if isinstance(s, str) and s.strip()
                    ]
            except (json.JSONDecodeError, TypeError):
                pass

            # Try comma-separated
            if "," in skills_data:
                return [s.lower().strip() for s in skills_data.split(",") if s.strip()]

            # Single skill
            return [skills_data.lower().strip()] if skills_data.strip() else []

        return []

    def _compute_skill_match_score(
        self, user_skills: List[str], opportunity_skills: List[str]
    ) -> float:
        """
        Compute skill match score using exact and semantic matching.

        Scoring:
        - Exact match: 1.0 per matching skill
        - Semantic match (embedding similarity > 0.7): 0.5 per skill
        - Normalized by total required skills

        Args:
            user_skills: List of user's skills
            opportunity_skills: List of skills required by opportunity

        Returns:
            Score between 0 and 1
        """
        if not opportunity_skills:
            return 0.5  # Neutral score if no skills required

        if not user_skills:
            return 0.0

        user_skills_lower = [s.lower() for s in user_skills]
        opp_skills_lower = [s.lower() for s in opportunity_skills]

        total_score = 0.0
        max_possible = len(opp_skills_lower)

        for opp_skill in opp_skills_lower:
            # Check exact match
            if opp_skill in user_skills_lower:
                total_score += 1.0
                continue

            # Check semantic match if embeddings available
            if self._ensure_model_loaded():
                opp_embedding = self._get_embedding(opp_skill)
                best_semantic_score = 0.0

                for user_skill in user_skills_lower:
                    user_embedding = self._get_embedding(user_skill)
                    if opp_embedding is not None and user_embedding is not None:
                        similarity = self._cosine_similarity(
                            opp_embedding, user_embedding
                        )
                        best_semantic_score = max(best_semantic_score, similarity)

                # Award partial credit for semantic matches
                if best_semantic_score > 0.7:
                    total_score += 0.7 * best_semantic_score
                elif best_semantic_score > 0.5:
                    total_score += 0.3 * best_semantic_score

        return min(total_score / max_possible, 1.0)

    def _compute_bio_similarity_score(
        self, user_bio: str, opportunity_description: str
    ) -> float:
        """
        Compute semantic similarity between user bio and opportunity description.

        Uses sentence embeddings to capture semantic meaning beyond keywords.

        Args:
            user_bio: User's bio/description text
            opportunity_description: Opportunity's description

        Returns:
            Similarity score between 0 and 1
        """
        if not user_bio or not opportunity_description:
            return 0.0

        # Use embeddings if available
        if self._ensure_model_loaded():
            user_embedding = self._get_embedding(user_bio[:1000])  # Limit text length
            opp_embedding = self._get_embedding(opportunity_description[:1000])
            return self._cosine_similarity(user_embedding, opp_embedding)

        # Fallback: Simple keyword overlap
        return self._fallback_text_similarity(user_bio, opportunity_description)

    def _fallback_text_similarity(self, text1: str, text2: str) -> float:
        """
        Fallback text similarity using keyword overlap when embeddings unavailable.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Jaccard similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0

        # Simple word tokenization
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
        }

        words1 = words1 - stop_words
        words2 = words2 - stop_words

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _compute_tag_match_score(
        self,
        user_interests: List[str],
        opportunity_tags: List[str],
        opportunity_type: str = None,
    ) -> float:
        """
        Compute match score between user interests/preferences and opportunity tags.

        Args:
            user_interests: User's interests or preferences
            opportunity_tags: Opportunity's tags or categories
            opportunity_type: Type of opportunity (Internship, Volunteer, etc.)

        Returns:
            Score between 0 and 1
        """
        if not user_interests and not opportunity_tags:
            return 0.5  # Neutral

        if not user_interests:
            return 0.3  # Slight penalty for no user interests defined

        if not opportunity_tags:
            opportunity_tags = []

        # Include opportunity type as a tag
        if opportunity_type:
            opportunity_tags = opportunity_tags + [opportunity_type.lower()]

        user_interests_lower = [i.lower() for i in user_interests if i]
        opp_tags_lower = [t.lower() for t in opportunity_tags if t]

        if not opp_tags_lower:
            return 0.5

        matches = sum(1 for tag in opp_tags_lower if tag in user_interests_lower)

        # Use embeddings for semantic tag matching
        if self._ensure_model_loaded():
            for opp_tag in opp_tags_lower:
                if opp_tag not in user_interests_lower:
                    opp_embedding = self._get_embedding(opp_tag)
                    for user_interest in user_interests_lower:
                        user_embedding = self._get_embedding(user_interest)
                        if opp_embedding is not None and user_embedding is not None:
                            similarity = self._cosine_similarity(
                                opp_embedding, user_embedding
                            )
                            if similarity > 0.7:
                                matches += 0.5
                                break

        return min(matches / len(opp_tags_lower), 1.0)

    def _compute_recency_score(self, created_at: str) -> float:
        """
        Compute recency score with exponential decay.

        Newer opportunities get higher scores, with a half-life of RECENCY_HALF_LIFE_DAYS.

        Args:
            created_at: ISO format timestamp of opportunity creation

        Returns:
            Score between 0 and 1
        """
        if not created_at:
            return 0.5  # Unknown date gets neutral score

        try:
            # Parse ISO format date
            if isinstance(created_at, str):
                created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                created_date = created_at

            # Make comparison timezone-aware or naive consistently
            now = (
                datetime.now(created_date.tzinfo)
                if created_date.tzinfo
                else datetime.now()
            )

            days_old = (now - created_date).days

            # Exponential decay: score = 0.5^(days_old / half_life)
            decay_factor = 0.5 ** (days_old / self.RECENCY_HALF_LIFE_DAYS)

            return max(decay_factor, 0.1)  # Minimum 0.1 for very old items

        except Exception as e:
            logger.warning(f"Error computing recency score: {e}")
            return 0.5

    def _compute_interaction_score(
        self,
        opportunity_id: int,
        saved_ids: List[int] = None,
        viewed_ids: List[int] = None,
        applied_ids: List[int] = None,
        dismissed_ids: List[int] = None,
    ) -> float:
        """
        Compute score adjustment based on user's past interactions.

        Interactions affect scores as follows:
        - Saved: +0.3 boost
        - Recently viewed: +0.1 boost
        - Applied: -1.0 (exclude from results)
        - Dismissed: -0.5 penalty

        Args:
            opportunity_id: ID of the opportunity
            saved_ids: List of saved opportunity IDs
            viewed_ids: List of viewed opportunity IDs
            applied_ids: List of applied opportunity IDs
            dismissed_ids: List of dismissed opportunity IDs

        Returns:
            Score adjustment between -1.0 and 1.0
        """
        saved_ids = saved_ids or []
        viewed_ids = viewed_ids or []
        applied_ids = applied_ids or []
        dismissed_ids = dismissed_ids or []

        # Already applied - should be excluded
        if opportunity_id in applied_ids:
            return -1.0

        # Dismissed - significant penalty
        if opportunity_id in dismissed_ids:
            return -0.5

        score = 0.5  # Base neutral score

        # Saved - positive signal
        if opportunity_id in saved_ids:
            score += 0.3

        # Viewed - slight positive (shows interest)
        if opportunity_id in viewed_ids:
            score += 0.1

        return min(score, 1.0)

    def compute_relevance_score(
        self,
        user_profile: Dict[str, Any],
        opportunity: Dict[str, Any],
        saved_ids: List[int] = None,
        viewed_ids: List[int] = None,
        applied_ids: List[int] = None,
        dismissed_ids: List[int] = None,
    ) -> Dict[str, Any]:
        """
        Compute the overall relevance score for a user-opportunity pair.

        Returns both the total score and component breakdowns for transparency.

        Args:
            user_profile: User's profile data
            opportunity: Opportunity data
            saved_ids: List of saved opportunity IDs
            viewed_ids: List of viewed opportunity IDs
            applied_ids: List of applied opportunity IDs
            dismissed_ids: List of dismissed opportunity IDs

        Returns:
            Dictionary with:
                - total_score: Combined relevance score (0-1)
                - components: Individual component scores
                - should_exclude: Whether to exclude from results
        """
        opportunity_id = opportunity.get("id")

        # Check cache
        cache_key = f"{user_profile.get('id')}_{opportunity_id}"
        if cache_key in self._score_cache:
            cached_score, cached_time = self._score_cache[cache_key]
            if datetime.now() - cached_time < timedelta(
                minutes=self.SCORE_CACHE_TTL_MINUTES
            ):
                return cached_score

        # Extract user data
        user_skills = self._parse_skills(user_profile.get("skills", []))
        user_bio = user_profile.get("bio", "") or user_profile.get("description", "")

        # Extract user interests from bio keywords or skills
        user_interests = user_skills.copy()

        # Extract opportunity data
        opp_skills = self._parse_skills(opportunity.get("skills_needed", []))
        opp_description = opportunity.get("description", "")
        opp_type = opportunity.get("type", "")
        opp_category = opportunity.get("category", "")
        opp_tags = [opp_category] if opp_category else []
        created_at = opportunity.get("created_at", "")

        # Compute component scores
        skill_score = self._compute_skill_match_score(user_skills, opp_skills)
        bio_score = self._compute_bio_similarity_score(user_bio, opp_description)
        tag_score = self._compute_tag_match_score(user_interests, opp_tags, opp_type)
        recency_score = self._compute_recency_score(created_at)
        interaction_score = self._compute_interaction_score(
            opportunity_id, saved_ids, viewed_ids, applied_ids, dismissed_ids
        )

        # Check if should be excluded (applied or strongly dismissed)
        should_exclude = interaction_score <= -1.0

        if should_exclude:
            result = {
                "total_score": 0.0,
                "components": {
                    "skill_match": skill_score,
                    "bio_similarity": bio_score,
                    "tag_match": tag_score,
                    "recency": recency_score,
                    "interaction": interaction_score,
                },
                "should_exclude": True,
            }
        else:
            # Compute weighted total
            # Adjust interaction score to 0-1 range for weighting
            adjusted_interaction = max(0, min(1, interaction_score))

            total_score = (
                self.WEIGHT_SKILL_MATCH * skill_score
                + self.WEIGHT_BIO_SIMILARITY * bio_score
                + self.WEIGHT_TAG_MATCH * tag_score
                + self.WEIGHT_RECENCY * recency_score
                + self.WEIGHT_INTERACTIONS * adjusted_interaction
            )

            result = {
                "total_score": total_score,
                "components": {
                    "skill_match": skill_score,
                    "bio_similarity": bio_score,
                    "tag_match": tag_score,
                    "recency": recency_score,
                    "interaction": interaction_score,
                },
                "should_exclude": False,
            }

        # Cache the result
        self._score_cache[cache_key] = (result, datetime.now())

        return result

    def rank_opportunities(
        self,
        user_profile: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        saved_ids: List[int] = None,
        viewed_ids: List[int] = None,
        applied_ids: List[int] = None,
        dismissed_ids: List[int] = None,
        limit: Optional[int] = None,
        exclude_applied: bool = True,
        exclude_dismissed: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Rank opportunities by relevance for a specific user.

        Args:
            user_profile: User's profile data
            opportunities: List of opportunities to rank
            saved_ids: List of saved opportunity IDs
            viewed_ids: List of viewed opportunity IDs
            applied_ids: List of applied opportunity IDs
            dismissed_ids: List of dismissed opportunity IDs
            limit: Maximum number of results to return
            exclude_applied: Whether to exclude already applied opportunities
            exclude_dismissed: Whether to exclude dismissed opportunities

        Returns:
            Sorted list of opportunities with relevance scores
        """
        if not opportunities:
            return []

        if not user_profile:
            # No user profile - return opportunities sorted by recency
            return (
                sorted(
                    opportunities, key=lambda x: x.get("created_at", ""), reverse=True
                )[:limit]
                if limit
                else opportunities
            )

        scored_opportunities = []

        for opportunity in opportunities:
            score_result = self.compute_relevance_score(
                user_profile,
                opportunity,
                saved_ids,
                viewed_ids,
                applied_ids,
                dismissed_ids,
            )

            # Handle exclusions
            if score_result["should_exclude"]:
                if exclude_applied and opportunity.get("id") in (applied_ids or []):
                    continue
                if exclude_dismissed and opportunity.get("id") in (dismissed_ids or []):
                    continue

            # Add score to opportunity
            opportunity_with_score = opportunity.copy()
            opportunity_with_score["relevance_score"] = score_result["total_score"]
            opportunity_with_score["score_components"] = score_result["components"]

            scored_opportunities.append(opportunity_with_score)

        # Sort by relevance score (descending)
        sorted_opportunities = sorted(
            scored_opportunities,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True,
        )

        # Apply limit if specified
        if limit:
            sorted_opportunities = sorted_opportunities[:limit]

        return sorted_opportunities

    def get_suggested_opportunities(
        self,
        user_profile: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        saved_ids: List[int] = None,
        applied_ids: List[int] = None,
        dismissed_ids: List[int] = None,
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        """
        Get personalized opportunity suggestions for the dashboard.

        This is optimized for the "Suggested Opportunities" section:
        - Excludes applied opportunities
        - Limits results to top N
        - Prioritizes high-relevance matches

        Args:
            user_profile: User's profile data
            opportunities: All available opportunities
            saved_ids: List of saved opportunity IDs
            applied_ids: List of applied opportunity IDs
            dismissed_ids: List of dismissed opportunity IDs
            limit: Maximum suggestions to return

        Returns:
            Top N personalized opportunity suggestions
        """
        return self.rank_opportunities(
            user_profile=user_profile,
            opportunities=opportunities,
            saved_ids=saved_ids,
            applied_ids=applied_ids,
            dismissed_ids=dismissed_ids,
            limit=limit,
            exclude_applied=True,
            exclude_dismissed=True,
        )

    def clear_cache(self):
        """Clear all cached embeddings and scores."""
        self._embedding_cache.clear()
        self._score_cache.clear()
        logger.info("Relevance service cache cleared")

    def precompute_embeddings(self, texts: List[str]):
        """
        Precompute and cache embeddings for a list of texts.

        Useful for batch processing opportunities or user profiles.

        Args:
            texts: List of texts to embed
        """
        if not self._ensure_model_loaded():
            return

        for text in texts:
            if text:
                self._get_embedding(text[:1000])

        logger.info(f"Precomputed embeddings for {len(texts)} texts")


# Singleton instance for use across the application
_relevance_service_instance: Optional[RelevanceService] = None


def get_relevance_service() -> RelevanceService:
    """
    Get the singleton relevance service instance.

    Returns:
        RelevanceService instance
    """
    global _relevance_service_instance

    if _relevance_service_instance is None:
        _relevance_service_instance = RelevanceService()

    return _relevance_service_instance

"""
Relevance Service for InterSpark - Lightweight Vercel-Compatible Ranking

This module provides TF-IDF + FAISS-based relevance ranking for opportunities and people.
Uses lightweight embeddings that are Vercel deployment-safe.

Scoring Components:
1. Skill overlap (exact + TF-IDF semantic matching)
2. Bio/description similarity using TF-IDF vectors
3. Interest/tag matching
4. Recency and interaction signal boosts (for opportunities)
5. Experience compatibility (for people)
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from functools import lru_cache
import os
import re

logger = logging.getLogger(__name__)

# Import lightweight ML libraries
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    EMBEDDINGS_AVAILABLE = True
    logger.info("TF-IDF vectorization loaded successfully")
except ImportError as e:
    EMBEDDINGS_AVAILABLE = False
    logger.warning(f"TF-IDF not available: {e}. Using fallback methods.")
    np = None


class RelevanceService:
    """
    Lightweight relevance scoring using TF-IDF.

    Scoring Weights:
    - Skill Match (40%): Exact and TF-IDF semantic skill overlap
    - Bio Similarity (25%): TF-IDF cosine similarity
    - Interest/Tag Match (15%): Category and tag alignment
    - Recency (10%): Newer opportunities get boost
    - Interactions (10%): User interaction signals
    """

    # Scoring weights
    WEIGHT_SKILL_MATCH = 0.40
    WEIGHT_BIO_SIMILARITY = 0.25
    WEIGHT_TAG_MATCH = 0.15
    WEIGHT_RECENCY = 0.10
    WEIGHT_INTERACTIONS = 0.10

    # Cache settings
    CACHE_SIZE = 1000
    SCORE_CACHE_TTL_MINUTES = 30
    RECENCY_HALF_LIFE_DAYS = 14

    def __init__(self):
        """Initialize the relevance service with TF-IDF vectorizers."""
        self._text_vectorizer = None
        self._skill_vectorizer = None
        self._embedding_cache: Dict[str, Any] = {}
        self._score_cache: Dict[str, Tuple[float, datetime]] = {}

        if EMBEDDINGS_AVAILABLE:
            # Initialize TF-IDF vectorizers
            self._text_vectorizer = TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                stop_words="english",
                lowercase=True,
                min_df=1,
            )
            self._skill_vectorizer = TfidfVectorizer(
                max_features=200, ngram_range=(1, 2), lowercase=True, min_df=1
            )
            logger.info("TF-IDF vectorizers initialized")

    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text for vectorization."""
        if not text:
            return ""
        # Remove special characters, keep alphanumeric and spaces
        text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)
        return text.strip().lower()

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()

    def _compute_tfidf_similarity(self, text1: str, text2: str) -> float:
        """
        Compute TF-IDF cosine similarity between two texts.

        IMPORTANT: We fit_transform BOTH texts together to ensure consistent vocabulary.
        This fixes the dimension mismatch issue.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2 or not EMBEDDINGS_AVAILABLE:
            return 0.0

        try:
            # Preprocess both texts
            processed1 = self._preprocess_text(text1)
            processed2 = self._preprocess_text(text2)

            if not processed1 or not processed2:
                return 0.0

            # Create a fresh vectorizer and fit on BOTH texts together
            # This ensures consistent vocabulary and vector dimensions
            vectorizer = TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                stop_words="english",
                lowercase=True,
                min_df=1,
            )

            # Fit and transform both texts together
            tfidf_matrix = vectorizer.fit_transform([processed1, processed2])

            # Compute cosine similarity between the two vectors
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(max(0.0, min(1.0, similarity)))

        except Exception as e:
            logger.warning(f"Error computing TF-IDF similarity: {e}")
            return self._fallback_text_similarity(text1, text2)

    def _parse_skills(self, skills_data: Any) -> List[str]:
        """Parse skills from various formats."""
        if not skills_data:
            return []

        if isinstance(skills_data, list):
            return [
                s.lower().strip()
                for s in skills_data
                if isinstance(s, str) and s.strip()
            ]

        if isinstance(skills_data, str):
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

            if "," in skills_data:
                return [s.lower().strip() for s in skills_data.split(",") if s.strip()]

            return [skills_data.lower().strip()] if skills_data.strip() else []

        return []

    def _compute_skill_match_score(
        self, user_skills: List[str], target_skills: List[str]
    ) -> float:
        """
        Compute skill match using exact matches + partial matches + TF-IDF similarity.

        Enhanced algorithm:
        - Exact matches (full word match)
        - Partial matches (substring or related terms)
        - TF-IDF semantic similarity for remaining skills

        Args:
            user_skills: User's skills
            target_skills: Target skills (opportunity or person)

        Returns:
            Score between 0 and 1
        """
        if not target_skills:
            return 0.5  # Neutral if no skills required

        if not user_skills:
            return 0.0

        user_skills_lower = [s.lower() for s in user_skills]
        target_skills_lower = [s.lower() for s in target_skills]

        # Track matches
        matched_targets = set()

        # 1. Exact match check
        for i, skill in enumerate(target_skills_lower):
            if skill in user_skills_lower:
                matched_targets.add(i)

        # 2. Partial/substring match for unmatched skills
        # e.g., "javascript" matches "javascript development" or "react js"
        for i, target_skill in enumerate(target_skills_lower):
            if i in matched_targets:
                continue
            for user_skill in user_skills_lower:
                # Check if either is a substring of the other
                if target_skill in user_skill or user_skill in target_skill:
                    matched_targets.add(i)
                    break
                # Check word overlap (e.g., "machine learning" matches "ml")
                target_words = set(target_skill.split())
                user_words = set(user_skill.split())
                if target_words.intersection(user_words):
                    matched_targets.add(i)
                    break

        # Calculate direct match score
        direct_match_score = len(matched_targets) / len(target_skills_lower)

        # 3. TF-IDF semantic similarity for any remaining unmatched skills
        semantic_score = 0.0
        if EMBEDDINGS_AVAILABLE and direct_match_score < 1.0:
            try:
                # Combine skills into text for TF-IDF
                user_text = " ".join(user_skills_lower)
                target_text = " ".join(target_skills_lower)

                # Use corrected TF-IDF similarity
                semantic_score = self._compute_tfidf_similarity(user_text, target_text)
            except Exception as e:
                logger.warning(f"Error in skill semantic matching: {e}")

        # Combine: 70% direct matches (exact + partial), 30% semantic similarity
        final_score = 0.7 * direct_match_score + 0.3 * semantic_score
        return min(final_score, 1.0)

    def _compute_bio_similarity_score(self, user_bio: str, target_bio: str) -> float:
        """
        Compute TF-IDF similarity between bios.

        Args:
            user_bio: User's bio
            target_bio: Target bio

        Returns:
            Similarity score 0-1
        """
        if not user_bio or not target_bio:
            return 0.0

        if EMBEDDINGS_AVAILABLE:
            # Use the corrected method that ensures same dimensions
            return self._compute_tfidf_similarity(user_bio[:1000], target_bio[:1000])

        # Fallback: keyword overlap
        return self._fallback_text_similarity(user_bio, target_bio)

    def _fallback_text_similarity(self, text1: str, text2: str) -> float:
        """Jaccard similarity as fallback."""
        if not text1 or not text2:
            return 0.0

        words1 = set(self._preprocess_text(text1).split())
        words2 = set(self._preprocess_text(text2).split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _compute_tag_match_score(
        self,
        user_interests: List[str],
        target_tags: List[str],
        target_type: str = None,
    ) -> float:
        """Compute interest/tag match score."""
        if not user_interests and not target_tags:
            return 0.5

        if not user_interests:
            return 0.3

        if not target_tags:
            target_tags = []

        if target_type:
            target_tags = target_tags + [target_type.lower()]

        user_interests_lower = [i.lower() for i in user_interests if i]
        target_tags_lower = [t.lower() for t in target_tags if t]

        if not target_tags_lower:
            return 0.5

        matches = sum(1 for tag in target_tags_lower if tag in user_interests_lower)

        # Add TF-IDF semantic matching for remaining unmatched tags
        if EMBEDDINGS_AVAILABLE and matches < len(target_tags_lower):
            try:
                user_text = " ".join(user_interests_lower)
                target_text = " ".join(target_tags_lower)

                # Use corrected TF-IDF similarity
                semantic_sim = self._compute_tfidf_similarity(user_text, target_text)
                matches += semantic_sim * (len(target_tags_lower) - matches)
            except Exception:
                pass

        return min(matches / len(target_tags_lower), 1.0)

    def _compute_recency_score(self, created_at: str) -> float:
        """Compute recency score with exponential decay."""
        if not created_at:
            return 0.5

        try:
            if isinstance(created_at, str):
                created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                created_date = created_at

            now = (
                datetime.now(created_date.tzinfo)
                if created_date.tzinfo
                else datetime.now()
            )
            days_old = (now - created_date).days

            decay_factor = 0.5 ** (days_old / self.RECENCY_HALF_LIFE_DAYS)
            return max(decay_factor, 0.1)

        except Exception as e:
            logger.warning(f"Error computing recency: {e}")
            return 0.5

    def _compute_interaction_score(
        self,
        item_id: int,
        saved_ids: List[int] = None,
        viewed_ids: List[int] = None,
        applied_ids: List[int] = None,
        dismissed_ids: List[int] = None,
    ) -> float:
        """Compute interaction-based score adjustment."""
        saved_ids = saved_ids or []
        viewed_ids = viewed_ids or []
        applied_ids = applied_ids or []
        dismissed_ids = dismissed_ids or []

        if item_id in applied_ids:
            return -1.0

        if item_id in dismissed_ids:
            return -0.5

        score = 0.5

        if item_id in saved_ids:
            score += 0.3

        if item_id in viewed_ids:
            score += 0.1

        return min(score, 1.0)

    # ========================================================================
    # OPPORTUNITY RANKING
    # ========================================================================

    def compute_relevance_score(
        self,
        user_profile: Dict[str, Any],
        opportunity: Dict[str, Any],
        saved_ids: List[int] = None,
        viewed_ids: List[int] = None,
        applied_ids: List[int] = None,
        dismissed_ids: List[int] = None,
    ) -> Dict[str, Any]:
        """Compute relevance score for user-opportunity pair."""
        opportunity_id = opportunity.get("id")

        # Check cache
        cache_key = f"{user_profile.get('id')}_{opportunity_id}"
        if cache_key in self._score_cache:
            cached_score, cached_time = self._score_cache[cache_key]
            if datetime.now() - cached_time < timedelta(
                minutes=self.SCORE_CACHE_TTL_MINUTES
            ):
                return cached_score

        # Extract data
        user_skills = self._parse_skills(user_profile.get("skills", []))
        user_bio = user_profile.get("bio", "") or user_profile.get("description", "")
        user_interests = user_skills.copy()

        opp_skills = self._parse_skills(opportunity.get("skills_needed", []))
        opp_description = opportunity.get("description", "")
        opp_type = opportunity.get("type", "")
        opp_category = opportunity.get("category", "")
        opp_tags = [opp_category] if opp_category else []
        created_at = opportunity.get("created_at", "")

        # Compute components
        skill_score = self._compute_skill_match_score(user_skills, opp_skills)
        bio_score = self._compute_bio_similarity_score(user_bio, opp_description)
        tag_score = self._compute_tag_match_score(user_interests, opp_tags, opp_type)
        recency_score = self._compute_recency_score(created_at)
        interaction_score = self._compute_interaction_score(
            opportunity_id, saved_ids, viewed_ids, applied_ids, dismissed_ids
        )

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

        # Cache result
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
        """Rank opportunities by relevance."""
        if not opportunities:
            return []

        if not user_profile:
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

            if score_result["should_exclude"]:
                if exclude_applied and opportunity.get("id") in (applied_ids or []):
                    continue
                if exclude_dismissed and opportunity.get("id") in (dismissed_ids or []):
                    continue

            opportunity_with_score = opportunity.copy()
            opportunity_with_score["relevance_score"] = score_result["total_score"]
            opportunity_with_score["score_components"] = score_result["components"]

            scored_opportunities.append(opportunity_with_score)

        sorted_opportunities = sorted(
            scored_opportunities,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True,
        )

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
        """Get personalized opportunity suggestions for dashboard."""
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

    # ========================================================================
    # PEOPLE/TALENT RANKING
    # ========================================================================

    def _compute_skill_overlap_score(
        self, viewer_skills: List[str], candidate_skills: List[str]
    ) -> float:
        """Compute skill overlap and complementarity for people matching."""
        if not candidate_skills:
            return 0.3

        if not viewer_skills:
            return 0.5

        viewer_skills_lower = [s.lower() for s in viewer_skills]
        candidate_skills_lower = [s.lower() for s in candidate_skills]

        # Overlap score
        overlap_count = len(
            set(viewer_skills_lower).intersection(set(candidate_skills_lower))
        )
        overlap_score = min(overlap_count / max(len(viewer_skills_lower), 1), 1.0)

        # Complementarity via TF-IDF
        complementary_score = 0.0
        if EMBEDDINGS_AVAILABLE:
            try:
                viewer_text = " ".join(viewer_skills_lower)
                candidate_text = " ".join(candidate_skills_lower)

                # Use corrected TF-IDF similarity
                sim = self._compute_tfidf_similarity(viewer_text, candidate_text)
                # Related but not identical skills score in 0.4-0.7 range
                if 0.3 < sim < 0.8:
                    complementary_score = sim * 0.5
            except Exception:
                pass

        # 60% overlap, 40% complementarity
        return 0.6 * overlap_score + 0.4 * complementary_score

    def _compute_bio_similarity_people(
        self, viewer_bio: str, candidate_bio: str
    ) -> float:
        """Compute bio similarity for people matching."""
        if not viewer_bio or not candidate_bio:
            return 0.3

        if EMBEDDINGS_AVAILABLE:
            # Use corrected TF-IDF similarity
            return self._compute_tfidf_similarity(
                viewer_bio[:1000], candidate_bio[:1000]
            )

        return self._fallback_text_similarity(viewer_bio, candidate_bio)

    def _compute_interest_overlap_score(
        self, viewer_interests: List[str], candidate_interests: List[str]
    ) -> float:
        """Compute interest overlap for people matching."""
        if not viewer_interests and not candidate_interests:
            return 0.5

        if not viewer_interests or not candidate_interests:
            return 0.3

        viewer_lower = [i.lower() for i in viewer_interests if i]
        candidate_lower = [i.lower() for i in candidate_interests if i]

        overlap = len(set(viewer_lower).intersection(set(candidate_lower)))
        overlap_score = min(overlap / max(len(viewer_lower), 1), 1.0)

        # TF-IDF semantic matching
        if EMBEDDINGS_AVAILABLE:
            try:
                viewer_text = " ".join(viewer_lower)
                candidate_text = " ".join(candidate_lower)

                # Use corrected TF-IDF similarity
                semantic_score = self._compute_tfidf_similarity(
                    viewer_text, candidate_text
                )
                return 0.7 * overlap_score + 0.3 * semantic_score
            except Exception:
                pass

        return overlap_score

    def _compute_experience_compatibility_score(
        self, viewer_profile: Dict[str, Any], candidate_profile: Dict[str, Any]
    ) -> float:
        """Compute experience compatibility for people matching."""
        score = 0.5

        viewer_grade = viewer_profile.get("grade", "")
        candidate_grade = candidate_profile.get("grade", "")

        if viewer_grade and candidate_grade:
            try:
                viewer_year = int("".join(filter(str.isdigit, str(viewer_grade))))
                candidate_year = int("".join(filter(str.isdigit, str(candidate_grade))))

                year_diff = abs(viewer_year - candidate_year)
                if year_diff == 0:
                    score += 0.3
                elif year_diff == 1:
                    score += 0.2
                elif year_diff == 2:
                    score += 0.1
            except (ValueError, TypeError):
                pass

        viewer_school = viewer_profile.get("school", "")
        candidate_school = candidate_profile.get("school", "")

        if viewer_school and candidate_school:
            if viewer_school.lower() == candidate_school.lower():
                score += 0.2

        return min(score, 1.0)

    def _parse_profile_interests(self, profile: Dict[str, Any]) -> List[str]:
        """Extract interests from profile."""
        interests = []

        skills = self._parse_skills(profile.get("skills", []))
        interests.extend(skills)

        if "interests" in profile:
            profile_interests = profile["interests"]
            if isinstance(profile_interests, list):
                interests.extend(profile_interests)
            elif isinstance(profile_interests, str):
                interests.extend(
                    [i.strip() for i in profile_interests.split(",") if i.strip()]
                )

        return interests

    def compute_people_relevance_score(
        self,
        viewer_profile: Dict[str, Any],
        candidate_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute relevance between two users."""
        if viewer_profile.get("id") == candidate_profile.get("id"):
            return {"total_score": 0.0, "components": {}, "should_exclude": True}

        viewer_skills = self._parse_skills(viewer_profile.get("skills", []))
        viewer_bio = viewer_profile.get("bio", "") or viewer_profile.get(
            "description", ""
        )
        viewer_interests = self._parse_profile_interests(viewer_profile)

        candidate_skills = self._parse_skills(candidate_profile.get("skills", []))
        candidate_bio = candidate_profile.get("bio", "") or candidate_profile.get(
            "description", ""
        )
        candidate_interests = self._parse_profile_interests(candidate_profile)

        skill_score = self._compute_skill_overlap_score(viewer_skills, candidate_skills)
        bio_score = self._compute_bio_similarity_people(viewer_bio, candidate_bio)
        interest_score = self._compute_interest_overlap_score(
            viewer_interests, candidate_interests
        )
        experience_score = self._compute_experience_compatibility_score(
            viewer_profile, candidate_profile
        )

        total_score = (
            0.35 * skill_score
            + 0.30 * bio_score
            + 0.20 * interest_score
            + 0.15 * experience_score
        )

        return {
            "total_score": total_score,
            "components": {
                "skill_overlap": skill_score,
                "bio_similarity": bio_score,
                "interest_overlap": interest_score,
                "experience_compatibility": experience_score,
            },
            "should_exclude": False,
        }

    def rank_people(
        self,
        viewer_profile: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Rank people by relevance."""
        if not candidates:
            return []

        if not viewer_profile:
            return candidates[:limit] if limit else candidates

        scored_candidates = []

        for candidate in candidates:
            score_result = self.compute_people_relevance_score(
                viewer_profile, candidate
            )

            if score_result["should_exclude"]:
                continue

            candidate_with_score = candidate.copy()
            candidate_with_score["relevance_score"] = score_result["total_score"]
            candidate_with_score["score_components"] = score_result["components"]

            scored_candidates.append(candidate_with_score)

        sorted_candidates = sorted(
            scored_candidates,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True,
        )

        if limit:
            sorted_candidates = sorted_candidates[:limit]

        return sorted_candidates

    def clear_cache(self):
        """Clear all caches."""
        self._embedding_cache.clear()
        self._score_cache.clear()
        logger.info("Relevance service cache cleared")

    def precompute_embeddings(self, texts: List[str]):
        """
        Precompute step is no longer needed with TF-IDF.
        Each similarity is computed fresh with its own vocabulary.
        This method is kept for backwards compatibility.
        """
        if not EMBEDDINGS_AVAILABLE:
            return

        # TF-IDF doesn't benefit from precomputation since we fit
        # a new vectorizer for each pair comparison
        logger.info(
            f"Precompute skipped - TF-IDF computes on-demand for {len(texts)} texts"
        )


# Singleton instance
_relevance_service_instance: Optional[RelevanceService] = None


def get_relevance_service() -> RelevanceService:
    """Get the singleton relevance service instance."""
    global _relevance_service_instance

    if _relevance_service_instance is None:
        _relevance_service_instance = RelevanceService()

    return _relevance_service_instance

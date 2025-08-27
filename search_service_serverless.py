"""
Serverless-compatible search service for InterSpark application.
Uses in-memory search with JSON-based data storage for Vercel deployment.
"""

import json
import os
import re
from typing import Dict, List, Any, Optional, Union
import logging
from dataclasses import dataclass, asdict
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class SearchableProfile:
    """Data class for searchable student profiles."""

    id: str
    name: str
    bio: str
    skills: str
    school: str
    grade: str
    email: str
    location: str
    github_url: str
    linkedin_url: str
    portfolio_url: str
    interests: str
    phone: str
    user_type: str
    created_at: str
    updated_at: str

    # Computed search fields
    _search_text: str = ""
    _skills_list: List[str] = None
    _interests_list: List[str] = None

    def __post_init__(self):
        """Prepare search fields after initialization."""
        self._skills_list = self._parse_comma_separated(self.skills)
        self._interests_list = self._parse_comma_separated(self.interests)

        # Create combined search text
        search_parts = [
            self.name,
            self.bio,
            self.skills,
            self.school,
            self.location,
            self.interests,
            self.grade,
        ]
        self._search_text = " ".join(filter(None, search_parts)).lower()

    @staticmethod
    def _parse_comma_separated(text: str) -> List[str]:
        """Parse comma-separated text into a list."""
        if not text:
            return []
        return [
            item.strip().lower() for item in re.split(r"[,;|\n]+", text) if item.strip()
        ]


class ServerlessSearchService:
    """In-memory search service optimized for serverless environments."""

    def __init__(self, profiles_file: str = "search_profiles.json"):
        """
        Initialize the serverless search service.

        Args:
            profiles_file: JSON file containing indexed profiles
        """
        self.profiles_file = profiles_file
        self.profiles: List[SearchableProfile] = []
        self.last_loaded = None
        self._load_profiles()

    def _load_profiles(self):
        """Load profiles from JSON file."""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, "r") as f:
                    data = json.load(f)

                self.profiles = []
                for profile_data in data.get("profiles", []):
                    profile = SearchableProfile(**profile_data)
                    self.profiles.append(profile)

                self.last_loaded = datetime.now()
                logger.info(
                    f"Loaded {len(self.profiles)} profiles from {self.profiles_file}"
                )
            else:
                logger.warning(
                    f"Profiles file {self.profiles_file} not found, using fallback"
                )
                # Try to use fallback data
                try:
                    from search_profiles_fallback import FALLBACK_PROFILES

                    data = FALLBACK_PROFILES

                    self.profiles = []
                    for profile_data in data.get("profiles", []):
                        profile = SearchableProfile(**profile_data)
                        self.profiles.append(profile)

                    logger.info(
                        f"Loaded {len(self.profiles)} profiles from fallback data"
                    )
                except ImportError:
                    logger.warning("No fallback profiles available")
                    self.profiles = []

        except Exception as e:
            logger.error(f"Error loading profiles: {e}")
            self.profiles = []

    def _save_profiles(self):
        """Save profiles to JSON file."""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "profiles": [
                    {
                        k: v
                        for k, v in asdict(profile).items()
                        if not k.startswith("_")
                    }  # Exclude computed fields
                    for profile in self.profiles
                ],
            }

            with open(self.profiles_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self.profiles)} profiles to {self.profiles_file}")

        except Exception as e:
            logger.error(f"Error saving profiles: {e}")

    def build_index_from_db(self, supabase_service) -> bool:
        """
        Build the search index from database data.
        This should be run during build time or manually.

        Args:
            supabase_service: Supabase service instance

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all student profiles from database
            profiles_data = supabase_service.search_students()

            if not profiles_data:
                logger.warning("No student profiles found in database")
                return False

            self.profiles = []

            for profile_data in profiles_data:
                if profile_data.get("user_type") == "student":
                    # Convert to SearchableProfile
                    profile = SearchableProfile(
                        id=str(profile_data.get("id", "")),
                        name=profile_data.get("name", ""),
                        bio=profile_data.get("bio", ""),
                        skills=profile_data.get("skills", ""),
                        school=profile_data.get("school", ""),
                        grade=profile_data.get("grade", ""),
                        email=profile_data.get("email", ""),
                        location=profile_data.get("location", ""),
                        github_url=profile_data.get("github_url", ""),
                        linkedin_url=profile_data.get("linkedin_url", ""),
                        portfolio_url=profile_data.get("portfolio_url", ""),
                        interests=profile_data.get("interests", ""),
                        phone=profile_data.get("phone", ""),
                        user_type=profile_data.get("user_type", "student"),
                        created_at=str(profile_data.get("created_at", "")),
                        updated_at=str(profile_data.get("updated_at", "")),
                    )
                    self.profiles.append(profile)

            # Save to file
            self._save_profiles()

            logger.info(
                f"Built search index with {len(self.profiles)} student profiles"
            )
            return True

        except Exception as e:
            logger.error(f"Error building index from database: {e}")
            return False

    def search_students(
        self,
        search_query: str = "",
        skills: str = "",
        school: str = "",
        grade: str = "",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search for student profiles using in-memory search.

        Args:
            search_query: General text search across all fields
            skills: Specific skills to search for
            school: School name to filter by
            grade: Grade level to filter by
            limit: Maximum number of results to return

        Returns:
            List of matching student profile data with search scores
        """
        try:
            # Reload profiles if needed (for development)
            if not self.profiles:
                self._load_profiles()

            results = []

            # Prepare search terms
            search_terms = (
                self._parse_search_query(search_query) if search_query else []
            )
            skills_terms = self._parse_comma_separated(skills) if skills else []
            school_term = school.lower().strip() if school else ""
            grade_term = grade.lower().strip() if grade else ""

            for profile in self.profiles:
                score = 0.0
                matches = True

                # General text search
                if search_terms:
                    text_score = self._calculate_text_score(
                        profile._search_text, search_terms
                    )
                    if text_score > 0:
                        score += text_score * 1.0  # Base weight
                    else:
                        matches = False

                # Skills matching
                if skills_terms and matches:
                    skills_score = self._calculate_skills_score(
                        profile._skills_list, skills_terms
                    )
                    if skills_score > 0:
                        score += skills_score * 2.0  # Higher weight for skills
                    elif skills_terms:  # If skills were specified but no match
                        matches = False

                # School filtering
                if school_term and matches:
                    if school_term in profile.school.lower():
                        score += 1.5  # Bonus for school match
                    else:
                        matches = False

                # Grade filtering
                if grade_term and matches:
                    if grade_term == profile.grade.lower():
                        score += 1.0  # Bonus for exact grade match
                    else:
                        matches = False

                # If no specific criteria, include all profiles
                if not any([search_terms, skills_terms, school_term, grade_term]):
                    matches = True
                    score = 1.0

                if matches:
                    # Convert profile to dict and add score
                    profile_dict = {
                        "id": profile.id,
                        "name": profile.name,
                        "bio": profile.bio,
                        "skills": profile.skills,
                        "school": profile.school,
                        "grade": profile.grade,
                        "email": profile.email,
                        "location": profile.location,
                        "github_url": profile.github_url,
                        "linkedin_url": profile.linkedin_url,
                        "portfolio_url": profile.portfolio_url,
                        "interests": profile.interests,
                        "phone": profile.phone,
                        "user_type": profile.user_type,
                        "created_at": profile.created_at,
                        "updated_at": profile.updated_at,
                        "search_score": score,
                    }
                    results.append(profile_dict)

            # Sort by score (descending) and limit results
            results.sort(key=lambda x: x["search_score"], reverse=True)
            results = results[:limit]

            logger.info(f"Search completed: {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error searching students: {e}")
            return []

    def _parse_search_query(self, query: str) -> List[str]:
        """
        Parse search query into individual terms.
        Handles quoted phrases, AND/OR operators.
        """
        if not query:
            return []

        terms = []
        query = query.lower()

        # Find quoted phrases
        import re

        quoted_phrases = re.findall(r'"([^"]+)"', query)
        for phrase in quoted_phrases:
            terms.append(phrase.strip())
            query = query.replace(f'"{phrase}"', "")

        # Split remaining terms by common separators
        remaining_terms = re.split(r"[\s,;|]+", query)
        for term in remaining_terms:
            term = term.strip()
            if term and term not in ["and", "or", "&", "|"]:
                terms.append(term)

        return terms

    def _parse_comma_separated(self, text: str) -> List[str]:
        """Parse comma-separated text into list of terms."""
        if not text:
            return []
        return [
            item.strip().lower() for item in re.split(r"[,;|\n]+", text) if item.strip()
        ]

    def _calculate_text_score(self, search_text: str, search_terms: List[str]) -> float:
        """Calculate relevance score for text search."""
        if not search_terms:
            return 0.0

        score = 0.0
        for term in search_terms:
            if term in search_text:
                # Bonus for exact matches
                score += search_text.count(term)

                # Additional bonus if it's a complete word
                if f" {term} " in f" {search_text} ":
                    score += 0.5

        return min(score, 10.0)  # Cap the score

    def _calculate_skills_score(
        self, profile_skills: List[str], search_skills: List[str]
    ) -> float:
        """Calculate relevance score for skills matching."""
        if not search_skills or not profile_skills:
            return 0.0

        score = 0.0
        for search_skill in search_skills:
            for profile_skill in profile_skills:
                if search_skill in profile_skill or profile_skill in search_skill:
                    score += 1.0
                    # Bonus for exact match
                    if search_skill == profile_skill:
                        score += 0.5

        return min(score, 10.0)  # Cap the score

    def update_profile(self, profile_data: Dict[str, Any]) -> bool:
        """
        Update or add a profile to the search index.
        Note: In serverless environments, this won't persist between deployments.
        """
        try:
            if profile_data.get("user_type") != "student":
                return False

            profile_id = str(profile_data.get("id"))

            # Remove existing profile if it exists
            self.profiles = [p for p in self.profiles if p.id != profile_id]

            # Add new profile
            profile = SearchableProfile(
                id=profile_id,
                name=profile_data.get("name", ""),
                bio=profile_data.get("bio", ""),
                skills=profile_data.get("skills", ""),
                school=profile_data.get("school", ""),
                grade=profile_data.get("grade", ""),
                email=profile_data.get("email", ""),
                location=profile_data.get("location", ""),
                github_url=profile_data.get("github_url", ""),
                linkedin_url=profile_data.get("linkedin_url", ""),
                portfolio_url=profile_data.get("portfolio_url", ""),
                interests=profile_data.get("interests", ""),
                phone=profile_data.get("phone", ""),
                user_type=profile_data.get("user_type", "student"),
                created_at=str(profile_data.get("created_at", "")),
                updated_at=str(profile_data.get("updated_at", "")),
            )

            self.profiles.append(profile)
            logger.info(f"Updated profile in search index: {profile_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating profile in search index: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get search service statistics."""
        return {
            "total_profiles": len(self.profiles),
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "profiles_file": self.profiles_file,
            "file_exists": os.path.exists(self.profiles_file),
        }


# Global serverless search service instance
serverless_search_service = ServerlessSearchService()

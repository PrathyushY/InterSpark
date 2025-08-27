"""
Whoosh-based search service for InterSpark application.
Handles full-text search indexing and querying for student profiles.
"""

import os
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, KEYWORD, STORED
from whoosh.qparser import MultifieldParser, QueryParser
from whoosh.query import And, Or, Term, Wildcard
from whoosh import analysis
from whoosh.analysis import StandardAnalyzer, StemmingAnalyzer, Filter
from whoosh.writing import CLEAR
from typing import Dict, List, Any, Optional
import logging
import re

# Set up logging
logger = logging.getLogger(__name__)


class SearchService:
    """Service class for Whoosh-based search operations."""

    def __init__(self, index_dir: str = "search_index"):
        """
        Initialize the search service.

        Args:
            index_dir: Directory to store the search index
        """
        self.index_dir = index_dir
        self.schema = self._create_schema()
        self.ix = None
        self._ensure_index_exists()

    def _create_schema(self) -> Schema:
        """
        Create the Whoosh schema for student profiles.

        Returns:
            Schema object defining the searchable fields
        """
        # Use a stemming analyzer for better text matching
        text_analyzer = StemmingAnalyzer()

        # Create schema with all the fields we want to search
        schema = Schema(
            # Primary identifier
            id=ID(stored=True, unique=True),
            # Main searchable text fields
            name=TEXT(stored=True, analyzer=text_analyzer, field_boost=2.0),
            bio=TEXT(stored=True, analyzer=text_analyzer),
            # Skills with both keyword and text indexing for different search types
            skills=TEXT(stored=True, analyzer=text_analyzer, field_boost=1.5),
            skills_keyword=KEYWORD(stored=True, lowercase=True, commas=True),
            # Educational information
            school=TEXT(stored=True, analyzer=text_analyzer, field_boost=1.5),
            school_keyword=KEYWORD(stored=True, lowercase=True),
            grade=KEYWORD(stored=True, lowercase=True),
            # Contact and additional info
            email=STORED(),  # Not searchable for privacy
            location=TEXT(stored=True, analyzer=text_analyzer),
            location_keyword=KEYWORD(stored=True, lowercase=True),
            # Social links and interests
            github_url=STORED(),
            linkedin_url=STORED(),
            portfolio_url=STORED(),
            interests=TEXT(stored=True, analyzer=text_analyzer),
            interests_keyword=KEYWORD(stored=True, lowercase=True, commas=True),
            # Additional stored fields
            phone=STORED(),
            user_type=KEYWORD(stored=True),
            created_at=STORED(),
            updated_at=STORED(),
        )

        return schema

    def _ensure_index_exists(self):
        """Ensure the search index directory and index exist."""
        try:
            if not os.path.exists(self.index_dir):
                os.makedirs(self.index_dir)
                logger.info(f"Created search index directory: {self.index_dir}")

            if index.exists_in(self.index_dir):
                self.ix = index.open_dir(self.index_dir)
                logger.info("Opened existing search index")
            else:
                self.ix = index.create_in(self.index_dir, self.schema)
                logger.info("Created new search index")
        except Exception as e:
            logger.error(f"Error setting up search index: {e}")
            raise

    def _clean_text(self, text: str) -> str:
        """
        Clean and prepare text for indexing.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace and normalize
        text = re.sub(r"\s+", " ", text.strip())
        return text

    def _prepare_skills_list(self, skills: str) -> str:
        """
        Prepare skills string for keyword indexing.

        Args:
            skills: Comma or space separated skills string

        Returns:
            Cleaned, comma-separated skills string
        """
        if not skills:
            return ""

        # Split on common separators and clean each skill
        skills_list = re.split(r"[,;|\n]+", skills)
        cleaned_skills = []

        for skill in skills_list:
            skill = skill.strip().lower()
            if skill and len(skill) > 1:  # Ignore very short terms
                cleaned_skills.append(skill)

        return ", ".join(cleaned_skills)

    def index_student_profile(self, profile: Dict[str, Any]) -> bool:
        """
        Index or update a student profile in the search index.

        Args:
            profile: Student profile data

        Returns:
            True if successful, False otherwise
        """
        try:
            if not profile.get("user_type") == "student":
                logger.warning(
                    f"Attempted to index non-student profile: {profile.get('id')}"
                )
                return False

            writer = self.ix.writer()

            # Prepare the document data
            doc_data = {
                "id": str(profile.get("id", "")),
                "name": self._clean_text(profile.get("name", "")),
                "bio": self._clean_text(profile.get("bio", "")),
                "skills": self._clean_text(profile.get("skills", "")),
                "skills_keyword": self._prepare_skills_list(profile.get("skills", "")),
                "school": self._clean_text(profile.get("school", "")),
                "school_keyword": (
                    profile.get("school", "").strip().lower()
                    if profile.get("school")
                    else ""
                ),
                "grade": (
                    profile.get("grade", "").strip().lower()
                    if profile.get("grade")
                    else ""
                ),
                "email": profile.get("email", ""),
                "location": self._clean_text(profile.get("location", "")),
                "location_keyword": (
                    profile.get("location", "").strip().lower()
                    if profile.get("location")
                    else ""
                ),
                "github_url": profile.get("github_url", ""),
                "linkedin_url": profile.get("linkedin_url", ""),
                "portfolio_url": profile.get("portfolio_url", ""),
                "interests": self._clean_text(profile.get("interests", "")),
                "interests_keyword": self._prepare_skills_list(
                    profile.get("interests", "")
                ),
                "phone": profile.get("phone", ""),
                "user_type": profile.get("user_type", "student"),
                "created_at": str(profile.get("created_at", "")),
                "updated_at": str(profile.get("updated_at", "")),
            }

            # Add or update the document
            writer.update_document(**doc_data)
            writer.commit()

            logger.info(
                f"Indexed student profile: {profile.get('id')} - {profile.get('name')}"
            )
            return True

        except Exception as e:
            logger.error(f"Error indexing student profile {profile.get('id')}: {e}")
            return False

    def remove_from_index(self, profile_id: str) -> bool:
        """
        Remove a profile from the search index.

        Args:
            profile_id: ID of the profile to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            writer = self.ix.writer()
            writer.delete_by_term("id", profile_id)
            writer.commit()

            logger.info(f"Removed profile from index: {profile_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing profile {profile_id} from index: {e}")
            return False

    def rebuild_index(self, profiles: List[Dict[str, Any]]) -> bool:
        """
        Rebuild the entire search index from scratch.

        Args:
            profiles: List of all student profiles to index

        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear the existing index
            writer = self.ix.writer()
            writer.commit(mergetype=CLEAR)

            # Index all profiles
            success_count = 0
            for profile in profiles:
                if profile.get("user_type") == "student":
                    if self.index_student_profile(profile):
                        success_count += 1

            logger.info(f"Rebuilt search index with {success_count} student profiles")
            return True

        except Exception as e:
            logger.error(f"Error rebuilding search index: {e}")
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
        Search for student profiles using Whoosh.

        Args:
            search_query: General text search across name, bio, skills, etc.
            skills: Specific skills to search for
            school: School name to filter by
            grade: Grade level to filter by
            limit: Maximum number of results to return

        Returns:
            List of matching student profile data
        """
        try:
            with self.ix.searcher() as searcher:
                # Build the query
                query_parts = []

                # General text search across multiple fields
                if search_query:
                    search_query = search_query.strip()
                    if search_query:
                        # Create a multifield parser for general search
                        multifield_parser = MultifieldParser(
                            [
                                "name",
                                "bio",
                                "skills",
                                "school",
                                "location",
                                "interests",
                            ],
                            schema=self.ix.schema,
                        )

                        # Parse the general query
                        general_query = multifield_parser.parse(search_query)
                        query_parts.append(general_query)

                # Skills search (both exact keyword matching and fuzzy text matching)
                if skills:
                    skills = skills.strip()
                    if skills:
                        skills_parts = []

                        # Exact keyword match (higher priority)
                        skills_keyword_query = QueryParser(
                            "skills_keyword", self.ix.schema
                        ).parse(skills)
                        skills_parts.append(skills_keyword_query)

                        # Text match in skills field
                        skills_text_query = QueryParser("skills", self.ix.schema).parse(
                            skills
                        )
                        skills_parts.append(skills_text_query)

                        # Combine with OR
                        if skills_parts:
                            skills_combined = Or(skills_parts)
                            query_parts.append(skills_combined)

                # School search (both exact and partial matching)
                if school:
                    school = school.strip()
                    if school:
                        school_parts = []

                        # Exact keyword match
                        if school.lower():
                            school_keyword_query = Term(
                                "school_keyword", school.lower()
                            )
                            school_parts.append(school_keyword_query)

                        # Partial text match
                        school_text_query = QueryParser("school", self.ix.schema).parse(
                            school
                        )
                        school_parts.append(school_text_query)

                        # Combine with OR
                        if school_parts:
                            school_combined = Or(school_parts)
                            query_parts.append(school_combined)

                # Grade filter (exact match)
                if grade:
                    grade = grade.strip().lower()
                    if grade:
                        grade_query = Term("grade", grade)
                        query_parts.append(grade_query)

                # Combine all query parts with AND
                if query_parts:
                    final_query = (
                        And(query_parts) if len(query_parts) > 1 else query_parts[0]
                    )
                else:
                    # If no specific search terms, return all students
                    final_query = Term("user_type", "student")

                # Execute the search
                results = searcher.search(final_query, limit=limit)

                # Convert results to list of dictionaries
                student_profiles = []
                for hit in results:
                    profile = {
                        "id": hit["id"],
                        "name": hit.get("name", ""),
                        "bio": hit.get("bio", ""),
                        "skills": hit.get("skills", ""),
                        "school": hit.get("school", ""),
                        "grade": hit.get("grade", ""),
                        "email": hit.get("email", ""),
                        "location": hit.get("location", ""),
                        "github_url": hit.get("github_url", ""),
                        "linkedin_url": hit.get("linkedin_url", ""),
                        "portfolio_url": hit.get("portfolio_url", ""),
                        "interests": hit.get("interests", ""),
                        "phone": hit.get("phone", ""),
                        "user_type": hit.get("user_type", "student"),
                        "created_at": hit.get("created_at", ""),
                        "updated_at": hit.get("updated_at", ""),
                        "search_score": hit.score,  # Add search relevance score
                    }
                    student_profiles.append(profile)

                logger.info(
                    f"Search completed: {len(student_profiles)} results for query '{search_query}', skills '{skills}', school '{school}', grade '{grade}'"
                )
                return student_profiles

        except Exception as e:
            logger.error(f"Error searching students: {e}")
            return []

    def get_search_suggestions(
        self, field: str, partial_term: str, limit: int = 10
    ) -> List[str]:
        """
        Get search suggestions for a specific field.

        Args:
            field: The field to get suggestions for (skills, school, etc.)
            partial_term: Partial term to match
            limit: Maximum number of suggestions

        Returns:
            List of suggested terms
        """
        try:
            with self.ix.searcher() as searcher:
                suggestions = []

                # Get all terms in the specified field
                terms = list(searcher.lexicon(field))

                # Filter terms that start with the partial term
                partial_lower = partial_term.lower()
                matching_terms = [
                    term
                    for term in terms
                    if term.lower().startswith(partial_lower)
                    and len(term) > len(partial_term)
                ]

                # Sort by length and frequency
                matching_terms.sort(key=len)

                return matching_terms[:limit]

        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the search index.

        Returns:
            Dictionary with index statistics
        """
        try:
            with self.ix.searcher() as searcher:
                stats = {
                    "total_documents": searcher.doc_count_all(),
                    "total_students": len(
                        list(searcher.search(Term("user_type", "student"), limit=None))
                    ),
                    "index_size": (
                        os.path.getsize(os.path.join(self.index_dir, "_MAIN_1.toc"))
                        if os.path.exists(os.path.join(self.index_dir, "_MAIN_1.toc"))
                        else 0
                    ),
                    "schema_fields": list(self.schema.names()),
                }
                return stats
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}


# Global search service instance
search_service = SearchService()

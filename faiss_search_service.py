"""
Lightweight FAISS Search Service for InterSpark

Uses FAISS vector database with ONNX Runtime for embeddings.
Small quantized model (~20MB) suitable for Vercel deployments.

No hardcoded mappings - pure vector similarity search.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

# Import only numpy and FAISS
try:
    import numpy as np
    from numpy import ndarray

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not available")
    np = None
    ndarray = Any

try:
    import faiss

    FAISS_AVAILABLE = True
    logger.info("FAISS loaded successfully")
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available")
    faiss = None

# Import ONNX Runtime for lightweight embeddings
try:
    import onnxruntime as ort
    from huggingface_hub import hf_hub_download

    ONNX_AVAILABLE = True
    logger.info("ONNX Runtime loaded successfully")
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("ONNX Runtime not available - will use fallback embeddings")
    ort = None

SEARCH_AVAILABLE = NUMPY_AVAILABLE and FAISS_AVAILABLE


class LightweightFAISSSearch:
    """Lightweight FAISS-based search with ONNX Runtime embeddings."""

    def __init__(self, embedding_dim: int = 384):
        """Initialize FAISS search service with ONNX embedding model."""
        self._embedding_dim = embedding_dim
        self._student_index = None
        self._opportunity_index = None
        self._student_map = {}
        self._opportunity_map = {}

        # ONNX model for embeddings
        self._onnx_session = None
        self._tokenizer_vocab = None

        # Initialize ONNX model if available
        if ONNX_AVAILABLE:
            self._load_onnx_model()

        logger.info(
            f"Initialized FAISS search (dim={embedding_dim}, onnx={self._onnx_session is not None})"
        )

    def _load_onnx_model(self):
        """Load lightweight ONNX model for embeddings."""
        try:
            # Download all-MiniLM-L6-v2 ONNX model (quantized, ~20MB)
            model_path = hf_hub_download(
                repo_id="Xenova/all-MiniLM-L6-v2", filename="onnx/model_quantized.onnx"
            )

            # Load vocabulary
            vocab_path = hf_hub_download(
                repo_id="Xenova/all-MiniLM-L6-v2", filename="tokenizer.json"
            )

            # Initialize ONNX session
            self._onnx_session = ort.InferenceSession(model_path)

            # Load tokenizer vocabulary
            with open(vocab_path, "r") as f:
                tokenizer_data = json.load(f)
                self._tokenizer_vocab = tokenizer_data.get("model", {}).get("vocab", {})

            logger.info("Loaded ONNX embedding model successfully")
        except Exception as e:
            logger.warning(f"Failed to load ONNX model: {e}. Will use fallback.")
            self._onnx_session = None

    def _simple_tokenize(self, text: str, max_length: int = 128) -> List[int]:
        """Simple tokenization for ONNX model."""
        if not text or not self._tokenizer_vocab:
            return [101, 102]  # [CLS] and [SEP] tokens

        # Lowercase and split
        tokens = text.lower().split()[: max_length - 2]

        # Convert to token IDs
        token_ids = [101]  # [CLS] token
        for token in tokens:
            token_id = self._tokenizer_vocab.get(token, 100)  # 100 = [UNK]
            token_ids.append(token_id)
        token_ids.append(102)  # [SEP] token

        # Pad to max_length
        while len(token_ids) < max_length:
            token_ids.append(0)  # Padding token

        return token_ids[:max_length]

    def _text_to_vector_onnx(self, text: str) -> Union[ndarray, Any]:
        """Convert text to vector using ONNX model."""
        if not self._onnx_session or not NUMPY_AVAILABLE:
            return None

        try:
            # Tokenize
            input_ids = self._simple_tokenize(text)
            attention_mask = [1 if id != 0 else 0 for id in input_ids]
            token_type_ids = [0] * len(input_ids)  # All zeros for single sentence

            # Create numpy arrays
            input_ids_array = np.array([input_ids], dtype=np.int64)
            attention_mask_array = np.array([attention_mask], dtype=np.int64)
            token_type_ids_array = np.array([token_type_ids], dtype=np.int64)

            # Run inference
            outputs = self._onnx_session.run(
                None,
                {
                    "input_ids": input_ids_array,
                    "attention_mask": attention_mask_array,
                    "token_type_ids": token_type_ids_array,
                },
            )

            # Get embeddings (mean pooling of last hidden state)
            last_hidden_state = outputs[
                0
            ]  # Shape: (batch_size, seq_length, hidden_size)

            # Apply attention mask for mean pooling
            attention_mask_expanded = np.expand_dims(attention_mask_array, -1)
            masked_embeddings = last_hidden_state * attention_mask_expanded
            sum_embeddings = np.sum(masked_embeddings, axis=1)
            sum_mask = np.clip(
                np.sum(attention_mask_expanded, axis=1), a_min=1e-9, a_max=None
            )
            embeddings = (sum_embeddings / sum_mask)[0]  # Shape: (embedding_dim,)

            # L2 normalization
            norm = np.linalg.norm(embeddings)
            if norm > 0:
                embeddings = embeddings / norm

            return embeddings
        except Exception as e:
            logger.error(f"Error in ONNX embedding: {e}")
            return None

    def _text_to_vector(self, text: str) -> Union[ndarray, Any]:
        """
        Convert text to vector using available method.
        Tries ONNX first, falls back to simple hash-based approach.
        """
        # Try ONNX embedding
        if self._onnx_session:
            vec = self._text_to_vector_onnx(text)
            if vec is not None:
                return vec

        # Fallback: simple hash-based embedding
        if not NUMPY_AVAILABLE:
            return None

        # Create simple hash-based vector
        tokens = text.lower().split()[:50]
        vector = np.zeros(self._embedding_dim, dtype=np.float32)

        for token in tokens:
            # Hash token to index
            hash_val = hash(token)
            idx = abs(hash_val) % self._embedding_dim
            vector[idx] += 1.0

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    def _combine_profile_text(
        self, profile: Dict[str, Any], is_opportunity: bool = False
    ) -> str:
        """Combine all searchable fields into single text."""
        parts = []

        if not is_opportunity:
            # Student/Organization profile
            parts.append(profile.get("name") or profile.get("organization_name", ""))
            parts.append(profile.get("bio") or profile.get("description", ""))

            # Skills
            skills = profile.get("skills", [])
            if isinstance(skills, str):
                try:
                    skills = json.loads(skills)
                except:
                    skills = [s.strip() for s in skills.split(",") if s.strip()]
            if isinstance(skills, list):
                parts.extend(skills)

            parts.append(profile.get("school", ""))
            parts.append(profile.get("grade", ""))
            parts.append(profile.get("location", ""))
        else:
            # Opportunity
            parts.append(profile.get("title", ""))
            parts.append(profile.get("description", ""))
            parts.append(profile.get("type", ""))
            parts.append(profile.get("category", ""))

            # Skills needed
            skills = profile.get("skills_needed", [])
            if isinstance(skills, str):
                try:
                    skills = json.loads(skills)
                except:
                    skills = [s.strip() for s in skills.split(",") if s.strip()]
            if isinstance(skills, list):
                parts.extend(skills)

            parts.append(profile.get("location", ""))

        return " ".join(str(p) for p in parts if p)

    def build_student_index(self, students: List[Dict[str, Any]]) -> bool:
        """Build FAISS index for students."""
        if not SEARCH_AVAILABLE or not students:
            logger.info("FAISS not available or no students to index")
            return False

        try:
            # Extract text
            texts = [self._combine_profile_text(s) for s in students]

            # Generate embeddings
            embeddings = np.array(
                [self._text_to_vector(t) for t in texts], dtype=np.float32
            )

            # Create FAISS index
            index = faiss.IndexFlatIP(
                self._embedding_dim
            )  # Inner product (cosine similarity)
            index.add(embeddings)

            # Store index and mapping
            self._student_index = index
            self._student_map = {i: student for i, student in enumerate(students)}

            logger.info(f"Built FAISS index for {len(students)} students")
            return True

        except Exception as e:
            logger.error(f"Error building student index: {e}")
            return False

    def build_opportunity_index(self, opportunities: List[Dict[str, Any]]) -> bool:
        """Build FAISS index for opportunities."""
        if not SEARCH_AVAILABLE or not opportunities:
            logger.info("FAISS not available or no opportunities to index")
            return False

        try:
            # Extract text
            texts = [
                self._combine_profile_text(o, is_opportunity=True)
                for o in opportunities
            ]

            # Generate embeddings
            embeddings = np.array(
                [self._text_to_vector(t) for t in texts], dtype=np.float32
            )

            # Create FAISS index
            index = faiss.IndexFlatIP(self._embedding_dim)
            index.add(embeddings)

            # Store index and mapping
            self._opportunity_index = index
            self._opportunity_map = {i: opp for i, opp in enumerate(opportunities)}

            logger.info(f"Built FAISS index for {len(opportunities)} opportunities")
            return True

        except Exception as e:
            logger.error(f"Error building opportunity index: {e}")
            return False

    def search_students(
        self,
        query: str,
        students: List[Dict[str, Any]],
        top_k: int = 50,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search students using FAISS semantic search."""
        if not SEARCH_AVAILABLE or not students:
            return students

        try:
            # Build index if needed
            if not self._student_index or len(self._student_map) != len(students):
                self.build_student_index(students)

            if not self._student_index:
                return students

            # Encode query (no expansion needed with ONNX embeddings)
            query_vector = self._text_to_vector(query).reshape(1, -1)

            # Search
            scores, indices = self._student_index.search(
                query_vector, min(top_k, len(students))
            )

            # Get results - filter by minimum relevance score
            MIN_RELEVANCE_SCORE = (
                0.15  # Threshold for relevance (lowered to ensure results)
            )
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx in self._student_map:
                    # Only include if score meets minimum threshold
                    if float(score) >= MIN_RELEVANCE_SCORE:
                        student = self._student_map[idx].copy()
                        student["faiss_score"] = float(score)
                        results.append(student)

            # Apply filters
            if filters:
                if filters.get("school"):
                    results = [
                        s
                        for s in results
                        if filters["school"].lower()
                        in (s.get("school", "") or "").lower()
                    ]
                if filters.get("grade"):
                    results = [
                        s
                        for s in results
                        if filters["grade"].lower()
                        in (s.get("grade", "") or "").lower()
                    ]
                if filters.get("location"):
                    results = [
                        s
                        for s in results
                        if filters["location"].lower()
                        in (s.get("location", "") or "").lower()
                    ]

            logger.info(f"FAISS search returned {len(results)} students for: {query}")
            return results

        except Exception as e:
            logger.error(f"Error in FAISS student search: {e}")
            return students

    def search_opportunities(
        self,
        query: str,
        opportunities: List[Dict[str, Any]],
        top_k: int = 50,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search opportunities using FAISS semantic search."""
        if not SEARCH_AVAILABLE or not opportunities:
            return opportunities

        try:
            # Build index if needed
            if not self._opportunity_index or len(self._opportunity_map) != len(
                opportunities
            ):
                self.build_opportunity_index(opportunities)

            if not self._opportunity_index:
                return opportunities

            # Encode query (no expansion needed with ONNX embeddings)
            query_vector = self._text_to_vector(query).reshape(1, -1)

            # Search
            scores, indices = self._opportunity_index.search(
                query_vector, min(top_k, len(opportunities))
            )

            # Get results - filter by minimum relevance score
            # FAISS inner product scores: higher is more similar
            # Only include opportunities with a meaningful relevance
            MIN_RELEVANCE_SCORE = (
                0.15  # Threshold for relevance (lowered to ensure results)
            )
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx in self._opportunity_map:
                    # Only include if score meets minimum threshold
                    if float(score) >= MIN_RELEVANCE_SCORE:
                        opp = self._opportunity_map[idx].copy()
                        opp["faiss_score"] = float(score)
                        results.append(opp)

            # Apply filters
            if filters:
                if filters.get("type"):
                    results = [
                        o
                        for o in results
                        if o.get("type", "").lower() == filters["type"].lower()
                    ]
                if filters.get("category"):
                    results = [
                        o
                        for o in results
                        if o.get("category", "").lower() == filters["category"].lower()
                    ]
                if filters.get("location"):
                    results = [
                        o
                        for o in results
                        if filters["location"].lower()
                        in (o.get("location", "") or "").lower()
                    ]

            logger.info(
                f"FAISS search returned {len(results)} opportunities for: {query}"
            )
            return results

        except Exception as e:
            logger.error(f"Error in FAISS opportunity search: {e}")
            return opportunities

    def recommend_opportunities_for_user(
        self,
        user_profile: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        top_k: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Recommend opportunities based on user's profile using semantic similarity.

        Uses the user's skills, bio, and interests as a query to find
        semantically similar opportunities.
        """
        if not SEARCH_AVAILABLE or not opportunities or not user_profile:
            return opportunities

        try:
            # Build index if needed
            if not self._opportunity_index or len(self._opportunity_map) != len(
                opportunities
            ):
                self.build_opportunity_index(opportunities)

            if not self._opportunity_index:
                return opportunities

            # Create a "query" from user profile
            user_text_parts = []

            # Add user's skills (most important for matching)
            skills = user_profile.get("skills", [])
            if isinstance(skills, str):
                try:
                    skills = json.loads(skills)
                except:
                    skills = [s.strip() for s in skills.split(",") if s.strip()]
            if isinstance(skills, list):
                user_text_parts.extend(skills)

            # Add bio/description
            bio = user_profile.get("bio") or user_profile.get("description", "")
            if bio:
                user_text_parts.append(bio)

            # Add interests if available
            interests = user_profile.get("interests", [])
            if isinstance(interests, str):
                try:
                    interests = json.loads(interests)
                except:
                    interests = [i.strip() for i in interests.split(",") if i.strip()]
            if isinstance(interests, list):
                user_text_parts.extend(interests)

            if not user_text_parts:
                # No profile data to match on, return original order
                return opportunities

            user_query = " ".join(str(p) for p in user_text_parts if p)

            # Encode user profile as query vector
            query_vector = self._text_to_vector(user_query).reshape(1, -1)

            # Search for similar opportunities
            scores, indices = self._opportunity_index.search(
                query_vector, min(top_k, len(opportunities))
            )

            # Get results sorted by relevance
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx in self._opportunity_map:
                    opp = self._opportunity_map[idx].copy()
                    opp["relevance_score"] = float(score)
                    results.append(opp)

            logger.info(
                f"FAISS recommended {len(results)} opportunities for user profile"
            )
            return results

        except Exception as e:
            logger.error(f"Error in FAISS opportunity recommendation: {e}")
            return opportunities

    def recommend_people_for_user(
        self,
        user_profile: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        top_k: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Recommend people based on user's profile using semantic similarity.

        Finds people with similar skills, interests, and backgrounds.
        Great for networking and collaboration suggestions.
        """
        if not SEARCH_AVAILABLE or not candidates or not user_profile:
            return candidates

        try:
            # Build index if needed
            if not self._student_index or len(self._student_map) != len(candidates):
                self.build_student_index(candidates)

            if not self._student_index:
                return candidates

            # Create a "query" from user profile
            user_text_parts = []

            # Add user's skills
            skills = user_profile.get("skills", [])
            if isinstance(skills, str):
                try:
                    skills = json.loads(skills)
                except:
                    skills = [s.strip() for s in skills.split(",") if s.strip()]
            if isinstance(skills, list):
                user_text_parts.extend(skills)

            # Add bio/description
            bio = user_profile.get("bio") or user_profile.get("description", "")
            if bio:
                user_text_parts.append(bio)

            # Add interests
            interests = user_profile.get("interests", [])
            if isinstance(interests, str):
                try:
                    interests = json.loads(interests)
                except:
                    interests = [i.strip() for i in interests.split(",") if i.strip()]
            if isinstance(interests, list):
                user_text_parts.extend(interests)

            # Add school for finding similar students
            school = user_profile.get("school", "")
            if school:
                user_text_parts.append(school)

            if not user_text_parts:
                # No profile data to match on, return original order
                return candidates

            user_query = " ".join(str(p) for p in user_text_parts if p)

            # Encode user profile as query vector
            query_vector = self._text_to_vector(user_query).reshape(1, -1)

            # Search for similar people
            scores, indices = self._student_index.search(
                query_vector, min(top_k, len(candidates))
            )

            # Get results sorted by relevance, excluding the user themselves
            user_id = user_profile.get("user_id") or user_profile.get("id")
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx in self._student_map:
                    person = self._student_map[idx].copy()
                    # Skip the user themselves
                    person_id = person.get("user_id") or person.get("id")
                    if person_id and user_id and str(person_id) == str(user_id):
                        continue
                    person["relevance_score"] = float(score)
                    results.append(person)

            logger.info(f"FAISS recommended {len(results)} people for user profile")
            return results

        except Exception as e:
            logger.error(f"Error in FAISS people recommendation: {e}")
            return candidates

    def generate_dynamic_categories_for_opportunities(
        self,
        user_profile: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        max_categories: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Dynamically generate personalized category suggestions for opportunities.

        Categories are generated from:
        1. User's skills/interests (highest priority - semantic search)
        2. Unique opportunity types in the database
        3. Unique categories from opportunities
        4. Skills needed across opportunities

        Returns list of category dicts with 'name' and 'query' for FAISS search.
        """
        categories = []
        seen_names = set()

        # Always start with personalized recommendations
        categories.append(
            {
                "name": "Recommended for You",
                "type": "personalized",
                "query": None,  # Uses user profile directly
            }
        )
        seen_names.add("recommended for you")

        # Extract user's skills and interests for semantic categories
        user_skills = user_profile.get("skills", [])
        if isinstance(user_skills, str):
            try:
                user_skills = json.loads(user_skills)
            except:
                user_skills = [s.strip() for s in user_skills.split(",") if s.strip()]

        user_interests = user_profile.get("interests", "")
        if isinstance(user_interests, str):
            interest_list = [i.strip() for i in user_interests.split(",") if i.strip()]
        else:
            interest_list = user_interests if isinstance(user_interests, list) else []

        # Add categories based on user's skills (semantic search)
        for skill in (user_skills or [])[:5]:  # Top 5 skills
            if isinstance(skill, str) and skill.strip():
                skill_name = skill.strip()
                if skill_name.lower() not in seen_names:
                    categories.append(
                        {
                            "name": f"{skill_name} Opportunities",
                            "type": "semantic",
                            "query": skill_name,
                        }
                    )
                    seen_names.add(skill_name.lower())

        # Add categories based on user's interests
        for interest in (interest_list or [])[:3]:  # Top 3 interests
            if isinstance(interest, str) and interest.strip():
                interest_name = interest.strip()
                if interest_name.lower() not in seen_names:
                    categories.append(
                        {
                            "name": f"{interest_name} Opportunities",
                            "type": "semantic",
                            "query": interest_name,
                        }
                    )
                    seen_names.add(interest_name.lower())

        # Extract unique opportunity types from actual data
        opp_types = set()
        for opp in opportunities:
            opp_type = opp.get("type", "")
            if opp_type and isinstance(opp_type, str):
                opp_types.add(opp_type.strip())

        # Add opportunity type categories
        for opp_type in sorted(opp_types):
            if opp_type.lower() not in seen_names and len(categories) < max_categories:
                # Pluralize type name for category title
                display_name = opp_type if opp_type.endswith("s") else f"{opp_type}s"
                categories.append(
                    {"name": display_name, "type": "filter_type", "query": opp_type}
                )
                seen_names.add(opp_type.lower())

        # Extract unique categories from opportunities
        opp_categories = set()
        for opp in opportunities:
            cat = opp.get("category", "")
            if cat and isinstance(cat, str):
                opp_categories.add(cat.strip())

        for cat in sorted(opp_categories):
            if cat.lower() not in seen_names and len(categories) < max_categories:
                categories.append(
                    {"name": cat, "type": "filter_category", "query": cat}
                )
                seen_names.add(cat.lower())

        # Extract common skills from opportunities for additional semantic categories
        skill_counts = {}
        for opp in opportunities:
            skills_needed = opp.get("skills_needed", [])
            if isinstance(skills_needed, str):
                try:
                    skills_needed = json.loads(skills_needed)
                except:
                    skills_needed = [
                        s.strip() for s in skills_needed.split(",") if s.strip()
                    ]

            for skill in skills_needed or []:
                if isinstance(skill, str) and skill.strip():
                    skill_lower = skill.strip().lower()
                    skill_counts[skill_lower] = skill_counts.get(skill_lower, 0) + 1

        # Add top skills as semantic categories
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for skill, count in top_skills:
            if skill not in seen_names and len(categories) < max_categories:
                # Capitalize skill name
                display_name = skill.title()
                categories.append(
                    {
                        "name": f"{display_name} Related",
                        "type": "semantic",
                        "query": skill,
                    }
                )
                seen_names.add(skill)

        # Limit to max_categories first, then add "All Opportunities" at the end
        categories = categories[:max_categories]

        # Always add "All Opportunities" at the very end
        categories.append({"name": "All Opportunities", "type": "all", "query": None})

        return categories

    def generate_dynamic_categories_for_talent(
        self,
        user_profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
        max_categories: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Dynamically generate personalized category suggestions for talent search.

        Categories are generated from:
        1. User's skills/interests (find similar people)
        2. Unique schools in the database
        3. Unique grades
        4. Common skills across profiles

        Returns list of category dicts with 'name' and 'query' for FAISS search.
        """
        categories = []
        seen_names = set()

        # Ensure profiles is not None
        if profiles is None:
            profiles = []

        # Ensure user_profile is not None
        if user_profile is None:
            user_profile = {}

        # Always start with personalized matches
        categories.append(
            {"name": "Best Matches for You", "type": "personalized", "query": None}
        )
        seen_names.add("best matches for you")

        # Extract user's skills for finding similar people
        user_skills = user_profile.get("skills", [])
        if isinstance(user_skills, str):
            try:
                user_skills = json.loads(user_skills)
            except:
                user_skills = [s.strip() for s in user_skills.split(",") if s.strip()]

        # Ensure user_skills is a list
        if user_skills is None:
            user_skills = []
        if not isinstance(user_skills, list):
            user_skills = []

        # Add "Similar Skills" if user has skills
        if user_skills:
            categories.append(
                {
                    "name": "People with Similar Skills",
                    "type": "similar_skills",
                    "query": None,
                }
            )
            seen_names.add("people with similar skills")

        # Add user's school as a category if they have one
        user_school = user_profile.get("school", "")
        if user_school and isinstance(user_school, str) and user_school.strip():
            categories.append(
                {
                    "name": f"From {user_school.strip()}",
                    "type": "filter_school",
                    "query": user_school.strip(),
                }
            )
            seen_names.add(user_school.strip().lower())

        # Add categories based on user's skills (find experts)
        for skill in (user_skills or [])[:4]:
            if isinstance(skill, str) and skill.strip():
                skill_name = skill.strip()
                if skill_name.lower() not in seen_names:
                    categories.append(
                        {
                            "name": f"{skill_name.title()} Experts",
                            "type": "semantic",
                            "query": skill_name,
                        }
                    )
                    seen_names.add(skill_name.lower())

        # Extract unique grades from profiles
        grades = set()
        for profile in profiles or []:
            grade = profile.get("grade", "")
            if grade and isinstance(grade, str):
                grades.add(grade.strip())

        # Add grade categories
        grade_order = [
            "9th Grade",
            "10th Grade",
            "11th Grade",
            "12th Grade",
            "Freshman",
            "Sophomore",
            "Junior",
            "Senior",
            "College",
            "Graduate",
        ]
        for grade in grade_order:
            if any(grade.lower() in g.lower() for g in grades):
                if grade.lower() not in seen_names and len(categories) < max_categories:
                    categories.append(
                        {
                            "name": f"{grade} Students",
                            "type": "filter_grade",
                            "query": grade,
                        }
                    )
                    seen_names.add(grade.lower())

        # Extract common skills from all profiles
        skill_counts = {}
        for profile in profiles or []:
            profile_skills = profile.get("skills", [])
            if isinstance(profile_skills, str):
                try:
                    profile_skills = json.loads(profile_skills)
                except:
                    profile_skills = [
                        s.strip() for s in profile_skills.split(",") if s.strip()
                    ]

            # Ensure profile_skills is a list
            if profile_skills is None:
                profile_skills = []
            if not isinstance(profile_skills, list):
                profile_skills = []

            for skill in profile_skills or []:
                if isinstance(skill, str) and skill.strip():
                    skill_lower = skill.strip().lower()
                    skill_counts[skill_lower] = skill_counts.get(skill_lower, 0) + 1

        # Add top skills as semantic categories
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:6]
        for skill, count in top_skills:
            if skill not in seen_names and len(categories) < max_categories:
                display_name = skill.title()
                categories.append(
                    {
                        "name": f"{display_name} Skilled",
                        "type": "semantic",
                        "query": skill,
                    }
                )
                seen_names.add(skill)

        # Extract unique schools for more variety
        schools = {}
        for profile in profiles or []:
            school = profile.get("school", "")
            if school and isinstance(school, str) and school.strip():
                school_clean = school.strip()
                schools[school_clean] = schools.get(school_clean, 0) + 1

        # Add top schools as categories
        top_schools = sorted(schools.items(), key=lambda x: x[1], reverse=True)[:3]
        for school, count in top_schools:
            if school.lower() not in seen_names and len(categories) < max_categories:
                categories.append(
                    {"name": f"From {school}", "type": "filter_school", "query": school}
                )
                seen_names.add(school.lower())

        # Always add "All Talent" at the end
        if "all talent" not in seen_names:
            categories.append({"name": "All Talent", "type": "all", "query": None})

        return categories[: max_categories + 1]  # +1 to include All Talent

    def get_opportunities_for_category(
        self,
        category_info: Dict[str, Any],
        user_profile: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get opportunities for a specific category.

        Args:
            category_info: Dict with 'name', 'type', and 'query' keys
            user_profile: User's profile for personalized categories
            opportunities: All opportunities to search/filter
            limit: Max results to return
            offset: Pagination offset

        Returns:
            List of matching opportunities
        """
        # Ensure opportunities is not None
        if opportunities is None:
            opportunities = []

        cat_type = category_info.get("type", "semantic")
        query = category_info.get("query", "") or ""  # Ensure query is never None

        results = []

        if cat_type == "personalized":
            # Use FAISS recommendation
            results = self.recommend_opportunities_for_user(
                user_profile=user_profile, opportunities=opportunities, top_k=100
            )

        elif cat_type == "filter_type":
            # Filter by opportunity type
            results = [
                o for o in opportunities if o.get("type", "").lower() == query.lower()
            ]

        elif cat_type == "filter_category":
            # Filter by category field
            results = [
                o
                for o in opportunities
                if o.get("category", "").lower() == query.lower()
            ]

        elif cat_type == "semantic":
            # Use FAISS semantic search
            results = self.search_opportunities(
                query=query, opportunities=opportunities, top_k=100
            )

        elif cat_type == "all":
            # Return all opportunities
            results = opportunities

        else:
            results = opportunities

        # Ensure results is not None
        if results is None:
            results = []

        # Apply pagination
        return results[offset : offset + limit]

    def get_profiles_for_category(
        self,
        category_info: Dict[str, Any],
        user_profile: Dict[str, Any],
        profiles: List[Dict[str, Any]],
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get profiles for a specific talent category.

        Args:
            category_info: Dict with 'name', 'type', and 'query' keys
            user_profile: User's profile for personalized categories
            profiles: All profiles to search/filter
            limit: Max results to return
            offset: Pagination offset

        Returns:
            List of matching profiles
        """
        # Ensure profiles is not None
        if profiles is None:
            profiles = []

        cat_type = category_info.get("type", "semantic")
        query = category_info.get("query", "") or ""  # Ensure query is never None

        results = []

        if cat_type == "personalized":
            # Use FAISS recommendation
            results = self.recommend_people_for_user(
                user_profile=user_profile, candidates=profiles, top_k=100
            )

        elif cat_type == "similar_skills":
            # Find people with overlapping skills
            user_skills = user_profile.get("skills", [])
            if isinstance(user_skills, str):
                try:
                    user_skills = json.loads(user_skills)
                except:
                    user_skills = [
                        s.strip() for s in user_skills.split(",") if s.strip()
                    ]

            # Ensure user_skills is a list
            if user_skills is None:
                user_skills = []
            if not isinstance(user_skills, list):
                user_skills = []

            user_skills_lower = set(
                s.lower() for s in user_skills if isinstance(s, str)
            )

            # If user has no skills, return all profiles (fallback)
            if not user_skills_lower:
                results = profiles if profiles else []
            else:
                scored_profiles = []
                for profile in profiles or []:
                    profile_skills = profile.get("skills", [])
                    if isinstance(profile_skills, str):
                        try:
                            profile_skills = json.loads(profile_skills)
                        except:
                            profile_skills = [
                                s.strip()
                                for s in profile_skills.split(",")
                                if s.strip()
                            ]

                    # Ensure profile_skills is a list
                    if profile_skills is None:
                        profile_skills = []
                    if not isinstance(profile_skills, list):
                        profile_skills = []

                    profile_skills_lower = set(
                        s.lower() for s in profile_skills if isinstance(s, str)
                    )
                    overlap = len(user_skills_lower & profile_skills_lower)
                    if overlap > 0:
                        p = profile.copy()
                        p["_skill_overlap"] = overlap
                        scored_profiles.append(p)

                # Sort by overlap count
                results = sorted(
                    scored_profiles,
                    key=lambda x: x.get("_skill_overlap", 0),
                    reverse=True,
                )

        elif cat_type == "filter_school":
            # Filter by school
            results = [
                p
                for p in profiles
                if query.lower() in (p.get("school", "") or "").lower()
            ]

        elif cat_type == "filter_grade":
            # Filter by grade
            results = [
                p
                for p in profiles
                if query.lower() in (p.get("grade", "") or "").lower()
            ]

        elif cat_type == "semantic":
            # Use FAISS semantic search
            results = self.search_students(query=query, students=profiles, top_k=100)

        elif cat_type == "all":
            # Return all profiles
            results = profiles

        else:
            results = profiles

        # Ensure results is not None
        if results is None:
            results = []

        # Apply pagination
        return results[offset : offset + limit]


# Singleton instance
_faiss_search_instance: Optional[LightweightFAISSSearch] = None


def get_faiss_search() -> LightweightFAISSSearch:
    """Get singleton FAISS search instance."""
    global _faiss_search_instance

    if _faiss_search_instance is None:
        _faiss_search_instance = LightweightFAISSSearch()

    return _faiss_search_instance

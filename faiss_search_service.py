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

            # Get results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx in self._student_map:
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

            # Get results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx in self._opportunity_map:
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


# Singleton instance
_faiss_search_instance: Optional[LightweightFAISSSearch] = None


def get_faiss_search() -> LightweightFAISSSearch:
    """Get singleton FAISS search instance."""
    global _faiss_search_instance

    if _faiss_search_instance is None:
        _faiss_search_instance = LightweightFAISSSearch()

    return _faiss_search_instance

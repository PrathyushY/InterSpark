"""
Supabase configuration and service module for InterSpark Flask application.
Handles authentication, user management, and database operations.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseService:
    """Service class for all Supabase operations including auth and database."""

    def __init__(self):
        """Initialize Supabase client with environment variables."""
        self.url = os.getenv("SUPABASE_URL")
        self.public_key = os.getenv("SUPABASE_PUBLIC_KEY")
        self.service_key = os.getenv("SUPABASE_SECRET_KEY")

        if not self.url or not self.public_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_PUBLIC_KEY must be set in environment variables"
            )

        # Public client for authentication operations
        self.client: Client = create_client(self.url, self.public_key)

        # Service client for administrative operations (bypasses RLS)
        if self.service_key:
            self.service_client: Client = create_client(self.url, self.service_key)
        else:
            self.service_client = self.client  # Fallback to public client

        logger.info("Supabase client initialized successfully")

    def is_profile_complete(
            self, profile: Dict[str, Any], user_type: str = None
    ) -> Dict[str, Any]:
        """
        Check if a user profile has all required fields completed.

        Args:
            profile: User profile data
            user_type: Optional user type override

        Returns:
            Dictionary with 'complete' boolean and 'missing_fields' list
        """
        if not profile:
            return {"complete": False, "missing_fields": ["Profile not found"]}

        user_type = user_type or profile.get("user_type", "student")
        missing_fields = []

        # Required fields for all users
        if (
                not profile.get("name")
                or profile.get("name").strip() == ""
                or profile.get("name") == "User"
        ):
            missing_fields.append("name")

        # Additional required fields for students
        if user_type == "student":
            if not profile.get("bio") or profile.get("bio").strip() == "":
                missing_fields.append("bio")
            if not profile.get("school") or profile.get("school").strip() == "":
                missing_fields.append("school")
            if not profile.get("grade") or profile.get("grade").strip() == "":
                missing_fields.append("grade")

        # Additional required fields for organizations
        elif user_type == "organization":
            if (
                    not profile.get("description")
                    or profile.get("description").strip() == ""
            ):
                missing_fields.append("description")

        return {"complete": len(missing_fields) == 0, "missing_fields": missing_fields}

    # Authentication Methods
    def create_user(
            self, email: str, password: str, user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new user account with profile data and email verification.

        Args:
            email: User's email address
            password: User's password
            user_data: Additional profile data (name, user_type, etc.)

        Returns:
            Dictionary containing user data or error information
        """
        try:
            # Create user in auth.users table with email confirmation required
            response = self.client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "name": user_data.get("name", ""),
                            "user_type": user_data.get("user_type", "student"),
                        },
                        # This will send a confirmation email
                        "email_redirect_to": f"{os.getenv('SITE_URL', 'http://localhost:5000')}/auth/confirm"
                    },
                }
            )

            if response.user:
                logger.info(f"User created successfully in auth: {response.user.id}")
                logger.info(f"Email confirmation required: {not response.user.email_confirmed_at}")

                # Store profile data temporarily (will be completed after email confirmation)
                profile_data = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "name": user_data.get("name", ""),
                    "user_type": user_data.get("user_type", "student"),
                    "email_confirmed": False,  # Track email confirmation status
                }

                # Add user type-specific fields
                if user_data.get("user_type") == "student":
                    profile_data.update(
                        {
                            "school": user_data.get("school", ""),
                            "grade": user_data.get("grade", ""),
                            "bio": user_data.get("bio", ""),
                        }
                    )
                elif user_data.get("user_type") == "organization":
                    profile_data.update(
                        {
                            "description": user_data.get("description", ""),
                            "organization_name": user_data.get(
                                "organization_name", user_data.get("name", "")
                            ),
                        }
                    )

                try:
                    # Create the profile with email_confirmed flag
                    profile_response = (
                        self.service_client.table("profiles")
                        .insert(profile_data)
                        .execute()
                    )
                    if profile_response.data:
                        logger.info(
                            f"Profile created successfully (pending email confirmation): {response.user.id}"
                        )
                    else:
                        logger.warning(
                            f"Profile creation may have failed, but user was created: {response.user.id}"
                        )
                except Exception as profile_error:
                    logger.info(
                        f"Profile creation via insert failed, trying update: {str(profile_error)}"
                    )
                    try:
                        update_data = {
                            k: v for k, v in profile_data.items() if k != "id"
                        }
                        update_response = (
                            self.service_client.table("profiles")
                            .update(update_data)
                            .eq("id", response.user.id)
                            .execute()
                        )
                        if update_response.data:
                            logger.info(
                                f"Profile updated with complete data: {response.user.id}"
                            )
                    except Exception as update_error:
                        logger.warning(
                            f"Could not update profile with complete data: {str(update_error)}"
                        )

                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "created_at": response.user.created_at,
                        "email_confirmed": bool(response.user.email_confirmed_at),
                    },
                    "message": "Registration successful! Please check your email to confirm your account before signing in."
                }
            else:
                logger.error("Failed to create user - no user returned")
                return {"success": False, "error": "Failed to create user"}

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return {"success": False, "error": str(e)}

    def verify_email_token(self, token_hash: str) -> Dict[str, Any]:
        """
        Verify an email confirmation token.

        Args:
            token_hash: The email confirmation token

        Returns:
            Dictionary containing verification result
        """
        try:
            # Verify the token using Supabase's verify OTP method
            response = self.client.auth.verify_otp({
                'token_hash': token_hash,
                'type': 'signup'
            })

            if response.user:
                # Update the profile to mark email as confirmed
                profile_update = self.update_profile(
                    response.user.id,
                    {"email_confirmed": True}
                )

                logger.info(f"Email verified successfully for user: {response.user.id}")
                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "email_confirmed": True,
                    },
                    "message": "Email verified successfully! You can now sign in."
                }
            else:
                return {"success": False, "error": "Invalid or expired verification token"}

        except Exception as e:
            logger.error(f"Error verifying email token: {str(e)}")
            return {"success": False, "error": "Invalid or expired verification token"}

    def resend_confirmation_email(self, email: str) -> Dict[str, Any]:
        """
        Resend email confirmation for a user.

        Args:
            email: User's email address

        Returns:
            Dictionary containing success/error response
        """
        try:
            response = self.client.auth.resend({
                'type': 'signup',
                'email': email,
                'options': {
                    'email_redirect_to': f"{os.getenv('SITE_URL', 'http://localhost:5000')}/auth/confirm"
                }
            })

            logger.info(f"Confirmation email resent to: {email}")
            return {
                "success": True,
                "message": "Confirmation email sent! Please check your inbox."
            }

        except Exception as e:
            logger.error(f"Error resending confirmation email: {str(e)}")
            return {"success": False, "error": "Failed to resend confirmation email"}

    def sign_in_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in an existing user.

        Args:
            email: User's email address
            password: User's password

        Returns:
            Dictionary containing user session data or error information
        """
        try:
            response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if response.user and response.session:
                logger.info(f"User signed in successfully: {response.user.id}")
                return {
                    "success": True,
                    "user": {"id": response.user.id, "email": response.user.email},
                    "session": response.session,
                }
            else:
                return {"success": False, "error": "Invalid credentials"}

        except Exception as e:
            logger.error(f"Error signing in user: {str(e)}")
            return {"success": False, "error": str(e)}

    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and return user data with profile.

        Args:
            email: User's email address
            password: User's password

        Returns:
            Dictionary containing user and profile data or error information
        """
        try:
            # Sign in the user
            auth_response = self.sign_in_user(email, password)

            if not auth_response["success"]:
                return auth_response

            # Get the user's profile
            user_id = auth_response["user"]["id"]
            user_email = auth_response["user"]["email"]
            logger.info(f"Looking up profile for user ID: {user_id}")
            profile = self.get_profile(user_id)

            if profile:
                logger.info(
                    f"Profile found: user_type={profile.get('user_type')}, name={profile.get('name')}"
                )
            else:
                logger.warning(
                    f"No profile found for user ID: {user_id}, attempting to create one"
                )
                # Try to create a missing profile with default values
                profile_result = self.ensure_profile_exists(
                    user_id, user_email, "User", "student"
                )
                if profile_result["success"]:
                    profile = profile_result["profile"]
                    logger.info(
                        f"Created missing profile: user_type={profile.get('user_type')}"
                    )
                else:
                    logger.error(
                        f"Failed to create missing profile: {profile_result.get('error')}"
                    )

            return {
                "success": True,
                "user": auth_response["user"],
                "profile": profile,
                "session": auth_response.get("session"),
            }

        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return {"success": False, "error": str(e)}

    def sign_out_user(self) -> Dict[str, Any]:
        """Sign out the current user."""
        try:
            self.client.auth.sign_out()
            logger.info("User signed out successfully")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error signing out user: {str(e)}")
            return {"success": False, "error": str(e)}

    def set_session(self, access_token: str, refresh_token: str) -> Dict[str, Any]:
        """
        Set the client session using tokens.

        Args:
            access_token: The access token
            refresh_token: The refresh token

        Returns:
            Success/error response
        """
        try:
            self.client.auth.set_session(access_token, refresh_token)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error setting session: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the currently authenticated user."""
        try:
            user = self.client.auth.get_user()
            if user and user.user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "created_at": user.user.created_at,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            return None

    # Profile Management Methods
    def ensure_profile_exists(
            self, user_id: str, email: str, name: str = "", user_type: str = "student"
    ) -> Dict[str, Any]:
        """
        Ensure a profile exists for a user, create if missing.

        Args:
            user_id: The user's ID
            email: The user's email
            name: The user's name
            user_type: The user type

        Returns:
            The profile data or error information
        """
        try:
            # First check if profile exists
            existing_profile = self.get_profile(user_id)
            if existing_profile:
                return {"success": True, "profile": existing_profile}

            # Create missing profile
            profile_data = {
                "id": user_id,
                "email": email,
                "name": name or "User",
                "user_type": user_type,
            }

            profile_response = (
                self.service_client.table("profiles").insert(profile_data).execute()
            )
            if profile_response.data and len(profile_response.data) > 0:
                logger.info(f"Created missing profile for user: {user_id}")
                return {"success": True, "profile": profile_response.data[0]}
            else:
                logger.error(f"Failed to create missing profile for user: {user_id}")
                return {"success": False, "error": "Failed to create profile"}

        except Exception as e:
            logger.error(f"Error ensuring profile exists: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by ID.

        Args:
            user_id: The user's ID

        Returns:
            User profile data or None if not found
        """
        try:
            response = (
                self.client.table("profiles").select("*").eq("id", user_id).execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            return None

    def get_profile_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by email.

        Args:
            email: The user's email address

        Returns:
            User profile data or None if not found
        """
        try:
            response = (
                self.client.table("profiles").select("*").eq("email", email).execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting profile by email: {str(e)}")
            return None

    def update_profile(
            self, user_id: str, profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user profile data.

        Args:
            user_id: The user's ID
            profile_data: Dictionary containing profile updates

        Returns:
            Success/error response
        """
        try:
            print(f"DEBUG - Supabase update_profile called:")
            print(f"  User ID: {user_id}")
            print(f"  Profile data to update: {profile_data}")

            response = (
                self.service_client.table("profiles")
                .update(profile_data)
                .eq("id", user_id)
                .execute()
            )

            print(f"DEBUG - Supabase response: {response}")
            print(f"DEBUG - Response data: {response.data}")

            if response.data:
                logger.info(f"Profile updated successfully for user: {user_id}")
                return {"success": True, "data": response.data[0]}
            else:
                return {"success": False, "error": "Failed to update profile"}

        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            print(f"DEBUG - Exception in update_profile: {str(e)}")
            return {"success": False, "error": str(e)}

    def search_students(
        self,
        search_query: str = "",
        skills: str = "",
        school: str = "",
        grade: str = "",
        location: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Search for student profiles with filters. Skills filter matches ALL selected skills.

        Args:
            search_query: Text to search in name and bio
            skills: Filter by skills (JSON array or comma-separated string)
            school: Filter by school
            grade: Filter by grade
            location: Filter by location

        Returns:
            List of matching student profiles
        """
        import json

        try:
            query = self.client.table("profiles").select("*").eq("user_type", "student")

            # Apply text search if provided
            if search_query:
                query = query.or_(
                    f"name.ilike.%{search_query}%,bio.ilike.%{search_query}%"
                )

            # Apply school filter
            if school:
                query = query.ilike("school", f"%{school}%")

            # Apply grade filter
            if grade:
                query = query.ilike("grade", f"%{grade}%")

            # Apply location filter
            if location:
                query = query.ilike("location", f"%{location}%")

            # Order by creation date, newest first
            query = query.order("created_at", desc=True)

            response = query.execute()
            students = response.data if response.data else []

            # Robustly parse skills filter
            def parse_skills(val):
                if not val:
                    return []
                if isinstance(val, list):
                    return val
                try:
                    loaded = json.loads(val)
                    if isinstance(loaded, list):
                        return loaded
                except Exception:
                    pass
                if "," in val:
                    return [s.strip() for s in val.split(",") if s.strip()]
                return [val.strip()] if val.strip() else []

            selected_skills = set(parse_skills(skills))
            if selected_skills:
                # Only keep students who have ALL selected skills
                def student_has_all_skills(student):
                    profile_skills = student.get("skills", [])
                    # Robustly parse profile_skills
                    if isinstance(profile_skills, str):
                        try:
                            loaded = json.loads(profile_skills)
                            if isinstance(loaded, list):
                                profile_skills = loaded
                        except Exception:
                            if "," in profile_skills:
                                profile_skills = [
                                    s.strip()
                                    for s in profile_skills.split(",")
                                    if s.strip()
                                ]
                            else:
                                profile_skills = (
                                    [profile_skills.strip()]
                                    if profile_skills.strip()
                                    else []
                                )
                    if not isinstance(profile_skills, list):
                        return False
                    return selected_skills.issubset(set(profile_skills))

                students = [s for s in students if student_has_all_skills(s)]

            return students

        except Exception as e:
            logger.error(f"Error searching students: {str(e)}")
            return []

    def search_students_enhanced(
        self,
        search_query: str = "",
        skills: str = "",
        school: str = "",
        grade: str = "",
        location: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search for student profiles with improved skills matching.
        Uses ANY skills match instead of ALL skills match for better results.
        """
        import json

        try:
            query = self.client.table("profiles").select("*").eq("user_type", "student")

            # Apply text search if provided
            if search_query:
                query = query.or_(
                    f"name.ilike.%{search_query}%,bio.ilike.%{search_query}%"
                )

            # Apply school filter
            if school:
                query = query.ilike("school", f"%{school}%")

            # Apply grade filter
            if grade:
                query = query.ilike("grade", f"%{grade}%")

            # Apply location filter
            if location:
                query = query.ilike("location", f"%{location}%")

            # Order by creation date, newest first
            query = query.order("created_at", desc=True)

            response = query.execute()
            students = response.data if response.data else []

            # Enhanced skills filtering - use ANY match instead of ALL match
            def parse_skills(val):
                if not val:
                    return []
                if isinstance(val, list):
                    return val
                try:
                    loaded = json.loads(val)
                    if isinstance(loaded, list):
                        return loaded
                except Exception:
                    pass
                if "," in val:
                    return [s.strip() for s in val.split(",") if s.strip()]
                return [val.strip()] if val.strip() else []

            selected_skills = set(parse_skills(skills))
            if selected_skills:
                # Client-side filtering for skills
                def student_has_any_skills(student):
                    profile_skills = student.get("skills", [])
                    # Robustly parse profile_skills
                    if isinstance(profile_skills, str):
                        try:
                            loaded = json.loads(profile_skills)
                            if isinstance(loaded, list):
                                profile_skills = loaded
                        except Exception:
                            if "," in profile_skills:
                                profile_skills = [
                                    s.strip()
                                    for s in profile_skills.split(",")
                                    if s.strip()
                                ]
                            else:
                                profile_skills = (
                                    [profile_skills.strip()]
                                    if profile_skills.strip()
                                    else []
                                )
                    if not isinstance(profile_skills, list):
                        return False
                    # Check if any selected skill matches any profile skill (case-insensitive exact match)
                    profile_skills_lower = [s.lower().strip() for s in profile_skills]
                    selected_skills_lower = [s.lower().strip() for s in selected_skills]
                    return any(skill in profile_skills_lower for skill in selected_skills_lower)

                students = [s for s in students if student_has_any_skills(s)]

            # If no skills filter but we have a search query, also search within skills
            if not selected_skills and search_query:
                def student_skills_match_query(student):
                    profile_skills = student.get("skills", [])
                    if isinstance(profile_skills, str):
                        try:
                            loaded = json.loads(profile_skills)
                            if isinstance(loaded, list):
                                profile_skills = loaded
                        except Exception:
                            if "," in profile_skills:
                                profile_skills = [
                                    s.strip()
                                    for s in profile_skills.split(",")
                                    if s.strip()
                                ]
                            else:
                                profile_skills = (
                                    [profile_skills.strip()]
                                    if profile_skills.strip()
                                    else []
                                )
                    if not isinstance(profile_skills, list):
                        return False
                    # Check if any skill contains the search query (case-insensitive)
                    return any(search_query.lower() in skill.lower() for skill in profile_skills)

                # Add students whose skills match the search query
                skill_matches = [s for s in students if student_skills_match_query(s)]
                # Prioritize skill matches by putting them first
                students = skill_matches + [s for s in students if s not in skill_matches]

            return students

        except Exception as e:
            logger.error(f"Error in enhanced student search: {str(e)}")
            return []

    # Opportunities Management Methods
    def get_opportunities(
            self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all opportunities with optional filters and limit.

        Args:
            filters: Optional dictionary of filters (type, location, etc.)
            limit: Optional limit on number of results

        Returns:
            List of opportunity records with organization profile info
        """
        try:
            # Select opportunities with organization profile information
            query = self.client.table("opportunities").select(
                "*, profiles!company_id(name, organization_name, email)"
            )

            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if value:  # Only apply non-empty filters
                        query = query.eq(key, value)

            # Only show active opportunities
            query = query.eq("status", "active")

            # Order by creation date, newest first
            query = query.order("created_at", desc=True)

            # Apply limit if specified
            if limit:
                query = query.limit(limit)

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error getting opportunities: {str(e)}")
            return []

    def search_opportunities(
        self,
        search_query: str = "",
        opportunity_type: str = "",
        category: str = "",
        location: str = "",
        skills_needed: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Search opportunities with text and filters, including skills_needed.

        Args:
            search_query: Text to search in title and description
            opportunity_type: Filter by opportunity type
            category: Filter by category
            location: Filter by location
            skills_needed: Filter by required skills (JSON array or comma-separated string)

        Returns:
            List of matching opportunity records
        """
        import json

        try:
            # Select opportunities with organization profile information
            query = self.client.table("opportunities").select(
                "*, profiles!company_id(name, organization_name, email)"
            )

            # Apply text search if provided
            if search_query:
                query = query.or_(
                    f"title.ilike.%{search_query}%,description.ilike.%{search_query}%"
                )

            # Apply type filter
            if opportunity_type:
                query = query.eq("type", opportunity_type)

            # Apply category filter
            if category:
                query = query.eq("category", category)

            # Apply location filter
            if location:
                query = query.ilike("location", f"%{location}%")

            # Only show active opportunities
            query = query.eq("status", "active")

            # Order by creation date, newest first
            query = query.order("created_at", desc=True)

            response = query.execute()
            opportunities = response.data if response.data else []

            # Robustly parse skills_needed filter
            def parse_skills(val):
                if not val:
                    return []
                if isinstance(val, list):
                    return val
                try:
                    loaded = json.loads(val)
                    if isinstance(loaded, list):
                        return loaded
                except Exception:
                    pass
                if "," in val:
                    return [s.strip() for s in val.split(",") if s.strip()]
                return [val.strip()] if val.strip() else []

            selected_skills_needed = set(parse_skills(skills_needed))
            if selected_skills_needed:
                # Use ANY match with case-insensitive comparison
                def opp_has_any_skills(opp):
                    opp_skills = opp.get("skills_needed", [])
                    # Robustly parse opp_skills
                    if isinstance(opp_skills, str):
                        try:
                            loaded = json.loads(opp_skills)
                            if isinstance(loaded, list):
                                opp_skills = loaded
                        except Exception:
                            if "," in opp_skills:
                                opp_skills = [
                                    s.strip()
                                    for s in opp_skills.split(",")
                                    if s.strip()
                                ]
                            else:
                                opp_skills = (
                                    [opp_skills.strip()] if opp_skills.strip() else []
                                )
                    if not isinstance(opp_skills, list):
                        return False
                    # Case-insensitive matching
                    opp_skills_lower = [s.lower() for s in opp_skills]
                    selected_skills_lower = [s.lower() for s in selected_skills_needed]
                    return any(skill in opp_skills_lower for skill in selected_skills_lower)

                opportunities = [o for o in opportunities if opp_has_any_skills(o)]

            return opportunities

        except Exception as e:
            logger.error(f"Error searching opportunities: {str(e)}")
            return []

    def get_opportunity_by_id(self, opportunity_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific opportunity by ID with organization profile.

        Args:
            opportunity_id: The opportunity's ID

        Returns:
            Opportunity data with organization info or None if not found
        """
        try:
            response = (
                self.client.table("opportunities")
                .select("*, profiles!company_id(*)")
                .eq("id", opportunity_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting opportunity: {str(e)}")
            return None

    def get_opportunity(self, opportunity_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific opportunity by ID.

        Args:
            opportunity_id: The opportunity's ID

        Returns:
            Opportunity data or None if not found
        """
        try:
            response = (
                self.client.table("opportunities")
                .select("*")
                .eq("id", opportunity_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting opportunity: {str(e)}")
            return None

    def create_opportunity(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new opportunity.

        Args:
            opportunity_data: Dictionary containing opportunity details

        Returns:
            Success/error response with created opportunity data
        """
        try:
            response = (
                self.service_client.table("opportunities")
                .insert(opportunity_data)
                .execute()
            )

            if response.data:
                logger.info(
                    f"Opportunity created successfully: {response.data[0]['id']}"
                )
                return {"success": True, "data": response.data[0]}
            else:
                return {"success": False, "error": "Failed to create opportunity"}

        except Exception as e:
            logger.error(f"Error creating opportunity: {str(e)}")
            return {"success": False, "error": str(e)}

    def update_opportunity(
            self, opportunity_id: int, opportunity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing opportunity.

        Args:
            opportunity_id: The ID of the opportunity to update
            opportunity_data: Dictionary containing opportunity data

        Returns:
            Dictionary with success status and result
        """
        try:
            response = (
                self.service_client.table("opportunities")
                .update(opportunity_data)
                .eq("id", opportunity_id)
                .execute()
            )

            if response.data:
                logger.info(f"Opportunity updated successfully: {opportunity_id}")
                return {"success": True, "data": response.data[0]}
            else:
                return {"success": False, "error": "Failed to update opportunity"}

        except Exception as e:
            logger.error(f"Error updating opportunity: {str(e)}")
            return {"success": False, "error": str(e)}

    def delete_opportunity(self, opportunity_id: int) -> Dict[str, Any]:
        """
        Delete an opportunity.

        Args:
            opportunity_id: The ID of the opportunity to delete

        Returns:
            Dictionary with success status and result
        """
        try:
            response = (
                self.service_client.table("opportunities")
                .delete()
                .eq("id", opportunity_id)
                .execute()
            )

            # Treat non-empty response.data as success
            if (
                    response.data
                    and isinstance(response.data, list)
                    and len(response.data) > 0
            ):
                logger.info(f"Opportunity deleted successfully: {opportunity_id}")
                return {"success": True}
            else:
                logger.error(f"Failed to delete opportunity: {response}")
                return {"success": False, "error": "Failed to delete opportunity"}

        except Exception as e:
            logger.error(f"Error deleting opportunity: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_organization_opportunities(
            self, organization_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all opportunities for a specific organization, including drafts and all statuses.

        Args:
            organization_id: The organization's user ID

        Returns:
            List of opportunity records
        """
        try:
            response = (
                self.client.table("opportunities")
                .select("*")
                .eq("company_id", organization_id)
                .order("created_at", desc=True)
                .execute()
            )

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error getting organization opportunities: {str(e)}")
            return []

    def get_applications(self, user_id: str, user_type: str) -> List[Dict[str, Any]]:
        """
        Get applications - for students: their applications, for companies: applications to their opportunities.

        Args:
            user_id: The user's ID
            user_type: 'student' or 'organization'

        Returns:
            List of application records
        """
        try:
            if user_type == "student":
                response = (
                    self.client.table("applications")
                    .select("*, opportunities(*)")
                    .eq("student_id", user_id)
                    .order("applied_at", desc=True)
                    .execute()
                )
            else:  # organization
                response = (
                    self.client.table("applications")
                    .select("*, opportunities(*), profiles(*)")
                    .eq("opportunities.company_id", user_id)
                    .order("applied_at", desc=True)
                    .execute()
                )

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error getting applications: {str(e)}")
            return []

    # Bookmark/Saved Items Management Methods
    def save_opportunity(self, user_id: str, opportunity_id: int) -> Dict[str, Any]:
        """
        Save/bookmark an opportunity for a user.

        Args:
            user_id: The user's ID
            opportunity_id: The opportunity's ID

        Returns:
            Success/error response
        """
        try:
            # Try to save the opportunity - if it already exists, handle gracefully
            response = (
                self.service_client.table("saved_opportunities")
                .insert({"user_id": user_id, "opportunity_id": opportunity_id})
                .execute()
            )

            if response.data:
                logger.info(f"Opportunity {opportunity_id} saved by user {user_id}")
                return {"success": True, "message": "Opportunity saved successfully"}
            else:
                return {"success": False, "error": "Failed to save opportunity"}

        except Exception as e:
            # Check if it's a duplicate key constraint error
            error_str = str(e)
            if (
                    "duplicate key value violates unique constraint" in error_str
                    or "23505" in error_str
            ):
                logger.info(
                    f"Opportunity {opportunity_id} already saved by user {user_id}"
                )
                return {
                    "success": True,
                    "message": "Opportunity already saved",
                    "already_saved": True,
                }

            logger.error(f"Error saving opportunity: {str(e)}")
            return {"success": False, "error": str(e)}

    def unsave_opportunity(self, user_id: str, opportunity_id: int) -> Dict[str, Any]:
        """
        Remove an opportunity from user's saved list.

        Args:
            user_id: The user's ID
            opportunity_id: The opportunity's ID

        Returns:
            Success/error response
        """
        try:
            response = (
                self.service_client.table("saved_opportunities")
                .delete()
                .eq("user_id", user_id)
                .eq("opportunity_id", opportunity_id)
                .execute()
            )

            logger.info(
                f"Opportunity {opportunity_id} removed from saved by user {user_id}"
            )
            return {"success": True, "message": "Opportunity removed from saved items"}

        except Exception as e:
            logger.error(f"Error removing saved opportunity: {str(e)}")
            return {"success": False, "error": str(e)}

    def save_profile(self, user_id: str, profile_id: str) -> Dict[str, Any]:
        """
        Save/bookmark a student profile for an organization.

        Args:
            user_id: The organization's user ID
            profile_id: The student profile's ID

        Returns:
            Success/error response
        """
        try:
            # Try to save the profile - if it already exists, handle gracefully
            response = (
                self.service_client.table("saved_profiles")
                .insert({"user_id": user_id, "profile_id": profile_id})
                .execute()
            )

            if response.data:
                logger.info(f"Profile {profile_id} saved by user {user_id}")
                return {"success": True, "message": "Profile saved successfully"}
            else:
                return {"success": False, "error": "Failed to save profile"}

        except Exception as e:
            # Check if it's a duplicate key constraint error
            error_str = str(e)
            if (
                    "duplicate key value violates unique constraint" in error_str
                    or "23505" in error_str
            ):
                logger.info(f"Profile {profile_id} already saved by user {user_id}")
                return {
                    "success": True,
                    "message": "Profile already saved",
                    "already_saved": True,
                }

            logger.error(f"Error saving profile: {str(e)}")
            return {"success": False, "error": str(e)}

    def unsave_profile(self, user_id: str, profile_id: str) -> Dict[str, Any]:
        """
        Remove a profile from user's saved list.

        Args:
            user_id: The user's ID
            profile_id: The profile's ID

        Returns:
            Success/error response
        """
        try:
            response = (
                self.service_client.table("saved_profiles")
                .delete()
                .eq("user_id", user_id)
                .eq("profile_id", profile_id)
                .execute()
            )

            logger.info(f"Profile {profile_id} removed from saved by user {user_id}")
            return {"success": True, "message": "Profile removed from saved items"}

        except Exception as e:
            logger.error(f"Error removing saved profile: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_saved_opportunities(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all saved opportunities for a user.

        Args:
            user_id: The user's ID

        Returns:
            List of saved opportunity records with opportunity details
        """
        try:
            response = (
                self.service_client.table("saved_opportunities")
                .select(
                    "*, opportunities(*, profiles!company_id(name, organization_name, email))"
                )
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error getting saved opportunities: {str(e)}")
            return []

    def get_saved_profiles(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all saved profiles for an organization.

        Args:
            user_id: The organization's user ID

        Returns:
            List of saved profile records with profile details
        """
        try:
            response = (
                self.service_client.table("saved_profiles")
                .select("*, profiles(*)")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error getting saved profiles: {str(e)}")
            return []

    def is_opportunity_saved(self, user_id: str, opportunity_id: int) -> bool:
        """
        Check if an opportunity is already saved by a user.

        Args:
            user_id: The user's ID
            opportunity_id: The opportunity's ID

        Returns:
            True if saved, False otherwise
        """
        try:
            response = (
                self.service_client.table("saved_opportunities")
                .select("id")
                .eq("user_id", user_id)
                .eq("opportunity_id", opportunity_id)
                .execute()
            )

            return response.data and len(response.data) > 0

        except Exception as e:
            logger.error(f"Error checking saved opportunity: {str(e)}")
            return False

    def is_profile_saved(self, user_id: str, profile_id: str) -> bool:
        """
        Check if a profile is already saved by a user.

        Args:
            user_id: The user's ID
            profile_id: The profile's ID

        Returns:
            True if saved, False otherwise
        """
        try:
            response = (
                self.service_client.table("saved_profiles")
                .select("id")
                .eq("user_id", user_id)
                .eq("profile_id", profile_id)
                .execute()
            )

            return response.data and len(response.data) > 0

        except Exception as e:
            logger.error(f"Error checking saved profile: {str(e)}")
            return False

    # Storage Management Methods
    def create_profile_picture_bucket(self) -> Dict[str, Any]:
        """
        Create the profile pictures bucket with appropriate settings.

        Returns:
            Success/error response
        """
        try:
            # Create bucket for profile pictures
            response = self.service_client.storage.create_bucket(
                "profile-pictures",
                {
                    "public": True,  # Public bucket for easy serving
                    "allowedMimeTypes": [
                        "image/jpeg",
                        "image/png",
                        "image/webp",
                        "image/gif",
                    ],
                    "fileSizeLimit": 5242880,  # 5MB in bytes
                },
            )

            logger.info(f"Bucket creation response: {response}")

            if response:
                logger.info("Profile pictures bucket created successfully")
                return {"success": True, "data": response}
            else:
                return {"success": False, "error": "Failed to create bucket"}

        except Exception as e:
            # Bucket might already exist
            error_str = str(e)
            if (
                    "already exists" in error_str.lower()
                    or "duplicate" in error_str.lower()
            ):
                logger.info("Profile pictures bucket already exists")
                return {"success": True, "message": "Bucket already exists"}

            logger.error(f"Error creating profile pictures bucket: {str(e)}")
            return {"success": False, "error": str(e)}

    def _extract_file_path_from_url(self, image_url: str) -> Optional[str]:
        """
        Extract the file path from a Supabase storage URL.

        Args:
            image_url: The full public URL to the image

        Returns:
            The file path within the bucket or None if invalid
        """
        try:
            if not image_url:
                return None

            # Handle different URL formats
            if "/profile-pictures/" in image_url:
                # Extract everything after /profile-pictures/
                path = image_url.split("/profile-pictures/")[-1]
                # Remove query parameters if present
                if "?" in path:
                    path = path.split("?")[0]
                return path

            return None
        except Exception:
            return None

    def _delete_existing_profile_image(self, user_id: str) -> bool:
        """
        Delete the user's existing profile image from storage (internal helper).

        Args:
            user_id: The user's ID

        Returns:
            True if deleted or no image existed, False if error
        """
        try:
            # Method 1: Try to get existing image from profile
            profile = self.get_profile(user_id)
            if profile and profile.get("profile_image"):
                file_path = self._extract_file_path_from_url(profile["profile_image"])
                if file_path:
                    try:
                        response = self.service_client.storage.from_(
                            "profile-pictures"
                        ).remove([file_path])
                        logger.info(
                            f"Deleted existing profile image from profile data: {file_path}"
                        )
                        return True
                    except Exception as e:
                        logger.warning(f"Failed to delete image from profile data: {e}")

            # Method 2: List and clean up all images in user's folder (fallback)
            # This handles cases where profile DB entry might be missing but files exist
            safe_user_id = user_id.replace("/", "_").replace("\\", "_")
            try:
                # List files in the user's folder
                files_response = self.service_client.storage.from_(
                    "profile-pictures"
                ).list(safe_user_id)

                if files_response and len(files_response) > 0:
                    # Delete all existing profile images for this user
                    file_paths = [
                        f"{safe_user_id}/{file['name']}"
                        for file in files_response
                        if file.get("name")
                    ]
                    if file_paths:
                        response = self.service_client.storage.from_(
                            "profile-pictures"
                        ).remove(file_paths)
                        logger.info(
                            f"Cleaned up {len(file_paths)} existing files for user {user_id}: {file_paths}"
                        )

            except Exception as e:
                logger.info(f"No existing files to clean up for user {user_id}: {e}")

            return True  # Always return True to not block uploads

        except Exception as e:
            logger.warning(f"Error during cleanup for user {user_id}: {str(e)}")
            return True  # Don't fail the upload because of cleanup error

    def upload_profile_picture(
            self, user_id: str, file_data: bytes, file_name: str, content_type: str = None
    ) -> Dict[str, Any]:
        """
        Upload a profile picture for a user.

        Args:
            user_id: The user's ID
            file_data: The image file data
            file_name: Original file name
            content_type: MIME type of the file

        Returns:
            Success/error response with file URL
        """
        try:
            # Validate inputs
            if not isinstance(user_id, str) or not user_id.strip():
                return {"success": False, "error": "Invalid user_id"}

            if not isinstance(file_name, str) or not file_name.strip():
                return {"success": False, "error": "Invalid file_name"}

            if not isinstance(file_data, bytes) or len(file_data) == 0:
                return {"success": False, "error": "Invalid file_data"}

            # STEP 1: Delete existing profile image before uploading new one
            logger.info(f"Deleting existing profile image for user: {user_id}")
            self._delete_existing_profile_image(user_id)

            # Generate unique filename with user folder structure
            import uuid
            import os

            # Extract file extension
            file_ext = os.path.splitext(file_name)[1].lower()
            if not file_ext:
                file_ext = ".jpg"  # Default extension

            # Create unique filename: user_id/profile_uuid.ext
            # Ensure filename is safe for URLs
            safe_user_id = user_id.replace("/", "_").replace("\\", "_")
            unique_filename = f"{safe_user_id}/profile_{uuid.uuid4().hex}{file_ext}"

            # Upload to storage
            # Ensure content_type is a valid string
            if not content_type or not isinstance(content_type, str):
                # Default content type based on file extension
                content_type_map = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".webp": "image/webp",
                    ".gif": "image/gif",
                }
                content_type = content_type_map.get(file_ext, "image/jpeg")

            # Debug logging
            logger.info(
                f"Upload parameters - filename: {unique_filename}, content_type: {content_type}, file_size: {len(file_data)}"
            )

            # Try upload - use the correct parameter format for supabase-py
            upload_options = {}
            if content_type and isinstance(content_type, str) and content_type.strip():
                upload_options["content_type"] = content_type.strip()

            response = self.service_client.storage.from_("profile-pictures").upload(
                path=unique_filename,
                file=file_data,
                file_options={
                    "content-type": upload_options.get(
                        "content_type", "application/octet-stream"
                    ),
                    "upsert": "true",
                },
            )

            if response:
                # Get public URL for the uploaded image
                public_url = self.service_client.storage.from_(
                    "profile-pictures"
                ).get_public_url(unique_filename)

                # Update user profile with new image URL
                profile_update_result = self.update_profile(
                    user_id, {"profile_image": public_url}
                )

                if profile_update_result["success"]:
                    logger.info(
                        f"Profile picture uploaded and profile updated for user: {user_id}"
                    )
                    return {
                        "success": True,
                        "url": public_url,
                        "path": unique_filename,
                        "message": "Profile picture uploaded successfully",
                    }
                else:
                    # Upload succeeded but profile update failed
                    logger.warning(
                        f"Profile picture uploaded but profile update failed for user: {user_id}"
                    )
                    return {
                        "success": True,
                        "url": public_url,
                        "path": unique_filename,
                        "warning": "Image uploaded but profile update failed",
                    }
            else:
                return {"success": False, "error": "Failed to upload image"}

        except Exception as e:
            logger.error(f"Error uploading profile picture: {str(e)}")
            return {"success": False, "error": str(e)}

    def delete_profile_picture(
            self, user_id: str, file_path: str = None
    ) -> Dict[str, Any]:
        """
        Delete a user's profile picture from storage.

        Args:
            user_id: The user's ID
            file_path: Optional specific file path to delete

        Returns:
            Success/error response
        """
        try:
            # If no specific path provided, get current profile image
            if not file_path:
                profile = self.get_profile(user_id)
                if not profile or not profile.get("profile_image"):
                    return {"success": True, "message": "No profile image to delete"}

                # Extract path from URL using helper function
                file_path = self._extract_file_path_from_url(profile["profile_image"])
                if not file_path:
                    logger.warning(
                        f"Could not extract file path from URL: {profile['profile_image']}"
                    )
                    # Still update profile to remove the invalid URL
                    profile_update_result = self.update_profile(
                        user_id, {"profile_image": None}
                    )
                    return {
                        "success": True,
                        "message": "Profile image URL cleared (file may have been already deleted)",
                    }

            # Delete from storage
            logger.info(f"Deleting profile image from storage: {file_path}")
            response = self.service_client.storage.from_("profile-pictures").remove(
                [file_path]
            )
            logger.info(f"Storage delete response: {response}")

            # Update profile to remove image URL
            profile_update_result = self.update_profile(
                user_id, {"profile_image": None}
            )

            if profile_update_result["success"]:
                logger.info(f"Profile picture deleted successfully for user: {user_id}")
                return {
                    "success": True,
                    "message": "Profile picture deleted successfully",
                }
            else:
                logger.warning(
                    f"File deleted from storage but profile update failed: {profile_update_result}"
                )
                return {
                    "success": True,
                    "message": "Profile picture deleted from storage, but profile update failed",
                }

        except Exception as e:
            logger.error(f"Error deleting profile picture: {str(e)}")
            # Still try to update profile to clear the image URL
            try:
                self.update_profile(user_id, {"profile_image": None})
            except:
                pass
            return {"success": False, "error": str(e)}

    def get_profile_picture_url(self, user_id: str) -> Optional[str]:
        """
        Get the public URL for a user's profile picture.

        Args:
            user_id: The user's ID

        Returns:
            Public URL or None if no image
        """
        try:
            profile = self.get_profile(user_id)
            if profile and profile.get("profile_image"):
                return profile["profile_image"]
            return None

        except Exception as e:
            logger.error(f"Error getting profile picture URL: {str(e)}")
            return None

    # --- Chat History Management ---

    def save_chat_message(self, user_id: str, role: str, content: str) -> Dict[str, Any]:
        """
        Save a chat message to the database.
        
        Args:
            user_id: The user's ID
            role: 'user' or 'assistant'
            content: The message content
            
        Returns:
            Success/error response
        """
        try:
            message_data = {
                "user_id": user_id,
                "role": role,
                "content": content,
                "created_at": datetime.now().isoformat()
            }
            
            response = self.service_client.table("chat_history").insert(message_data).execute()
            
            if response.data:
                return {"success": True, "data": response.data[0]}
            else:
                return {"success": False, "error": "Failed to save chat message"}
                
        except Exception as e:
            logger.error(f"Error saving chat message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get chat history for a user.
        
        Args:
            user_id: The user's ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of chat messages
        """
        try:
            response = (
                self.service_client.table("chat_history")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=False)
                .limit(limit)
                .execute()
            )
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            return []
    
    def get_user_prompt_count(self, user_id: str) -> int:
        """
        Get the total number of prompts a user has sent.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Total number of prompts sent
        """
        try:
            response = (
                self.service_client.table("chat_history")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("role", "user")
                .execute()
            )
            
            return response.count if response.count else 0
            
        except Exception as e:
            logger.error(f"Error getting user prompt count: {str(e)}")
            return 0
    
    def clear_chat_history(self, user_id: str) -> Dict[str, Any]:
        """
        Clear all chat history for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Success/error response
        """
        try:
            response = (
                self.service_client.table("chat_history")
                .delete()
                .eq("user_id", user_id)
                .execute()
            )
            
            return {"success": True, "message": "Chat history cleared"}
            
        except Exception as e:
            logger.error(f"Error clearing chat history: {str(e)}")
            return {"success": False, "error": str(e)}

    # --- Skills Management ---

    def add_new_skill(self, skill_name: str, user_id: str = None) -> Dict[str, Any]:
        """
        Add a new skill to the skills table.

        Args:
            skill_name: The name of the skill to add
            user_id: The user adding the skill (optional)

        Returns:
            Dictionary with success status and skill data or error
        """
        try:
            # Check if skill already exists (case-insensitive)
            existing_response = (
                self.service_client.table("skills")
                .select("id, name")
                .ilike("name", skill_name)
                .execute()
            )

            if existing_response.data:
                return {
                    "success": False,
                    "error": "Skill already exists",
                    "existing_skill": existing_response.data[0]["name"],
                }

            # Add the new skill
            skill_data = {"name": skill_name.strip(), "created_by": user_id}

            response = self.service_client.table("skills").insert(skill_data).execute()

            if response.data:
                return {"success": True, "skill": response.data[0]}
            else:
                return {"success": False, "error": "Failed to add skill"}

        except Exception as e:
            logger.error(f"Error adding new skill: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_all_skills(self) -> List[str]:
        """
        Get all available skills from the database.

        Returns:
            List of skill names
        """
        try:
            response = (
                self.client.table("skills")
                .select("name")
                .order("name", desc=False)
                .execute()
            )

            if response.data:
                return [skill["name"] for skill in response.data]
            else:
                return []

        except Exception as e:
            logger.error(f"Error getting all skills: {str(e)}")
            return []

    def skill_exists(self, skill_name: str) -> bool:
        """
        Check if a skill exists in the database (case-insensitive).

        Args:
            skill_name: The skill name to check

        Returns:
            True if skill exists, False otherwise
        """
        try:
            response = (
                self.client.table("skills")
                .select("id")
                .ilike("name", skill_name)
                .limit(1)
                .execute()
            )

            return len(response.data) > 0

        except Exception as e:
            logger.error(f"Error checking if skill exists: {str(e)}")
            return False


# Global instance - will be created in app.py after environment variables are loaded
# supabase_service = SupabaseService()

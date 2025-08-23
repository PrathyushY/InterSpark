"""
Supabase configuration and service module for InterSpark Flask application.
Handles authentication, user management, and database operations.
"""

import os
from supabase import create_client, Client
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import logging

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

    # Authentication Methods
    def create_user(
        self, email: str, password: str, user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new user account with profile data.

        Args:
            email: User's email address
            password: User's password
            user_data: Additional profile data (name, user_type, etc.)

        Returns:
            Dictionary containing user data or error information
        """
        try:
            # Create user in auth.users table
            response = self.client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "name": user_data.get("name", ""),
                            "user_type": user_data.get("user_type", "student"),
                        }
                    },
                }
            )

            if response.user:
                logger.info(f"User created successfully in auth: {response.user.id}")

                # Explicitly create profile in profiles table
                # The trigger should handle this, but let's ensure it exists
                profile_data = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "name": user_data.get("name", ""),
                    "user_type": user_data.get("user_type", "student"),
                }

                try:
                    # Try to create the profile directly
                    profile_response = (
                        self.service_client.table("profiles")
                        .insert(profile_data)
                        .execute()
                    )
                    if profile_response.data:
                        logger.info(f"Profile created successfully: {response.user.id}")
                    else:
                        logger.warning(
                            f"Profile creation may have failed, but user was created: {response.user.id}"
                        )
                except Exception as profile_error:
                    # This might fail if the trigger already created it, which is fine
                    logger.info(
                        f"Profile creation via insert failed (trigger may have handled it): {str(profile_error)}"
                    )

                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "created_at": response.user.created_at,
                    },
                    "session": response.session,
                }
            else:
                logger.error("Failed to create user - no user returned")
                return {"success": False, "error": "Failed to create user"}

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return {"success": False, "error": str(e)}

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
    ) -> List[Dict[str, Any]]:
        """
        Search for student profiles with filters.

        Args:
            search_query: Text to search in name and bio
            skills: Filter by skills
            school: Filter by school
            grade: Filter by grade

        Returns:
            List of matching student profiles
        """
        try:
            query = self.client.table("profiles").select("*").eq("user_type", "student")

            # Apply text search if provided
            if search_query:
                query = query.or_(
                    f"name.ilike.%{search_query}%,bio.ilike.%{search_query}%"
                )

            # Apply skills filter
            if skills:
                query = query.ilike("skills", f"%{skills}%")

            # Apply school filter
            if school:
                query = query.ilike("school", f"%{school}%")

            # Apply grade filter
            if grade:
                query = query.ilike("grade", f"%{grade}%")

            # Order by creation date, newest first
            query = query.order("created_at", desc=True)

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error searching students: {str(e)}")
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
        self, search_query: str = "", opportunity_type: str = "", location: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Search opportunities with text and filters.

        Args:
            search_query: Text to search in title and description
            opportunity_type: Filter by opportunity type
            location: Filter by location

        Returns:
            List of matching opportunity records
        """
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

            # Apply location filter
            if location:
                query = query.ilike("location", f"%{location}%")

            # Only show active opportunities
            query = query.eq("status", "active")

            # Order by creation date, newest first
            query = query.order("created_at", desc=True)

            response = query.execute()
            return response.data if response.data else []

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

    def get_organization_opportunities(
        self, organization_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all opportunities for a specific organization.

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
            return []  # Application Management Methods (for future use)

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


# Global instance
supabase_service = SupabaseService()

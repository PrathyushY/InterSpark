import json
import logging
import os
from datetime import datetime
from typing import Dict, Any

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

from ai_service import AIService
from supabase_config import SupabaseService

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce verbosity of third-party libraries in production
# This helps prevent Vercel from flagging routine logs as errors
if os.getenv("FLASK_ENV") != "development":
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("supabase_config").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)


def get_all_available_skills():
    """Get all available skills from database only."""
    try:
        db_skills = supabase_service.get_all_skills()
        return sorted(db_skills)
    except Exception as e:
        logger.error(f"Error loading skills from database: {e}")
        return []  # Return empty list if DB fails


def normalize_and_validate_skills(value):
    """
    Normalize input to a list of valid, non-empty, stripped skills.
    Now checks only against database skills.
    """
    if value is None:
        return []

    # Get all valid skills from database only
    try:
        all_valid_skills = set(supabase_service.get_all_skills())
    except Exception as e:
        logger.error(f"Could not load skills from database: {e}")
        all_valid_skills = set()

    if isinstance(value, list):
        return [
            s.strip()
            for s in value
            if isinstance(s, str) and s.strip() in all_valid_skills
        ]
    if isinstance(value, str):
        try:
            loaded = json.loads(value)
            if isinstance(loaded, list):
                return [
                    s.strip()
                    for s in loaded
                    if isinstance(s, str) and s.strip() in all_valid_skills
                ]
        except Exception:
            pass
        # Comma-separated string
        if "," in value:
            return [
                s.strip() for s in value.split(",") if s.strip() in all_valid_skills
            ]
        val = value.strip()
        return [val] if val in all_valid_skills else []
    return []


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "2a15f8283ab2353f15089e80d8acf104")

# Initialize services after environment variables are loaded
supabase_service = SupabaseService()

# Initialize AI service with error handling
try:
    ai_service = AIService()  # Modern SDK automatically picks up GEMINI_API_KEY
except ValueError as e:
    logger.warning(f"AI service not available: {e}")
    ai_service = None


def fallback_search(query: str, supabase_service) -> Dict[str, Any]:
    """
    Fallback search function when AI service is not available.
    Performs basic keyword-based search.
    """
    try:
        results = {"profiles": [], "opportunities": [], "total_matches": 0}

        # Simple keyword extraction
        query_lower = query.lower()
        skills_to_search = []

        # Common skill keywords
        skill_keywords = {
            "python": ["python", "py"],
            "javascript": ["javascript", "js", "node"],
            "react": ["react", "reactjs"],
            "java": ["java"],
            "html": ["html"],
            "css": ["css"],
            "sql": ["sql", "database"],
            "machine learning": [
                "machine learning",
                "ml",
                "ai",
                "artificial intelligence",
            ],
            "data science": ["data science", "data analysis"],
            "web development": ["web development", "web dev", "frontend", "backend"],
        }

        # Extract skills from query
        for skill, keywords in skill_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                skills_to_search.append(skill)

        # Search profiles
        profile_results = supabase_service.search_students_enhanced(
            search_query=query,
            skills=",".join(skills_to_search) if skills_to_search else "",
            school="",
            grade="",
            location="",
        )

        # Search opportunities
        opportunity_results = supabase_service.search_opportunities(
            search_query=query,
            opportunity_type="",
            category="",
            location="",
            skills_needed=",".join(skills_to_search) if skills_to_search else "",
        )

        results["profiles"] = profile_results[:5]
        results["opportunities"] = opportunity_results[:5]
        results["total_matches"] = len(profile_results) + len(opportunity_results)

        return results

    except Exception as e:
        logger.error(f"Error in fallback search: {str(e)}")
        return {"profiles": [], "opportunities": [], "total_matches": 0}


def generate_fallback_response(user_message: str, db_results: Dict[str, Any]) -> str:
    """
    Generate a fallback response when AI service is not available.
    """
    try:
        response_parts = []

        if db_results["total_matches"] > 0:
            response_parts.append("I found some relevant results for you:")

            if db_results["profiles"]:
                response_parts.append("\n**Student Profiles:**")
                for profile in db_results["profiles"]:
                    name = profile.get("name", "Unknown")
                    school = profile.get("school", "Unknown school")
                    skills = profile.get("skills", [])
                    if isinstance(skills, str):
                        try:
                            skills = json.loads(skills)
                        except:
                            skills = [skills] if skills else []

                    response_parts.append(f"- **{name}** from {school}")
                    if skills:
                        response_parts.append(f"  Skills: {', '.join(skills[:5])}")
                    response_parts.append(f"  [View Profile](/profile/{profile['id']})")

            if db_results["opportunities"]:
                response_parts.append("\n**Opportunities:**")
                for opp in db_results["opportunities"]:
                    title = opp.get("title", "Unknown title")
                    org_name = "Unknown organization"
                    if opp.get("profiles"):
                        org_name = opp["profiles"].get("name", org_name)

                    response_parts.append(f"- **{title}** at {org_name}")
                    response_parts.append(
                        f"  [View Opportunity](/opportunity/{opp['id']})"
                    )
        else:
            response_parts.append(
                "I didn't find any matching profiles or opportunities for your query."
            )
            response_parts.append(
                "Try rephrasing your request or being more specific about the skills or type of opportunity you're looking for."
            )

        return "\n".join(response_parts)

    except Exception as e:
        logger.error(f"Error generating fallback response: {str(e)}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again later."


def check_profile_completion():
    """
    Check if the current user's profile is complete.
    Redirect to profile page if incomplete (except for certain routes).
    """
    # Skip profile check for these routes
    exempt_routes = ["profile", "logout", "static", "login", "signup", "home"]

    if request.endpoint in exempt_routes:
        return

    # Only check for logged-in users
    if "user_id" not in session:
        return

    try:
        user_id = session.get("user_id")
        user_type = session.get("user_type")

        profile = supabase_service.get_profile(user_id)
        if profile:
            completion_check = supabase_service.is_profile_complete(profile, user_type)

            if not completion_check["complete"]:
                # Only redirect if not already on profile page to prevent infinite loop
                if request.endpoint != "profile":
                    missing_fields_str = ", ".join(completion_check["missing_fields"])
                    flash(
                        f"Please complete your profile. Missing: {missing_fields_str}",
                        "warning",
                    )
                    return redirect(url_for("profile"))

    except Exception as e:
        # Log error but don't block navigation
        print(f"Profile completion check error: {str(e)}")


# Apply the profile completion check before each request
app.before_request(check_profile_completion)


# Custom template filter for date formatting
@app.template_filter("format_date")
def format_date_filter(date_string, format="%B %d, %Y"):
    """
    Format an ISO date string to a readable format.

    Args:
        date_string: ISO format date string from database
        format: strftime format string

    Returns:
        Formatted date string or 'Recently' if parsing fails
    """
    if not date_string:
        return "Recently"

    try:
        # Parse ISO format: 2025-08-21T23:02:27.393868+00:00
        dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        return dt.strftime(format)
    except (ValueError, AttributeError):
        # Fallback: just return the date part if it's already formatted
        try:
            return date_string.split("T")[0]
        except:
            return "Recently"


@app.context_processor
def inject_user_profile():
    """
    Make current user's profile data available in all templates.
    This includes profile image for navbar display.
    """
    if "user_id" in session:
        try:
            user_profile = supabase_service.get_profile(session["user_id"])
            if user_profile:
                return {"current_user_profile": user_profile}
        except Exception as e:
            # Log error but don't break the template rendering
            print(f"Error loading user profile for navbar: {str(e)}")

    return {"current_user_profile": None}


@app.route("/")
def home():
    # Redirect logged-in users to dashboard
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    # Get featured opportunities from database
    try:
        opportunities = supabase_service.get_opportunities(limit=3)
        return render_template("home.html", opportunities=opportunities)
    except Exception as e:
        flash(f"Error loading opportunities: {str(e)}", "error")
        return render_template("home.html", opportunities=[])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Authenticate user credentials
        try:
            auth_result = supabase_service.authenticate_user(email, password)

            if auth_result["success"]:
                user = auth_result["user"]
                profile = auth_result["profile"]

                # Check if profile exists and has user_type
                if profile and profile.get("user_type"):
                    # Check if email is confirmed
                    if profile.get(
                        "email_confirmed", True
                    ):  # Default to True for existing users
                        session["user_id"] = user["id"]
                        session["user_type"] = profile["user_type"]
                        session["user_name"] = profile["name"]
                        session["user_email"] = profile["email"]

                        flash("Login successful!", "success")
                        return redirect(url_for("dashboard"))
                    else:
                        flash(
                            "Please verify your email address before logging in. Check your email for the verification link.",
                            "warning",
                        )
                        return render_template("login.html")
                elif profile and profile.get("name") == "User":
                    # This is a newly created default profile, redirect to complete profile
                    if profile.get("email_confirmed", True):  # Check email confirmation
                        session["user_id"] = user["id"]
                        session["user_type"] = "student"  # Default to student
                        session["user_name"] = profile["name"]
                        session["user_email"] = profile["email"]

                        flash("Please complete your profile to continue.", "info")
                        return redirect(url_for("profile"))
                    else:
                        flash(
                            "Please verify your email address before completing your profile. Check your email for the verification link.",
                            "warning",
                        )
                        return render_template("login.html")
                else:
                    if not profile:
                        flash(
                            "User profile not found. Please contact support.", "error"
                        )
                    else:
                        flash(
                            "Profile incomplete. Please complete your profile.",
                            "warning",
                        )
                        if profile.get(
                            "email_confirmed", True
                        ):  # Check email confirmation
                            session["user_id"] = user["id"]
                            session["user_type"] = profile.get("user_type", "student")
                            session["user_name"] = profile.get("name", "User")
                            session["user_email"] = profile.get("email", email)
                            return redirect(url_for("profile"))
                        else:
                            flash(
                                "Please verify your email address before completing your profile. Check your email for the verification link.",
                                "warning",
                            )
                            return render_template("login.html")
            else:
                error_message = auth_result.get("error", "Invalid credentials")
                if (
                    "email" in error_message.lower()
                    and "confirm" in error_message.lower()
                ):
                    flash(
                        "Please check your email and click the verification link to activate your account.",
                        "warning",
                    )
                else:
                    flash(error_message, "error")

        except Exception as e:
            flash(f"Login error: {str(e)}", "error")

    return render_template("login.html")


@app.route("/auth/google")
def auth_google():
    """Redirect to Supabase OAuth authorize endpoint for Google.

    Accepts optional query param user_type (student|organization) so we can
    remember which account type the user wants to create.
    """
    user_type = request.args.get("user_type", "student")
    supabase_url = os.getenv("SUPABASE_URL")
    site_url = os.getenv("SITE_URL", "http://localhost:5000")
    # Supabase authorize endpoint - use redirect_to to our /auth/callback
    redirect_to = f"{site_url}/auth/callback?user_type={user_type}"
    authorize_url = (
        f"{supabase_url}/auth/v1/authorize?provider=google&redirect_to={redirect_to}"
    )
    return redirect(authorize_url)


@app.route("/auth/callback")
def auth_callback():
    """Simple page that receives the OAuth fragment from Supabase and posts it to the server.

    Supabase returns tokens in the URL fragment (after #). The page will parse them
    client-side using a small script and POST to /auth/complete where the server
    will verify the token and create/ensure a profile with the selected user_type.
    """
    # user_type is passed in query string from our auth_google redirect
    user_type = request.args.get("user_type", "student")
    return render_template("auth_callback.html", user_type=user_type)


@app.route("/auth/complete", methods=["POST"])
def auth_complete():
    """Finalize OAuth sign-in: accept access_token from client, verify it with Supabase,
    ensure a profile exists, set Flask session, and redirect accordingly.
    """
    data = request.get_json() or {}
    access_token = data.get("access_token")
    user_type = data.get("user_type", "student")

    if not access_token:
        return jsonify({"success": False, "error": "Missing access_token"}), 400

    try:
        # Use supabase service helper to get user info from token
        user_info = supabase_service.get_user_by_token(access_token)
        if not user_info or not user_info.get("id"):
            return jsonify({"success": False, "error": "Could not validate token"}), 400

        user_id = user_info["id"]
        email = user_info.get("email")
        name = (
            user_info.get("user_metadata", {}).get("name")
            or user_info.get("email", "").split("@")[0]
        )

        # Extract Google profile picture URL from user metadata
        profile_image = None
        user_metadata = user_info.get("user_metadata", {})

        # Google OAuth typically provides the profile picture in these fields
        if "picture" in user_metadata:
            profile_image = user_metadata["picture"]
        elif "avatar_url" in user_metadata:
            profile_image = user_metadata["avatar_url"]
        elif "profile_picture" in user_metadata:
            profile_image = user_metadata["profile_picture"]

        # Log the extracted profile image for debugging
        if profile_image:
            logger.info(
                f"Extracted Google profile picture for user {user_id}: {profile_image}"
            )
        else:
            logger.info(f"No profile picture found in user metadata for user {user_id}")
            logger.debug(f"User metadata: {user_metadata}")

        # Ensure profile exists with the requested user_type and profile image
        supabase_service.ensure_profile_exists(
            user_id, email, name, user_type, profile_image
        )

        # Set Flask session
        session["user_id"] = user_id
        session["user_type"] = user_type
        session["user_name"] = name
        session["user_email"] = email

        # Check profile completion and redirect accordingly
        profile = supabase_service.get_profile(user_id)
        completion = supabase_service.is_profile_complete(profile, user_type)
        if not completion["complete"]:
            # Send the client to the signup completion page where they can fill
            # in student/organization specific fields. The client will navigate
            # to this URL after receiving the JSON response.
            return (
                jsonify(
                    {
                        "success": True,
                        "redirect": url_for("signup_complete", user_type=user_type),
                    }
                ),
                200,
            )

        return jsonify({"success": True, "redirect": url_for("dashboard")}), 200

    except Exception as e:
        logger.error(f"Error completing OAuth sign-in: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/signup/complete", methods=["GET", "POST"])
def signup_complete():
    """Page to complete profile after OAuth sign-up.

    Renders a student or organization specific form prefilled with info from
    the authenticated user session (set during OAuth completion).
    """
    if "user_id" not in session:
        flash("Please sign in first using Google or email/password.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user_type = request.args.get("user_type", session.get("user_type", "student"))

    if request.method == "POST":
        # Collect profile updates depending on user_type
        profile_updates = {}
        profile_updates["name"] = request.form.get("name")
        # Email should already be set from OAuth, but allow override
        profile_updates["email"] = request.form.get("email")

        if user_type == "student":
            profile_updates["school"] = request.form.get("school")
            profile_updates["grade"] = request.form.get("grade")
            profile_updates["bio"] = request.form.get("bio")
        else:
            profile_updates["description"] = request.form.get("description")
            profile_updates["organization_name"] = request.form.get("organization_name")

        profile_updates["user_type"] = user_type

        try:
            res = supabase_service.update_profile(user_id, profile_updates)
            flash("Profile updated successfully.", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Error updating profile: {e}", "error")

    # GET: render form prefilled from profile
    profile = supabase_service.get_profile(user_id) or {}
    # Prefill from session if available
    prefill = {
        "name": session.get("user_name") or profile.get("name", ""),
        "email": session.get("user_email") or profile.get("email", ""),
    }
    return render_template(
        "signup_complete.html", user_type=user_type, profile=profile, prefill=prefill
    )


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form.get("confirm_password", "")
        user_type = request.form["user_type"]

        # Basic validation
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("signup.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long", "error")
            return render_template("signup.html")

        # Collect additional required fields based on user type
        user_data = {"name": name, "user_type": user_type}

        if user_type == "student":
            school = request.form.get("school", "").strip()
            grade = request.form.get("grade", "").strip()

            # Validate required student fields
            if not school or not grade:
                flash(
                    "Please fill in all required fields: School and Grade",
                    "error",
                )
                return render_template("signup.html")

            user_data.update({"school": school, "grade": grade})

        elif user_type == "organization":
            description = request.form.get("description", "").strip()

            # Validate required organization fields
            if not description:
                flash("Please fill in the organization description", "error")
                return render_template("signup.html")

            user_data.update(
                {
                    "description": description,
                    "organization_name": name,  # Set organization_name same as name
                }
            )

        # Create user with custom email verification
        try:
            # Try user creation with our custom email verification
            result = supabase_service.create_user(email, password, user_data)

            if result["success"]:
                user = result["user"]
                user_id = user["id"]

                # Send our custom verification email
                logger.info(
                    f"User created successfully: {user_id}, sending custom verification email"
                )

                email_result = supabase_service.send_verification_email(user_id, email)

                if email_result["success"]:
                    verification_link = email_result["verification_link"]
                    expires_at = email_result["expires_at"]
                    email_sent = email_result.get("email_sent", False)

                    if email_sent:
                        flash(
                            "Registration successful! Please check your email and click the verification link to activate your account. "
                            f"The verification link will expire in 24 hours.",
                            "info",
                        )
                        logger.info(
                            f"User {email} registered with secure verification token - email sent successfully"
                        )
                        # Don't show development link when email is sent successfully
                    else:
                        flash(
                            "Registration successful! Email verification system is temporarily unavailable. "
                            "Please use the manual verification link below.",
                            "warning",
                        )
                        logger.warning(
                            f"User {email} registered with secure verification token - email could not be sent"
                        )

                    logger.info(f"Verification link: {verification_link}")
                else:
                    # Fallback to manual confirmation if token creation fails
                    site_url = os.getenv("SITE_URL", "http://localhost:5001")
                    manual_confirmation_link = (
                        f"{site_url}/auth/confirm-manual?email={email}"
                    )

                    flash(
                        "Registration successful! Email verification system is temporarily unavailable. "
                        f'You can confirm manually here: <a href="{manual_confirmation_link}" target="_blank">Confirm Email</a>',
                        "warning",
                    )
                    logger.warning(
                        f"Failed to create verification token for {email}, using manual fallback"
                    )

                return redirect(url_for("login"))
            else:
                error_message = result.get("error", "Registration failed")
                flash(error_message, "error")
                logger.error(f"User creation failed for {email}: {error_message}")

        except Exception as e:
            flash(f"Registration error: {str(e)}", "error")
            logger.error(f"Registration exception for {email}: {str(e)}")

    return render_template("signup.html")


@app.route("/auth/confirm")
def confirm_email():
    """Handle email confirmation after user clicks the link in their email."""
    try:
        # If this is the initial request (no query parameters), serve the processing page
        # This page will handle URL hash fragments and redirect back with query parameters
        if not request.args:
            return render_template("auth_confirm.html")

        # Check for error parameters first (these come in the URL fragment, but may be passed as query params)
        error = request.args.get("error")
        error_code = request.args.get("error_code")
        error_description = request.args.get("error_description")

        if error:
            # Handle various error cases
            if error_code == "otp_expired":
                flash(
                    "The email verification link has expired. Please request a new verification email below.",
                    "error",
                )
            elif error == "access_denied":
                flash(
                    "Email verification was denied or cancelled. Please try again.",
                    "error",
                )
            else:
                flash(
                    f"Email verification failed: {error_description or error}. Please try again.",
                    "error",
                )
            return redirect(url_for("login"))

        # Get the various possible parameters for verification
        access_token = request.args.get("access_token")
        refresh_token = request.args.get("refresh_token")
        token = request.args.get("token")
        token_hash = request.args.get("token_hash")
        type_param = request.args.get("type")
        logger.info(
            f"  - refresh_token: {'***' + str(refresh_token)[-4:] if refresh_token else None}"
        )

        if not access_token and not token_hash and not token:
            logger.error("No valid tokens found in confirmation request")
            flash("Invalid confirmation link. Please try signing up again.", "error")
            return redirect(url_for("signup"))

        # Handle different token formats for verification
        verification_successful = False
        user_id = None
        user_email = None

        # Method 1: Try token verification (newer format)
        if token and type_param:
            try:
                logger.info(
                    f"Attempting token verification with token: ***{token[-4:]} and type: {type_param}"
                )

                # For signup tokens, try multiple approaches
                if type_param == "signup":
                    # Approach 1: Try exchange_code_for_session
                    try:
                        logger.info("Using exchange_code_for_session for signup token")
                        result = supabase_service.client.auth.exchange_code_for_session(
                            token
                        )
                        logger.info(f"Exchange code result type: {type(result)}")
                        logger.info(f"Exchange code result: {str(result)[:200]}...")

                        # Handle different response formats
                        if hasattr(result, "user") and result.user:
                            verification_successful = True
                            user_id = result.user.id
                            user_email = result.user.email
                            logger.info(
                                f"Email verified successfully using exchange_code_for_session for user: {user_id}"
                            )
                        elif (
                            hasattr(result, "session")
                            and result.session
                            and hasattr(result.session, "user")
                        ):
                            verification_successful = True
                            user_id = result.session.user.id
                            user_email = result.session.user.email
                            logger.info(
                                f"Email verified successfully using session from exchange_code_for_session for user: {user_id}"
                            )
                        elif isinstance(result, dict):
                            # Handle dictionary response
                            if "user" in result and result["user"]:
                                verification_successful = True
                                user_data = result["user"]
                                user_id = user_data["id"]
                                user_email = user_data["email"]
                                logger.info(
                                    f"Email verified successfully using dict result for user: {user_id}"
                                )
                            elif (
                                "session" in result
                                and result["session"]
                                and "user" in result["session"]
                            ):
                                verification_successful = True
                                user_data = result["session"]["user"]
                                user_id = user_data["id"]
                                user_email = user_data["email"]
                                logger.info(
                                    f"Email verified successfully using dict session for user: {user_id}"
                                )
                        else:
                            logger.warning(
                                f"exchange_code_for_session returned unexpected format: {type(result)}"
                            )

                    except Exception as e1:
                        logger.error(f"exchange_code_for_session failed: {str(e1)}")

                    # Approach 2: If exchange_code_for_session failed, try verify_otp with phone/email format
                    if not verification_successful:
                        try:
                            logger.info(
                                "Trying verify_otp with token_hash approach for signup"
                            )
                            # Sometimes signup tokens work with verify_otp if we treat them as token_hash
                            result = supabase_service.client.auth.verify_otp(
                                {"token_hash": token, "type": "signup"}
                            )
                            logger.info(f"verify_otp result: {result}")
                            if hasattr(result, "user") and result.user:
                                verification_successful = True
                                user_id = result.user.id
                                user_email = result.user.email
                                logger.info(
                                    f"Email verified successfully using verify_otp token_hash method for user: {user_id}"
                                )
                        except Exception as e2:
                            logger.error(
                                f"verify_otp token_hash approach failed: {str(e2)}"
                            )

                else:
                    # For other types (like email), use the standard verify_otp
                    result = supabase_service.client.auth.verify_otp(
                        {"token": token, "type": type_param}
                    )
                    logger.info(f"Token verification result: {result}")
                    if result.user:
                        verification_successful = True
                        user_id = result.user.id
                        user_email = result.user.email
                        logger.info(
                            f"Email verified successfully using token method for user: {user_id}"
                        )

            except Exception as e:
                logger.error(f"Token verification failed: {str(e)}")
                logger.error(f"Exception type: {type(e)}")

        # Method 2: Try token_hash verification
        if not verification_successful and token_hash and type_param == "email":
            try:
                logger.info(
                    f"Attempting token_hash verification with hash: ***{token_hash[-4:]}"
                )
                result = supabase_service.client.auth.verify_otp(
                    {"token_hash": token_hash, "type": "email"}
                )
                logger.info(f"Token hash verification result: {result}")
                if result.user:
                    verification_successful = True
                    user_id = result.user.id
                    user_email = result.user.email
                    logger.info(
                        f"Email verified successfully using token_hash method for user: {user_id}"
                    )
            except Exception as e:
                logger.error(f"Token hash verification failed: {str(e)}")
                logger.error(f"Exception type: {type(e)}")

        # Method 3: Try session-based verification (older format)
        if not verification_successful and access_token and refresh_token:
            try:
                session_result = supabase_service.set_session(
                    access_token, refresh_token
                )
                if session_result["success"]:
                    current_user = supabase_service.get_current_user()
                    if current_user:
                        verification_successful = True
                        user_id = current_user["id"]
                        user_email = current_user["email"]
                        logger.info(
                            f"Email verified successfully using session method for user: {user_id}"
                        )
            except Exception as e:
                logger.error(f"Session verification failed: {str(e)}")

        if not verification_successful:
            logger.error("All verification methods failed")
            logger.error(
                f"Final state - token: {bool(token)}, token_hash: {bool(token_hash)}, access_token: {bool(access_token)}"
            )
            flash(
                "Email verification failed. Please try again or request a new verification email.",
                "error",
            )
            return redirect(url_for("login"))

        # Update the profile to mark email as confirmed
        try:
            profile_update_result = supabase_service.update_profile(
                user_id, {"email_confirmed": True}
            )
            logger.info(
                f"Profile updated to mark email as confirmed for user: {user_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to update email_confirmed status: {str(e)}")

        # Get the user's profile
        profile = supabase_service.get_profile(user_id)

        if profile:
            # Auto-login the user after email confirmation
            session["user_id"] = user_id
            session["user_type"] = profile.get("user_type", "student")
            session["user_name"] = profile.get("name", "User")
            session["user_email"] = user_email

            flash("Email confirmed successfully! Welcome to InterSpark!", "success")

            # Check if profile is complete, redirect accordingly
            completion_check = supabase_service.is_profile_complete(
                profile, profile.get("user_type")
            )
            if completion_check["complete"]:
                return redirect(url_for("dashboard"))
            else:
                flash("Please complete your profile to get started.", "info")
                return redirect(url_for("profile"))
        else:
            flash("Profile not found. Please complete your registration.", "warning")
            return redirect(url_for("profile"))

    except Exception as e:
        logger.error(f"Error in email confirmation: {str(e)}")
        flash(
            "An error occurred during email confirmation. Please try logging in.",
            "error",
        )
        return redirect(url_for("login"))


@app.route("/auth/verify")
def verify_email():
    """Secure email verification using our custom tokens."""
    try:
        token = request.args.get("token")

        if not token:
            flash("Invalid verification link. Missing token.", "error")
            return redirect(url_for("login"))

        logger.info(f"Email verification attempt with token: ***{token[-4:]}")

        # Verify the token
        verification_result = supabase_service.verify_token(token)

        if not verification_result["success"]:
            error_message = verification_result.get(
                "error", "Invalid verification token"
            )

            if "expired" in error_message.lower():
                flash(
                    "The verification link has expired. Please request a new verification email.",
                    "warning",
                )
            elif "already been used" in error_message.lower():
                flash(
                    "This verification link has already been used. Please try logging in.",
                    "info",
                )
            else:
                flash(
                    "Invalid verification link. Please request a new verification email.",
                    "error",
                )

            return redirect(url_for("login"))

        # Token is valid, get user info
        user_id = verification_result["user_id"]
        email = verification_result["email"]

        # Update the profile to mark email as confirmed
        try:
            profile_update_result = supabase_service.update_profile(
                user_id, {"email_confirmed": True}
            )

            if profile_update_result:
                logger.info(
                    f"Email verified successfully for user: {user_id} ({email})"
                )

                # Get the user's profile for auto-login
                profile = supabase_service.get_profile(user_id)

                if profile:
                    # Auto-login the user after email confirmation
                    session["user_id"] = user_id
                    session["user_type"] = profile.get("user_type", "student")
                    session["user_name"] = profile.get("name", "User")
                    session["user_email"] = email

                    flash(
                        "Email verified successfully! Welcome to InterSpark!", "success"
                    )

                    # Check if profile is complete, redirect accordingly
                    completion_check = supabase_service.is_profile_complete(
                        profile, profile.get("user_type")
                    )
                    if completion_check["complete"]:
                        return redirect(url_for("dashboard"))
                    else:
                        flash("Please complete your profile to get started.", "info")
                        return redirect(url_for("profile"))
                else:
                    flash("Profile not found. Please contact support.", "error")
                    return redirect(url_for("login"))
            else:
                flash(
                    "Failed to update email confirmation status. Please contact support.",
                    "error",
                )
                return redirect(url_for("login"))

        except Exception as update_error:
            logger.error(
                f"Failed to update email confirmation status: {str(update_error)}"
            )
            flash("Email verification failed. Please contact support.", "error")
            return redirect(url_for("login"))

    except Exception as e:
        logger.error(f"Error in email verification: {str(e)}")
        flash("An error occurred during email verification. Please try again.", "error")
        return redirect(url_for("login"))


@app.route("/auth/confirm-manual")
def confirm_email_manual():
    """Manual email confirmation using email parameter instead of unreliable tokens."""
    try:
        email = request.args.get("email")

        if not email:
            flash("Invalid confirmation link. Missing email parameter.", "error")
            return redirect(url_for("login"))

        # Validate email format
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            flash("Invalid email format in confirmation link.", "error")
            return redirect(url_for("login"))

        logger.info(f"Manual email confirmation attempt for: {email}")

        # Check if user exists in our profiles table
        profile = supabase_service.get_profile_by_email(email)
        if not profile:
            flash(
                "No account found with that email address. Please sign up first.",
                "error",
            )
            return redirect(url_for("signup"))

        # Check if email is already confirmed
        if profile.get("email_confirmed", False):
            flash("Your email is already confirmed! Please log in.", "info")
            return redirect(url_for("login"))

        # Update the profile to mark email as confirmed
        try:
            user_id = profile.get("id")
            profile_update_result = supabase_service.update_profile(
                user_id, {"email_confirmed": True}
            )

            if profile_update_result:
                logger.info(f"Email manually confirmed for user: {user_id} ({email})")

                # Auto-login the user after email confirmation
                session["user_id"] = user_id
                session["user_type"] = profile.get("user_type", "student")
                session["user_name"] = profile.get("name", "User")
                session["user_email"] = email

                flash("Email confirmed successfully! Welcome to InterSpark!", "success")

                # Check if profile is complete, redirect accordingly
                completion_check = supabase_service.is_profile_complete(
                    profile, profile.get("user_type")
                )
                if completion_check["complete"]:
                    return redirect(url_for("dashboard"))
                else:
                    flash("Please complete your profile to get started.", "info")
                    return redirect(url_for("profile"))
            else:
                flash(
                    "Failed to confirm email. Please try again or contact support.",
                    "error",
                )
                return redirect(url_for("login"))

        except Exception as update_error:
            logger.error(
                f"Failed to update email confirmation status: {str(update_error)}"
            )
            flash(
                "Email confirmation failed. Please try again or contact support.",
                "error",
            )
            return redirect(url_for("login"))

    except Exception as e:
        logger.error(f"Error in manual email confirmation: {str(e)}")
        flash("An error occurred during email confirmation. Please try again.", "error")
        return redirect(url_for("login"))


@app.route("/auth/manual-confirm-page")
def manual_confirm_page():
    """Show manual email confirmation page."""
    email = request.args.get("email")

    if not email:
        flash("Invalid confirmation request. Missing email parameter.", "error")
        return redirect(url_for("login"))

    # Validate email format
    import re

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        flash("Invalid email format.", "error")
        return redirect(url_for("login"))

    return render_template("manual_confirm.html", email=email)


@app.route("/auth/resend-confirmation", methods=["POST"])
def resend_confirmation():
    """Resend email confirmation link."""
    try:
        email = request.form.get("email")
        if not email:
            flash("Please provide your email address.", "error")
            return redirect(url_for("login"))

        # Get the user by email to check if they exist
        profile = supabase_service.get_profile_by_email(email)
        if not profile:
            flash("No account found with that email address.", "error")
            return redirect(url_for("login"))

        # Check if email is already confirmed
        if profile.get("email_confirmed", True):
            flash("Your email is already confirmed. Please try logging in.", "info")
            return redirect(url_for("login"))

        # Resend verification email with secure token
        try:
            user_id = profile.get("id")

            # Create and send verification email with our secure token
            email_result = supabase_service.send_verification_email(user_id, email)

            if email_result["success"]:
                verification_link = email_result["verification_link"]

                logger.info(f"Secure verification email resent to: {email}")
                logger.info(f"Verification link: {verification_link}")

                flash(
                    "Verification email resent! Please check your email and click the verification link. "
                    "The link will expire in 24 hours.",
                    "success",
                )
            else:
                # Fallback to manual confirmation if token creation fails
                site_url = os.getenv("SITE_URL", "http://localhost:5001")
                confirmation_link = f"{site_url}/auth/confirm-manual?email={email}"

                flash(
                    "Verification system temporarily unavailable. "
                    f'You can confirm manually here: <a href="{confirmation_link}" target="_blank">Confirm Email</a>',
                    "warning",
                )
                logger.warning(
                    f"Failed to create verification token for resend: {email}"
                )

        except Exception as e:
            logger.error(f"Error resending verification email: {str(e)}")

            # Provide fallback manual confirmation link
            site_url = os.getenv("SITE_URL", "http://localhost:5001")
            confirmation_link = f"{site_url}/auth/confirm-manual?email={email}"

            flash(
                f"Email service temporarily unavailable. You can confirm your email directly using this link: "
                f'<a href="{confirmation_link}" target="_blank">Confirm Email</a>',
                "warning",
            )

        return redirect(url_for("login"))

    except Exception as e:
        logger.error(f"Error in resend confirmation: {str(e)}")
        flash("An error occurred. Please try again.", "error")
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully", "success")
    return redirect(url_for("home"))


@app.route("/delete_account", methods=["POST"])
def delete_account():
    """Delete user account and all associated data"""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    user_id = session.get("user_id")

    try:
        # Delete user account from Supabase
        result = supabase_service.delete_user_account(user_id)

        if result["success"]:
            # Clear session
            session.clear()
            return jsonify({"success": True, "message": "Account deleted successfully"})
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": result.get("error", "Failed to delete account"),
                    }
                ),
                400,
            )

    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "An error occurred while deleting your account",
                }
            ),
            500,
        )


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    user_type = session.get("user_type")

    # Get user profile for dashboard display
    try:
        user_profile = supabase_service.get_profile(user_id)
        if not user_profile:
            # Create a basic profile from session data
            user_profile = {
                "id": user_id,
                "name": session.get("user_name", "User"),
                "email": session.get("user_email", ""),
                "user_type": user_type,
            }
        else:
            # Ensure user_type is in the profile
            user_profile["user_type"] = user_type
    except Exception as e:
        flash(f"Error loading user profile: {str(e)}", "error")
        user_profile = {
            "id": user_id,
            "name": session.get("user_name", "User"),
            "email": session.get("user_email", ""),
            "user_type": user_type,
        }

    if user_type == "student":
        # Get student's applications, relevant opportunities, and saved opportunities/profiles
        try:
            opportunities = supabase_service.get_opportunities()
            saved_opportunities = supabase_service.get_saved_opportunities(user_id)
            saved_profiles = supabase_service.get_saved_profiles(user_id)
            return render_template(
                "dashboard.html",
                user_type="student",
                opportunities=opportunities,
                saved_opportunities=saved_opportunities,
                saved_profiles=saved_profiles,
                user=user_profile,
            )
        except Exception as e:
            flash(f"Error loading dashboard: {str(e)}", "error")
            return render_template(
                "dashboard.html",
                user_type="student",
                opportunities=[],
                saved_opportunities=[],
                saved_profiles=[],
                user=user_profile,
            )

    elif user_type == "organization":
        # Get organization's posted opportunities, applications, and saved profiles/opportunities
        try:
            company_opportunities = supabase_service.get_organization_opportunities(
                user_id
            )
            # Ensure all opportunities are properly formatted
            if not company_opportunities:
                company_opportunities = []

            saved_profiles = supabase_service.get_saved_profiles(user_id)
            if not saved_profiles:
                saved_profiles = []

            saved_opportunities = supabase_service.get_saved_opportunities(user_id)
            if not saved_opportunities:
                saved_opportunities = []

            return render_template(
                "dashboard.html",
                user_type="organization",
                opportunities=company_opportunities,
                saved_profiles=saved_profiles,
                saved_opportunities=saved_opportunities,
                user=user_profile,
            )
        except Exception as e:
            flash(f"Error loading dashboard: {str(e)}", "error")
            return render_template(
                "dashboard.html",
                user_type="organization",
                opportunities=[],
                saved_profiles=[],
                saved_opportunities=[],
                user=user_profile,
            )

    return render_template("dashboard.html", user_type=user_type, user=user_profile)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    user_type = session.get("user_type")

    if request.method == "POST":
        # Update profile with form data
        profile_data = {}

        if user_type == "student":
            # Normalize and validate skills from form
            skills_json = normalize_and_validate_skills(request.form.get("skills"))
            profile_data = {
                "name": request.form.get("full_name"),
                "school": request.form.get("school"),
                "grade": request.form.get("grade"),
                "skills": skills_json,
                "bio": request.form.get("bio"),
                "github_url": request.form.get("github_url"),
                "linkedin_url": request.form.get("linkedin_url"),
                "portfolio_url": request.form.get("portfolio_url"),
                "phone": request.form.get("phone"),
                "location": request.form.get("location"),
            }
        elif user_type == "organization":
            profile_data = {
                "name": request.form.get("full_name"),
                "organization_name": request.form.get("full_name"),
                "description": request.form.get("description"),
                "website": request.form.get("website"),
                "location": request.form.get("location"),
                "phone": request.form.get("phone"),
            }

        # Remove empty values to avoid overwriting existing data with blank fields
        def is_valid_value(v):
            if v is None:
                return False
            if isinstance(v, str):
                return v.strip() != ""
            if isinstance(v, list):
                return len(v) > 0
            return True

        profile_data = {k: v for k, v in profile_data.items() if is_valid_value(v)}

        try:
            # Persist skills as JSON array (not double-encoded)
            if "skills" in profile_data:
                profile_data["skills"] = profile_data["skills"]
            result = supabase_service.update_profile(user_id, profile_data)
            if result["success"]:
                flash("Profile updated successfully!", "success")
                # Update session data
                if "name" in profile_data:
                    session["user_name"] = profile_data["name"]

                return redirect(url_for("profile"))
            else:
                flash(
                    f"Failed to update profile: {result.get('error', 'Unknown error')}",
                    "error",
                )
        except Exception as e:
            flash(f"Error updating profile: {str(e)}", "error")

    # Get current profile data
    try:
        profile = supabase_service.get_profile(user_id)
        if not profile:
            profile = {
                "name": session.get("user_name", ""),
                "email": session.get("user_email", ""),
                "user_type": user_type,
            }
        # Ensure user_type is in the profile data
        profile["user_type"] = user_type

        # Always pass skills_json as a Python list of valid skills
        skills_json = normalize_and_validate_skills(profile.get("skills"))

        return render_template(
            "profile.html",
            user_type=user_type,
            profile=profile,
            user=profile,
            is_own_profile=True,
            read_only=False,
            skills_json=skills_json,
            skills_master=get_all_available_skills(),
        )
    except Exception as e:
        flash(f"Error loading profile: {str(e)}", "error")
        default_profile = {
            "name": session.get("user_name", ""),
            "email": session.get("user_email", ""),
            "user_type": user_type,
        }
        return render_template(
            "profile.html",
            user_type=user_type,
            profile=default_profile,
            user=default_profile,
            is_own_profile=True,
            read_only=False,
            skills_json=[],
        )


@app.route("/profile/<user_id>", methods=["GET"])
def view_profile(user_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    current_user_id = session.get("user_id")
    current_user_type = session.get("user_type")

    profile = supabase_service.get_profile(user_id)
    if not profile:
        flash("User profile not found.", "error")
        return redirect(url_for("talent_search"))

    is_own_profile = current_user_id == user_id

    # Check if profile is saved by current user (for all users viewing other profiles)
    is_saved = False
    if not is_own_profile:
        is_saved = supabase_service.is_profile_saved(current_user_id, user_id)

    # Always pass skills_json as a Python list of valid skills
    skills_json = normalize_and_validate_skills(profile.get("skills"))

    # Get Talent Search filter params from query string
    search_query = request.args.get("search")
    skills = request.args.get("skills")
    school = request.args.get("school")
    grade = request.args.get("grade")

    # Robustly parse selected_skills for Jinja2
    def parse_skills(val):
        import json

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

    selected_skills_list = parse_skills(skills)
    # Show button if any talent search param is present in the URL (even if empty)
    back_to_talent_search = (
        "search" in request.args
        or "skills" in request.args
        or "school" in request.args
        or "grade" in request.args
    ) or any([bool(search_query), bool(skills), bool(school), bool(grade)])

    return render_template(
        "profile.html",
        user_type=profile.get("user_type", "student"),
        profile=profile,
        user=profile,
        is_own_profile=is_own_profile,
        is_saved=is_saved,
        read_only=not is_own_profile,
        back_to_talent_search=back_to_talent_search,
        search_query=search_query,
        selected_skills=selected_skills_list,
        selected_school=school,
        selected_grade=grade,
        skills_json=skills_json,
        skills_master=get_all_available_skills(),
        # If this is an organization profile, include their opportunities
        organization_opportunities=(supabase_service.get_organization_opportunities(user_id) if profile.get('user_type') == 'organization' else []),
    )


@app.route("/opportunities")
def opportunities():
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        # Get filters from query parameters
        search_query = request.args.get("search", "")
        opportunity_type = request.args.get("type", "")
        category = request.args.get("category", "")
        location = request.args.get("location", "")
        skills_needed = request.args.get("skills_needed", "")

        # Get pagination parameters
        page = int(request.args.get("page", 1))
        per_page = 6  # 6 opportunities per page

        # Fetch all opportunities with filters first
        all_opportunities = supabase_service.search_opportunities(
            search_query=search_query,
            opportunity_type=opportunity_type,
            category=category,
            location=location,
            skills_needed=skills_needed,
        )

        # Calculate pagination
        total_opportunities = len(all_opportunities)
        total_pages = (total_opportunities + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        opportunities = all_opportunities[start_idx:end_idx]

        # Parse skills_needed (comma-separated or JSON)
        import json

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

        selected_skills_needed = parse_skills(skills_needed)

        return render_template(
            "opportunities.html",
            opportunities=opportunities,
            search_query=search_query,
            selected_type=opportunity_type,
            selected_category=category,
            selected_location=location,
            selected_skills_needed=selected_skills_needed,
            skills_master=get_all_available_skills(),
            current_page=page,
            total_pages=total_pages,
            total_opportunities=total_opportunities,
        )
    except Exception as e:
        flash(f"Error loading opportunities: {str(e)}", "error")
        return render_template("opportunities.html", opportunities=[])


@app.route("/opportunity/<int:id>")
def opportunity_details(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    try:
        opportunity = supabase_service.get_opportunity_by_id(id)
        if not opportunity:
            flash("Opportunity not found", "error")
            return redirect(url_for("opportunities"))

        # Check if opportunity is saved by current user
        is_saved = supabase_service.is_opportunity_saved(user_id, id)

        return render_template(
            "opportunity_details.html", opportunity=opportunity, is_saved=is_saved
        )
    except Exception as e:
        flash(f"Error loading opportunity: {str(e)}", "error")
        return redirect(url_for("opportunities"))


@app.route("/talent")
def talent_search():
    if "user_id" not in session:
        return redirect(url_for("login"))
    try:
        user_id = session.get("user_id")

        # Get search parameters from request
        search_query = request.args.get("search", "")
        skills = request.args.get("skills", "")
        school = request.args.get("school", "")
        grade = request.args.get("grade", "")
        location = request.args.get("location", "")
        # Optional type filter: 'student' or 'organization'
        profile_type = request.args.get("type", "student")

        # Get pagination parameters
        page = int(request.args.get("page", 1))
        per_page = 9  # 9 profiles per page

        # Branch by requested profile_type
        if profile_type == 'organization':
            all_orgs = supabase_service.search_organizations(
                search_query=search_query,
                location=location,
            )
            total_students = len(all_orgs)
            total_pages = (total_students + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            students = all_orgs[start_idx:end_idx]
        else:
            # Search all students with filters first
            all_students = supabase_service.search_students(
                search_query=search_query,
                skills=skills,
                school=school,
                grade=grade,
                location=location,
            )

            total_students = len(all_students)
            total_pages = (total_students + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            students = all_students[start_idx:end_idx]

        # Get saved profiles to determine which ones are bookmarked
        saved_profiles = supabase_service.get_saved_profiles(user_id)
        saved_profile_ids = set()
        if saved_profiles:
            for saved_profile in saved_profiles:
                if "profiles" in saved_profile and saved_profile["profiles"]:
                    saved_profile_ids.add(saved_profile["profiles"]["id"])
                elif "profile_id" in saved_profile:
                    saved_profile_ids.add(saved_profile["profile_id"])

        # Add is_saved flag to each student/org
        for student in students:
            student["is_saved"] = student.get("id") in saved_profile_ids

        # Parse selected_skills robustly (list or string)
        def parse_skills(val):
            import json

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

        selected_skills_list = parse_skills(skills)

        return render_template(
            "talent_search.html",
            students=students,
            search_query=search_query,
            selected_skills=selected_skills_list,
            selected_school=school,
            selected_grade=grade,
            selected_location=location,
            saved_profile_ids=list(saved_profile_ids),
            skills_master=get_all_available_skills(),
            current_page=page,
            total_pages=total_pages,
            total_students=total_students,
            profile_type=profile_type,
        )
    except Exception as e:
        flash(f"Error searching talent: {str(e)}", "error")
        return render_template("talent_search.html", students=[])


@app.route("/preview_opportunity", methods=["POST"])
def preview_opportunity():
    """Preview opportunity using form data without saving"""
    if "user_id" not in session or session.get("user_type") != "organization":
        return {"success": False, "error": "Not authorized"}, 401

    try:
        # Create a mock opportunity object from form data
        mock_opportunity = {
            "id": 0,  # Preview ID
            "title": request.form.get("title", ""),
            "description": request.form.get("description", ""),
            "type": request.form.get("type", ""),
            "category": request.form.get("category", ""),
            "location": request.form.get("location", ""),
            "requirements": request.form.get("requirements", ""),
            "compensation": request.form.get("compensation", ""),
            "duration": request.form.get("duration", ""),
            "application_deadline": request.form.get("application_deadline", ""),
            "skills_needed": request.form.get("skills_needed", "[]"),
            "eligibility_criteria": request.form.get("eligibility_criteria", ""),
            "age_range": request.form.get("age_range", ""),
            "prerequisite_skills": request.form.get("prerequisite_skills", ""),
            "award_amount": request.form.get("award_amount", ""),
            "program_dates": request.form.get("program_dates", ""),
            "mentor_info": request.form.get("mentor_info", ""),
            "research_field": request.form.get("research_field", ""),
            "commitment_level": request.form.get("commitment_level", ""),
            "application_materials": request.form.get("application_materials", ""),
            "selection_process": request.form.get("selection_process", ""),
            "created_at": "2024-01-01",  # Mock date
            "status": "active",
            "company_id": session.get("user_id"),
            "profiles": {
                "name": "Preview Organization",
                "organization_name": "Preview Organization",
                "location": "Preview Location",
                "profile_image": None,
                "website": None,
                "phone": None,
            },
        }

        # Parse skills_needed if it's a JSON string
        try:
            import json

            if isinstance(mock_opportunity["skills_needed"], str):
                mock_opportunity["skills_needed"] = json.loads(
                    mock_opportunity["skills_needed"]
                )
        except:
            mock_opportunity["skills_needed"] = []

        # Render the opportunity details template with preview flag
        return render_template(
            "opportunity_details.html", opportunity=mock_opportunity, is_preview=True
        )

    except Exception as e:
        return {"success": False, "error": str(e)}, 500


@app.route("/create_opportunity", methods=["GET", "POST"])
@app.route("/create_opportunity/<int:opportunity_id>", methods=["GET", "POST"])
def create_opportunity(opportunity_id=None):
    if "user_id" not in session or session.get("user_type") != "organization":
        flash(
            "You must be logged in as an organization to create opportunities", "error"
        )
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    opportunity = None
    is_editing = opportunity_id is not None

    # If editing, get the existing opportunity
    if is_editing:
        opportunity = supabase_service.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            flash("Opportunity not found", "error")
            return redirect(url_for("dashboard"))

        # Check if user owns this opportunity
        if opportunity.get("company_id") != user_id:
            flash("You can only edit your own opportunities", "error")
            return redirect(url_for("dashboard"))

        # Load the skills list for autocomplete

    if request.method == "POST":
        # Get form data and map to database fields
        status = request.form.get("status", "active")

        # Validate skills against database for both drafts and active opportunities
        skills_needed_json = normalize_and_validate_skills(
            request.form.get("skills_needed")
        )

        # Handle image upload to Supabase Storage
        image_url = None
        image_file = request.files.get("image")
        if image_file and image_file.filename:
            from werkzeug.utils import secure_filename

            filename = secure_filename(image_file.filename)
            file_data = image_file.read()
            content_type = image_file.mimetype
            # Use opportunity_id if editing, else user_id (will be replaced after creation)
            storage_id = opportunity_id if is_editing else user_id
            upload_result = supabase_service.upload_opportunity_banner(
                storage_id, file_data, filename, content_type
            )
            if upload_result.get("success"):
                image_url = upload_result["url"]
            else:
                # Image upload failed, show error and return to form
                flash(upload_result.get("error", "Failed to upload image"), "error")
                return render_template(
                    "create_opportunity.html",
                    opportunity=opportunity,
                    is_editing=is_editing,
                    skills_master=get_all_available_skills(),
                )

        opportunity_data = {
            "title": request.form.get("title") or None,
            "description": request.form.get("description") or None,
            "type": request.form.get("type") or None,
            "category": request.form.get("category") or None,
            "location": request.form.get("location") or None,
            "requirements": request.form.get("requirements") or None,
            "compensation": request.form.get("compensation") or None,
            "duration": request.form.get("duration") or None,
            "application_deadline": request.form.get("application_deadline") or None,
            "skills_needed": skills_needed_json,
            "status": status,
            "apply_link": request.form.get("apply_link") or None,
            "image": (
                image_url
                if image_url
                else (
                    opportunity["image"]
                    if opportunity and "image" in opportunity
                    else None
                )
            ),
            # New type-specific fields
            "eligibility_criteria": request.form.get("eligibility_criteria") or None,
            "age_range": request.form.get("age_range") or None,
            "prerequisite_skills": request.form.get("prerequisite_skills") or None,
            "award_amount": request.form.get("award_amount") or None,
            "program_dates": request.form.get("program_dates") or None,
            "mentor_info": request.form.get("mentor_info") or None,
            "research_field": request.form.get("research_field") or None,
            "commitment_level": request.form.get("commitment_level") or None,
            "application_materials": request.form.get("application_materials") or None,
            "selection_process": request.form.get("selection_process") or None,
        }

        # For drafts, ensure core keys exist, but allow None values
        # Type-specific fields are already handled above and can remain None
        if status == "draft":
            for key in [
                "title",
                "description",
                "type",
                "category",
                "location",
                "requirements",
                "compensation",
                "duration",
                "application_deadline",
            ]:
                if opportunity_data.get(key) is None:
                    opportunity_data[key] = None

        # Add company_id only for new opportunities
        if not is_editing:
            opportunity_data["company_id"] = user_id

        try:
            # Get referrer URL from form data
            referrer_url = request.form.get("referrer", url_for("dashboard"))

            # Helper function to get type-specific required fields
            def get_type_specific_required_fields(opportunity_type):
                """Get required fields based on opportunity type"""
                type_specific = []
                if opportunity_type in ["Scholarship", "Competition"]:
                    type_specific.append("eligibility_criteria")
                    if opportunity_type == "Scholarship":
                        type_specific.append("award_amount")
                elif opportunity_type in ["Summer Camp", "Workshop"]:
                    type_specific.append("age_range")
                elif opportunity_type == "Research Opportunity":
                    type_specific.append("research_field")
                elif opportunity_type == "Mentorship":
                    type_specific.append("mentor_info")
                return type_specific

            # If editing and publishing, require all fields
            is_publish = request.form.get("publish") == "1"
            required_fields = [
                "title",
                "description",
                "type",
                "category",
                "location",
                "requirements",
                "compensation",
                "duration",
                "application_deadline",
            ]

            # Add type-specific required fields if publishing
            if is_publish and opportunity_data.get("type"):
                type_specific_fields = get_type_specific_required_fields(
                    opportunity_data["type"]
                )
                required_fields.extend(type_specific_fields)
            if is_editing and is_publish:
                # Publishing: require all fields
                missing = [f for f in required_fields if not opportunity_data.get(f)]
                if missing:
                    flash(
                        f"Missing required fields for publishing: {', '.join(missing)}. Complete all fields to publish.",
                        "error",
                    )
                    return render_template(
                        "create_opportunity.html",
                        opportunity=opportunity_data,
                        is_editing=is_editing,
                        missing_fields=missing,
                    )
                opportunity_data["status"] = "active"
                result = supabase_service.update_opportunity(
                    opportunity_id, opportunity_data
                )
                success_message = "Opportunity published successfully!"
                redirect_route = url_for("opportunity_details", id=opportunity_id)
            elif is_editing:
                # Regular update, redirect back to referrer
                opportunity_data["status"] = "draft"
                # Validate skills against database
                opportunity_data["skills_needed"] = normalize_and_validate_skills(
                    request.form.get("skills_needed")
                )
                result = supabase_service.update_opportunity(
                    opportunity_id, opportunity_data
                )
                success_message = "Draft updated successfully!"
                redirect_route = referrer_url
            elif not is_editing and status == "active":
                # Creating and publishing
                missing = [f for f in required_fields if not opportunity_data.get(f)]
                if missing:
                    flash(
                        f"Missing required fields for publishing: {', '.join(missing)}. Complete all fields to publish.",
                        "error",
                    )
                    return render_template(
                        "create_opportunity.html",
                        opportunity=opportunity_data,
                        is_editing=is_editing,
                        missing_fields=missing,
                    )
                opportunity_data["status"] = "active"
                result = supabase_service.create_opportunity(opportunity_data)
                success_message = "Opportunity created successfully!"
                redirect_route = referrer_url
            else:
                # Creating a new draft
                opportunity_data["status"] = "draft"
                # Validate skills against database
                opportunity_data["skills_needed"] = normalize_and_validate_skills(
                    request.form.get("skills_needed")
                )
                result = supabase_service.create_opportunity(opportunity_data)
                success_message = "Draft saved successfully!"
                redirect_route = url_for("dashboard")

            if result["success"]:
                flash(success_message, "success")
                return redirect(redirect_route)
            else:
                error_message = (
                    "Failed to update opportunity"
                    if is_editing
                    else "Failed to create opportunity"
                )
                flash(result.get("error", error_message), "error")
        except Exception as e:
            error_message = (
                f"Error updating opportunity: {str(e)}"
                if is_editing
                else f"Error creating opportunity: {str(e)}"
            )
            flash(error_message, "error")

    return render_template(
        "create_opportunity.html",
        opportunity=opportunity,
        is_editing=is_editing,
        skills_master=get_all_available_skills(),
    )


@app.route("/delete_opportunity/<int:opportunity_id>", methods=["POST"])
def delete_opportunity(opportunity_id):
    if "user_id" not in session:
        return {"success": False, "error": "Not authenticated"}, 401

    user_id = session.get("user_id")
    user_type = session.get("user_type")

    if user_type != "organization":
        return {
            "success": False,
            "error": "Only organizations can delete opportunities",
        }, 403

    try:
        # Get the opportunity to check ownership
        opportunity = supabase_service.get_opportunity_by_id(opportunity_id)
        print(
            f"Delete request for opportunity_id={opportunity_id}, found: {opportunity}"
        )
        if not opportunity:
            print("Opportunity not found for deletion.")
            return {"success": False, "error": "Opportunity not found"}, 404

        # Check if user owns this opportunity
        if opportunity.get("company_id") != user_id:
            print(
                f"User {user_id} does not own opportunity {opportunity_id} (company_id={opportunity.get('company_id')})"
            )
            return {
                "success": False,
                "error": "You can only delete your own opportunities",
            }, 403

        result = supabase_service.delete_opportunity(opportunity_id)
        print(f"Delete result for opportunity_id={opportunity_id}: {result}")
        if result["success"]:
            return {"success": True, "message": "Opportunity deleted successfully"}
        else:
            print(f"Failed to delete opportunity: {result}")
            return {
                "success": False,
                "error": result.get("error", "Failed to delete opportunity"),
            }, 400
    except Exception as e:
        print(f"Exception during opportunity delete: {e}")
        return {"success": False, "error": str(e)}, 500


@app.route("/save_opportunity/<int:opportunity_id>", methods=["POST"])
def save_opportunity(opportunity_id):
    if "user_id" not in session:
        return {"success": False, "error": "Not authenticated"}, 401

    user_id = session.get("user_id")

    try:
        result = supabase_service.save_opportunity(user_id, opportunity_id)
        if result["success"]:
            return {"success": True, "message": "Opportunity saved successfully"}
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to save opportunity"),
            }, 400
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


@app.route("/unsave_opportunity/<int:opportunity_id>", methods=["POST"])
def unsave_opportunity(opportunity_id):
    if "user_id" not in session:
        return {"success": False, "error": "Not authenticated"}, 401

    user_id = session.get("user_id")

    try:
        result = supabase_service.unsave_opportunity(user_id, opportunity_id)
        return {"success": True, "message": "Opportunity removed from saved"}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


@app.route("/save_profile/<profile_id>", methods=["POST"])
def save_profile(profile_id):
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    user_id = session.get("user_id")
    user_type = session.get("user_type")

    try:
        logger.info(f"Received save_profile request: session_user_id={user_id}, profile_id={profile_id}")
        result = supabase_service.save_profile(user_id, profile_id)

        logger.info(f"save_profile result: {result}")
        if result["success"]:
            return jsonify({"success": True, "message": "Profile saved successfully"})
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": result.get("error", "Failed to save profile"),
                    }
                ),
                400,
            )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/unsave_profile/<profile_id>", methods=["POST"])
def unsave_profile(profile_id):
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    user_id = session.get("user_id")

    try:
        logger.info(f"Received unsave_profile request: session_user_id={user_id}, profile_id={profile_id}")
        result = supabase_service.unsave_profile(user_id, profile_id)
        logger.info(f"unsave_profile result: {result}")
        return jsonify({"success": True, "message": "Profile removed from saved"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/debug/my_saved_profiles')
def debug_my_saved_profiles():
    """Debug endpoint: return saved_profiles for current session user (dev only)."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    try:
        user_id = session.get('user_id')
        saved_profiles = supabase_service.get_saved_profiles(user_id)
        return jsonify({'success': True, 'saved_profiles': saved_profiles})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/profile_details/<profile>")
def profile_details(profile):
    """Alias route to maintain backward compatibility with older templates linking to profile_details."""
    return redirect(url_for("view_profile", user_id=profile))


@app.route("/upload_profile_picture", methods=["POST"])
def upload_profile_picture():
    """Handle profile picture upload."""
    if "user_id" not in session:
        return {"success": False, "error": "Not authenticated"}, 401

    user_id = session.get("user_id")

    try:
        # Check if file is present
        if "profile_picture" not in request.files:
            return {"success": False, "error": "No file provided"}, 400

        file = request.files["profile_picture"]
        if file.filename == "":
            return {"success": False, "error": "No file selected"}, 400

        # Validate file type
        allowed_extensions = {"jpg", "jpeg", "png", "webp", "gif"}
        file_ext = (
            file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
        )

        if file_ext not in allowed_extensions:
            return {
                "success": False,
                "error": f"Invalid file type. Allowed: {', '.join(allowed_extensions)}",
            }, 400

        # Validate file size (5MB limit)
        file_data = file.read()
        if len(file_data) > 5 * 1024 * 1024:  # 5MB
            return {"success": False, "error": "File size must be less than 5MB"}, 400

        # Get content type and ensure it's a string
        content_type = getattr(file, "content_type", None)
        if content_type and not isinstance(content_type, str):
            content_type = str(content_type)

        # Debug logging
        logger.info(
            f"File upload request - filename: {file.filename}, content_type: {content_type}, size: {len(file_data)}"
        )

        # Upload to Supabase Storage
        result = supabase_service.upload_profile_picture(
            user_id=user_id,
            file_data=file_data,
            file_name=file.filename,
            content_type=content_type,
        )

        if result["success"]:
            return {
                "success": True,
                "url": result["url"],
                "message": result.get(
                    "message", "Profile picture uploaded successfully"
                ),
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Upload failed"),
            }, 500

    except Exception as e:
        logger.error(f"Error in upload_profile_picture: {str(e)}")
        return {"success": False, "error": str(e)}, 500


@app.route("/delete_profile_picture", methods=["POST"])
def delete_profile_picture():
    """Handle profile picture deletion."""
    if "user_id" not in session:
        return {"success": False, "error": "Not authenticated"}, 401

    user_id = session.get("user_id")

    try:
        result = supabase_service.delete_profile_picture(user_id)

        if result["success"]:
            return {
                "success": True,
                "message": result.get(
                    "message", "Profile picture deleted successfully"
                ),
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Delete failed"),
            }, 500

    except Exception as e:
        logger.error(f"Error in delete_profile_picture: {str(e)}")
        return {"success": False, "error": str(e)}, 500


@app.route("/chat")
def chat():
    """AI chatbot interface for InterSpark."""
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    # Get chat history from database
    try:
        chat_history = supabase_service.get_chat_history(user_id)
        # Convert to format expected by template
        formatted_history = []
        for msg in chat_history:
            formatted_history.append(
                {
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": msg["created_at"],
                }
            )
    except Exception as e:
        logger.error(f"Error loading chat history: {str(e)}")
        formatted_history = []

    # Get remaining prompts for today
    prompt_count = supabase_service.get_user_prompt_count(user_id)
    remaining_prompts = max(0, 5 - prompt_count)

    return render_template(
        "chat.html", chat_history=formatted_history, remaining_prompts=remaining_prompts
    )


@app.route("/chat/send", methods=["POST"])
def chat_send():
    """Handle chat message and return AI response."""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    if not ai_service:
        return jsonify({"success": False, "error": "AI service is not available"}), 503

    try:
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"success": False, "error": "Message cannot be empty"}), 400

        user_id = session.get("user_id")

        # Check prompt limit (5 per day for beta)
        prompt_count = supabase_service.get_user_prompt_count(user_id)
        if prompt_count >= 5:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "You've reached the limit of 5 prompts. This feature is in beta with limited usage.",
                    }
                ),
                429,
            )

        # Save user message to database
        supabase_service.save_chat_message(user_id, "user", user_message)

        # Get recent chat history from database for context
        chat_history_db = supabase_service.get_chat_history(user_id, limit=20)
        chat_history = []
        for msg in chat_history_db:
            chat_history.append(
                {
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": msg["created_at"],
                }
            )

        # Search database for relevant results
        if ai_service:
            db_results = ai_service.search_database_for_context(
                user_message, supabase_service
            )
        else:
            # Fallback search without AI service
            logger.warning("AI service not available, using fallback search")
            db_results = fallback_search(user_message, supabase_service)

        # Generate AI response with conversation context
        if ai_service:
            ai_response = ai_service.generate_response_with_context(
                user_message, db_results, chat_history
            )
        else:
            # Fallback response without AI
            ai_response = generate_fallback_response(user_message, db_results)

        # Save AI response to database
        supabase_service.save_chat_message(user_id, "assistant", ai_response)

        # Get updated remaining prompts
        updated_prompt_count = supabase_service.get_user_prompt_count(user_id)
        remaining_prompts = max(0, 5 - updated_prompt_count)

        return jsonify(
            {
                "success": True,
                "response": ai_response,
                "db_results": db_results,
                "remaining_prompts": remaining_prompts,
            }
        )

    except Exception as e:
        logger.error(f"Error in chat_send: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "An error occurred while processing your message",
                }
            ),
            500,
        )


@app.route("/chat/clear", methods=["POST"])
def chat_clear():
    """Clear chat history."""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    user_id = session.get("user_id")

    try:
        result = supabase_service.clear_chat_history(user_id)
        if result["success"]:
            return jsonify({"success": True, "message": "Chat history cleared"})
        else:
            return jsonify({"success": False, "error": result["error"]}), 500
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}")
        return jsonify({"success": False, "error": "Failed to clear chat history"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)

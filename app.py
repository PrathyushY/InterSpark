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


def normalize_skills_for_draft(value):
    """
    Normalize skills input for drafts - accepts all skills without validation against database.
    This allows saving new skills in drafts before they're added to the database.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [s.strip() for s in value if isinstance(s, str) and s.strip()]
    if isinstance(value, str):
        try:
            loaded = json.loads(value)
            if isinstance(loaded, list):
                return [s.strip() for s in loaded if isinstance(s, str) and s.strip()]
        except Exception:
            pass
        # Comma-separated string
        if "," in value:
            return [s.strip() for s in value.split(",") if s.strip()]
        val = value.strip()
        return [val] if val else []
    return []


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "2a15f8283ab2353f15089e80d8acf104")

# Initialize services after environment variables are loaded
supabase_service = SupabaseService()

# Initialize AI service with error handling
try:
    ai_service = AIService(api_key=os.getenv("GEMINI_API_KEY"))
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
            'python': ['python', 'py'],
            'javascript': ['javascript', 'js', 'node'],
            'react': ['react', 'reactjs'],
            'java': ['java'],
            'html': ['html'],
            'css': ['css'],
            'sql': ['sql', 'database'],
            'machine learning': ['machine learning', 'ml', 'ai', 'artificial intelligence'],
            'data science': ['data science', 'data analysis'],
            'web development': ['web development', 'web dev', 'frontend', 'backend']
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
                    name = profile.get('name', 'Unknown')
                    school = profile.get('school', 'Unknown school')
                    skills = profile.get('skills', [])
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
                    title = opp.get('title', 'Unknown title')
                    org_name = "Unknown organization"
                    if opp.get("profiles"):
                        org_name = opp["profiles"].get("name", org_name)
                    
                    response_parts.append(f"- **{title}** at {org_name}")
                    response_parts.append(f"  [View Opportunity](/opportunity/{opp['id']})")
        else:
            response_parts.append("I didn't find any matching profiles or opportunities for your query.")
            response_parts.append("Try rephrasing your request or being more specific about the skills or type of opportunity you're looking for.")
        
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
        date_string: ISO format date string from Supabase
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
    # Get featured opportunities from Supabase
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

        # Authenticate with Supabase - no longer need user_type selection
        try:
            auth_result = supabase_service.authenticate_user(email, password)

            if auth_result["success"]:
                user = auth_result["user"]
                profile = auth_result["profile"]

                print(f"DEBUG - Login attempt:")
                print(f"  Profile exists: {profile is not None}")
                if profile:
                    print(f"  Profile user_type: '{profile.get('user_type')}'")
                    print(f"  Profile name: '{profile.get('name')}'")

                # Check if profile exists and has user_type
                if profile and profile.get("user_type"):
                    session["user_id"] = user["id"]
                    session["user_type"] = profile["user_type"]
                    session["user_name"] = profile["name"]
                    session["user_email"] = profile["email"]

                    flash("Login successful!", "success")
                    return redirect(url_for("dashboard"))
                elif profile and profile.get("name") == "User":
                    # This is a newly created default profile, redirect to complete profile
                    session["user_id"] = user["id"]
                    session["user_type"] = "student"  # Default to student
                    session["user_name"] = profile["name"]
                    session["user_email"] = profile["email"]

                    flash("Please complete your profile to continue.", "info")
                    return redirect(url_for("profile"))
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
                        session["user_id"] = user["id"]
                        session["user_type"] = profile.get("user_type", "student")
                        session["user_name"] = profile.get("name", "User")
                        session["user_email"] = profile.get("email", email)
                        return redirect(url_for("profile"))
            else:
                flash(auth_result.get("error", "Invalid credentials"), "error")

        except Exception as e:
            flash(f"Login error: {str(e)}", "error")

    return render_template("login.html")


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
            bio = request.form.get("bio", "").strip()

            # Validate required student fields
            if not school or not grade or not bio:
                flash(
                    "Please fill in all required fields: School, Grade, and Bio",
                    "error",
                )
                return render_template("signup.html")

            user_data.update({"school": school, "grade": grade, "bio": bio})

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

        # Create user with Supabase
        try:
            result = supabase_service.create_user(email, password, user_data)

            if result["success"]:
                # Auto-login the user
                session["user_id"] = result["user"]["id"]
                session["user_type"] = user_type
                session["user_name"] = name
                session["user_email"] = email

                flash("Registration successful! Welcome to InterSpark!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash(result.get("error", "Registration failed"), "error")

        except Exception as e:
            flash(f"Registration error: {str(e)}", "error")

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully", "success")
    return redirect(url_for("home"))


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

        print(f"DEBUG - Profile update attempt:")
        print(f"  User ID: {user_id}")
        print(f"  User Type: {user_type}")
        print(f"  Profile data: {profile_data}")

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

        # Fetch opportunities with filters (including skills_needed)
        opportunities = supabase_service.search_opportunities(
            search_query=search_query,
            opportunity_type=opportunity_type,
            category=category,
            location=location,
            skills_needed=skills_needed,
        )

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

        # Search students with filters
        students = supabase_service.search_students(
            search_query=search_query,
            skills=skills,
            school=school,
            grade=grade,
            location=location,
        )

        # Get saved profiles to determine which ones are bookmarked
        saved_profiles = supabase_service.get_saved_profiles(user_id)
        saved_profile_ids = set()
        if saved_profiles:
            for saved_profile in saved_profiles:
                if "profiles" in saved_profile and saved_profile["profiles"]:
                    saved_profile_ids.add(saved_profile["profiles"]["id"])
                elif "profile_id" in saved_profile:
                    saved_profile_ids.add(saved_profile["profile_id"])

        # Add is_saved flag to each student
        for student in students:
            student["is_saved"] = student["id"] in saved_profile_ids

        # Pass allowed skills for dropdown
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
        )
    except Exception as e:
        flash(f"Error searching talent: {str(e)}", "error")
        return render_template("talent_search.html", students=[])


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

        # For drafts, allow any skills without validation. For active opportunities, validate against database
        if status == "draft":
            skills_needed_json = normalize_skills_for_draft(
                request.form.get("skills_needed")
            )
        else:
            skills_needed_json = normalize_and_validate_skills(
                request.form.get("skills_needed")
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
        }

        # For drafts, ensure all keys exist, but allow None values
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
                # Re-normalize skills for draft since status changed
                opportunity_data["skills_needed"] = normalize_skills_for_draft(
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
                # Re-normalize skills for draft since status is draft
                opportunity_data["skills_needed"] = normalize_skills_for_draft(
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

    print(f"DEBUG - Save profile request:")
    print(f"  User ID: {user_id}")
    print(f"  User Type: {user_type}")
    print(f"  Profile ID to save: {profile_id}")

    try:
        result = supabase_service.save_profile(user_id, profile_id)
        print(f"DEBUG - Supabase save_profile result: {result}")

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
        print(f"DEBUG - Exception in save_profile route: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/unsave_profile/<profile_id>", methods=["POST"])
def unsave_profile(profile_id):
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    user_id = session.get("user_id")

    try:
        result = supabase_service.unsave_profile(user_id, profile_id)
        return jsonify({"success": True, "message": "Profile removed from saved"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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


@app.route("/add_skill", methods=["POST"])
def add_skill():
    """Add a new skill to the skills database."""
    if "user_id" not in session:
        return {"success": False, "error": "Authentication required"}, 401

    try:
        data = request.get_json()
        if not data or "skill" not in data:
            return {"success": False, "error": "Skill name is required"}, 400

        skill_name = data["skill"].strip()
        if not skill_name:
            return {"success": False, "error": "Skill name cannot be empty"}, 400

        # Validate skill name (no special characters, reasonable length)
        if len(skill_name) > 100:
            return {"success": False, "error": "Skill name too long"}, 400

        if not skill_name.replace(" ", "").replace("-", "").replace(".", "").isalnum():
            return {
                "success": False,
                "error": "Skill name contains invalid characters",
            }, 400

        # Add the skill to the database
        result = supabase_service.add_new_skill(skill_name, session.get("user_id"))

        if result["success"]:
            # No need to maintain in-memory list - always fetch from database
            return {"success": True, "skill": result["skill"]}
        else:
            return {"success": False, "error": result["error"]}, 400

    except Exception as e:
        logger.error(f"Error adding skill: {str(e)}")
        return {"success": False, "error": str(e)}, 500


@app.route("/chat")
def chat():
    """AI chatbot interface for InterSpark."""
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Initialize chat history in session if it doesn't exist
    if "chat_history" not in session:
        session["chat_history"] = []

    return render_template("chat.html", chat_history=session["chat_history"])


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

        # Initialize chat history if not exists
        if "chat_history" not in session:
            session["chat_history"] = []

        # Add user message to history
        session["chat_history"].append(
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
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
                user_message, db_results, session["chat_history"]
            )
        else:
            # Fallback response without AI
            ai_response = generate_fallback_response(user_message, db_results)

        # Add AI response to history
        session["chat_history"].append(
            {
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Keep only last 20 messages to prevent session bloat
        if len(session["chat_history"]) > 20:
            session["chat_history"] = session["chat_history"][-20:]

        return jsonify(
            {"success": True, "response": ai_response, "db_results": db_results}
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

    session["chat_history"] = []
    return jsonify({"success": True, "message": "Chat history cleared"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

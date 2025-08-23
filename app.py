from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
import os
from datetime import datetime
from supabase_config import supabase_service

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "2a15f8283ab2353f15089e80d8acf104")


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
        user_type = request.form.get("user_type", "student")

        # Authenticate with Supabase
        try:
            auth_result = supabase_service.authenticate_user(email, password)

            if auth_result["success"]:
                user = auth_result["user"]
                profile = auth_result["profile"]

                print(f"DEBUG - Login attempt:")
                print(f"  Requested user_type: '{user_type}'")
                print(f"  Profile exists: {profile is not None}")
                if profile:
                    print(f"  Profile user_type: '{profile.get('user_type')}'")
                    print(f"  Profile name: '{profile.get('name')}'")

                # Check if user type matches
                if profile and profile.get("user_type") == user_type:
                    session["user_id"] = user["id"]
                    session["user_type"] = profile["user_type"]
                    session["user_name"] = profile["name"]
                    session["user_email"] = profile["email"]

                    flash("Login successful!", "success")
                    return redirect(url_for("dashboard"))
                elif (
                    profile
                    and profile.get("user_type") == "student"
                    and profile.get("name") == "User"
                ):
                    # This is a newly created default profile, let's update it with the selected user type
                    try:
                        update_result = supabase_service.update_profile(
                            user["id"], {"user_type": user_type}
                        )
                        if update_result["success"]:
                            session["user_id"] = user["id"]
                            session["user_type"] = user_type
                            session["user_name"] = profile["name"]
                            session["user_email"] = profile["email"]

                            flash(
                                "Login successful! Please complete your profile.",
                                "success",
                            )
                            return redirect(url_for("profile"))
                        else:
                            flash(
                                "Login successful, but there was an issue updating your profile.",
                                "warning",
                            )
                    except Exception as update_error:
                        print(f"Error updating profile: {update_error}")
                        flash(
                            "Login successful, but there was an issue updating your profile.",
                            "warning",
                        )

                    # Fall back to basic login even if update failed
                    session["user_id"] = user["id"]
                    session["user_type"] = user_type  # Use the selected type
                    session["user_name"] = profile["name"]
                    session["user_email"] = profile["email"]
                    return redirect(url_for("dashboard"))
                else:
                    if not profile:
                        flash(
                            "User profile not found. Please contact support.", "error"
                        )
                    else:
                        flash(
                            f"Invalid user type selected. Your account is registered as '{profile.get('user_type')}'",
                            "error",
                        )
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
            company_opportunities = supabase_service.get_organization_opportunities(user_id)
            # Ensure all opportunities are dicts with all expected fields
            expected_fields = ["title", "description", "type", "category", "location", "requirements", "compensation", "duration", "application_deadline", "status"]
            for opp in company_opportunities:
                for field in expected_fields:
                    if field not in opp:
                        opp[field] = None
                print("company_opportunities for dashboard:", company_opportunities)
                # Extra: ensure every opportunity is a dict and has all expected fields
                for i, opp in enumerate(company_opportunities):
                    if not isinstance(opp, dict):
                        company_opportunities[i] = dict(opp)
                    for field in expected_fields:
                        if field not in company_opportunities[i] or company_opportunities[i][field] is None:
                            company_opportunities[i][field] = '' if field in ['title', 'description', 'type', 'category', 'location', 'requirements', 'compensation', 'duration'] else None
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
            profile_data = {
                "name": request.form.get("full_name"),
                "school": request.form.get("school"),
                "grade": request.form.get("grade"),
                "skills": request.form.get("skills"),
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
        profile_data = {
            k: v for k, v in profile_data.items() if v is not None and v.strip() != ""
        }

        print(f"DEBUG - Profile update attempt:")
        print(f"  User ID: {user_id}")
        print(f"  User Type: {user_type}")
        print(f"  Profile data: {profile_data}")

        try:
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
        return render_template(
            "profile.html",
            user_type=user_type,
            profile=profile,
            user=profile,
            is_own_profile=True,
            read_only=False,
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

    # Get Talent Search filter params from query string
    search_query = request.args.get("search", "")
    skills = request.args.get("skills", "")
    school = request.args.get("school", "")
    grade = request.args.get("grade", "")

    return render_template(
        "profile.html",
        user_type=profile.get("user_type", "student"),
        profile=profile,
        user=profile,
        is_own_profile=is_own_profile,
        is_saved=is_saved,
        read_only=not is_own_profile,
        back_to_talent_search=True,
        search_query=search_query,
        selected_skills=skills,
        selected_school=school,
        selected_grade=grade,
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

        # Fetch opportunities with filters
        opportunities = supabase_service.search_opportunities(
            search_query=search_query,
            opportunity_type=opportunity_type,
            category=category,
            location=location,
        )

        return render_template(
            "opportunities.html",
            opportunities=opportunities,
            search_query=search_query,
            selected_type=opportunity_type,
            selected_category=category,
            selected_location=location,
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
        # Get filters from query parameters
        search_query = request.args.get("search", "")
        skills = request.args.get("skills", "")
        school = request.args.get("school", "")
        grade = request.args.get("grade", "")

        # Search for students
        students = supabase_service.search_students(
            search_query=search_query, skills=skills, school=school, grade=grade
        )

        return render_template(
            "talent_search.html",
            students=students,
            search_query=search_query,
            selected_skills=skills,
            selected_school=school,
            selected_grade=grade,
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

    if request.method == "POST":
        # Get form data and map to database fields
        status = request.form.get("status", "active")
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
            "status": status,
        }

        # For drafts, ensure all keys exist, but allow None values
        if status == "draft":
            for key in ["title", "description", "type", "category", "location", "requirements", "compensation", "duration", "application_deadline"]:
                if opportunity_data.get(key) is None:
                    opportunity_data[key] = None

        # Add company_id only for new opportunities
        if not is_editing:
            opportunity_data["company_id"] = user_id

        try:
            # If editing and publishing, require all fields
            is_publish = request.form.get("publish") == "1"
            required_fields = ["title", "description", "type", "category", "location", "requirements", "compensation", "duration", "application_deadline"]
            if is_editing and is_publish:
                # Publishing: require all fields
                missing = [f for f in required_fields if not opportunity_data.get(f)]
                if missing:
                    flash(f"Missing required fields for publishing: {', '.join(missing)}. Complete all fields to publish.", "error")
                    return render_template("create_opportunity.html", opportunity=opportunity_data, is_editing=is_editing, missing_fields=missing)
                opportunity_data["status"] = "active"
                result = supabase_service.update_opportunity(opportunity_id, opportunity_data)
                success_message = "Opportunity published successfully!"
                redirect_route = url_for("opportunity_details", id=opportunity_id)
            elif is_editing:
                # Regular update, always keep as draft
                opportunity_data["status"] = "draft"
                result = supabase_service.update_opportunity(opportunity_id, opportunity_data)
                success_message = "Opportunity updated successfully!"
                redirect_route = url_for("opportunity_details", id=opportunity_id)
            elif not is_editing and status == "active":
                # Creating and publishing
                missing = [f for f in required_fields if not opportunity_data.get(f)]
                if missing:
                    flash(f"Missing required fields for publishing: {', '.join(missing)}. Complete all fields to publish.", "error")
                    return render_template("create_opportunity.html", opportunity=opportunity_data, is_editing=is_editing, missing_fields=missing)
                opportunity_data["status"] = "active"
                result = supabase_service.create_opportunity(opportunity_data)
                success_message = "Opportunity created successfully!"
                redirect_route = url_for("dashboard")
            else:
                # Save as draft
                opportunity_data["status"] = "draft"
                result = supabase_service.create_opportunity(opportunity_data)
                success_message = "Draft saved successfully!"
                redirect_route = url_for("dashboard")

            if result["success"]:
                flash(success_message, "success")
                return redirect(redirect_route)
            else:
                error_message = "Failed to update opportunity" if is_editing else "Failed to create opportunity"
                flash(result.get("error", error_message), "error")
        except Exception as e:
            error_message = f"Error updating opportunity: {str(e)}" if is_editing else f"Error creating opportunity: {str(e)}"
            flash(error_message, "error")

    return render_template("create_opportunity.html", opportunity=opportunity, is_editing=is_editing)


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
        print(f"Delete request for opportunity_id={opportunity_id}, found: {opportunity}")
        if not opportunity:
            print("Opportunity not found for deletion.")
            return {"success": False, "error": "Opportunity not found"}, 404

        # Check if user owns this opportunity
        if opportunity.get("company_id") != user_id:
            print(f"User {user_id} does not own opportunity {opportunity_id} (company_id={opportunity.get('company_id')})")
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
        return {"success": False, "error": "Not authenticated"}, 401

    user_id = session.get("user_id")

    try:
        result = supabase_service.save_profile(user_id, profile_id)
        if result["success"]:
            return {"success": True, "message": "Profile saved successfully"}
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to save profile"),
            }, 400
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


@app.route("/unsave_profile/<profile_id>", methods=["POST"])
def unsave_profile(profile_id):
    if "user_id" not in session:
        return {"success": False, "error": "Not authenticated"}, 401

    user_id = session.get("user_id")

    try:
        result = supabase_service.unsave_profile(user_id, profile_id)
        return {"success": True, "message": "Profile removed from saved"}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


if __name__ == "__main__":
    import os

    app.run(debug=True, port=5000)

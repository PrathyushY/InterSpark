from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-change-this-in-production"

# TODO: Add Supabase configuration here


@app.route("/")
def home():
    # TODO: Replace with Supabase query to get featured opportunities
    opportunities = []  # Placeholder - will be replaced with Supabase data
    return render_template("home.html", opportunities=opportunities)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user_type = request.form.get("user_type", "student")

        # TODO: Replace with Supabase authentication
        flash("Login functionality will be implemented with Supabase", "info")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        user_type = request.form["user_type"]

        # TODO: Replace with Supabase user creation
        flash("Signup functionality will be implemented with Supabase", "info")
        return render_template("signup.html")

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # TODO: Replace with Supabase queries
    # Mock user data for now
    user = {
        "id": session.get("user_id"),
        "name": session.get("user_name", "User"),
        "user_type": session.get("user_type", "student"),
        "email": "user@example.com",
    }

    opportunities = []  # Placeholder - will be replaced with Supabase data
    return render_template("dashboard.html", user=user, opportunities=opportunities)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # TODO: Replace with Supabase queries
    # Mock user data for now
    user = {
        "id": session.get("user_id"),
        "name": session.get("user_name", "User"),
        "user_type": session.get("user_type", "student"),
        "email": "user@example.com",
        "phone": "",
        "location": "",
        "school": "",
        "grade": "",
        "bio": "",
        "interests": "",
        "description": "",
        "website": "",
    }

    if request.method == "POST":
        # TODO: Replace with Supabase update
        flash("Profile update functionality will be implemented with Supabase", "info")

    return render_template("profile.html", user=user)


@app.route("/opportunities")
def opportunities():
    # TODO: Replace with Supabase query
    opportunities = []  # Placeholder - will be replaced with Supabase data
    return render_template("opportunities.html", opportunities=opportunities)


@app.route("/opportunity/<int:id>")
def opportunity_details(id):
    # TODO: Replace with Supabase query
    # Mock opportunity data for now
    opportunity = {
        "id": id,
        "title": "Sample Opportunity",
        "description": "This is a placeholder opportunity. Data will be loaded from Supabase.",
        "organization": {"name": "Sample Organization", "email": "org@example.com"},
    }
    return render_template("opportunity_details.html", opportunity=opportunity)


@app.route("/talent")
def talent_search():
    # TODO: Replace with Supabase query
    students = []  # Placeholder - will be replaced with Supabase data
    return render_template("talent_search.html", students=students)


@app.route("/create_opportunity", methods=["GET", "POST"])
def create_opportunity():
    if "user_id" not in session or session.get("user_type") != "organization":
        flash(
            "You must be logged in as an organization to create opportunities", "error"
        )
        return redirect(url_for("login"))

    if request.method == "POST":
        # TODO: Replace with Supabase insert
        flash(
            "Opportunity creation functionality will be implemented with Supabase",
            "info",
        )
        return redirect(url_for("dashboard"))

    return render_template("create_opportunity.html")


if __name__ == "__main__":
    app.run(debug=True)

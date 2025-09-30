from flask import Blueprint, render_template, request, redirect, url_for, session, flash

auth_bp = Blueprint("auth", __name__, template_folder="templates")

# MVP users in memory
USERS = {"demo@habit.com": {"password": "123456", "name": "Demo"}}


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        pwd = request.form.get("password", "")
        user = USERS.get(email)
        if user and user["password"] == pwd:
            session["user"] = {"email": email, "name": user["name"]}
            flash("Welcome!", "success")
            return redirect(url_for("progress.panel"))
        flash("Invalid credentials", "danger")
    return render_template("auth/login.html", title="Sign in")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Signed out", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Stub for MVP
    return render_template("auth/register.html", title="Create account")

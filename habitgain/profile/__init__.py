from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..models import User, count_active_habits_from_db
from ..auth import USERS as AUTH_USERS  # login en memoria heredado

import secrets

profile_bp = Blueprint("profile", __name__, template_folder="templates")


def _require_login():
    if "user" not in session:
        flash("Please sign in to access this page.", "warning")
        return False
    return True


def _get_csrf_token() -> str:
    token = secrets.token_urlsafe(32)
    session["csrf_token"] = token
    session.modified = True
    return token


@profile_bp.route("/edit", methods=["GET", "POST"])
def edit():
    # Guard
    if not _require_login():
        return redirect(url_for("auth.login"))

    user_email = session["user"]["email"]

    # Asegura que exista registro en BD para operar perfil
    User.ensure_exists(
        email=user_email,
        name=session["user"].get("name", "User"),
    )

    if request.method == "POST":
        # CSRF check
        form_token = request.form.get("csrf_token", "")
        sess_token = session.pop("csrf_token", None)
        if not sess_token or form_token != sess_token:
            flash("Invalid or missing CSRF token.", "danger")
            return redirect(url_for("profile.edit"))

        # Form inputs
        new_name = (request.form.get("name") or "").strip()
        new_password = (request.form.get("new_password") or "").strip()
        confirm = (request.form.get("confirm_password") or "").strip()

        # Validación
        errors = []
        if not (1 <= len(new_name) <= 80):
            errors.append("Name must be between 1 and 80 characters.")
        if new_password:
            if len(new_password) < 8:
                errors.append("Password must be at least 8 characters.")
            if new_password != confirm:
                errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return redirect(url_for("profile.edit"))

        # Persistencia
        User.update_name(user_email, new_name)
        if new_password:
            User.update_password(user_email, new_password)
            # Mantener coherencia con el login en memoria del MVP
            if user_email in AUTH_USERS:
                AUTH_USERS[user_email]["password"] = new_password

        # Reflejar en sesión e in-memory
        session["user"]["name"] = new_name
        session.modified = True
        if user_email in AUTH_USERS:
            AUTH_USERS[user_email]["name"] = new_name

        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile.edit"))

    # GET
    user_data = User.get_by_email(user_email) or {
        "email": user_email,
        "name": session["user"].get("name", ""),
    }

    # Conteo de hábitos: ahora desde BD, no desde USER_HABITS
    habits_count = count_active_habits_from_db(user_email)

    csrf_token = _get_csrf_token()
    return render_template(
        "profile/edit.html",
        user=user_data,
        habits_count=habits_count,
        csrf_token=csrf_token,
    )

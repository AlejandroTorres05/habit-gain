from flask import Blueprint, render_template, session, redirect, url_for, flash
from ..models import User

premium_bp = Blueprint("premium", __name__, template_folder="templates")


@premium_bp.route("/premium")
def plans():
    if "user" not in session:
        flash("Debes iniciar sesión para ver los planes Premium.", "info")
        return redirect(url_for("auth.login"))

    user_email = session["user"].get("email")
    user = User.get_by_email(user_email) if user_email else None
    current_plan = (user.get("plan") or "free") if user else "free"

    return render_template("premium/plans.html", title="Planes Premium", current_plan=current_plan)

from flask import Blueprint, render_template, session, redirect, url_for
from ..habits import USER_HABITS

progress_bp = Blueprint("progress", __name__, template_folder="templates")

@progress_bp.route("/panel")
def panel():
    user = (session.get("user") or {}).get("email")
    if not user:
        return redirect(url_for("auth.login"))
    habits = USER_HABITS.get(user, [])
    completed = sum(1 for h in habits if h.get("done"))
    return render_template("progress/panel.html",
                           habits=habits, completed=completed, total=len(habits))

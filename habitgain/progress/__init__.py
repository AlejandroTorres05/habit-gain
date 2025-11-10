from flask import Blueprint, render_template, session, redirect, url_for
from ..models import Habit

progress_bp = Blueprint("progress", __name__, template_folder="templates")


@progress_bp.route("/panel")
def panel():
    """
    Panel de hábitos diario basado en la BD.

    - Lista hábitos activos del usuario (tabla habits).
    - completed/total por ahora solo cuenta activos; cuando tengas check-ins,
      aquí se calcula en serio.
    """
    user_email = (session.get("user") or {}).get("email")
    if not user_email:
        return redirect(url_for("auth.login"))

    habits = Habit.list_active_by_owner(user_email)
    completed = 0        # aún no hay registro real de completados por día
    total = len(habits)

    return render_template(
        "progress/panel.html",
        habits=habits,
        completed=completed,
        total=total,
    )

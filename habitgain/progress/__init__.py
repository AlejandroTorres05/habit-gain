from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
import datetime as _dt
import secrets
from ..models import Habit, Completion, DailyProgress

progress_bp = Blueprint("progress", __name__, template_folder="templates")


@progress_bp.route("/panel")
def panel():
    user = (session.get("user") or {}).get("email")
    if not user:
        return redirect(url_for("auth.login"))

    # Hábitos activos desde DB
    habits = Habit.list_active_by_owner(user)

    # Completados hoy
    completed_today_ids = set(Completion.completed_today_ids(user))
    completed = len(completed_today_ids)
    total_active_today = len(habits)

    # Denominador: máximo planificado del día (no baja si eliminas; puede subir si agregas)
    today = end_date = _dt.date.today()
    planned_total_max = DailyProgress.ensure_and_get_planned_max(user, today.isoformat(), total_active_today)
    denom = max(1, planned_total_max)
    percent = int(round((completed / denom) * 100))
    if percent < 0:
        percent = 0
    if percent > 100:
        percent = 100

    # Estadísticas últimos 7 días (días cumplidos vs planificados)
    start_date = end_date - _dt.timedelta(days=6)
    days_completed = Completion.count_days_with_completion(user, start_date.isoformat(), end_date.isoformat())
    days_planned = 7  # objetivo simple: cumplir algo cada día en la última semana

    # CSRF token para acciones POST del panel
    csrf_token = secrets.token_urlsafe(32)
    session["csrf_token_progress"] = csrf_token
    session.modified = True

    return render_template(
        "progress/panel.html",
        habits=habits,
        completed=completed,
        total=total_active_today,
        completed_today_ids=completed_today_ids,
        days_completed=days_completed,
        days_planned=days_planned,
        percent=percent,
        planned_total_max=planned_total_max,
        csrf_token=csrf_token,
    )


@progress_bp.route("/complete/<int:habit_id>", methods=["POST"])
def complete(habit_id: int):
    user = (session.get("user") or {}).get("email")
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    # CSRF check
    header_token = request.headers.get("X-CSRF-Token", "")
    sess_token = session.get("csrf_token_progress")
    if not sess_token or header_token != sess_token:
        return jsonify({"ok": False, "error": "invalid_csrf"}), 400
    try:
        Completion.mark_completed(habit_id, user)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

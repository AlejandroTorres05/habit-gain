from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
import datetime as _dt
import calendar as _cal
import secrets
from ..models import Habit, Completion, DailyProgress, Category, OnboardingStatus
from ..behavioral_science import MotivationalMessages, calculate_user_motivation_stats

progress_bp = Blueprint("progress", __name__, template_folder="templates")


@progress_bp.route("/panel")
def panel():
    """
    Panel de hábitos diario basado en la BD.

    - Lista hábitos activos del usuario (tabla habits).
    - completed/total por ahora solo cuenta activos; cuando tengas check-ins,
      aquí se calcula en serio.
    """
    user = (session.get("user") or {}).get("email")
    if not user:
        return redirect(url_for("auth.login"))

    # Hábitos activos desde DB
    habits = Habit.list_active_by_owner(user)

    # Enrich stacking info: base habit name for display
    id_to_name = {h["id"]: h.get("name") for h in habits}
    for h in habits:
        base_id = h.get("habit_base_id")
        if base_id:
            base_name = id_to_name.get(base_id)
            if not base_name:
                base = Habit.get_by_id(int(base_id))
                base_name = base.get("name") if base else None
            h["base_name"] = base_name

    # Enrich category names for badges
    cats = {c["id"]: c["name"] for c in Category.all()}
    for h in habits:
        cid = h.get("category_id")
        if cid:
            h["category_name"] = cats.get(cid)

    # HU-8: Calcular fortaleza de cada hábito basado en racha de cumplimiento
    for h in habits:
        strength_data = Completion.calculate_strength(h["id"], user)
        h["strength"] = strength_data["strength"]
        h["strength_level"] = strength_data["level"]
        h["strength_color"] = strength_data["color"]
        h["streak"] = strength_data["streak"]

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

    # Agrupar por hábito base y calcular "siguientes" sugeridos
    bases = [h for h in habits if not h.get("habit_base_id")]
    children_map = {}
    for h in habits:
        b = h.get("habit_base_id")
        if b:
            children_map.setdefault(int(b), []).append(h)
    next_due_ids = {h["id"] for h in habits if h.get("habit_base_id") in completed_today_ids and h["id"] not in completed_today_ids}

    # Separar pendientes vs completados (bases y vinculados) para dos secciones
    bases_pending = [b for b in bases if b["id"] not in completed_today_ids]
    bases_completed = [b for b in bases if b["id"] in completed_today_ids]
    children_pending_map = {}
    children_completed_map = {}
    for base in bases:
        for child in children_map.get(base["id"], []):
            target = children_completed_map if child["id"] in completed_today_ids else children_pending_map
            target.setdefault(base["id"], []).append(child)

    # CSRF token para acciones POST del panel
    csrf_token = secrets.token_urlsafe(32)
    session["csrf_token_progress"] = csrf_token
    session.modified = True

    # HU-17 CDA3: Calcular mensaje motivacional
    motivation_stats = calculate_user_motivation_stats(
        user_email=user,
        habits=habits,
        completed_today_ids=completed_today_ids,
        days_completed=days_completed
    )
    motivation_message = MotivationalMessages.get_message_for_user(motivation_stats)

    # TT-12 CDA2: Detectar pérdida de racha (ayer hubo actividad y hoy no)
    streak_loss_message = None
    if completed == 0 and motivation_stats.get("max_streak", 0) > 0:
        yesterday = today - _dt.timedelta(days=1)
        yesterday_completed = Completion.count_days_with_completion(
            user,
            yesterday.isoformat(),
            yesterday.isoformat(),
        )
        if yesterday_completed > 0:
            streak_loss_message = {
                "title": "¡No te desanimes!",
                "text": "Ayer mantenías una racha activa. Hoy es el día 1 de tu nueva mejor racha.",
            }

    # HU-18: Verificar si el usuario necesita onboarding
    needs_onboarding = OnboardingStatus.needs_onboarding(user)

    return render_template(
        "progress/panel.html",
        habits=habits,
        bases=bases,
        children_map=children_map,
        bases_pending=bases_pending,
        bases_completed=bases_completed,
        children_pending_map=children_pending_map,
        children_completed_map=children_completed_map,
        completed=completed,
        total=total_active_today,
        completed_today_ids=completed_today_ids,
        days_completed=days_completed,
        days_planned=days_planned,
        percent=percent,
        planned_total_max=planned_total_max,
        next_due_ids=next_due_ids,
        csrf_token=csrf_token,
        motivation_message=motivation_message,
        streak_loss_message=streak_loss_message,
        needs_onboarding=needs_onboarding,
    )


@progress_bp.route("/stats")
def stats():
    """Pantalla de estadísticas: calendario mensual + métricas de rendimiento.

    Implementa TT-12 CDA3 y CDA4.
    """
    user = (session.get("user") or {}).get("email")
    if not user:
        return redirect(url_for("auth.login"))

    # Parámetros opcionales de mes/año, por defecto mes actual
    today = _dt.date.today()
    year = request.args.get("year", type=int) or today.year
    month = request.args.get("month", type=int) or today.month

    # Hábitos del usuario (para calcular rachas)
    habits = Habit.list_active_by_owner(user)

    # Racha actual (máximo entre hábitos activos)
    current_streak = 0
    current_streak_habit_name = None
    for h in habits:
        s = Completion.get_current_streak(h["id"], user)
        if s > current_streak:
            current_streak = s
            current_streak_habit_name = h.get("name")

    # Mejor racha histórica (máximo best_streak entre hábitos)
    best_streak = 0
    for h in habits:
        bs = Completion.get_best_streak(h["id"], user)
        if bs > best_streak:
            best_streak = bs

    # Tasa de cumplimiento últimos 30 días
    window_days = 30
    start_30 = today - _dt.timedelta(days=window_days - 1)
    completion_dates_30 = set(
        Completion.get_completion_dates_in_range(
            user,
            start_30.isoformat(),
            today.isoformat(),
        )
    )
    success_days_30 = len(completion_dates_30)
    compliance_rate_30 = int(round((success_days_30 / window_days) * 100)) if window_days > 0 else 0

    # Calendario mensual (heatmap)
    cal = _cal.Calendar(firstweekday=0)
    month_weeks = []

    # Rango de fechas del mes
    first_of_month = _dt.date(year, month, 1)
    if month == 12:
        first_next = _dt.date(year + 1, 1, 1)
    else:
        first_next = _dt.date(year, month + 1, 1)
    last_of_month = first_next - _dt.timedelta(days=1)

    completion_dates_month = set(
        Completion.get_completion_dates_in_range(
            user,
            first_of_month.isoformat(),
            last_of_month.isoformat(),
        )
    )

    for week in cal.monthdatescalendar(year, month):
        week_cells = []
        for day in week:
            day_str = day.isoformat()
            in_month = (day.month == month)
            if not in_month:
                status = "other-month"
            elif day > today:
                status = "future"
            elif day_str in completion_dates_month:
                status = "completed"
            else:
                status = "missed"
            week_cells.append({
                "date": day,
                "in_month": in_month,
                "status": status,
            })
        month_weeks.append(week_cells)

    month_name = first_of_month.strftime("%B")

    return render_template(
        "progress/stats.html",
        habits=habits,
        year=year,
        month=month,
        month_name=month_name,
        month_weeks=month_weeks,
        today=today,
        current_streak=current_streak,
        current_streak_habit_name=current_streak_habit_name,
        best_streak=best_streak,
        compliance_rate_30=compliance_rate_30,
        success_days_30=success_days_30,
        window_days_30=window_days,
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
        # HU-8 CDA3: Calcular fortaleza actualizada en tiempo real
        strength_data = Completion.calculate_strength(habit_id, user)
        return jsonify({
            "ok": True,
            "strength": strength_data["strength"],
            "strength_level": strength_data["level"],
            "strength_color": strength_data["color"],
            "streak": strength_data["streak"]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

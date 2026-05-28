"""
HU-18: Onboarding Interactivo + Onboarding de Metas (emprendedores)
Blueprint para gestionar el onboarding de nuevos usuarios
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from ..models import OnboardingStatus, UserGoal, Habit

onboarding_bp = Blueprint("onboarding", __name__, template_folder="templates")

# Hábitos sugeridos para el demo (meta: construir base de clientes)
# Basados en Fanatical Prospecting (Blount), Never Split the Difference (Voss) y Atomic Habits (Clear)
DEMO_HABITS = [
    {
        "name": "Bloque de prospección matutina",
        "short_desc": "30 minutos diarios protegidos para conectar con nuevos prospectos, antes de cualquier otra tarea",
        "icon": "🌅",
        "frequency": "daily",
        "category_id": 2,
    },
    {
        "name": "Escucha activa en conversaciones",
        "short_desc": "En cada reunión o llamada, hacer al menos 3 preguntas abiertas y tomar nota de lo que realmente necesita el interlocutor",
        "icon": "👂",
        "frequency": "daily",
        "category_id": 1,
    },
    {
        "name": "Publicar contenido de valor",
        "short_desc": "Compartir un aprendizaje, insight o experiencia útil para tu audiencia objetivo en LinkedIn u otra red",
        "icon": "✍️",
        "frequency": "weekly",
        "category_id": 2,
    },
    {
        "name": "Conversación de networking 1:1",
        "short_desc": "Tener una conversación genuina con alguien de tu industria sin expectativa de venta inmediata",
        "icon": "🤝",
        "frequency": "weekly",
        "category_id": 1,
    },
    {
        "name": "Reflexión diaria de conversaciones",
        "short_desc": "Dedicar 15 minutos al final del día para anotar qué funcionó, qué no, y qué ajustar en las próximas interacciones",
        "icon": "📓",
        "frequency": "daily",
        "category_id": 2,
    },
]


@onboarding_bp.route("/goal", methods=["GET"])
def goal_input():
    user = session.get("user")
    if not user:
        return redirect(url_for("auth.login"))
    return render_template("onboarding/goal_input.html")


@onboarding_bp.route("/goal", methods=["POST"])
def goal_input_post():
    user = session.get("user")
    if not user:
        return redirect(url_for("auth.login"))

    goal_text = request.form.get("goal_text", "").strip()
    if not goal_text:
        flash("Por favor escribe tu meta antes de continuar.", "warning")
        return redirect(url_for("onboarding.goal_input"))

    UserGoal.set_goal(user["email"], goal_text)
    session["pending_goal_text"] = goal_text
    session.modified = True
    return redirect(url_for("onboarding.habit_suggest"))


@onboarding_bp.route("/habits", methods=["GET"])
def habit_suggest():
    user = session.get("user")
    if not user:
        return redirect(url_for("auth.login"))

    goal_text = session.get("pending_goal_text") or (
        (UserGoal.get_active(user["email"]) or {}).get("goal_text", "")
    )
    return render_template(
        "onboarding/habit_suggest.html",
        goal_text=goal_text,
        habits=DEMO_HABITS,
    )


@onboarding_bp.route("/habits", methods=["POST"])
def habit_suggest_post():
    user = session.get("user")
    if not user:
        return redirect(url_for("auth.login"))

    selected_indices = request.form.getlist("habit_idx")
    user_email = user["email"]

    for idx_str in selected_indices:
        try:
            idx = int(idx_str)
            if 0 <= idx < len(DEMO_HABITS):
                h = DEMO_HABITS[idx]
                Habit.create(
                    email=user_email,
                    name=h["name"],
                    short_desc=h["short_desc"],
                    category_id=h["category_id"],
                    frequency=h["frequency"],
                    icon=h["icon"],
                )
        except (ValueError, Exception):
            continue

    OnboardingStatus.mark_completed(user_email)
    session.pop("pending_goal_text", None)
    flash("¡Tus hábitos están listos! Empieza a trabajar en tu meta hoy.", "success")
    return redirect(url_for("progress.panel"))


@onboarding_bp.route("/step", methods=["POST"])
def mark_step():
    """
    Marca un paso del onboarding como completado.
    Recibe: { "step": 0-4 }
    """
    user = session.get("user")
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        data = request.get_json()
        step_number = data.get("step")

        if step_number is None or not isinstance(step_number, int):
            return jsonify({"error": "Número de paso inválido"}), 400

        if step_number < 0 or step_number >= 5:
            return jsonify({"error": "Paso fuera de rango"}), 400

        user_email = user["email"]
        OnboardingStatus.mark_step_complete(user_email, step_number)

        return jsonify({"ok": True, "step": step_number}), 200

    except Exception as e:
        print(f"Error al marcar paso: {e}")
        return jsonify({"error": str(e)}), 500


@onboarding_bp.route("/skip", methods=["POST"])
def skip():
    """
    Marca el onboarding como saltado por el usuario.
    """
    user = session.get("user")
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        user_email = user["email"]
        OnboardingStatus.mark_skipped(user_email)

        return jsonify({"ok": True, "skipped": True}), 200

    except Exception as e:
        print(f"Error al saltar onboarding: {e}")
        return jsonify({"error": str(e)}), 500


@onboarding_bp.route("/reset", methods=["POST"])
def reset():
    """
    Reinicia el onboarding para el usuario actual.
    Útil para volver a ver el tutorial.
    """
    user = session.get("user")
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        user_email = user["email"]
        OnboardingStatus.reset_status(user_email)

        return jsonify({"ok": True, "reset": True}), 200

    except Exception as e:
        print(f"Error al reiniciar onboarding: {e}")
        return jsonify({"error": str(e)}), 500


@onboarding_bp.route("/status", methods=["GET"])
def status():
    """
    Obtiene el estado del onboarding del usuario actual.
    """
    user = session.get("user")
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        user_email = user["email"]
        onboarding_status = OnboardingStatus.get_status(user_email)

        if onboarding_status is None:
            return jsonify({
                "needs_onboarding": True,
                "completed": False,
                "current_step": 0,
                "skipped": False
            }), 200

        return jsonify({
            "needs_onboarding": OnboardingStatus.needs_onboarding(user_email),
            "completed": onboarding_status["completed"],
            "current_step": onboarding_status["current_step"],
            "skipped": onboarding_status["skipped"],
            "steps_completed": onboarding_status["steps_completed"]
        }), 200

    except Exception as e:
        print(f"Error al obtener estado: {e}")
        return jsonify({"error": str(e)}), 500


@onboarding_bp.route("/complete", methods=["POST"])
def complete():
    """
    Marca el onboarding como completado por el usuario.
    """
    user = session.get("user")
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        user_email = user["email"]
        OnboardingStatus.mark_completed(user_email)

        return jsonify({"ok": True, "completed": True}), 200

    except Exception as e:
        print(f"Error al completar onboarding: {e}")
        return jsonify({"error": str(e)}), 500


@onboarding_bp.route("/analytics", methods=["GET"])
def analytics():
    """
    Obtiene analytics del onboarding (solo para admins).
    """
    user = session.get("user")
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    # TODO: Verificar si el usuario es admin
    # Por ahora, cualquier usuario autenticado puede ver las estadísticas

    try:
        stats = OnboardingStatus.get_analytics()
        return jsonify(stats), 200

    except Exception as e:
        print(f"Error al obtener analytics: {e}")
        return jsonify({"error": str(e)}), 500

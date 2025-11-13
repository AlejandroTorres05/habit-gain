"""
HU-18: Onboarding Interactivo
Blueprint para gestionar el onboarding de nuevos usuarios
"""

from flask import Blueprint, request, jsonify, session
from ..models import OnboardingStatus

onboarding_bp = Blueprint("onboarding", __name__, template_folder="templates")


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

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..models import Habit

habits_bp = Blueprint("habits", __name__, template_folder="templates")


def _user_email():
    return (session.get("user") or {}).get("email")


# HU5: Crear nuevo hábito con Habit Stacking (ahora usando BD)
@habits_bp.route("/new", methods=["GET", "POST"])
def create():
    user = _user_email()
    if not user:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        # Obtener datos del formulario
        nombre = (request.form.get("nombre")
                  or request.form.get("name") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        categoria = (request.form.get("categoria") or "General").strip()
        frecuencia = request.form.get("frecuencia") or "diaria"
        habit_base_id = request.form.get(
            "habit_base_id") or request.form.get("stack_after") or ""

        # Validaciones
        if not nombre:
            flash("El nombre del hábito es obligatorio", "warning")
            return render_template(
                "habits/new.html",
                habitos_existentes=Habit.list_by_owner(user),
                categorias=_get_categorias(),
            )

        # HU-18: validar duplicados también aquí (no sólo en explore)
        if Habit.exists_by_name(user, nombre):
            flash("Ya tienes un hábito con ese nombre. Intenta con otro.", "warning")
            return redirect(url_for("progress.panel"))

        # Crear nuevo hábito en la BD
        # Nota: por ahora no persistimos stacking en columnas, sólo como mensaje.
        Habit.create(
            email=user,
            name=nombre,
            short_desc=descripcion,
            # Podríamos mapear categoria -> category_id; por ahora usamos default
            category_id=None,
        )

        # Mensaje de éxito personalizado
        if habit_base_id:
            habit_base = _get_habit_by_id(user, int(habit_base_id))
            if habit_base:
                base_name = habit_base.get("nombre") or habit_base.get("name")
                flash(
                    f'¡Hábito "{nombre}" creado y vinculado a "{base_name}"!',
                    "success",
                )
            else:
                flash(f'¡Hábito "{nombre}" creado exitosamente!', "success")
        else:
            flash(f'¡Hábito "{nombre}" creado exitosamente!', "success")

        return redirect(url_for("progress.panel"))

    # GET - Mostrar formulario
    habitos_existentes = Habit.list_by_owner(user)
    categorias = _get_categorias()

    return render_template(
        "habits/new.html",
        habitos_existentes=habitos_existentes,
        categorias=categorias,
    )


# Funciones auxiliares


def _get_habit_by_id(user: str, habit_id: int):
    """
    Obtiene un hábito del usuario por id, desde la BD.
    Se usa para el mensaje de stacking.
    """
    habits = Habit.list_by_owner(user)
    for h in habits:
        if h.get("id") == habit_id:
            return h
    return None


def _get_categorias():
    """
    Lista de categorías usadas en el formulario.
    Sigue siendo estática para no romper el UI en español.
    """
    return [
        "Salud",
        "Productividad",
        "Mindfulness",
        "Nutrición",
        "Aprendizaje",
        "Relaciones",
        "Finanzas",
        "Creatividad",
        "General",
    ]


def get_user_habits_organized(user: str):
    """
    Versión simplificada: por ahora no reconstruimos relaciones de stacking
    desde BD; devolvemos todos como independientes.
    """
    habitos = Habit.list_by_owner(user)
    habitos_independientes = habitos
    habitos_vinculados = {}  # placeholder por compatibilidad con código viejo
    return habitos_independientes, habitos_vinculados


def get_progress_stats(user: str):
    """
    Stats rápidos a partir de la BD.
    De momento, como no tenemos check-ins diarios,
    completados = 0 y porcentaje = 0.
    """
    habitos = Habit.list_by_owner(user)
    total_habitos = len(habitos)
    completados_hoy = 0
    return {
        "total": total_habitos,
        "completados": completados_hoy,
        "porcentaje": int(
            (completados_hoy / total_habitos * 100) if total_habitos > 0 else 0
        ),
    }


# HU-11: eliminar hábito con confirmación
@habits_bp.route("/<int:habit_id>/delete", methods=["GET", "POST"])
def delete(habit_id: int):
    """
    Vista dedicada para confirmar y eliminar un hábito (HU-11).
    GET: mostrar página de confirmación.
    POST: eliminar y redirigir al panel con mensaje flash.
    """
    user = _user_email()
    if not user:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    # Buscar el hábito en BD y verificar que pertenezca al usuario
    habits = Habit.list_by_owner(user)
    habit = next((h for h in habits if h.get("id") == habit_id), None)
    if not habit:
        flash("No se encontró el hábito solicitado.", "danger")
        return redirect(url_for("progress.panel"))

    if request.method == "POST":
        try:
            Habit.delete(habit_id)
            name = habit.get("nombre") or habit.get("name")
            flash(f'Hábito "{name}" eliminado correctamente.', "success")
        except Exception:
            flash("Ocurrió un error al eliminar el hábito.", "danger")
        return redirect(url_for("progress.panel"))

    return render_template("habits/delete.html", habit=habit)

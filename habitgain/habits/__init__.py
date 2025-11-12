from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..models import Habit

habits_bp = Blueprint("habits", __name__, template_folder="templates")


def _user_email():
    return (session.get("user") or {}).get("email")



# HU5: Crear nuevo hábito con Habit Stacking
@habits_bp.route("/new", methods=["GET", "POST"])
def create():
    user = _user_email()
    if not user:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        # Obtener datos del formulario
        nombre = (request.form.get("nombre") or request.form.get("name") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        habit_base_id = request.form.get("habit_base_id") or request.form.get("stack_after") or ""

        # Validaciones
        if not nombre:
            flash("El nombre del hábito es obligatorio", "warning")
            # Habitos existentes desde DB para el select de stacking
            habitos_existentes = Habit.list_active_by_owner(user)
            return render_template(
                "habits/new.html",
                habitos_existentes=habitos_existentes,
                categorias=_get_categorias()
            )

        # Crear en DB (category_id por defecto 1 si no se especifica)
        new_id = Habit.create(email=user, name=nombre, short_desc=descripcion, category_id=None)

        # Mensaje de éxito personalizado
        if habit_base_id:
            try:
                base_id = int(habit_base_id)
                habit_base = Habit.get_by_id(base_id)
                if habit_base:
                    base_name = habit_base.get("name")
                    flash(f'¡Hábito "{nombre}" creado y vinculado a "{base_name}"!', "success")
                else:
                    flash(f'¡Hábito "{nombre}" creado exitosamente!', "success")
            except (ValueError, TypeError):
                flash(f'¡Hábito "{nombre}" creado exitosamente!', "success")
        else:
            flash(f'¡Hábito "{nombre}" creado exitosamente!', "success")

        return redirect(url_for("progress.panel"))
    
    # GET - Mostrar formulario
    # Habitos existentes desde DB
    habitos_existentes = Habit.list_active_by_owner(user)
    categorias = _get_categorias()
    
    return render_template(
        "habits/new.html",
        habitos_existentes=habitos_existentes,
        categorias=categorias
    )


# Funciones auxiliares
def _get_habit_by_id(user, habit_id):
    return Habit.get_by_id(habit_id)


def _get_categorias():
    
    return [
        'Salud', 
        'Productividad', 
        'Mindfulness', 
        'Nutrición',
        'Aprendizaje', 
        'Relaciones', 
        'Finanzas', 
        'Creatividad',
        'General'
    ]


def get_user_habits_organized(user):
    # No usado por el panel actual; mantenido para compatibilidad si se requiere.
    habitos = Habit.list_by_owner(user)
    
    habitos_independientes = []
    habitos_vinculados = {}
    
    for habito in habitos:
        habit_base_id = habito.get("habit_base_id") or habito.get("stack_after")
        
        if habit_base_id:
            # Es un hábito vinculado
            try:
                base_id = int(habit_base_id)
                if base_id not in habitos_vinculados:
                    habitos_vinculados[base_id] = []
                habitos_vinculados[base_id].append(habito)
            except (ValueError, TypeError):
                # Si no se puede convertir a int, tratarlo como independiente
                habitos_independientes.append(habito)
        else:
            # Es un hábito independiente
            habitos_independientes.append(habito)
    
    return habitos_independientes, habitos_vinculados


def get_progress_stats(user):
    habitos = Habit.list_by_owner(user)
    total_habitos = len(habitos)
    completados_hoy = 0  # este helper queda como placeholder; el panel usa Completion en DB
    
    return {
        "total": total_habitos,
        "completados": completados_hoy,
        "porcentaje": int((completados_hoy / total_habitos * 100) if total_habitos > 0 else 0)
    }


#H11:
@habits_bp.route("/<int:habit_id>/delete", methods=["GET", "POST"])
def delete(habit_id):
    """
    Vista dedicada para confirmar y eliminar un hábito (HU-11).
    GET: mostrar página de confirmación.
    POST: eliminar y redirigir al panel con mensaje flash.
    """
    user = _user_email()
    if not user:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    habit = Habit.get_by_id(habit_id)
    if not habit:
        flash("No se encontró el hábito solicitado.", "danger")
        return redirect(url_for("progress.panel"))
    # Validar propietario
    if habit.get("owner_email") != user:
        flash("No tienes permisos para eliminar este hábito.", "warning")
        return redirect(url_for("progress.panel"))

    if request.method == "POST":
        # eliminar en DB y notificar
        try:
            Habit.delete(habit_id)
            flash(f'Hábito "{habit.get("name")}" eliminado correctamente.', "success")
        except Exception:
            flash("Ocurrió un error al eliminar el hábito.", "danger")
        return redirect(url_for("progress.panel"))

    return render_template("habits/delete.html", habit=habit)

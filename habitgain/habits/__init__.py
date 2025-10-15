from flask import Blueprint, render_template, request, redirect, url_for, session, flash

habits_bp = Blueprint("habits", __name__, template_folder="templates")

# Simple in-memory store per user for MVP
USER_HABITS = {}


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
        categoria = (request.form.get("categoria") or "General").strip()
        frecuencia = request.form.get("frecuencia") or "diaria"
        habit_base_id = request.form.get("habit_base_id") or request.form.get("stack_after") or ""
        
        # Validaciones
        if not nombre:
            flash("El nombre del hábito es obligatorio", "warning")
            return render_template(
                "habits/new.html",
                habitos_existentes=USER_HABITS.get(user, []),
                categorias=_get_categorias()
            )
        
        # Crear nuevo hábito
        USER_HABITS.setdefault(user, [])
        nuevo_habito = {
            "id": len(USER_HABITS[user]) + 1000,
            "nombre": nombre,
            "name": nombre,  # Mantener compatibilidad con código existente
            "descripcion": descripcion,
            "categoria": categoria,
            "frecuencia": frecuencia,
            "done": False,
            "completado_hoy": False,
            "racha": 0,
            "fortaleza": 0,
            "stack_after": habit_base_id,  # Mantener compatibilidad
            "habit_base_id": int(habit_base_id) if habit_base_id else None
        }
        
        USER_HABITS[user].append(nuevo_habito)
        
        # Mensaje de éxito personalizado
        if habit_base_id:
            habit_base = _get_habit_by_id(user, int(habit_base_id))
            if habit_base:
                flash(f'¡Hábito "{nombre}" creado y vinculado a "{habit_base.get("nombre", habit_base.get("name"))}"!', "success")
            else:
                flash(f'¡Hábito "{nombre}" creado exitosamente!', "success")
        else:
            flash(f'¡Hábito "{nombre}" creado exitosamente!', "success")
        
        return redirect(url_for("progress.panel"))
    
    # GET - Mostrar formulario
    habitos_existentes = USER_HABITS.get(user, [])
    categorias = _get_categorias()
    
    return render_template(
        "habits/new.html",
        habitos_existentes=habitos_existentes,
        categorias=categorias
    )


# Funciones auxiliares
def _get_habit_by_id(user, habit_id):
    
    for habito in USER_HABITS.get(user, []):
        if habito["id"] == habit_id:
            return habito
    return None


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

    habitos = USER_HABITS.get(user, [])
    
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

    habitos = USER_HABITS.get(user, [])
    total_habitos = len(habitos)
    completados_hoy = sum(1 for h in habitos if h.get("completado_hoy") or h.get("done"))
    
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

    habits = USER_HABITS.get(user, [])
    habit = next((h for h in habits if h.get("id") == habit_id), None)
    if not habit:
        flash("No se encontró el hábito solicitado.", "danger")
        return redirect(url_for("progress.panel"))

    if request.method == "POST":
        # eliminar y notificar
        try:
            habits.remove(habit)
            flash(f'Hábito \"{habit.get("nombre") or habit.get("name")}\" eliminado correctamente.', "success")
        except ValueError:
            flash("Ocurrió un error al eliminar el hábito.", "danger")
        return redirect(url_for("progress.panel"))

    return render_template("habits/delete.html", habit=habit)

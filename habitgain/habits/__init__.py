from flask import Blueprint, render_template, request, redirect, url_for, session, flash

habits_bp = Blueprint("habits", __name__, template_folder="templates")

# Simple in-memory store per user for MVP
USER_HABITS = {}

def _user_email():
    return (session.get("user") or {}).get("email")

@habits_bp.route("/new", methods=["GET", "POST"])
def create():
    """
    Historia de Usuario: Crear hábitos personalizados
    CDA1: Permitir ingresar nombre, descripción, frecuencia, hora y duración
    CDA2: Guardar en estructura y mostrar en lista
    CDA3: Mostrar mensaje de confirmación
    """
    user = _user_email()
    if not user:
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        # Capturar todos los campos
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        frequency = (request.form.get("frequency") or "").strip()
        time = (request.form.get("time") or "").strip()  # NUEVO: Hora específica
        duration = (request.form.get("duration") or "").strip()  # NUEVO: Duración
        stack_after = request.form.get("stack_after") or ""
        
        # Validación
        if not name:
            flash("Habit name is required", "warning")
            return render_template("habits/new.html")
        
        if not frequency:
            flash("Frequency is required", "warning")
            return render_template("habits/new.html")
        
        # CDA2: Guardar el hábito con todos los campos
        USER_HABITS.setdefault(user, [])
        USER_HABITS[user].append({
            "id": len(USER_HABITS[user]) + 1000,
            "name": name,
            "description": description,
            "frequency": frequency,
            "time": time,              # NUEVO
            "duration": duration,      # NUEVO
            "done": False,
            "stack_after": stack_after
        })
        
        # CDA3: Mensaje de confirmación
        flash(f"✨ Habit '{name}' created successfully!", "success")
        return redirect(url_for("progress.panel"))
    
    return render_template("habits/new.html")

@habits_bp.route("/mark/<int:habit_id>", methods=["POST"], endpoint="habits_mark")
def mark(habit_id: int):
    user = _user_email()
    if not user:
        return redirect(url_for("auth.login"))
    for h in USER_HABITS.get(user, []):
        if h["id"] == habit_id:
            h["done"] = True
            break
    return redirect(url_for("progress.panel"))

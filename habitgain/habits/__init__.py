from flask import Blueprint, render_template, request, redirect, url_for, session, flash

habits_bp = Blueprint("habits", __name__, template_folder="templates")

# Simple in-memory store per user for MVP
USER_HABITS = {}

def _user_email():
    return (session.get("user") or {}).get("email")

@habits_bp.route("/new", methods=["GET", "POST"])
def create():
    user = _user_email()
    if not user:
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        # Capturar campos
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        frequency = (request.form.get("frequency") or "").strip()
        time = (request.form.get("time") or "").strip()
        duration = (request.form.get("duration") or "").strip()
        stack_after = request.form.get("stack_after") or ""
        
        # Manejar frecuencia personalizada
        if frequency == "Custom":
            custom_freq = (request.form.get("custom_frequency") or "").strip()
            if custom_freq:
                frequency = custom_freq
            selected_days = request.form.get("selected_days") or ""
            if selected_days:
                frequency = f"Días específicos: {selected_days}"
        
        # Manejar duración personalizada
        if duration == "Custom":
            custom_duration = (request.form.get("custom_duration") or "").strip()
            if custom_duration:
                duration = custom_duration
        
        # Validación
        if not name:
            flash("El nombre del hábito es requerido", "warning")
            return render_template("habits/new.html")
        
        if not frequency:
            flash("La frecuencia es requerida", "warning")
            return render_template("habits/new.html")
        
        # Guardar el hábito
        USER_HABITS.setdefault(user, [])
        USER_HABITS[user].append({
            "id": len(USER_HABITS[user]) + 1000,
            "name": name,
            "description": description,
            "frequency": frequency,
            "time": time,
            "duration": duration,
            "done": False,
            "stack_after": stack_after
        })
        
        flash(f"¡Hábito '{name}' creado exitosamente!", "success")
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

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import re

auth_bp = Blueprint("auth", __name__, template_folder="templates")

# MVP users in memory (se puede migrar a DB después)
USERS = {"demo@habit.com": {"password": "123456", "name": "Demo"}}

# Funciones auxiliares de validación
def is_valid_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    """Valida que la contraseña tenga al menos 6 caracteres"""
    return len(password) >= 6

def email_exists(email):
    """Verifica si el email ya está registrado"""
    return email in USERS

# Ruta Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pwd = request.form.get("password", "")
        
        user = USERS.get(email)
        if user and user["password"] == pwd:
            session["user"] = {"email": email, "name": user["name"]}
            flash("¡Bienvenido/a de nuevo!", "success")
            return redirect(url_for("progress.panel"))
        
        flash("Correo o contraseña incorrectos", "danger")
        return render_template("auth/login.html", title="Iniciar sesión", email=email)
    
    return render_template("auth/login.html", title="Iniciar sesión")

# Ruta register
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Obtener datos del formulario
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        # Lista de errores
        errors = []
        
        # Validación 1: Nombre
        if not name or len(name) < 2:
            errors.append("El nombre debe tener al menos 2 caracteres")
        
        # Validación 2: Email formato
        if not is_valid_email(email):
            errors.append("El correo electrónico no es válido")
        
        # Validación 3: Email único
        if email_exists(email):
            errors.append("Este correo ya está registrado. Intenta iniciar sesión")
        
        # Validación 4: Contraseña longitud
        if not is_valid_password(password):
            errors.append("La contraseña debe tener al menos 6 caracteres")
        
        # Validación 5: Contraseñas coinciden
        if password != confirm_password:
            errors.append("Las contraseñas no coinciden")
        
        # Si hay errores, mostrarlos
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template(
                "auth/register.html", 
                title="Crear cuenta",
                name=name,
                email=email
            )
        
        # Registrar usuario (todo esta bien)
        USERS[email] = {
            "password": password,
            "name": name
        }
        
        # Iniciar sesión automáticamente
        session["user"] = {"email": email, "name": name}
        
        flash("¡Cuenta creada exitosamente! Bienvenido/a a HabitFlow.", "success")
        return redirect(url_for("progress.panel"))
    
    # GET: Mostrar formulario
    return render_template("auth/register.html", title="Crear cuenta")

# Ruta logout
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente", "info")
    return redirect(url_for("auth.login"))
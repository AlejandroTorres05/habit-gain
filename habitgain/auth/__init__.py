from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import re
from ..models import User, OnboardingStatus

auth_bp = Blueprint("auth", __name__, template_folder="templates")

# Funciones auxiliares de validación
def is_valid_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    """Valida que la contraseña tenga al menos 6 caracteres"""
    return len(password) >= 6

def email_exists(email):
    """Verifica si el email ya está registrado en la base de datos"""
    return User.get_by_email(email) is not None

# Ruta Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pwd = request.form.get("password", "")

        # Verificar credenciales usando la base de datos
        user = User.verify_password(email, pwd)
        if user:
            session["user"] = {"email": email, "name": user.get("name", "Usuario")}
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
        
        # Registrar usuario en la base de datos
        try:
            User.create_user(email, name, password, role="user")

            # HU-18: Crear estado de onboarding para nuevo usuario
            OnboardingStatus.create_status(email)

            # Iniciar sesión automáticamente
            session["user"] = {"email": email, "name": name}

            flash("¡Cuenta creada exitosamente! Bienvenido/a a HabitGain.", "success")
            return redirect(url_for("progress.panel"))
        except Exception as e:
            flash(f"Error al crear la cuenta: {str(e)}", "danger")
            return render_template(
                "auth/register.html",
                title="Crear cuenta",
                name=name,
                email=email
            )
    
    # GET: Mostrar formulario
    return render_template("auth/register.html", title="Crear cuenta")

# Ruta logout
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente", "info")
    return redirect(url_for("auth.login"))
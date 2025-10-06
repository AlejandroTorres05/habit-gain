from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..models import User

auth_bp = Blueprint("auth", __name__, template_folder="templates")

# Demo user is now created via database seeding


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        # Verificar credenciales usando la base de datos
        if User.check_password(email, password):
            user = User.get_by_email(email)
            if user:
                session["user"] = {"email": email, "name": user["name"]}
                flash("¡Bienvenido!", "success")
                return redirect(url_for("progress.panel"))
        
        flash("Credenciales inválidas", "danger")
    return render_template("auth/login.html", title="Iniciar sesión")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Signed out", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # CDA1: Obtener datos del formulario (nombre, correo, contraseña)
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        
        # Validaciones básicas
        if not name or not email or not password:
            flash("Todos los campos son obligatorios", "danger")
            return render_template("auth/register.html", title="Crear cuenta")
        
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres", "danger")
            return render_template("auth/register.html", title="Crear cuenta")
        
        if password != password_confirm:
            flash("Las contraseñas no coinciden", "danger")
            return render_template("auth/register.html", title="Crear cuenta")
        
        # Validación básica de email
        if "@" not in email or "." not in email.split("@")[1]:
            flash("Ingrese un correo electrónico válido", "danger")
            return render_template("auth/register.html", title="Crear cuenta")
        
        # CDA2: Validar que el correo no esté previamente registrado
        existing_user = User.get_by_email(email)
        if existing_user:
            flash("Este correo electrónico ya está registrado", "danger")
            return render_template("auth/register.html", title="Crear cuenta")
        
        try:
            # Crear nuevo usuario usando la función ensure_exists
            # pero primero verificamos que no exista para usar la contraseña correcta
            User.ensure_exists(email, name, password)
            
            # CDA3: Mensaje de confirmación al completar el registro
            flash("¡Registro exitoso! Ya puedes iniciar sesión con tu cuenta", "success")
            return redirect(url_for("auth.login"))
            
        except Exception as e:
            flash("Error al crear la cuenta. Intenta nuevamente", "danger")
            return render_template("auth/register.html", title="Crear cuenta")
    
    return render_template("auth/register.html", title="Crear cuenta")

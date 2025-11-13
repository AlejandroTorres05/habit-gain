from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from ..models import User, Habit
import secrets
from functools import wraps

admin_bp = Blueprint("admin", __name__, template_folder="templates")


def require_admin(f):
    """HU-16 CDA1: Decorator para verificar que el usuario sea admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Debes iniciar sesión primero", "warning")
            return redirect(url_for("auth.login"))

        user_email = session["user"]["email"]
        user = User.get_by_email(user_email)

        if not user or user.get("role") != "admin":
            flash("No tienes permisos para acceder a esta sección", "danger")
            return redirect(url_for("progress.panel"))

        return f(*args, **kwargs)
    return decorated_function


def _get_csrf_token() -> str:
    token = secrets.token_urlsafe(32)
    session["csrf_token_admin"] = token
    session.modified = True
    return token


# ============== PANEL PRINCIPAL ==============

@admin_bp.route("/")
@require_admin
def dashboard():
    """HU-16: Panel principal de administración"""
    users = User.list_all()
    habits = Habit.list_all_habits()

    # Estadísticas básicas
    total_users = len(users)
    total_habits = len(habits)
    active_habits = len([h for h in habits if h.get("active")])
    admin_count = len([u for u in users if u.get("role") == "admin"])

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_habits=total_habits,
        active_habits=active_habits,
        admin_count=admin_count,
    )


# ============== CRUD USUARIOS ==============

@admin_bp.route("/users")
@require_admin
def users_list():
    """HU-16 CDA3: Listar todos los usuarios"""
    users = User.list_all()
    csrf_token = _get_csrf_token()
    return render_template("admin/users.html", users=users, csrf_token=csrf_token)


@admin_bp.route("/users/create", methods=["GET", "POST"])
@require_admin
def users_create():
    """HU-16 CDA2 & CDA3: Crear nuevo usuario con validación"""
    if request.method == "POST":
        # CSRF check
        form_token = request.form.get("csrf_token", "")
        sess_token = session.pop("csrf_token_admin", None)
        if not sess_token or form_token != sess_token:
            flash("Token CSRF inválido", "danger")
            return redirect(url_for("admin.users_create"))

        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "user").strip()

        # Validaciones (CDA2)
        errors = []
        if not email or "@" not in email:
            errors.append("Email inválido")
        if not name:
            errors.append("El nombre es obligatorio")
        if not password or len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")
        if role not in ["user", "admin"]:
            errors.append("Rol inválido")

        # Verificar email duplicado
        existing = User.get_by_email(email)
        if existing:
            errors.append(f"Ya existe un usuario con el email {email}")

        if errors:
            for e in errors:
                flash(e, "danger")
            return redirect(url_for("admin.users_create"))

        try:
            User.create_user(email, name, password, role)
            flash(f"Usuario {email} creado exitosamente", "success")
            return redirect(url_for("admin.users_list"))
        except Exception as e:
            flash(f"Error al crear usuario: {str(e)}", "danger")
            return redirect(url_for("admin.users_create"))

    csrf_token = _get_csrf_token()
    return render_template("admin/user_form.html", user=None, csrf_token=csrf_token)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@require_admin
def users_edit(user_id: int):
    """HU-16 CDA2 & CDA3: Editar usuario con validación"""
    user = User.get_by_id(user_id)
    if not user:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for("admin.users_list"))

    if request.method == "POST":
        # CSRF check
        form_token = request.form.get("csrf_token", "")
        sess_token = session.pop("csrf_token_admin", None)
        if not sess_token or form_token != sess_token:
            flash("Token CSRF inválido", "danger")
            return redirect(url_for("admin.users_edit", user_id=user_id))

        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "user").strip()

        # Validaciones (CDA2)
        errors = []
        if not email or "@" not in email:
            errors.append("Email inválido")
        if not name:
            errors.append("El nombre es obligatorio")
        if role not in ["user", "admin"]:
            errors.append("Rol inválido")

        # Verificar email duplicado (excepto el mismo usuario)
        existing = User.get_by_email(email)
        if existing and existing["id"] != user_id:
            errors.append(f"Ya existe otro usuario con el email {email}")

        if errors:
            for e in errors:
                flash(e, "danger")
            return redirect(url_for("admin.users_edit", user_id=user_id))

        try:
            User.update_user(user_id, email, name, role)
            flash(f"Usuario {email} actualizado exitosamente", "success")
            return redirect(url_for("admin.users_list"))
        except Exception as e:
            flash(f"Error al actualizar usuario: {str(e)}", "danger")
            return redirect(url_for("admin.users_edit", user_id=user_id))

    csrf_token = _get_csrf_token()
    return render_template("admin/user_form.html", user=user, csrf_token=csrf_token)


@admin_bp.route("/users/<int:user_id>/delete", methods=["GET", "POST"])
@require_admin
def users_delete(user_id: int):
    """HU-16 CDA2: Eliminar usuario con confirmación"""
    user = User.get_by_id(user_id)
    if not user:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for("admin.users_list"))

    # No permitir eliminar el último admin
    all_users = User.list_all()
    admin_count = len([u for u in all_users if u.get("role") == "admin"])
    if user.get("role") == "admin" and admin_count <= 1:
        flash("No se puede eliminar el último administrador del sistema", "danger")
        return redirect(url_for("admin.users_list"))

    if request.method == "POST":
        # CSRF check
        form_token = request.form.get("csrf_token", "")
        sess_token = session.pop("csrf_token_admin", None)
        if not sess_token or form_token != sess_token:
            flash("Token CSRF inválido", "danger")
            return redirect(url_for("admin.users_list"))

        try:
            User.delete_user(user_id)
            flash(f'Usuario "{user.get("email")}" eliminado exitosamente', "success")
            return redirect(url_for("admin.users_list"))
        except Exception as e:
            flash(f"Error al eliminar usuario: {str(e)}", "danger")
            return redirect(url_for("admin.users_list"))

    csrf_token = _get_csrf_token()
    return render_template("admin/user_delete.html", user=user, csrf_token=csrf_token)


# ============== CRUD HÁBITOS ==============

@admin_bp.route("/habits")
@require_admin
def habits_list():
    """HU-16 CDA3: Listar todos los hábitos"""
    habits = Habit.list_all_habits()
    csrf_token = _get_csrf_token()
    return render_template("admin/habits.html", habits=habits, csrf_token=csrf_token)


@admin_bp.route("/habits/<int:habit_id>/edit", methods=["GET", "POST"])
@require_admin
def habits_edit(habit_id: int):
    """HU-16 CDA2 & CDA3: Editar hábito con validación"""
    habit = Habit.get_by_id(habit_id)
    if not habit:
        flash("Hábito no encontrado", "danger")
        return redirect(url_for("admin.habits_list"))

    if request.method == "POST":
        # CSRF check
        form_token = request.form.get("csrf_token", "")
        sess_token = session.pop("csrf_token_admin", None)
        if not sess_token or form_token != sess_token:
            flash("Token CSRF inválido", "danger")
            return redirect(url_for("admin.habits_edit", habit_id=habit_id))

        name = request.form.get("name", "").strip()
        short_desc = request.form.get("short_desc", "").strip()
        owner_email = request.form.get("owner_email", "").strip()
        active = request.form.get("active") == "1"

        # Validaciones (CDA2)
        errors = []
        if not name:
            errors.append("El nombre del hábito es obligatorio")
        if not owner_email or "@" not in owner_email:
            errors.append("Email del propietario inválido")

        # Verificar que el propietario exista
        owner = User.get_by_email(owner_email)
        if not owner:
            errors.append(f"No existe un usuario con el email {owner_email}")

        if errors:
            for e in errors:
                flash(e, "danger")
            return redirect(url_for("admin.habits_edit", habit_id=habit_id))

        try:
            Habit.admin_update_habit(habit_id, name, short_desc, owner_email, active)
            flash(f'Hábito "{name}" actualizado exitosamente', "success")
            return redirect(url_for("admin.habits_list"))
        except Exception as e:
            flash(f"Error al actualizar hábito: {str(e)}", "danger")
            return redirect(url_for("admin.habits_edit", habit_id=habit_id))

    csrf_token = _get_csrf_token()
    return render_template("admin/habit_form.html", habit=habit, csrf_token=csrf_token)


@admin_bp.route("/habits/<int:habit_id>/delete", methods=["GET", "POST"])
@require_admin
def habits_delete(habit_id: int):
    """HU-16 CDA2: Eliminar hábito con confirmación"""
    habit = Habit.get_by_id(habit_id)
    if not habit:
        flash("Hábito no encontrado", "danger")
        return redirect(url_for("admin.habits_list"))

    if request.method == "POST":
        # CSRF check
        form_token = request.form.get("csrf_token", "")
        sess_token = session.pop("csrf_token_admin", None)
        if not sess_token or form_token != sess_token:
            flash("Token CSRF inválido", "danger")
            return redirect(url_for("admin.habits_list"))

        try:
            Habit.admin_delete_habit(habit_id)
            flash(f'Hábito "{habit.get("name")}" eliminado exitosamente', "success")
            return redirect(url_for("admin.habits_list"))
        except Exception as e:
            flash(f"Error al eliminar hábito: {str(e)}", "danger")
            return redirect(url_for("admin.habits_list"))

    csrf_token = _get_csrf_token()
    return render_template("admin/habit_delete.html", habit=habit, csrf_token=csrf_token)

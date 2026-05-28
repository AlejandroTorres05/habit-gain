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


@admin_bp.route("/experiment-report")
@require_admin
def experiment_report():
    """Reporte mockeado de 1 mes de experimentación con 5 emprendedores."""
    entrepreneurs = [
        {
            "id": 1,
            "name": "Valentina Torres",
            "initials": "VT",
            "sector": "Fintech",
            "goal": "Lanzar mi app de pagos en 90 días",
            "color": "#7c71ff",
            "avatar_bg": "linear-gradient(135deg,#7c71ff,#2bd2ff)",
            "habits": [
                {"name": "Meditación matutina", "icon": "🧘", "streak": 28, "pct": 93},
                {"name": "Revisar métricas clave", "icon": "📊", "streak": 25, "pct": 83},
                {"name": "Enviar 5 cold emails", "icon": "📧", "streak": 22, "pct": 73},
                {"name": "Ejercicio 30 min", "icon": "🏃", "streak": 20, "pct": 67},
            ],
            "weekly_done": [3, 4, 4, 4, 4, 4, 4],
            "weekly_total": 4,
            "overall_pct": 86,
            "streak": 28,
            "days_active": 29,
            "quote": "Antes olvidaba revisar métricas días enteros. Ahora es lo primero que hago.",
        },
        {
            "id": 2,
            "name": "Santiago Gómez",
            "initials": "SG",
            "sector": "E-commerce",
            "goal": "Triplicar ventas mensuales",
            "color": "#2bd2ff",
            "avatar_bg": "linear-gradient(135deg,#2bd2ff,#06c47a)",
            "habits": [
                {"name": "Crear contenido para RRSS", "icon": "📸", "streak": 30, "pct": 100},
                {"name": "Revisar reseñas de clientes", "icon": "⭐", "streak": 27, "pct": 90},
                {"name": "Actualizar inventario", "icon": "📦", "streak": 24, "pct": 80},
                {"name": "Caminata de reflexión", "icon": "🚶", "streak": 18, "pct": 60},
                {"name": "Journaling nocturno", "icon": "📓", "streak": 15, "pct": 50},
            ],
            "weekly_done": [3, 4, 5, 5, 5, 5, 5],
            "weekly_total": 5,
            "overall_pct": 76,
            "streak": 30,
            "days_active": 30,
            "quote": "El streak de contenido me obligó a ser constante. Ya tenemos 2x más seguidores.",
        },
        {
            "id": 3,
            "name": "Camila Herrera",
            "initials": "CH",
            "sector": "Agencia Digital",
            "goal": "Conseguir 3 clientes nuevos por mes",
            "color": "#d946ef",
            "avatar_bg": "linear-gradient(135deg,#d946ef,#f97316)",
            "habits": [
                {"name": "Planificación de contenido", "icon": "🗓️", "streak": 26, "pct": 87},
                {"name": "Standup con el equipo", "icon": "👥", "streak": 22, "pct": 73},
                {"name": "Propuesta a prospecto", "icon": "💼", "streak": 19, "pct": 63},
                {"name": "Yoga o stretching", "icon": "🧗", "streak": 24, "pct": 80},
            ],
            "weekly_done": [2, 3, 3, 4, 4, 4, 4],
            "weekly_total": 4,
            "overall_pct": 76,
            "streak": 26,
            "days_active": 28,
            "quote": "La IA me sugirió el hábito de prospección diaria. Cerré 4 clientes este mes.",
        },
        {
            "id": 4,
            "name": "Andrés Palacios",
            "initials": "AP",
            "sector": "SaaS / Dev",
            "goal": "Lanzar beta con 50 usuarios",
            "color": "#f59e0b",
            "avatar_bg": "linear-gradient(135deg,#f59e0b,#ef4444)",
            "habits": [
                {"name": "Deep work 2h sin distracciones", "icon": "💻", "streak": 25, "pct": 83},
                {"name": "Code review del equipo", "icon": "🔍", "streak": 20, "pct": 67},
                {"name": "Networking LinkedIn", "icon": "🤝", "streak": 16, "pct": 53},
                {"name": "Correr 5km", "icon": "🏅", "streak": 21, "pct": 70},
            ],
            "weekly_done": [2, 3, 3, 3, 4, 4, 4],
            "weekly_total": 4,
            "overall_pct": 69,
            "streak": 25,
            "days_active": 27,
            "quote": "El bloque de deep work cambió mi productividad. Entregamos la beta en tiempo.",
        },
        {
            "id": 5,
            "name": "María Fernanda Ruiz",
            "initials": "MF",
            "sector": "Food Startup",
            "goal": "Entrar a 10 tiendas locales",
            "color": "#06c47a",
            "avatar_bg": "linear-gradient(135deg,#06c47a,#2bd2ff)",
            "habits": [
                {"name": "Prueba de receta nueva", "icon": "🍳", "streak": 23, "pct": 77},
                {"name": "Post en Instagram", "icon": "📱", "streak": 30, "pct": 100},
                {"name": "Llamada a proveedor", "icon": "📞", "streak": 17, "pct": 57},
                {"name": "Caminata 20 min", "icon": "🌿", "streak": 26, "pct": 87},
            ],
            "weekly_done": [3, 3, 4, 4, 4, 4, 4],
            "weekly_total": 4,
            "overall_pct": 80,
            "streak": 30,
            "days_active": 30,
            "quote": "Con el hábito de publicar diario ganamos 800 seguidores. Ya estamos en 7 tiendas.",
        },
    ]

    weeks = ["Sem 1", "Sem 2", "Sem 3", "Sem 4"]
    global_weekly = [40, 55, 68, 80]

    return render_template(
        "admin/experiment_report.html",
        entrepreneurs=entrepreneurs,
        weeks=weeks,
        global_weekly=global_weekly,
    )


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

from flask import Blueprint, render_template, session, redirect, url_for, abort, flash, request
from ..models import Category, Habit

explore_bp = Blueprint("explore", __name__, template_folder="templates")

# Catálogo de hábitos sugeridos organizados por categoría
HABIT_CATALOG = {
    1: [  # Health
        {"id": "health_1", "name": "Beber 8 vasos de agua", "short_desc": "Mantente hidratado durante todo el día", "category_id": 1},
        {"id": "health_2", "name": "Hacer 30 min de ejercicio", "short_desc": "Cardio, yoga o cualquier actividad física", "category_id": 1},
        {"id": "health_3", "name": "Dormir 8 horas", "short_desc": "Descanso adecuado para recuperación", "category_id": 1},
        {"id": "health_4", "name": "Meditar 10 minutos", "short_desc": "Práctica de mindfulness y relajación", "category_id": 1},
        {"id": "health_5", "name": "Estiramientos matutinos", "short_desc": "5 minutos de estiramientos al despertar", "category_id": 1},
        {"id": "health_6", "name": "Caminar 10,000 pasos", "short_desc": "Actividad física diaria moderada", "category_id": 1},
    ],
    2: [  # Productivity
        {"id": "prod_1", "name": "Planificar el día", "short_desc": "Lista de prioridades cada mañana", "category_id": 2},
        {"id": "prod_2", "name": "Técnica Pomodoro (2 sesiones)", "short_desc": "25 min de trabajo enfocado + 5 min descanso", "category_id": 2},
        {"id": "prod_3", "name": "Revisar inbox cero", "short_desc": "Procesar todo el correo electrónico", "category_id": 2},
        {"id": "prod_4", "name": "Desconectar redes sociales", "short_desc": "2 horas sin distracciones digitales", "category_id": 2},
        {"id": "prod_5", "name": "Preparar ropa para mañana", "short_desc": "Ahorra tiempo en las mañanas", "category_id": 2},
        {"id": "prod_6", "name": "Limpiar escritorio", "short_desc": "5 minutos organizando espacio de trabajo", "category_id": 2},
    ],
    3: [  # Learning
        {"id": "learn_1", "name": "Leer 20 páginas", "short_desc": "Lectura diaria de libros", "category_id": 3},
        {"id": "learn_2", "name": "Aprender 10 palabras nuevas", "short_desc": "Expandir vocabulario o idioma", "category_id": 3},
        {"id": "learn_3", "name": "Ver un curso online", "short_desc": "30 minutos de aprendizaje estructurado", "category_id": 3},
        {"id": "learn_4", "name": "Practicar un instrumento", "short_desc": "15 minutos de práctica musical", "category_id": 3},
        {"id": "learn_5", "name": "Escribir en diario", "short_desc": "Reflexión personal y autoconocimiento", "category_id": 3},
        {"id": "learn_6", "name": "Podcast educativo", "short_desc": "Escuchar mientras haces otras tareas", "category_id": 3},
    ],
}


def _require_login():
    return "user" in session


@explore_bp.route("/")
def home():
    if not _require_login():
        return redirect(url_for("auth.login"))
    email = session["user"]["email"]
    categories = Category.all()
    user_habits = Habit.list_active_by_owner(email)

    # Obtener todos los hábitos sugeridos
    all_suggested_habits = []
    for cat_id, habits in HABIT_CATALOG.items():
        all_suggested_habits.extend(habits)

    return render_template("home.html",
                         categories=categories,
                         habits=user_habits,
                         suggested_habits=all_suggested_habits)


# Alias para compatibilidad si en algún lugar quedó explore.explore
explore_bp.add_url_rule("/", endpoint="explore", view_func=home)


@explore_bp.route("/category/<int:category_id>")
def category(category_id: int):
    if not _require_login():
        return redirect(url_for("auth.login"))
    email = session["user"]["email"]
    cat = Category.get_by_id(category_id)
    if not cat:
        abort(404)
    user_habits = Habit.list_active_by_owner_and_category(email, category_id)

    # Obtener hábitos sugeridos para esta categoría
    suggested_habits = HABIT_CATALOG.get(category_id, [])

    return render_template("category.html",
                         category=cat,
                         habits=user_habits,
                         suggested_habits=suggested_habits)


@explore_bp.route("/add_habit/<habit_id>", methods=["POST"])
def add_habit(habit_id: str):
    """Agregar un hábito del catálogo al panel del usuario"""
    if not _require_login():
        return redirect(url_for("auth.login"))

    email = session["user"]["email"]

    # Buscar el hábito en el catálogo
    habit_found = None
    for _, habits in HABIT_CATALOG.items():
        for h in habits:
            if h["id"] == habit_id:
                habit_found = h
                break
        if habit_found:
            break

    if not habit_found:
        flash("Hábito no encontrado en el catálogo", "danger")
        return redirect(url_for("explore.home"))

    # Crear el hábito en la base de datos con reintentos
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            Habit.create(
                email=email,
                name=habit_found["name"],
                short_desc=habit_found["short_desc"],
                category_id=habit_found["category_id"]
            )
            flash(f'¡Hábito "{habit_found["name"]}" agregado exitosamente!', "success")
            break
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = str(e)
                if "locked" in error_msg.lower():
                    flash("La base de datos está ocupada. Por favor intenta nuevamente.", "warning")
                else:
                    flash(f"Error al agregar el hábito: {error_msg}", "danger")
            else:
                # Esperar un poco antes de reintentar
                import time
                time.sleep(0.1)
                continue

    # Redirigir de vuelta según el referer
    referer = request.referrer
    if referer and "category" in referer:
        return redirect(referer)
    return redirect(url_for("explore.home"))

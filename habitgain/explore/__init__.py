from flask import Blueprint, render_template, session, redirect, url_for, abort, flash, request
from jinja2 import TemplateNotFound
from ..models import Category, Habit

explore_bp = Blueprint("explore", __name__, template_folder="templates")

# Catálogo de hábitos sugeridos organizados por categoría
HABIT_CATALOG = {
    1: [  # Health
        {"id": "health_1", "name": "Beber 8 vasos de agua", "short_desc": "Mantente hidratado durante todo el día",
         "long_desc": "La hidratación es fundamental para el funcionamiento óptimo del cuerpo. Beber suficiente agua ayuda a mantener la energía, mejora la concentración y apoya todas las funciones corporales.",
         "why_works": "El cuerpo humano es aproximadamente 60% agua. Mantenerse hidratado mejora la función cognitiva, ayuda a la digestión, regula la temperatura corporal y aumenta los niveles de energía.",
         "icon": "💧", "category_id": 1},
        {"id": "health_2", "name": "Hacer 30 min de ejercicio", "short_desc": "Cardio, yoga o cualquier actividad física",
         "long_desc": "30 minutos diarios de ejercicio moderado mejora significativamente la salud cardiovascular, fortalece músculos y huesos, y libera endorfinas que mejoran el estado de ánimo.",
         "why_works": "El ejercicio regular reduce el riesgo de enfermedades crónicas, mejora la calidad del sueño, aumenta la energía y reduce el estrés y la ansiedad.",
         "icon": "🏃", "category_id": 1},
        {"id": "health_3", "name": "Dormir 8 horas", "short_desc": "Descanso adecuado para recuperación",
         "long_desc": "El sueño de calidad es esencial para la recuperación física y mental. 7-8 horas de sueño permiten que el cuerpo repare tejidos y consolide memorias.",
         "why_works": "Durante el sueño, el cuerpo libera hormonas de crecimiento, consolida la memoria, fortalece el sistema inmune y regula el metabolismo.",
         "icon": "😴", "category_id": 1},
        {"id": "health_4", "name": "Meditar 10 minutos", "short_desc": "Práctica de mindfulness y relajación",
         "long_desc": "La meditación diaria reduce el estrés, mejora el enfoque y promueve el bienestar emocional. Solo 10 minutos al día pueden hacer una gran diferencia.",
         "why_works": "La meditación reduce la actividad de la amígdala (centro del estrés), aumenta la materia gris en áreas relacionadas con la memoria y la empatía, y mejora la regulación emocional.",
         "icon": "🧘", "category_id": 1},
        {"id": "health_5", "name": "Estiramientos matutinos", "short_desc": "5 minutos de estiramientos al despertar",
         "long_desc": "Estirar por la mañana activa la circulación, reduce la rigidez muscular y prepara el cuerpo para el día. Mejora la flexibilidad y previene lesiones.",
         "why_works": "Los estiramientos aumentan el flujo sanguíneo a los músculos, mejoran el rango de movimiento, reducen la tensión acumulada durante el sueño y activan el sistema nervioso.",
         "icon": "🤸", "category_id": 1},
        {"id": "health_6", "name": "Caminar 10,000 pasos", "short_desc": "Actividad física diaria moderada",
         "long_desc": "Caminar 10,000 pasos al día (aproximadamente 8 km) es una meta accesible que mejora la salud cardiovascular sin requerir equipo especial.",
         "why_works": "Caminar regularmente fortalece el corazón, quema calorías, mejora la salud ósea, reduce el estrés y aumenta la creatividad y claridad mental.",
         "icon": "🚶", "category_id": 1},
    ],
    2: [  # Productivity
        {"id": "prod_1", "name": "Planificar el día", "short_desc": "Lista de prioridades cada mañana",
         "long_desc": "Dedicar 10-15 minutos cada mañana para planificar el día aumenta la productividad y reduce el estrés al tener claridad sobre las prioridades.",
         "why_works": "La planificación matutina activa el pensamiento estratégico, reduce la toma de decisiones durante el día (fatiga de decisión) y te mantiene enfocado en lo importante.",
         "icon": "📋", "category_id": 2},
        {"id": "prod_2", "name": "Técnica Pomodoro (2 sesiones)", "short_desc": "25 min de trabajo enfocado + 5 min descanso",
         "long_desc": "Trabaja en bloques de 25 minutos con descansos de 5 minutos. Dos sesiones Pomodoro al día en tareas importantes mejoran significativamente la productividad.",
         "why_works": "Los bloques de tiempo cortos mantienen la concentración alta, los descansos previenen la fatiga mental, y la técnica reduce la procrastinación al hacer las tareas menos intimidantes.",
         "icon": "🍅", "category_id": 2},
        {"id": "prod_3", "name": "Revisar inbox cero", "short_desc": "Procesar todo el correo electrónico",
         "long_desc": "Procesa todos los emails hasta llegar a cero en la bandeja de entrada. Archiva, delega, responde o agenda lo que requiera acción.",
         "why_works": "Mantener inbox cero reduce la carga mental, previene que cosas importantes se pierdan, y crea un sistema confiable para gestionar comunicaciones.",
         "icon": "📧", "category_id": 2},
        {"id": "prod_4", "name": "Desconectar redes sociales", "short_desc": "2 horas sin distracciones digitales",
         "long_desc": "Desactiva notificaciones y evita redes sociales durante 2 horas de trabajo profundo. Usa este tiempo para tareas que requieren concentración.",
         "why_works": "Las interrupciones digitales fragmentan la atención. Bloques de trabajo sin distracciones permiten entrar en 'flow state' donde la productividad se multiplica.",
         "icon": "📵", "category_id": 2},
        {"id": "prod_5", "name": "Preparar ropa para mañana", "short_desc": "Ahorra tiempo en las mañanas",
         "long_desc": "Dedica 5 minutos cada noche a elegir y preparar la ropa del día siguiente. Simplifica tu rutina matutina y elimina una decisión del día.",
         "why_works": "Reduce la fatiga de decisión matutina, ahorra tiempo valioso, disminuye el estrés de las mañanas y te permite empezar el día con más energía mental.",
         "icon": "👔", "category_id": 2},
        {"id": "prod_6", "name": "Limpiar escritorio", "short_desc": "5 minutos organizando espacio de trabajo",
         "long_desc": "Al final del día, dedica 5 minutos a organizar tu espacio de trabajo. Un escritorio limpio mejora el enfoque y reduce el estrés.",
         "why_works": "El desorden físico crea desorden mental. Un espacio organizado reduce distracciones, mejora la concentración y facilita empezar el día siguiente con energía.",
         "icon": "🗂️", "category_id": 2},
    ],
    3: [  # Learning
        {"id": "learn_1", "name": "Leer 20 páginas", "short_desc": "Lectura diaria de libros",
         "long_desc": "Lee 20 páginas de un libro cada día. A este ritmo, completarás 15-20 libros al año, expandiendo significativamente tu conocimiento.",
         "why_works": "La lectura regular mejora la memoria, aumenta el vocabulario, reduce el estrés, mejora la concentración y expone a nuevas ideas y perspectivas.",
         "icon": "📚", "category_id": 3},
        {"id": "learn_2", "name": "Aprender 10 palabras nuevas", "short_desc": "Expandir vocabulario o idioma",
         "long_desc": "Aprende 10 palabras nuevas en tu idioma nativo o en uno que estés estudiando. Usa flashcards o apps de vocabulario para reforzar el aprendizaje.",
         "why_works": "La adquisición gradual de vocabulario es más efectiva que el estudio intensivo. 10 palabras diarias son 3,650 al año, suficiente para dominar un idioma.",
         "icon": "📝", "category_id": 3},
        {"id": "learn_3", "name": "Ver un curso online", "short_desc": "30 minutos de aprendizaje estructurado",
         "long_desc": "Dedica 30 minutos diarios a un curso online en una plataforma como Coursera, Udemy o YouTube. Aprende una nueva habilidad profesional o personal.",
         "why_works": "El aprendizaje estructurado y consistente es más efectivo que sesiones largas esporádicas. 30 minutos diarios equivalen a completar múltiples cursos al año.",
         "icon": "💻", "category_id": 3},
        {"id": "learn_4", "name": "Practicar un instrumento", "short_desc": "15 minutos de práctica musical",
         "long_desc": "Practica un instrumento musical durante 15 minutos cada día. La práctica diaria es más efectiva que sesiones largas ocasionales.",
         "why_works": "Tocar música activa múltiples áreas del cerebro, mejora la memoria, coordinación y creatividad. La práctica diaria desarrolla memoria muscular más rápido.",
         "icon": "🎸", "category_id": 3},
        {"id": "learn_5", "name": "Escribir en diario", "short_desc": "Reflexión personal y autoconocimiento",
         "long_desc": "Escribe en un diario durante 10-15 minutos. Reflexiona sobre tu día, emociones, aprendizajes y metas. Puede ser físico o digital.",
         "why_works": "Escribir clarifica pensamientos, procesa emociones, documenta progreso personal y mejora la autoconciencia. Es una herramienta poderosa de crecimiento personal.",
         "icon": "📔", "category_id": 3},
        {"id": "learn_6", "name": "Podcast educativo", "short_desc": "Escuchar mientras haces otras tareas",
         "long_desc": "Escucha un podcast educativo durante actividades rutinarias como cocinar, hacer ejercicio o el trayecto al trabajo. Aprovecha el tiempo muerto.",
         "why_works": "Los podcasts permiten aprendizaje multitarea. Puedes consumir contenido educativo sin dedicar tiempo exclusivo, maximizando tu productividad diaria.",
         "icon": "🎧", "category_id": 3},
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

    # Todos los sugeridos (para el home)
    all_suggested_habits = []
    for _, habits in HABIT_CATALOG.items():
        all_suggested_habits.extend(habits)

    return render_template(
        "home.html",
        categories=categories,
        habits=user_habits,
        suggested_habits=all_suggested_habits,
    )


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
    suggested_habits = HABIT_CATALOG.get(category_id, [])
    return render_template(
        "category.html",
        category=cat,
        habits=user_habits,
        suggested_habits=suggested_habits,
    )


@explore_bp.route("/add_habit/<habit_id>", methods=["POST"])
def add_habit(habit_id: str):
    """Agregar un hábito del catálogo al panel del usuario."""
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

    # HU-18: validar duplicado por nombre para este usuario
    if Habit.exists_by_name(email, habit_found["name"]):
        flash("Ya tienes un hábito con ese nombre. Intenta con otro.", "warning")
        referer = request.referrer
        return redirect(referer or url_for("explore.home"))

    # Crear el hábito en la base de datos con reintentos
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            Habit.create(
                email=email,
                name=habit_found["name"],
                short_desc=habit_found.get("short_desc", ""),
                category_id=habit_found.get("category_id") or 1,
            )
            flash(
                f'¡Hábito "{habit_found["name"]}" agregado exitosamente!', "success")
            break
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = str(e)
                if "locked" in error_msg.lower():
                    flash(
                        "La base de datos está ocupada. Por favor intenta nuevamente.", "warning")
                else:
                    flash(f"Error al agregar el hábito: {error_msg}", "danger")
            else:
                import time
                time.sleep(0.1)
                continue

    # Redirigir de vuelta según el referer
    referer = request.referrer
    if referer and "category" in referer:
        return redirect(referer)
    return redirect(url_for("explore.home"))


@explore_bp.route("/remove_habit/<int:habit_id>", methods=["POST"])
def remove_habit(habit_id: int):
    """Eliminar un hábito del panel del usuario."""
    if not _require_login():
        return redirect(url_for("auth.login"))

    try:
        Habit.delete(habit_id)
        flash("Hábito eliminado exitosamente", "success")
    except Exception as e:
        flash(f"Error al eliminar el hábito: {str(e)}", "danger")

    referer = request.referrer
    if referer:
        return redirect(referer)
    return redirect(url_for("explore.home"))


@explore_bp.route("/my-habits")
def my_habits():
    """TT-05: vista simple de hábitos del usuario."""
    if not _require_login():
        return redirect(url_for("auth.login"))
    email = session["user"]["email"]
    habits = Habit.list_by_owner(email)
    try:
        return render_template("my_habits.html", habits=habits)
    except TemplateNotFound:
        # Fallback temporal si aún no existe la plantilla
        categories = Category.all()
        return render_template("home.html", categories=categories, habits=habits, suggested_habits=[])

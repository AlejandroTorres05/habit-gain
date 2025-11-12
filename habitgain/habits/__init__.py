from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from ..models import Habit, Category, Completion
import secrets

habits_bp = Blueprint("habits", __name__, template_folder="templates")


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
        user = _user_email()
        # Obtener datos del formulario
        nombre = (request.form.get("nombre")
                  or request.form.get("name") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        icon = (request.form.get("icon") or request.form.get("emoji") or "").strip()
        habit_base_id = request.form.get("habit_base_id") or request.form.get("stack_after") or ""
        frecuencia_in = (request.form.get("frecuencia") or "diaria").strip().lower()
        categoria_nombre = (request.form.get("categoria") or "").strip()

        # Validaciones
        if not nombre:
            flash("El nombre del hábito es obligatorio", "warning")
            # Habitos existentes desde DB para el select de stacking
            habitos_existentes = Habit.list_active_by_owner(user)
            return render_template(
                "habits/new.html",
                habitos_existentes=habitos_existentes,
                categorias=_get_categorias()
            )

        # Validar duplicado de nombre (case-insensitive, mismo usuario)
        existing_names = { (h.get("name") or h.get("nombre") or "").strip().casefold(): True for h in Habit.list_by_owner(user) }
        if nombre.strip().casefold() in existing_names:
            flash("Ya tienes un hábito con ese nombre. Elige otro.", "warning")
            completed_today = set(Completion.completed_today_ids(user))
            habitos_existentes = [h for h in Habit.list_active_by_owner(user) if h.get("id") not in completed_today]
            return render_template(
                "habits/new.html",
                habitos_existentes=habitos_existentes,
                categorias=_get_categorias()
            )

        # Normalizar frecuencia a valores internos (extensiones mapean a buckets base)
        freq_map = {
            "diaria": "daily",
            "semanal": "weekly",
            "mensual": "monthly",
            "cada_2_dias": "daily",
            "cada_3_dias": "daily",
            "dias_laborales": "daily",
            "fin_de_semana": "weekly",
            "cada_2_semanas": "weekly",
        }
        frequency = freq_map.get(frecuencia_in, "daily")
        # frequency_detail: conservar la selección extendida si aplica
        extended_vals = {"cada_2_dias","cada_3_dias","dias_laborales","fin_de_semana","cada_2_semanas"}
        frequency_detail = frecuencia_in if frecuencia_in in extended_vals else ""

        # Resolver categoría por nombre (crear si no existe)
        category_id = None
        if categoria_nombre:
            cats = Category.all()
            match = next((c for c in cats if (c.get("name") or "").strip().casefold() == categoria_nombre.casefold()), None)
            if match:
                category_id = match.get("id")
            else:
                try:
                    category_id = Category.create(categoria_nombre, None)
                except Exception:
                    # fallback a primera categoría existente
                    category_id = (cats[0]["id"] if cats else 1)
        else:
            # predeterminada
            cats = Category.all()
            category_id = (cats[0]["id"] if cats else 1)

        # Parse habit_base_id si viene
        base_id_int = None
        if habit_base_id:
            try:
                base_id_int = int(habit_base_id)
            except (ValueError, TypeError):
                base_id_int = None

        # Validar que el hábito base no esté completado hoy
        completed_today = set(Completion.completed_today_ids(user))
        if base_id_int and base_id_int in completed_today:
            flash("No puedes anclar a un hábito que ya completaste hoy. Elige otro.", "warning")
            habitos_existentes = [h for h in Habit.list_active_by_owner(user) if h.get("id") not in completed_today]
            return render_template(
                "habits/new.html",
                habitos_existentes=habitos_existentes,
                categorias=_get_categorias()
            )
        # Validar que, si se envió base, exista y esté activa
        if base_id_int:
            base_h = Habit.get_by_id(base_id_int)
            if not base_h or base_h.get("owner_email") != user or not base_h.get("active"):
                flash("El hábito base no es válido o no está activo.", "warning")
                habitos_existentes = [h for h in Habit.list_active_by_owner(user) if h.get("id") not in completed_today]
                return render_template(
                    "habits/new.html",
                    habitos_existentes=habitos_existentes,
                    categorias=_get_categorias()
                )

        # Crear en DB (category_id por defecto 1 si no se especifica)
        new_id = Habit.create(email=user, name=nombre, short_desc=descripcion, category_id=category_id, frequency=frequency, habit_base_id=base_id_int, icon=icon or None, frequency_detail=frequency_detail)

        # Mensaje de éxito personalizado
        if habit_base_id:
            try:
                base_id = int(habit_base_id)
                habit_base = Habit.get_by_id(base_id)
                if habit_base:
                    base_name = habit_base.get("name")
                    flash(f'¡Hábito "{nombre}" creado y vinculado a "{base_name}"!', "success")
                else:
                    flash(f'¡Hábito "{nombre}" creado exitosamente!', "success")
            except (ValueError, TypeError):
                flash(f'¡Hábito "{nombre}" creado exitosamente!', "success")
        else:
            flash(f'¡Hábito "{nombre}" creado exitosamente!', "success")

        return redirect(url_for("progress.panel"))

    # GET - Mostrar formulario
    # Habitos existentes desde DB (excluir completados hoy para anclar)
    completed_today = set(Completion.completed_today_ids(user))
    habitos_existentes = [h for h in Habit.list_active_by_owner(user) if h.get("id") not in completed_today]
    categorias = _get_categorias()

    return render_template(
        "habits/new.html",
        habitos_existentes=habitos_existentes,
        categorias=categorias,
    )


# AJAX: validar duplicado de nombre
@habits_bp.route("/validate-name", methods=["GET"])
def validate_name():
    user = _user_email()
    if not user:
        return jsonify({"ok": False, "error": "not_authenticated"}), 401
    name = (request.args.get("name") or "").strip()
    exists = False
    if name:
        exists_map = { (h.get("name") or h.get("nombre") or "").strip().casefold(): True for h in Habit.list_by_owner(user) }
        exists = name.casefold() in exists_map
    return jsonify({"ok": True, "exists": exists})


# Funciones auxiliares
def _get_habit_by_id(user, habit_id):
    return Habit.get_by_id(habit_id)


def _get_categorias():
    # Se usa para compatibilidad con new.html (strings); para edición usamos Category.all()
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
    # No usado por el panel actual; mantenido para compatibilidad si se requiere.
    habitos = Habit.list_by_owner(user)

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
    habitos = Habit.list_by_owner(user)
    total_habitos = len(habitos)
    completados_hoy = 0  # este helper queda como placeholder; el panel usa Completion en DB

    return {
        "total": total_habitos,
        "completados": completados_hoy,
        "porcentaje": int(
            (completados_hoy / total_habitos * 100) if total_habitos > 0 else 0
        ),
    }


# HU-11: eliminar hábito con confirmación
@habits_bp.route("/<int:habit_id>/delete", methods=["GET", "POST"])
def delete(habit_id: int):
    """
    Vista dedicada para confirmar y eliminar un hábito (HU-11).
    GET: mostrar página de confirmación.
    POST: eliminar y redirigir al panel con mensaje flash.
    """
    user = _user_email()
    if not user:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    habit = Habit.get_by_id(habit_id)
    if not habit:
        flash("No se encontró el hábito solicitado.", "danger")
        return redirect(url_for("progress.panel"))
    # Validar propietario
    if habit.get("owner_email") != user:
        flash("No tienes permisos para eliminar este hábito.", "warning")
        return redirect(url_for("progress.panel"))

    if request.method == "POST":
        # eliminar en DB y notificar
        try:
            Habit.delete(habit_id)
            flash(f'Hábito "{habit.get("name")}" eliminado correctamente.', "success")
        except Exception:
            flash("Ocurrió un error al eliminar el hábito.", "danger")
        return redirect(url_for("progress.panel"))

    return render_template("habits/delete.html", habit=habit)


# HU-14: Editar hábito
def _get_csrf_token_edit() -> str:
    token = secrets.token_urlsafe(32)
    session["csrf_token_habits_edit"] = token
    session.modified = True
    return token


@habits_bp.route("/<int:habit_id>/edit", methods=["GET", "POST"])
def edit(habit_id: int):
    user = _user_email()
    if not user:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    habit = Habit.get_by_id(habit_id)
    if not habit:
        flash("No se encontró el hábito solicitado.", "danger")
        return redirect(url_for("progress.panel"))
    if habit.get("owner_email") != user:
        flash("No tienes permisos para editar este hábito.", "warning")
        return redirect(url_for("progress.panel"))

    if request.method == "POST":
        # CSRF
        form_token = request.form.get("csrf_token", "")
        sess_token = session.pop("csrf_token_habits_edit", None)
        if not sess_token or form_token != sess_token:
            flash("Token CSRF inválido.", "danger")
            return redirect(url_for("habits.edit", habit_id=habit_id))

        # Datos
        name = (request.form.get("name") or request.form.get("nombre") or "").strip()
        short_desc = (request.form.get("short_desc") or request.form.get("descripcion") or "").strip()
        freq_in = (request.form.get("frequency") or request.form.get("frecuencia") or "daily").strip().lower()
        cat_id_raw = request.form.get("category_id") or request.form.get("categoria_id") or ""
        base_raw = request.form.get("habit_base_id") or ""

        # Validaciones
        errors = []
        if not name:
            errors.append("El nombre del hábito es obligatorio")

        # Normalizar frecuencia (extensiones mapean a buckets base)
        freq_map = {
            "diaria": "daily", "semanal": "weekly", "mensual": "monthly",
            "daily": "daily", "weekly": "weekly", "monthly": "monthly",
            "cada_2_dias": "daily", "cada_3_dias": "daily", "dias_laborales": "daily",
            "fin_de_semana": "weekly", "cada_2_semanas": "weekly",
        }
        frequency = freq_map.get(freq_in)
        if frequency is None:
            errors.append("Frecuencia inválida")

        try:
            category_id = int(cat_id_raw) if cat_id_raw else (habit.get("category_id") or 1)
        except ValueError:
            errors.append("Categoría inválida")
            category_id = habit.get("category_id") or 1

        # Validar base (puede venir vacío para desanclar)
        habit_base_id = None
        if base_raw:
            try:
                base_candidate = int(base_raw)
                if base_candidate == habit_id:
                    errors.append("No puedes anclar un hábito a sí mismo")
                else:
                    base_habit = Habit.get_by_id(base_candidate)
                    if not base_habit or base_habit.get("owner_email") != user:
                        errors.append("El hábito base seleccionado no existe o no te pertenece")
                    elif not base_habit.get("active"):
                        errors.append("El hábito base seleccionado no está activo")
                    else:
                        habit_base_id = base_candidate
            except ValueError:
                errors.append("Hábito base inválido")

        if not Category.get_by_id(category_id):
            errors.append("La categoría seleccionada no existe")

        if errors:
            for e in errors:
                flash(e, "danger")
            categories = Category.all()
            # candidatos para anclar (excluye el propio y completados hoy)
            completed_today = set(Completion.completed_today_ids(user))
            candidatos = [h for h in Habit.list_active_by_owner(user) if h.get("id") != habit_id and h.get("id") not in completed_today]
            # Render nuevamente con valores actuales del form
            return render_template(
                "habits/edit.html",
                habit={**habit, "name": name, "short_desc": short_desc, "frequency": frequency, "category_id": category_id, "habit_base_id": habit_base_id},
                categories=categories,
                habitos_existentes=candidatos,
                csrf_token=_get_csrf_token_edit(),
            )

        # Persistir
        updated = Habit.update(user, habit_id, name=name, short_desc=short_desc, frequency=frequency, category_id=category_id, habit_base_id=habit_base_id)
        if updated <= 0:
            flash("No se pudo actualizar el hábito.", "danger")
            return redirect(url_for("habits.edit", habit_id=habit_id))

        flash("Hábito actualizado correctamente", "success")
        return redirect(url_for("progress.panel"))

    # GET
    categories = Category.all()
    csrf_token = _get_csrf_token_edit()
    # candidatos para anclar (excluye el propio y completados hoy)
    completed_today = set(Completion.completed_today_ids(user))
    habitos_existentes = [h for h in Habit.list_active_by_owner(user) if h.get("id") != habit_id and h.get("id") not in completed_today]
    return render_template("habits/edit.html", habit=habit, categories=categories, habitos_existentes=habitos_existentes, csrf_token=csrf_token)

from flask import Blueprint, render_template, session, redirect, url_for
from ..models import Category, Habit

# Este blueprint sirve /explore/ y busca plantillas en habitgain/explore/templates
explore_bp = Blueprint("explore", __name__,
                       template_folder="templates", url_prefix="/explore")


def _require_login():
    return "user" in session


@explore_bp.route("/")
def home():
    if not _require_login():
        return redirect(url_for("auth.login"))

    email = session["user"]["email"]
    categories = Category.all()
    habits = Habit.list_active_by_owner(email)
    # Esta plantilla está en habitgain/explore/templates/home.html
    return render_template("home.html", categories=categories, habits=habits)


# Alias de endpoint para mantener compatibilidad con base.html
# Ahora url_for("explore.explore") y url_for("explore.home") son equivalentes.
explore_bp.add_url_rule("/", endpoint="explore", view_func=home)

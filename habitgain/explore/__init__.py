from flask import Blueprint, render_template, session, redirect, url_for, abort
from ..models import Category, Habit

explore_bp = Blueprint("explore", __name__, template_folder="templates")


def _require_login():
    return "user" in session


@explore_bp.route("/")
def home():
    if not _require_login():
        return redirect(url_for("auth.login"))
    email = session["user"]["email"]
    categories = Category.all()
    habits = Habit.list_active_by_owner(email)
    return render_template("home.html", categories=categories, habits=habits)


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
    habits = Habit.list_active_by_owner_and_category(email, category_id)
    return render_template("category.html", category=cat, habits=habits)

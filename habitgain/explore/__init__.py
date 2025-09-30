from flask import Blueprint, render_template, request, jsonify
from ..models import Category, Habit

explore_bp = Blueprint("explore", __name__, template_folder="templates")


@explore_bp.route("/")
def explore():
    categories = Category.all()
    habits = Habit.all()
    return render_template("explore/explore.html",
                           categories=categories, habits=habits)


@explore_bp.route("/habit/<int:habit_id>")
def habit_detail(habit_id: int):
    habit = Habit.get(habit_id)
    if not habit:
        from flask import render_template
        return render_template("404.html"), 404
    return render_template("explore/detail_habit.html", habit=habit)

# APIs


@explore_bp.route("/api/by-category/<int:category_id>")
def api_by_category(category_id: int):
    return jsonify(Habit.by_category(category_id))


@explore_bp.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    return jsonify(Habit.all() if not q else Habit.search(q))

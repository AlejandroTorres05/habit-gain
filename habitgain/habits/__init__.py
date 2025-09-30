from flask import Blueprint, render_template, request, redirect, url_for, session, flash

habits_bp = Blueprint("habits", __name__, template_folder="templates")

# simple in-memory store per user for MVP
USER_HABITS = {}


def _user_email():
    return (session.get("user") or {}).get("email")


@habits_bp.route("/new", methods=["GET", "POST"])
def create():
    user = _user_email()
    if not user:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        stack_after = request.form.get("stack_after") or ""
        if not name:
            flash("Name is required", "warning")
            return render_template("habits/new.html")
        USER_HABITS.setdefault(user, [])
        USER_HABITS[user].append({
            "id": len(USER_HABITS[user])+1000,
            "name": name,
            "done": False,
            "stack_after": stack_after
        })
        flash("Habit created", "success")
        return redirect(url_for("progress.panel"))
    return render_template("habits/new.html")


@habits_bp.route("/mark/<int:habit_id>", methods=["POST"], endpoint="habits_mark")
def mark(habit_id: int):
    user = _user_email()
    if not user:
        return redirect(url_for("auth.login"))
    for h in USER_HABITS.get(user, []):
        if h["id"] == habit_id:
            h["done"] = True
            break
    return redirect(url_for("progress.panel"))

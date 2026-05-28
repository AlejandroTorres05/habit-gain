from flask import Blueprint, redirect, url_for, session, render_template

core_bp = Blueprint("core", __name__, template_folder="templates")


def _is_logged_in() -> bool:
    return "user" in session


@core_bp.route("/")
def home():
    if _is_logged_in():
        return redirect(url_for("explore.home"))
    return render_template("landing.html")

# Opcional: una ruta de salud si necesitas chequear que el server vive


@core_bp.route("/healthz")
def healthz():
    return {"status": "ok"}, 200

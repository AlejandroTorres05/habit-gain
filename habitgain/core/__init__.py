from flask import Blueprint, redirect, url_for, session, render_template

core_bp = Blueprint("core", __name__, template_folder="templates")


def _is_logged_in() -> bool:
    return "user" in session


@core_bp.route("/")
def home():
    # Si ya está logueado, mándalo a explorar
    if _is_logged_in():
        # <- antes decía explore.explore
        return redirect(url_for("explore.home"))
    # Si no hay sesión, manda a login (ajusta el endpoint si tu auth usa otro nombre)
    return redirect(url_for("auth.login"))

# Opcional: una ruta de salud si necesitas chequear que el server vive


@core_bp.route("/healthz")
def healthz():
    return {"status": "ok"}, 200

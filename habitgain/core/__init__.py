from flask import Blueprint, render_template, redirect, url_for

core_bp = Blueprint("core", __name__, template_folder="templates")

@core_bp.route("/")
def home():
    # direct users to explore for MVP
    return redirect(url_for("explore.explore"))

@core_bp.app_errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404

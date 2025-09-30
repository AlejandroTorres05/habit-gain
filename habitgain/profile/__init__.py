from flask import Blueprint, render_template

profile_bp = Blueprint("profile", __name__, template_folder="templates")


@profile_bp.route("/edit")
def edit():
    return render_template("profile/edit.html")

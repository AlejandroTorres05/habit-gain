from flask import Blueprint, render_template

manage_bp = Blueprint("manage", __name__, template_folder="templates")

@manage_bp.route("/delete")
def delete_stub():
    return render_template("manage/delete.html")

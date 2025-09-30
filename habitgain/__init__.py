from flask import Flask
from .core import core_bp
from .auth import auth_bp
from .explore import explore_bp
from .habits import habits_bp
from .progress import progress_bp
from .profile import profile_bp
from .manage import manage_bp
from .models import Database

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret"  # replace for production

    # DB init + seed
    db = Database()
    db.init_db()
    db.seed_data()

    # Blueprints
    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp,     url_prefix="/auth")
    app.register_blueprint(explore_bp,  url_prefix="/explore")
    app.register_blueprint(habits_bp,   url_prefix="/habits")
    app.register_blueprint(progress_bp, url_prefix="/progress")
    app.register_blueprint(profile_bp,  url_prefix="/profile")
    app.register_blueprint(manage_bp,   url_prefix="/manage")

    return app

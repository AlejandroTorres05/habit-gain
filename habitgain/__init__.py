# habitgain/__init__.py

import os
from flask import Flask, url_for
from werkzeug.routing import BuildError

from .core import core_bp
from .auth import auth_bp
from .explore import explore_bp
from .habits import habits_bp
from .progress import progress_bp
from .profile import profile_bp
from .manage import manage_bp
from .admin import admin_bp
from .models import Database

# SECRET_KEY configurable por entorno, con fallback dev
SECRET_KEY = os.environ.get("HABITGAIN_SECRET_KEY", "dev-secret")


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY  # reemplazar en prod por algo serio

    # DB init + seed
    db = Database()
    db.init_db()
    db.seed_data()

    # ===== Contexto para plantillas (sin current_app en Jinja, sin BuildError) =====
    @app.context_processor
    def inject_template_vars():
        # intenta resolver una URL válida para "Panel" entre varios endpoints comunes
        candidates = [
            "progress.panel",          # panel actual
            "manage.home", "manage.index",
            "panel.home", "panel.index",
            "dashboard.home", "dashboard.index",
            "explore.home",            # fallback si no hay panel
        ]
        panel_url = url_for("core.home")
        for ep in candidates:
            try:
                panel_url = url_for(ep)
                break
            except BuildError:
                continue

        return {
            "has_auth": "auth" in app.blueprints,
            "panel_url": panel_url,
        }

    # ===== Blueprints =====
    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp,     url_prefix="/auth")
    app.register_blueprint(explore_bp,  url_prefix="/explore")
    app.register_blueprint(habits_bp,   url_prefix="/habits")
    app.register_blueprint(progress_bp, url_prefix="/progress")
    app.register_blueprint(profile_bp,  url_prefix="/profile")
    app.register_blueprint(manage_bp,   url_prefix="/manage")
    app.register_blueprint(admin_bp,    url_prefix="/admin")

    return app

#!/usr/bin/env bash
set -e

PROJ="habitgain"
PKG="$PROJ"

mkdir -p "$PROJ"
cd "$PROJ"

# Python package
mkdir -p "$PKG"/{core,auth,explore,habits,progress,profile,manage}/templates
mkdir -p "$PKG"/static/{css,js,img}
mkdir -p "$PKG"/templates  # para base compartida
mkdir -p "$PKG"/tests
touch "$PKG"/__init__.py

# ---------------- base files ----------------
cat > "$PKG/__init__.py" << 'PY'
from flask import Flask
from .core import core_bp
from .auth import auth_bp
from .explore import explore_bp
from .habits import habits_bp
from .progress import progress_bp
from .profile import profile_bp
from .manage import manage_bp

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret"  # cambiar en prod

    # Blueprints
    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp,    url_prefix="/auth")
    app.register_blueprint(explore_bp, url_prefix="/explore")
    app.register_blueprint(habits_bp,  url_prefix="/habits")
    app.register_blueprint(progress_bp,url_prefix="/progress")
    app.register_blueprint(profile_bp, url_prefix="/profile")
    app.register_blueprint(manage_bp,  url_prefix="/manage")

    return app
PY

# ---------------- core (layout, home, errors) ----------------
cat > "$PKG/core/__init__.py" << 'PY'
from flask import Blueprint, render_template

core_bp = Blueprint("core", __name__, template_folder="templates", static_folder="../static")

@core_bp.route("/")
def home():
    return render_template("base.html", title="HabitGain — Home")

@core_bp.app_errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404
PY

cat > "$PKG/core/templates/404.html" << 'HTML'
{% extends "base.html" %}
{% block content %}
  <div class="container py-5 text-center">
    <h1 class="display-5 fw-bold text-light">404</h1>
    <p class="lead text-secondary">Página no encontrada</p>
  </div>
{% endblock %}
HTML

# ---------------- auth (HU1, HU2) ----------------
cat > "$PKG/auth/__init__.py" << 'PY'
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

auth_bp = Blueprint("auth", __name__, template_folder="templates")

# datos de ejemplo; luego puedes moverlos a data.py
USERS = {"demo@habit.com": {"password": "123456", "name": "Demo"}}

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip()
        pwd   = request.form.get("password","")
        user  = USERS.get(email)
        if user and user["password"] == pwd:
            session["user"] = {"email": email, "name": user["name"]}
            return redirect(url_for("progress.panel"))
        flash("Credenciales inválidas", "danger")
    return render_template("auth/login.html", title="Iniciar sesión")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # stub: solo muestra la vista
    return render_template("auth/register.html", title="Crear cuenta")
PY

mkdir -p "$PKG/auth/templates/auth"
cat > "$PKG/auth/templates/auth/login.html" << 'HTML'
{% extends "base.html" %}
{% block content %}
<div class="container py-5" style="max-width:420px">
  <h2 class="text-light mb-4">Iniciar sesión</h2>
  <form method="post" class="card p-4 bg-dark-subtle border-0 rounded-4">
    <div class="mb-3">
      <label class="form-label">Correo</label>
      <input class="form-control" name="email" placeholder="demo@habit.com" required>
    </div>
    <div class="mb-3">
      <label class="form-label">Contraseña</label>
      <input type="password" class="form-control" name="password" placeholder="••••••" required>
    </div>
    <button class="btn btn-primary w-100 rounded-pill">Entrar</button>
  </form>
</div>
{% endblock %}
HTML

cat > "$PKG/auth/templates/auth/register.html" << 'HTML'
{% extends "base.html" %}
{% block content %}
<div class="container py-5" style="max-width:480px">
  <h2 class="text-light mb-4">Crear cuenta</h2>
  <div class="alert alert-info">Registro simulado para MVP.</div>
</div>
{% endblock %}
HTML

# ---------------- explore (HU3) ----------------
cat > "$PKG/explore/__init__.py" << 'PY'
from flask import Blueprint, render_template, request

explore_bp = Blueprint("explore", __name__, template_folder="templates")

CATEGORIES = ["Productividad", "Bienestar", "Salud"]
HABITS = [
    {"id":1,"name":"Leer 10 min","cat":"Productividad"},
    {"id":2,"name":"Meditar 5 min","cat":"Bienestar"},
    {"id":3,"name":"Caminar 20 min","cat":"Salud"},
]

@explore_bp.route("/")
def list_habits():
    cat = request.args.get("cat")
    q   = request.args.get("q","").lower().strip()
    items = HABITS
    if cat: items = [h for h in items if h["cat"] == cat]
    if q:   items = [h for h in items if q in h["name"].lower()]
    return render_template("explore/explore.html",
                           categories=CATEGORIES, selected=cat, q=q, habits=items)
PY

mkdir -p "$PKG/explore/templates/explore"
cat > "$PKG/explore/templates/explore/explore.html" << 'HTML'
{% extends "base.html" %}
{% block content %}
<div class="container py-4">
  <h2 class="text-light">Explorar hábitos</h2>
  <form class="row g-2 my-3">
    <div class="col-md-3">
      <select class="form-select" name="cat" onchange="this.form.submit()">
        <option value="">Todas las categorías</option>
        {% for c in categories %}
          <option value="{{c}}" {{ 'selected' if c==selected else '' }}>{{c}}</option>
        {% endfor %}
      </select>
    </div>
    <div class="col-md-6">
      <input class="form-control" name="q" value="{{q}}" placeholder="Buscar...">
    </div>
    <div class="col-md-3">
      <button class="btn btn-outline-light w-100">Filtrar</button>
    </div>
  </form>
  <div class="row">
    {% for h in habits %}
      <div class="col-md-4 mb-3">
        <div class="card bg-dark text-light rounded-4 p-3">{{h.name}}
          <div class="small text-secondary">{{h.cat}}</div>
        </div>
      </div>
    {% else %}
      <p class="text-secondary">Sin resultados.</p>
    {% endfor %}
  </div>
</div>
{% endblock %}
HTML

# ---------------- habits (HU4, HU5, HU6) ----------------
cat > "$PKG/habits/__init__.py" << 'PY'
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

habits_bp = Blueprint("habits", __name__, template_folder="templates")

# estado en memoria por usuario (MVP)
USER_HABITS = {}

def _get_user():
    return (session.get("user") or {}).get("email")

@habits_bp.route("/new", methods=["GET","POST"])
def create():
    user = _get_user()
    if not user:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        name = request.form.get("name","").strip()
        base = request.form.get("stack_base")  # habit stacking (opcional)
        if not name:
            flash("El nombre es obligatorio", "warning")
            return render_template("habits/new.html")
        USER_HABITS.setdefault(user, [])
        USER_HABITS[user].append({"id":len(USER_HABITS[user])+100, "name":name, "done":False, "base":base})
        flash("Hábito creado", "success")
        return redirect(url_for("progress.panel"))
    return render_template("habits/new.html")

@habits_bp.route("/mark/<int:hid>", methods=["POST"])
def mark(hid):
    user = _get_user()
    if not user:
        return redirect(url_for("auth.login"))
    for h in USER_HABITS.get(user, []):
        if h["id"] == hid:
            h["done"] = True
            break
    flash("¡Hábito completado!", "success")
    return redirect(url_for("progress.panel"))
PY

mkdir -p "$PKG/habits/templates/habits"
cat > "$PKG/habits/templates/habits/new.html" << 'HTML'
{% extends "base.html" %}
{% block content %}
<div class="container py-4" style="max-width:580px">
  <h2 class="text-light">Crear hábito</h2>
  <form method="post" class="card p-4 bg-dark-subtle border-0 rounded-4">
    <div class="mb-3">
      <label class="form-label">Nombre</label>
      <input class="form-control" name="name" placeholder="Leer 10 minutos" required>
    </div>
    <div class="mb-3">
      <label class="form-label">Habit stacking (opcional) — después de:</label>
      <input class="form-control" name="stack_base" placeholder="Tomar café">
    </div>
    <button class="btn btn-primary rounded-pill">Guardar</button>
  </form>
</div>
{% endblock %}
HTML

# ---------------- progress (HU7, HU8, HU9) ----------------
cat > "$PKG/progress/__init__.py" << 'PY'
from flask import Blueprint, render_template, session, redirect, url_for
from ..habits import USER_HABITS

progress_bp = Blueprint("progress", __name__, template_folder="templates")

@progress_bp.route("/panel")
def panel():
    user = (session.get("user") or {}).get("email")
    if not user:
        return redirect(url_for("auth.login"))
    habits = USER_HABITS.get(user, [])
    completed = sum(1 for h in habits if h.get("done"))
    return render_template("progress/panel.html", habits=habits, completed=completed, total=len(habits))
PY

mkdir -p "$PKG/progress/templates/progress"
cat > "$PKG/progress/templates/progress/panel.html" << 'HTML'
{% extends "base.html" %}
{% block content %}
<div class="container py-4">
  <div class="d-flex justify-content-between align-items-center">
    <h2 class="text-light">Mi Panel</h2>
    <a class="btn btn-outline-light rounded-pill" href="{{ url_for('habits.create') }}">+ Nuevo hábito</a>
  </div>
  <p class="text-secondary">Progreso de hoy: <strong>{{completed}}</strong> de <strong>{{total}}</strong></p>
  <div class="row">
    {% for h in habits %}
      <div class="col-md-4 mb-3">
        <div class="card bg-dark text-light rounded-4 p-3 h-100">
          <div class="fw-semibold">{{h.name}}</div>
          {% if h.base %}<div class="small text-info">Después de: {{h.base}}</div>{% endif %}
          <div class="mt-auto">
            {% if h.done %}
              <span class="badge text-bg-success rounded-pill">Completado</span>
            {% else %}
              <form method="post" action="{{ url_for('habits.mark', hid=h.id) }}">
                <button class="btn btn-primary btn-sm rounded-pill">Hecho</button>
              </form>
            {% endif %}
          </div>
        </div>
      </div>
    {% else %}
      <p class="text-secondary">Aún no tienes hábitos. Crea uno.</p>
    {% endfor %}
  </div>
</div>
{% endblock %}
HTML

# ---------------- profile (HU10) ----------------
cat > "$PKG/profile/__init__.py" << 'PY'
from flask import Blueprint, render_template

profile_bp = Blueprint("profile", __name__, template_folder="templates")

@profile_bp.route("/edit")
def edit_profile():
    return render_template("profile/edit.html")
PY

mkdir -p "$PKG/profile/templates/profile"
cat > "$PKG/profile/templates/profile/edit.html" << 'HTML'
{% extends "base.html" %}
{% block content %}
<div class="container py-5">
  <h2 class="text-light">Editar perfil (stub)</h2>
  <p class="text-secondary">Para semana 12.</p>
</div>
{% endblock %}
HTML

# ---------------- manage (HU11) ----------------
cat > "$PKG/manage/__init__.py" << 'PY'
from flask import Blueprint, render_template

manage_bp = Blueprint("manage", __name__, template_folder="templates")

@manage_bp.route("/delete")
def delete_stub():
    return render_template("manage/delete.html")
PY

mkdir -p "$PKG/manage/templates/manage"
cat > "$PKG/manage/templates/manage/delete.html" << 'HTML'
{% extends "base.html" %}
{% block content %}
<div class="container py-5">
  <h2 class="text-light">Eliminar/archivar hábito (stub)</h2>
  <p class="text-secondary">Implementar en iteración siguiente.</p>
</div>
{% endblock %}
HTML

# ---------------- shared base & static ----------------
cat > "$PKG/templates/base.html" << 'HTML'
<!doctype html>
<html lang="es" data-bs-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title or "HabitGain" }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="{{ url_for('static', filename='css/styles.css') }}" rel="stylesheet">
</head>
<body class="bg-gradient">
<nav class="navbar navbar-dark">
  <div class="container">
    <a class="navbar-brand fw-bold" href="/">HabitGain</a>
    <div class="d-flex gap-2">
      <a class="btn btn-sm btn-outline-light" href="{{ url_for('explore.list_habits') }}">Explorar</a>
      <a class="btn btn-sm btn-outline-light" href="{{ url_for('progress.panel') }}">Panel</a>
      <a class="btn btn-sm btn-primary" href="{{ url_for('auth.login') }}">Entrar</a>
    </div>
  </div>
</nav>

{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="container mt-3">
      {% for cat, msg in messages %}
        <div class="alert alert-{{cat}} rounded-4">{{ msg }}</div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}

{% block content %}{% endblock %}

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
HTML

cat > "$PKG/static/css/styles.css" << 'CSS'
/* Paleta propuesta */
:root{
  --purple:#2D1B69; --violet:#5A3BBA; --electric:#3BB4FF; --cyan:#67E8F9;
}
.bg-gradient{
  background: linear-gradient(180deg, var(--purple) 0%, var(--violet) 100%);
  min-height: 100vh;
}
.btn-primary{
  background: linear-gradient(90deg, var(--electric), var(--cyan));
  border: none;
}
CSS

# ---------------- top-level files ----------------
cat > "run.py" << 'PY'
from habitgain import create_app
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
PY

cat > "requirements.txt" << 'REQ'
Flask==3.0.0
REQ

cat > "README.md" << 'MD'
# HabitGain (MVP)

## Setup rápido
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py

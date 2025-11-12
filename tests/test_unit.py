import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from flask import session, url_for
from habitgain import create_app
from habitgain.models import Database, User, Category, Habit
from habitgain.auth import is_valid_email, is_valid_password 
from habitgain.core import _is_logged_in, healthz
from habitgain.habits import (
    _get_categorias,
    get_progress_stats,
    get_user_habits_organized,
)
from habitgain.profile import _get_csrf_token, edit




@pytest.fixture(scope="module")
def client():
    """Crea una app Flask en modo de testing y prepara DB temporal."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })

    # Crear base de datos limpia
    db = Database()
    db.init_db()
    db.seed_data()

    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def logged_client(client):
    """Simula sesión autenticada para pruebas de rutas protegidas."""
    with client.session_transaction() as sess:
        sess["user"] = {"email": "test@example.com", "name": "Tester"}
    return client


#auth
def test_is_valid_email_valid():
    """Debe aceptar un correo electrónico con formato válido."""
    assert is_valid_email("user@example.com") is True


def test_is_valid_email_invalid():
    """Debe rechazar un correo electrónico sin formato válido."""
    assert is_valid_email("invalid-email") is False


def test_is_valid_password_strong():
    """Debe aceptar contraseñas fuertes con letras, números y símbolos."""
    assert is_valid_password("StrongPass123!") is True


def test_is_valid_password_weak():
    """Debe rechazar contraseñas demasiado cortas o simples."""
    assert is_valid_password("123") is False


# ---------------------------
# TEST: HOME ("/explore/")
# ---------------------------
def test_home_redirect_if_not_logged(client):
    """Debe redirigir a /auth/login si no hay sesión."""
    response = client.get("/explore/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_home_render_logged(logged_client):
    """Debe renderizar la plantilla home con hábitos sugeridos."""
    response = logged_client.get("/explore/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    # Debe contener nombres de categorías o hábitos sugeridos
    assert "Health" in html or "Beber 8 vasos de agua" in html



def test_category_not_found_returns_404(logged_client):
    """Debe devolver 404 si la categoría no existe."""
    response = logged_client.get("/explore/category/9999")
    assert response.status_code == 404


# ---------------------------
# TEST: ADD HABIT ("/explore/add_habit/<habit_id>")
# ---------------------------



def test_add_habit_success(logged_client):
    """Debe agregar un hábito correctamente al usuario."""
    response = logged_client.post("/explore/add_habit/health_1", follow_redirects=True)
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Hábito" in html or "agregado exitosamente" in html

    # Verificar en BD
    habits = Habit.list_by_owner("test@example.com")
    assert any("Beber 8 vasos de agua" in h["name"] for h in habits)


def test_add_habit_not_found_in_catalog(logged_client):
    """Si el hábito no existe en el catálogo, debe mostrar flash 'no encontrado'."""
    response = logged_client.post("/explore/add_habit/no_existe", follow_redirects=True)
    html = response.get_data(as_text=True)
    assert "Hábito no encontrado" in html


# ---------------------------
# TEST: REMOVE HABIT ("/explore/remove_habit/<id>")
# ---------------------------


def test_remove_habit_success(logged_client):
    """Debe eliminar un hábito del usuario correctamente."""
    # Crear uno manualmente
    habit_id = Habit.create("test@example.com", "Test habit", "desc", 1)

    response = logged_client.post(f"/explore/remove_habit/{habit_id}", follow_redirects=True)
    html = response.get_data(as_text=True)

    assert "Hábito eliminado exitosamente" in html
    # Verificar que ya no exista
    habits = Habit.list_by_owner("test@example.com")
    assert all(h["id"] != habit_id for h in habits)


#core
def test_is_logged_in_with_user(monkeypatch):
    """Debe retornar True cuando el usuario está en la sesión."""
    monkeypatch.setattr("habitgain.core.session", {"user": "test@example.com"})
    assert _is_logged_in() is True


def test_is_logged_in_without_user(monkeypatch):
    """Debe retornar False cuando no hay usuario en la sesión."""
    monkeypatch.setattr("habitgain.core.session", {})
    assert _is_logged_in() is False

#habits

def test_get_categorias_returns_list():
    """Debe retornar una lista de categorías disponibles."""
    categorias = _get_categorias()
    assert isinstance(categorias, list)


def test_get_categorias_not_empty():
    """Debe contener al menos una categoría."""
    categorias = _get_categorias()
    assert len(categorias) > 0


def test_edit_profile_without_login(monkeypatch):
    """Debe lanzar excepción si se intenta editar sin autenticación."""
    monkeypatch.setattr("habitgain.profile._require_login", lambda: False)
    with pytest.raises(Exception):
        edit("Nuevo nombre")






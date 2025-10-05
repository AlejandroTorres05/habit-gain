import sqlite3
from typing import Optional, Dict, Any, List
import os
import secrets
import hashlib
import hmac

DB_NAME = os.environ.get("HABITGAIN_DB", "habitgain.db")


class Database:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    # ---------------------------
    # Init + migraciones seguras
    # ---------------------------
    def init_db(self) -> None:
        conn = self.get_connection()
        cur = conn.cursor()

        # USERS (creación mínima; luego migramos columnas que falten)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT
            )
            """
        )

        # CATEGORIES
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                icon TEXT
            )
            """
        )

        # HABITS (creación mínima; luego migramos columnas que falten)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
            """
        )
        conn.commit()

        # ---- Migraciones users ----
        # por si alguna DB vieja no tiene
        self._ensure_column(conn, "users", "name", "TEXT")
        self._ensure_column(conn, "users", "password_hash", "TEXT")
        self._ensure_column(conn, "users", "password_salt", "TEXT")
        self._maybe_create_index(conn, "users", "idx_users_email", "email")
        # intenta migrar desde columnas viejas
        self._migrate_users_passwords(conn)
        self._backfill_missing_user_hashes(conn)   # y completa donde falte

        # ---- Migraciones habits ----
        self._ensure_column(conn, "habits", "owner_email", "TEXT")
        self._ensure_column(conn, "habits", "active",
                            "INTEGER NOT NULL DEFAULT 1")
        self._ensure_column(conn, "habits", "short_desc", "TEXT")
        self._ensure_column(conn, "habits", "category_id", "INTEGER")
        self._migrate_owner_email(conn)
        self._maybe_create_index(
            conn, "habits", "idx_habits_owner_email", "owner_email")
        self._maybe_create_index(conn, "habits", "idx_habits_active", "active")

        conn.commit()
        conn.close()

    # ---------- helpers de migración ----------
    def _get_table_columns(self, conn: sqlite3.Connection, table: str) -> List[str]:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        return [row["name"] for row in cur.fetchall()]

    def _has_column(self, conn: sqlite3.Connection, table: str, column: str) -> bool:
        return column in self._get_table_columns(conn, table)

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, decl: str) -> None:
        if not self._has_column(conn, table, column):
            cur = conn.cursor()
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
            conn.commit()

    def _index_exists(self, conn: sqlite3.Connection, table: str, index_name: str) -> bool:
        cur = conn.cursor()
        cur.execute(f"PRAGMA index_list({table})")
        rows = cur.fetchall()
        return any(r["name"] == index_name for r in rows)

    def _maybe_create_index(self, conn: sqlite3.Connection, table: str, idx_name: str, col: str) -> None:
        if not self._has_column(conn, table, col):
            return
        if not self._index_exists(conn, table, idx_name):
            cur = conn.cursor()
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({col})")
            conn.commit()

    def _migrate_users_passwords(self, conn: sqlite3.Connection) -> None:
        """
        Si existen columnas legacy en users, migra a password_hash/password_salt.
        Legacy posibles: password (plaintext), passwd (plaintext), pwd_hash (ya hash sin sal).
        """
        cols = self._get_table_columns(conn, "users")
        legacy_cols = [c for c in ["password",
                                   "passwd", "pwd_hash"] if c in cols]
        if not legacy_cols:
            return
        cur = conn.cursor()

        # Prefiere 'pwd_hash' si existe; luego 'password'/'passwd'
        source = "pwd_hash" if "pwd_hash" in legacy_cols else (
            "password" if "password" in legacy_cols else "passwd")

        # Para cada usuario sin hash, leer el valor legacy y convertirlo a PBKDF2+salt.
        cur.execute(
            f"SELECT id, {source} FROM users WHERE (password_hash IS NULL OR password_hash = '')")
        rows = cur.fetchall()
        for r in rows:
            uid = r["id"]
            legacy_val = r[source] or ""
            if not legacy_val:
                # si está vacío, se completará en _backfill_missing_user_hashes
                continue
            # Si la fuente era 'pwd_hash' sin sal, no podemos reusar tal cual; lo rehash con sal.
            pack = _hash_password(legacy_val)
            cur.execute(
                "UPDATE users SET password_hash=?, password_salt=? WHERE id=?",
                (pack["hash"], pack["salt"], uid),
            )
        conn.commit()

    def _backfill_missing_user_hashes(self, conn: sqlite3.Connection) -> None:
        """
        A cualquier fila que siga sin password_hash/password_salt le asigna un hash de 'changeme'.
        Mejor tener algo seguro que un null que rompa todo.
        """
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM users
            WHERE (password_hash IS NULL OR password_hash = '')
               OR (password_salt IS NULL OR password_salt = '')
        """)
        rows = cur.fetchall()
        if not rows:
            return
        for r in rows:
            uid = r["id"]
            pack = _hash_password("changeme")
            cur.execute(
                "UPDATE users SET password_hash=?, password_salt=? WHERE id=?",
                (pack["hash"], pack["salt"], uid),
            )
        conn.commit()

    def _migrate_owner_email(self, conn: sqlite3.Connection) -> None:
        """Rellena habits.owner_email desde posibles columnas antiguas."""
        if not self._has_column(conn, "habits", "owner_email"):
            return
        cols = self._get_table_columns(conn, "habits")
        legacy_candidates = [c for c in ["user_email",
                                         "owner", "email", "user"] if c in cols]
        if not legacy_candidates:
            return
        legacy_col = legacy_candidates[0]
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE habits
               SET owner_email = {legacy_col}
             WHERE (owner_email IS NULL OR owner_email = '')
               AND {legacy_col} IS NOT NULL
               AND {legacy_col} <> ''
        """)
        conn.commit()

    def seed_data(self) -> None:
        """Seed mínimo para categorías."""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM categories")
        count = cur.fetchone()["c"]
        if count == 0:
            cur.executemany(
                "INSERT INTO categories (name, icon) VALUES (?, ?)",
                [
                    ("Health", "heart-pulse"),
                    ("Productivity", "rocket"),
                    ("Learning", "book-open"),
                ],
            )
            conn.commit()
        conn.close()


# -----------------------
# Password hashing helpers (PBKDF2+salt)
# -----------------------

_PBKDF_ITER = 200_000
_ALGO = "sha256"


def _hash_password(password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
    if salt is None:
        salt = secrets.token_bytes(16)
    pwd = password.encode("utf-8")
    dk = hashlib.pbkdf2_hmac(_ALGO, pwd, salt, _PBKDF_ITER)
    return {
        "salt": salt.hex(),
        "hash": dk.hex(),
        "algo": _ALGO,
        "iter": str(_PBKDF_ITER),
    }


def _verify_password(password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    pwd = password.encode("utf-8")
    dk = hashlib.pbkdf2_hmac(_ALGO, pwd, salt, _PBKDF_ITER)
    return hmac.compare_digest(dk.hex(), expected_hash_hex)


# -----------------------
# User: helper CRUD
# -----------------------

class User:
    @staticmethod
    def ensure_exists(email: str, name: str, provisional_password: str = "changeme") -> None:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        if row is None:
            pack = _hash_password(provisional_password)
            cur.execute(
                "INSERT INTO users (email, name, password_hash, password_salt) VALUES (?, ?, ?, ?)",
                (email, name, pack["hash"], pack["salt"]),
            )
            conn.commit()
        conn.close()

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, name, password_hash, password_salt FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_name(email: str, new_name: str) -> None:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET name=? WHERE email=?", (new_name, email))
        conn.commit()
        conn.close()

    @staticmethod
    def update_password(email: str, new_password: str) -> None:
        pack = _hash_password(new_password)
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password_hash=?, password_salt=? WHERE email=?",
            (pack["hash"], pack["salt"], email),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def check_password(email: str, password: str) -> bool:
        user = User.get_by_email(email)
        if not user:
            return False
        return _verify_password(password, user["password_salt"], user["password_hash"])


# -----------------------
# Category: helper CRUD
# -----------------------

class Category:
    @staticmethod
    def all() -> List[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, icon FROM categories ORDER BY name ASC")
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(category_id: int) -> Optional[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, icon FROM categories WHERE id=?", (category_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create(name: str, icon: Optional[str] = None) -> int:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO categories (name, icon) VALUES (?, ?)", (name, icon))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return int(new_id)

    @staticmethod
    def delete(category_id: int) -> None:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM categories WHERE id=?", (category_id,))
        conn.commit()
        conn.close()


# -----------------------
# Habit: helper CRUD
# -----------------------

class Habit:
    @staticmethod
    def list_by_owner(email: str) -> List[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, owner_email, name, active, short_desc, category_id
            FROM habits
            WHERE owner_email=?
            ORDER BY id DESC
            """,
            (email,),
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def list_active_by_owner(email: str) -> List[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, owner_email, name, active, short_desc, category_id
            FROM habits
            WHERE owner_email=? AND active=1
            ORDER BY id DESC
            """,
            (email,),
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def count_active(email: str) -> int:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS c FROM habits WHERE owner_email=? AND active=1", (email,))
        (c,) = cur.fetchone()
        conn.close()
        return int(c or 0)

    @staticmethod
    def create(email: str, name: str, short_desc: Optional[str] = None, category_id: Optional[int] = None) -> int:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO habits (owner_email, name, active, short_desc, category_id) VALUES (?, ?, 1, ?, ?)",
            (email, name, short_desc, category_id),
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return int(new_id)

    @staticmethod
    def set_active(habit_id: int, active: bool) -> None:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE habits SET active=? WHERE id=?",
                    (1 if active else 0, habit_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(habit_id: int) -> None:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM habits WHERE id=?", (habit_id,))
        conn.commit()
        conn.close()


# -----------------------
# Helper para perfil
# -----------------------

def count_active_habits_from_db(email: str) -> int:
    return Habit.count_active(email)

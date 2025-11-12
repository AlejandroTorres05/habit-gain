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
        conn = sqlite3.connect(self.db_name, timeout=20.0,
                               check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Mejor concurrencia en SQLite
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=20000")
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
        self._ensure_column(conn, "users", "name", "TEXT")
        self._ensure_column(conn, "users", "password_hash", "TEXT")
        self._ensure_column(conn, "users", "password_salt", "TEXT")
        self._maybe_create_index(conn, "users", "idx_users_email", "email")
        self._migrate_users_passwords(conn)
        self._backfill_missing_user_hashes(conn)

        # ---- Migraciones habits ----
        self._ensure_column(conn, "habits", "owner_email", "TEXT")
        self._ensure_column(conn, "habits", "active",
                            "INTEGER NOT NULL DEFAULT 1")
        self._ensure_column(conn, "habits", "short_desc", "TEXT")
        self._ensure_column(conn, "habits", "category_id", "INTEGER")
        # columnas usadas por Habit.create y catálogo sugerido
        self._ensure_column(conn, "habits", "frequency", "TEXT")
        self._ensure_column(conn, "habits", "frequency_detail", "TEXT")
        self._ensure_column(conn, "habits", "long_desc", "TEXT")
        self._ensure_column(conn, "habits", "why_works", "TEXT")
        self._ensure_column(conn, "habits", "icon", "TEXT")
        self._ensure_column(conn, "habits", "habit_base_id", "INTEGER")

        self._migrate_owner_email(conn)
        self._maybe_create_index(
            conn, "habits", "idx_habits_owner_email", "owner_email")
        self._maybe_create_index(conn, "habits", "idx_habits_active", "active")
        # Para validación de duplicados eficiente
        self._maybe_create_index(
            conn, "habits", "idx_habits_owner_name", "owner_email, name")

        # ---- Tabla de completados (habit_completions) ----
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS habit_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                owner_email TEXT NOT NULL,
                date TEXT NOT NULL,
                UNIQUE (habit_id, date),
                FOREIGN KEY (habit_id) REFERENCES habits(id)
            )
            """
        )
        self._maybe_create_index(conn, "habit_completions", "idx_hc_owner_date", "owner_email")

        # ---- Tabla de progreso diario (max planificado por día) ----
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_email TEXT NOT NULL,
                date TEXT NOT NULL,
                planned_total_max INTEGER NOT NULL,
                UNIQUE(owner_email, date)
            )
            """
        )

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
        """
        Crea el índice si no existe. Soporta compuestos con "col1, col2".
        """
        cols = [c.strip() for c in col.split(",")]
        for c in cols:
            if not self._has_column(conn, table, c):
                return
        if not self._index_exists(conn, table, idx_name):
            cur = conn.cursor()
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({col})")
            conn.commit()

    def _migrate_users_passwords(self, conn: sqlite3.Connection) -> None:
        """
        Si existen columnas legacy en users, migra a password_hash/password_salt.
        Legacy posibles: password (plaintext), passwd (plaintext), pwd_hash (hash sin sal).
        """
        cols = self._get_table_columns(conn, "users")
        legacy_cols = [c for c in ["password",
                                   "passwd", "pwd_hash"] if c in cols]
        if not legacy_cols:
            return
        cur = conn.cursor()

        source = "pwd_hash" if "pwd_hash" in legacy_cols else (
            "password" if "password" in legacy_cols else "passwd")

        cur.execute(
            f"SELECT id, {source} FROM users WHERE (password_hash IS NULL OR password_hash = '')"
        )
        rows = cur.fetchall()
        for r in rows:
            uid = r["id"]
            legacy_val = r[source] or ""
            if not legacy_val:
                continue
            pack = _hash_password(legacy_val)
            cur.execute(
                "UPDATE users SET password_hash=?, password_salt=? WHERE id=?",
                (pack["hash"], pack["salt"], uid),
            )
        conn.commit()

    def _backfill_missing_user_hashes(self, conn: sqlite3.Connection) -> None:
        """
        A cualquier fila que siga sin password_hash/password_salt le asigna un hash de 'changeme'.
        """
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id FROM users
            WHERE (password_hash IS NULL OR password_hash = '')
               OR (password_salt IS NULL OR password_salt = '')
            """
        )
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
        cur.execute(
            f"""
            UPDATE habits
               SET owner_email = {legacy_col}
             WHERE (owner_email IS NULL OR owner_email = '')
               AND {legacy_col} IS NOT NULL
               AND {legacy_col} <> ''
            """
        )
        conn.commit()

    def seed_data(self) -> None:
        """
        Seed mínimo para:
        - categorías base
        - usuario demo
        - algunos hábitos demo para ese usuario
        """
        conn = self.get_connection()
        cur = conn.cursor()

        # 1) Categorías base
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

        # Detectar columnas actuales de users (por compatibilidad con schema viejo)
        cols_users = self._get_table_columns(conn, "users")

        # 2) Usuario demo
        demo_email = "demo@habitgain.local"
        cur.execute("SELECT id FROM users WHERE email = ?", (demo_email,))
        row = cur.fetchone()
        if row is None:
            pack = _hash_password("demo123")
            if "password" in cols_users:
                # Schema legacy con columna password NOT NULL
                cur.execute(
                    """
                    INSERT INTO users (email, name, password, password_hash, password_salt)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (demo_email, "Usuario Demo", "changeme",
                     pack["hash"], pack["salt"]),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO users (email, name, password_hash, password_salt)
                    VALUES (?, ?, ?, ?)
                    """,
                    (demo_email, "Usuario Demo", pack["hash"], pack["salt"]),
                )

        # 3) Hábitos demo para ese usuario (si no tiene ninguno)
        cur.execute(
            "SELECT COUNT(*) AS c FROM habits WHERE owner_email = ?",
            (demo_email,),
        )
        hcount = cur.fetchone()["c"]

        if hcount == 0:
            # buscar ids de categorías para asignar
            cur.execute("SELECT id, name FROM categories")
            cats = {row["name"]: row["id"] for row in cur.fetchall()}

            habits_seed = [
                ("Beber 8 vasos de agua",
                 "Mantente hidratado durante el día",
                 cats.get("Health")),
                ("Planificar el día",
                 "Define tus 3 prioridades principales",
                 cats.get("Productivity")),
                ("Leer 20 páginas",
                 "Progreso constante en tus lecturas",
                 cats.get("Learning")),
            ]

            for name, short_desc, cat_id in habits_seed:
                cur.execute(
                    """
                    INSERT INTO habits
                    (owner_email, name, active, short_desc, category_id,
                     frequency, long_desc, why_works, icon)
                    VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        demo_email,
                        name,
                        short_desc,
                        cat_id or 1,
                        "daily",
                        "",
                        "",
                        "🎯",
                    ),
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
            # Mirar columnas actuales para soportar schema legacy
            cols_users = db._get_table_columns(conn, "users")
            if "password" in cols_users:
                cur.execute(
                    """
                    INSERT INTO users (email, name, password, password_hash, password_salt)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (email, name, "changeme", pack["hash"], pack["salt"]),
                )
            else:
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
            SELECT id, owner_email, name, active, short_desc, category_id, frequency, habit_base_id
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
            SELECT id, owner_email, name, active, short_desc, category_id, frequency, habit_base_id
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
    def get_by_id(habit_id: int) -> Optional[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, owner_email, name, active, short_desc, category_id, frequency, habit_base_id
            FROM habits
            WHERE id=?
            """,
            (habit_id,),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def count_active(email: str) -> int:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS c FROM habits WHERE owner_email=? AND active=1", (email,))
        row = cur.fetchone()
        conn.close()
        return int(row["c"] if row else 0)

    @staticmethod
    def exists_by_name(email: str, name: str) -> bool:
        """True si ya existe un hábito con ese nombre para ese usuario (case/espacios-insensible)."""
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1
                  FROM habits
                 WHERE owner_email = ?
                   AND lower(trim(name)) = lower(trim(?))
                 LIMIT 1
                """,
                (email, name),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()

    @staticmethod
    def create(email: str, name: str, short_desc: Optional[str] = None, category_id: Optional[int] = None, *, frequency: str = "daily", habit_base_id: Optional[int] = None, icon: Optional[str] = None, frequency_detail: Optional[str] = None) -> int:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO habits
                (owner_email, name, active, short_desc, category_id, frequency, frequency_detail, long_desc, why_works, icon, habit_base_id)
                VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (email, name, short_desc or "", category_id or 1, frequency or "daily", frequency_detail or "", "", "", icon or "🎯", habit_base_id),
            )
            conn.commit()
            new_id = cur.lastrowid
            return int(new_id)
        finally:
            conn.close()

    @staticmethod
    def set_active(habit_id: int, active: bool) -> None:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE habits SET active=? WHERE id=?",
                        (1 if active else 0, habit_id))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def delete(habit_id: int) -> None:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM habits WHERE id=?", (habit_id,))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update(owner_email: str, habit_id: int, *, name: str, short_desc: str, frequency: str, category_id: int, habit_base_id: Optional[int] = None) -> int:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE habits
                   SET name=?, short_desc=?, frequency=?, category_id=?, habit_base_id=?
                 WHERE id=? AND owner_email=?
                """,
                (name, short_desc, frequency, category_id, habit_base_id, habit_id, owner_email),
            )
            conn.commit()
            return int(cur.rowcount or 0)
        finally:
            conn.close()

    @staticmethod
    def list_active_by_owner_and_category(email: str, category_id: int) -> List[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, owner_email, name, active, short_desc, category_id
            FROM habits
            WHERE owner_email=? AND active=1 AND (category_id = ?)
            ORDER BY id DESC
            """,
            (email, category_id),
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]


# -----------------------
# Daily progress tracking (planned total max per day)
# -----------------------

class DailyProgress:
    @staticmethod
    def ensure_and_get_planned_max(owner_email: str, date_str: str, current_active_total: int) -> int:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT planned_total_max FROM daily_progress WHERE owner_email=? AND date=?",
                (owner_email, date_str),
            )
            row = cur.fetchone()
            if row is None:
                planned = max(0, int(current_active_total))
                cur.execute(
                    "INSERT INTO daily_progress (owner_email, date, planned_total_max) VALUES (?, ?, ?)",
                    (owner_email, date_str, planned),
                )
                conn.commit()
                return planned
            planned = int(row[0])
            if current_active_total > planned:
                planned = int(current_active_total)
                cur.execute(
                    "UPDATE daily_progress SET planned_total_max=? WHERE owner_email=? AND date=?",
                    (planned, owner_email, date_str),
                )
                conn.commit()
            return planned
        finally:
            conn.close()

    # (CRUD de hábitos se encuentra en la clase Habit)


# -----------------------
# Helper para perfil
# -----------------------

def count_active_habits_from_db(email: str) -> int:
    return Habit.count_active(email)


# -----------------------
# Habit completion tracking
# -----------------------

class Completion:
    @staticmethod
    def mark_completed(habit_id: int, owner_email: str, date_str: Optional[str] = None) -> None:
        import datetime as _dt
        db = Database()
        conn = db.get_connection()
        try:
            if not date_str:
                date_str = _dt.date.today().isoformat()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR IGNORE INTO habit_completions (habit_id, owner_email, date)
                VALUES (?, ?, ?)
                """,
                (habit_id, owner_email, date_str),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def completed_today_ids(owner_email: str) -> List[int]:
        import datetime as _dt
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        today = _dt.date.today().isoformat()
        cur.execute(
            """
            SELECT habit_id FROM habit_completions
            WHERE owner_email=? AND date=?
            """,
            (owner_email, today),
        )
        rows = cur.fetchall()
        conn.close()
        return [int(r[0]) for r in rows]

    @staticmethod
    def count_completed_in_range(owner_email: str, start_date: str, end_date: str) -> int:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) AS c FROM habit_completions
            WHERE owner_email=? AND date BETWEEN ? AND ?
            """,
            (owner_email, start_date, end_date),
        )
        (c,) = cur.fetchone()
        conn.close()
        return int(c or 0)

    @staticmethod
    def count_days_with_completion(owner_email: str, start_date: str, end_date: str) -> int:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(DISTINCT date) AS c FROM habit_completions
            WHERE owner_email=? AND date BETWEEN ? AND ?
            """,
            (owner_email, start_date, end_date),
        )
        (c,) = cur.fetchone()
        conn.close()
        return int(c or 0)

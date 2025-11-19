import sqlite3
from typing import Optional, Dict, Any, List
import os
import secrets
import hashlib
import hmac

DB_NAME = os.environ.get("HABITGAIN_DB", "habitgain.db")


class Database:
    _wal_enabled = False  # Flag para configurar WAL solo una vez

    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self._ensure_wal_mode()

    def _ensure_wal_mode(self):
        """Configura WAL mode una sola vez para toda la aplicación"""
        if not Database._wal_enabled:
            try:
                conn = sqlite3.connect(self.db_name, timeout=30.0)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.close()
                Database._wal_enabled = True
            except Exception:
                pass  # Si falla, continuamos sin WAL

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_name, timeout=30.0,
                               check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Configuraciones por conexión (no requieren locks)
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA cache_size=10000")
        return conn

    @property
    def db_path(self) -> str:
        """Alias para compatibilidad"""
        return self.db_name

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
        self._ensure_column(conn, "users", "role", "TEXT DEFAULT 'user'")
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

        # ---- Tabla de onboarding_status (HU-18: Onboarding interactivo) ----
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS onboarding_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL UNIQUE,
                completed INTEGER NOT NULL DEFAULT 0,
                current_step INTEGER NOT NULL DEFAULT 0,
                skipped INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT,
                steps_completed TEXT DEFAULT '',
                FOREIGN KEY (user_email) REFERENCES users(email)
            )
            """
        )
        self._maybe_create_index(conn, "onboarding_status", "idx_onboarding_email", "user_email")

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
        # 1) Categorías base - transacción separada y rápida
        conn = self.get_connection()
        try:
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
        finally:
            conn.close()

        # 2) Usuario demo - transacción separada
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cols_users = self._get_table_columns(conn, "users")
            demo_email = "demo@habitgain.local"

            cur.execute("SELECT id FROM users WHERE email = ?", (demo_email,))
            row = cur.fetchone()
            if row is None:
                pack = _hash_password("demo123")
                if "password" in cols_users:
                    cur.execute(
                        """
                        INSERT INTO users (email, name, password, password_hash, password_salt, role)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (demo_email, "Usuario Demo", "changeme",
                         pack["hash"], pack["salt"], "user"),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO users (email, name, password_hash, password_salt, role)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (demo_email, "Usuario Demo", pack["hash"], pack["salt"], "user"),
                    )
                conn.commit()
        finally:
            conn.close()

        # 3) Hábitos demo - transacción separada
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            demo_email = "demo@habitgain.local"

            cur.execute(
                "SELECT COUNT(*) AS c FROM habits WHERE owner_email = ?",
                (demo_email,),
            )
            hcount = cur.fetchone()["c"]

            if hcount == 0:
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
        finally:
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
        try:
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
                        INSERT INTO users (email, name, password, password_hash, password_salt, role)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (email, name, "changeme", pack["hash"], pack["salt"], "user"),
                    )
                else:
                    cur.execute(
                        "INSERT INTO users (email, name, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
                        (email, name, pack["hash"], pack["salt"], "user"),
                    )
                conn.commit()
        finally:
            conn.close()


    @staticmethod
    def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, email, name, password_hash, password_salt, role FROM users WHERE email=?", (email,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, email, name, role FROM users WHERE id=?", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def list_all() -> List[Dict[str, Any]]:
        """HU-16: Listar todos los usuarios para panel admin"""
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, email, name, role FROM users ORDER BY id DESC")
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def create_user(email: str, name: str, password: str, role: str = "user") -> int:
        """HU-16: Crear usuario desde panel admin"""
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            pack = _hash_password(password)
            cols_users = db._get_table_columns(conn, "users")

            if "password" in cols_users:
                cur.execute(
                    "INSERT INTO users (email, name, password, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?, ?)",
                    (email, name, "changeme", pack["hash"], pack["salt"], role),
                )
            else:
                cur.execute(
                    "INSERT INTO users (email, name, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
                    (email, name, pack["hash"], pack["salt"], role),
                )
            conn.commit()
            new_id = cur.lastrowid
            return int(new_id)
        finally:
            conn.close()

    @staticmethod
    def update_user(user_id: int, email: str, name: str, role: str) -> None:
        """HU-16: Actualizar usuario desde panel admin"""
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET email=?, name=?, role=? WHERE id=?",
                (email, name, role, user_id),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def delete_user(user_id: int) -> None:
        """HU-16: Eliminar usuario desde panel admin"""
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update_name(email: str, new_name: str) -> None:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE users SET name=? WHERE email=?", (new_name, email))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update_password(email: str, new_password: str) -> None:
        pack = _hash_password(new_password)
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET password_hash=?, password_salt=? WHERE email=?",
                (pack["hash"], pack["salt"], email),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def check_password(email: str, password: str) -> bool:
        user = User.get_by_email(email)
        if not user:
            return False
        return _verify_password(password, user["password_salt"], user["password_hash"])

    @staticmethod
    def verify_password(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verifica credenciales y retorna el usuario si son correctas, None si no"""
        user = User.get_by_email(email)
        if not user:
            return None
        if _verify_password(password, user["password_salt"], user["password_hash"]):
            return user
        return None


# -----------------------
# Category: helper CRUD
# -----------------------

class Category:
    @staticmethod
    def all() -> List[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, icon FROM categories ORDER BY name ASC")
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


    @staticmethod
    def get_by_id(category_id: int) -> Optional[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, icon FROM categories WHERE id=?", (category_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def create(name: str, icon: Optional[str] = None) -> int:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO categories (name, icon) VALUES (?, ?)", (name, icon))
            conn.commit()
            new_id = cur.lastrowid
            return int(new_id)
        finally:
            conn.close()

    @staticmethod
    def delete(category_id: int) -> None:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM categories WHERE id=?", (category_id,))
            conn.commit()
        finally:
            conn.close()


# -----------------------
# Habit: helper CRUD
# -----------------------

class Habit:
    @staticmethod
    def list_by_owner(email: str) -> List[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        try:
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
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def list_active_by_owner(email: str) -> List[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        try:
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
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_by_id(habit_id: int) -> Optional[Dict[str, Any]]:
        db = Database()
        conn = db.get_connection()
        try:
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
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def count_active(email: str) -> int:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) AS c FROM habits WHERE owner_email=? AND active=1", (email,))
            row = cur.fetchone()
            return int(row["c"] if row else 0)
        finally:
            conn.close()

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
            # Forzar un checkpoint ligero para liberar el WAL y evitar locks
            try:
                conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            except Exception:
                pass  # No es crítico si falla
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
        try:
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
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def list_all_habits() -> List[Dict[str, Any]]:
        """HU-16: Listar todos los hábitos para panel admin"""
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, owner_email, name, active, short_desc, category_id, frequency, habit_base_id
                FROM habits
                ORDER BY id DESC
                """
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def admin_update_habit(habit_id: int, name: str, short_desc: str, owner_email: str, active: bool) -> int:
        """HU-16: Actualizar hábito desde panel admin"""
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE habits
                SET name=?, short_desc=?, owner_email=?, active=?
                WHERE id=?
                """,
                (name, short_desc, owner_email, 1 if active else 0, habit_id),
            )
            conn.commit()
            return int(cur.rowcount or 0)
        finally:
            conn.close()

    @staticmethod
    def admin_delete_habit(habit_id: int) -> None:
        """HU-16: Eliminar hábito desde panel admin"""
        Habit.delete(habit_id)


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
        try:
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
            return [int(r[0]) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def count_completed_in_range(owner_email: str, start_date: str, end_date: str) -> int:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*) AS c FROM habit_completions
                WHERE owner_email=? AND date BETWEEN ? AND ?
                """,
                (owner_email, start_date, end_date),
            )
            (c,) = cur.fetchone()
            return int(c or 0)
        finally:
            conn.close()

    @staticmethod
    def count_days_with_completion(owner_email: str, start_date: str, end_date: str) -> int:
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(DISTINCT date) AS c FROM habit_completions
                WHERE owner_email=? AND date BETWEEN ? AND ?
                """,
                (owner_email, start_date, end_date),
            )
            (c,) = cur.fetchone()
            return int(c or 0)
        finally:
            conn.close()

    @staticmethod
    def get_completion_dates_in_range(owner_email: str, start_date: str, end_date: str) -> List[str]:
        """Retorna todas las fechas (YYYY-MM-DD) con al menos un hábito completado en el rango.

        Útil para vistas de calendario/heatmap.
        """
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT DISTINCT date
                FROM habit_completions
                WHERE owner_email=? AND date BETWEEN ? AND ?
                ORDER BY date ASC
                """,
                (owner_email, start_date, end_date),
            )
            rows = cur.fetchall()
            return [r["date"] for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_current_streak(habit_id: int, owner_email: str) -> int:
        """Calcula la racha actual de cumplimiento de un hábito.

        Cuenta días consecutivos desde hoy hacia atrás utilizando las fechas de
        la tabla habit_completions.
        """
        import datetime as _dt
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()

            # Obtener todas las fechas de completado para este hábito, ordenadas descendentemente
            cur.execute(
                """
                SELECT date FROM habit_completions
                WHERE habit_id=? AND owner_email=?
                ORDER BY date DESC
                """,
                (habit_id, owner_email),
            )
            rows = cur.fetchall()

            if not rows:
                return 0

            # Convertir a objetos date
            completion_dates = [_dt.date.fromisoformat(r[0]) for r in rows]
            today = _dt.date.today()

            streak = 0
            expected_date = today

            for completion_date in completion_dates:
                if completion_date == expected_date:
                    streak += 1
                    expected_date -= _dt.timedelta(days=1)
                elif completion_date < expected_date:
                    # Hubo un salto, la racha se rompe
                    break

            return streak
        finally:
            conn.close()

    @staticmethod
    def get_best_streak(habit_id: int, owner_email: str) -> int:
        """Calcula la mejor racha histórica (máximo de días consecutivos) de un hábito.

        A diferencia de get_current_streak, aquí buscamos la racha más larga en
        todas las fechas registradas para ese hábito.
        """
        import datetime as _dt
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT date FROM habit_completions
                WHERE habit_id=? AND owner_email=?
                ORDER BY date ASC
                """,
                (habit_id, owner_email),
            )
            rows = cur.fetchall()
            if not rows:
                return 0

            dates = [_dt.date.fromisoformat(r[0]) for r in rows]
            best = 1
            current = 1
            for prev, curr in zip(dates, dates[1:]):
                if (curr - prev).days == 1:
                    current += 1
                    if current > best:
                        best = current
                else:
                    current = 1
            return best
        finally:
            conn.close()

    @staticmethod
    def calculate_strength(habit_id: int, owner_email: str) -> Dict[str, Any]:
        """
        Calcula la fortaleza de un hábito basado en la racha de cumplimiento.

        Retorna:
            - streak: racha actual (días consecutivos)
            - strength: nivel de fortaleza (0-100)
            - level: nivel descriptivo (débil, en desarrollo, fuerte, inquebrantable)
            - color: color para representación visual
        """
        streak = Completion.get_current_streak(habit_id, owner_email)

        # Calcular fortaleza en escala 0-100
        # Fórmula: fortaleza crece logarítmicamente con la racha
        # 0 días = 0%, 7 días = 50%, 21 días = 75%, 66 días = 90%, 100+ días = 100%
        if streak == 0:
            strength = 0
        elif streak <= 7:
            strength = int((streak / 7) * 50)
        elif streak <= 21:
            strength = 50 + int(((streak - 7) / 14) * 25)
        elif streak <= 66:
            strength = 75 + int(((streak - 21) / 45) * 15)
        else:
            strength = min(100, 90 + int(((streak - 66) / 34) * 10))

        # Determinar nivel y color
        if strength < 25:
            level = "Débil"
            color = "danger"  # rojo
        elif strength < 50:
            level = "En desarrollo"
            color = "warning"  # amarillo
        elif strength < 75:
            level = "Fuerte"
            color = "info"  # azul
        else:
            level = "Inquebrantable"
            color = "success"  # verde

        return {
            "streak": streak,
            "strength": strength,
            "level": level,
            "color": color
        }


# ===========================
# OnboardingStatus Model
# ===========================
class OnboardingStatus:
    """
    Gestiona el estado del onboarding interactivo para nuevos usuarios.
    Tracking de pasos completados y analytics de uso.
    """

    @staticmethod
    def get_status(user_email: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado del onboarding para un usuario.

        Returns:
            Dict con: completed (bool), current_step (int), skipped (bool),
                     completed_at (str), steps_completed (list)
            None si no hay registro (usuario nuevo)
        """
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT user_email, completed, current_step, skipped,
                       completed_at, steps_completed
                FROM onboarding_status
                WHERE user_email = ?
                """,
                (user_email,)
            )
            row = cur.fetchone()
            if row:
                return {
                    "user_email": row["user_email"],
                    "completed": bool(row["completed"]),
                    "current_step": row["current_step"],
                    "skipped": bool(row["skipped"]),
                    "completed_at": row["completed_at"],
                    "steps_completed": row["steps_completed"].split(",") if row["steps_completed"] else []
                }
            return None
        finally:
            conn.close()

    @staticmethod
    def needs_onboarding(user_email: str) -> bool:
        """
        Verifica si un usuario necesita ver el onboarding.

        Returns:
            True si el usuario NO ha completado o saltado el onboarding
        """
        status = OnboardingStatus.get_status(user_email)
        if status is None:
            return True  # Usuario nuevo, necesita onboarding
        return not status["completed"] and not status["skipped"]

    @staticmethod
    def create_status(user_email: str) -> None:
        """
        Crea un registro inicial de onboarding para un usuario nuevo.
        """
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR IGNORE INTO onboarding_status
                (user_email, completed, current_step, skipped, steps_completed)
                VALUES (?, 0, 0, 0, '')
                """,
                (user_email,)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def mark_step_complete(user_email: str, step_number: int) -> None:
        """
        Marca un paso específico como completado y actualiza el progreso.

        Args:
            user_email: Email del usuario
            step_number: Número del paso completado (0-4)
        """
        db = Database()
        conn = db.get_connection()
        try:
            # Obtener estado actual
            status = OnboardingStatus.get_status(user_email)
            if status is None:
                OnboardingStatus.create_status(user_email)
                status = OnboardingStatus.get_status(user_email)

            # Agregar paso a la lista de completados
            steps_completed = status["steps_completed"]
            step_str = str(step_number)
            if step_str not in steps_completed:
                steps_completed.append(step_str)

            steps_completed_str = ",".join(steps_completed)
            new_current_step = step_number + 1

            # Si completó todos los pasos (0-4 = 5 pasos), marcar como completado
            is_completed = len(steps_completed) >= 5

            cur = conn.cursor()
            if is_completed:
                from datetime import datetime
                completed_at = datetime.now().isoformat()
                cur.execute(
                    """
                    UPDATE onboarding_status
                    SET current_step = ?, steps_completed = ?,
                        completed = 1, completed_at = ?
                    WHERE user_email = ?
                    """,
                    (new_current_step, steps_completed_str, completed_at, user_email)
                )
            else:
                cur.execute(
                    """
                    UPDATE onboarding_status
                    SET current_step = ?, steps_completed = ?
                    WHERE user_email = ?
                    """,
                    (new_current_step, steps_completed_str, user_email)
                )

            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def mark_completed(user_email: str) -> None:
        """
        Marca el onboarding como completado por el usuario.
        """
        import datetime as _dt
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            completed_at = _dt.datetime.now().isoformat()
            cur.execute(
                """
                INSERT OR REPLACE INTO onboarding_status
                (user_email, completed, current_step, skipped, completed_at, steps_completed)
                VALUES (?, 1, 5, 0, ?, '0,1,2,3,4')
                """,
                (user_email, completed_at)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def mark_skipped(user_email: str) -> None:
        """
        Marca el onboarding como saltado por el usuario.
        """
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO onboarding_status
                (user_email, completed, current_step, skipped, steps_completed)
                VALUES (?, 0, 0, 1, '')
                """,
                (user_email,)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def reset_status(user_email: str) -> None:
        """
        Reinicia el estado del onboarding (útil para testing o re-onboarding).
        """
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                DELETE FROM onboarding_status
                WHERE user_email = ?
                """,
                (user_email,)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_analytics() -> Dict[str, Any]:
        """
        Obtiene estadísticas generales del onboarding para analytics.

        Returns:
            Dict con métricas: total_users, completed, skipped, in_progress,
                              completion_rate, skip_rate, avg_steps_completed
        """
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()

            # Total de usuarios en el sistema
            cur.execute("SELECT COUNT(*) as total FROM users")
            total_users = cur.fetchone()["total"]

            # Estadísticas de onboarding
            cur.execute(
                """
                SELECT
                    COUNT(*) as total_onboarding,
                    SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN skipped = 1 THEN 1 ELSE 0 END) as skipped,
                    SUM(CASE WHEN completed = 0 AND skipped = 0 THEN 1 ELSE 0 END) as in_progress,
                    AVG(LENGTH(steps_completed) - LENGTH(REPLACE(steps_completed, ',', '')) +
                        CASE WHEN LENGTH(steps_completed) > 0 THEN 1 ELSE 0 END) as avg_steps
                FROM onboarding_status
                """
            )
            row = cur.fetchone()

            completed = row["completed"] or 0
            skipped = row["skipped"] or 0
            in_progress = row["in_progress"] or 0
            total_onboarding = row["total_onboarding"] or 0
            avg_steps = row["avg_steps"] or 0

            # Tasas de completitud y skip
            completion_rate = (completed / total_onboarding * 100) if total_onboarding > 0 else 0
            skip_rate = (skipped / total_onboarding * 100) if total_onboarding > 0 else 0

            return {
                "total_users": total_users,
                "total_onboarding": total_onboarding,
                "completed": completed,
                "skipped": skipped,
                "in_progress": in_progress,
                "completion_rate": round(completion_rate, 2),
                "skip_rate": round(skip_rate, 2),
                "avg_steps_completed": round(avg_steps, 2)
            }
        finally:
            conn.close()

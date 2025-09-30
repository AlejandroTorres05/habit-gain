import sqlite3
from typing import List, Optional, Dict

DB_NAME = "habitgain.db"


class Database:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                icon TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                frequency TEXT NOT NULL,
                short_desc TEXT NOT NULL,
                long_desc  TEXT NOT NULL,
                why_works  TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                icon TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        conn.commit()
        conn.close()

    def seed_data(self):
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) AS c FROM categories")
        if cur.fetchone()["c"] > 0:
            conn.close()
            return

        categories = [
            ("Wellbeing", "🍃"),
            ("Physical Health", "💪"),
            ("Productivity", "⚡"),
            ("Mindfulness", "🧘")
        ]
        cur.executemany(
            "INSERT INTO categories (name, icon) VALUES (?,?)", categories)

        habits = [
            # Wellbeing (1)
            ("Daily Meditation", "Daily",
             "Reduce stress with a few minutes a day.",
             "Improves focus and emotional stability. Ten minutes can lower cortisol.",
             "Mindfulness builds regulation via neuroplasticity.",
             1, "🧘‍♀️"),
            ("Night Gratitude", "Daily",
             "Write 3 things before bed.",
             "Reprograms your attention to positives, improves sleep, reduces anxiety.",
             "Positive psychology: dopamine/serotonin reward system.",
             1, "📝"),
            ("Breathing Practice", "Daily",
             "5 minutes of deep breathing.",
             "Activates parasympathetic system and lowers stress quickly.",
             "Deep breathing lowers HR and BP, triggers relaxation.",
             1, "🌬️"),

            # Physical Health (2)
            ("10-min Walk", "Daily",
             "Short walk to activate body and mind.",
             "Circulation up, mood better, zero equipment.",
             "Light aerobic exercise releases endorphins.",
             2, "🚶"),
            ("Drink Water (8)", "8 glasses",
             "Stay hydrated through the day.",
             "Hydration boosts focus, energy, digestion and skin.",
             "Water is ~60% of body and key to cell function.",
             2, "💧"),
            ("Morning Stretch", "Morning",
             "Wake up with 5 min stretch.",
             "Improves flexibility and reduces stiffness.",
             "Increases blood flow and oxygenation to muscles.",
             2, "🤸"),

            # Productivity (3)
            ("Pomodoro", "Daily",
             "25-min focus blocks + 5-min breaks.",
             "Helps maintain focus and avoid burnout.",
             "Matches human attention spans; breaks prevent fatigue.",
             3, "⏲️"),
            ("Daily Planning", "Morning",
             "Define your top 3 tasks.",
             "Clarity lowers overwhelm and raises effectiveness.",
             "Prioritizing reduces cognitive load.",
             3, "📋"),
            ("Digital Detox", "Night",
             "No screens 1 hour before bed.",
             "Drastically improves sleep quality.",
             "Blue light suppresses melatonin; removing it restores rhythm.",
             3, "📵"),

            # Mindfulness (4)
            ("Body Scan", "Daily",
             "Scan sensations for 5 minutes.",
             "Connects with body, reduces stress, improves awareness.",
             "Interoception reduces stress response.",
             4, "🧘"),
            ("Mindful Meal", "Daily",
             "One meal without distractions.",
             "Improves digestion and relationship with food.",
             "Enhances hunger/satiety signals.",
             4, "🍽️"),
            ("Thought Watching", "Daily",
             "Observe thoughts without judgment.",
             "Builds distance from rumination and reactivity.",
             "Metacognition reduces anxiety/depression patterns.",
             4, "💭"),
        ]

        cur.executemany("""
            INSERT INTO habits (name, frequency, short_desc, long_desc, why_works, category_id, icon)
            VALUES (?,?,?,?,?,?,?)
        """, habits)

        conn.commit()
        conn.close()


class Category:
    @staticmethod
    def all() -> List[Dict]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM categories ORDER BY name")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get(category_id: int) -> Optional[Dict]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        r = cur.fetchone()
        conn.close()
        return dict(r) if r else None


class Habit:
    @staticmethod
    def all() -> List[Dict]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT h.*, c.name AS category_name, c.icon AS category_icon
            FROM habits h JOIN categories c ON h.category_id = c.id
            ORDER BY h.name
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get(habit_id: int) -> Optional[Dict]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT h.*, c.name AS category_name, c.icon AS category_icon
            FROM habits h JOIN categories c ON h.category_id = c.id
            WHERE h.id = ?
        """, (habit_id,))
        r = cur.fetchone()
        conn.close()
        return dict(r) if r else None

    @staticmethod
    def by_category(category_id: int) -> List[Dict]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT h.*, c.name AS category_name, c.icon AS category_icon
            FROM habits h JOIN categories c ON h.category_id = c.id
            WHERE h.category_id = ?
            ORDER BY h.name
        """, (category_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def search(q: str) -> List[Dict]:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()
        term = f"%{q}%"
        cur.execute("""
            SELECT h.*, c.name AS category_name, c.icon AS category_icon
            FROM habits h JOIN categories c ON h.category_id = c.id
            WHERE h.name LIKE ? OR h.short_desc LIKE ?
            ORDER BY h.name
        """, (term, term))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

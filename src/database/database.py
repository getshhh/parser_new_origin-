# database/database.py
import sqlite3
import json
from typing import Optional, List, Tuple, Dict
from datetime import datetime

class Source:
    def __init__(self, id, link, send_to, send_to_gpt, from_out, white_list, black_list, status, type, use_from_out, is_test, last_check_gpt_at, last_msg_id):
        self.id = id
        self.link = link
        self.send_to = send_to
        self.send_to_gpt = send_to_gpt
        self.from_out = from_out
        self.white_list = white_list
        self.black_list = black_list
        self.status = status
        self.type = type
        self.use_from_out = bool(use_from_out)
        self.is_test = bool(is_test)
        self.last_check_gpt_at = datetime.fromisoformat(last_check_gpt_at) if last_check_gpt_at else None
        self.last_msg_id = last_msg_id

class Database:
    # This class uses sqlite3 directly, not SQLAlchemy.
    # The `sources` table and its related methods were implemented based on a
    # user-provided SQLAlchemy model, adapted to the existing sqlite3 stack.
    def __init__(self, path: str = "projects.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup_db()

    def setup_db(self):
        # --- Kwork ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                price INTEGER,
                url TEXT,
                date_create TEXT,
                username TEXT,
                category_id INTEGER
            )
        """)

        # --- FL ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fl_projects (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                price INTEGER,
                url TEXT,
                date_create TEXT,
                username TEXT,
                category_id INTEGER
            )
        """)

        # --- Guru ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS guru_projects (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                price INTEGER,
                url TEXT,
                date_create TEXT
            )
        """)

        # --- Weblancer ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS weblancer_projects (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                price INTEGER,
                url TEXT,
                date_create TEXT,
                username TEXT
            )
        """)

        # --- Work-Zilla ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS workzilla_vacancies (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                price INTEGER,
                url TEXT,
                date_create TEXT
            )
        """)

        # --- YouDo ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS youdo_tasks (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                address TEXT,
                budget TEXT,
                date TEXT,
                url TEXT,
                date_create TEXT
            )
        """)

        # --- VK ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vk_posts (
                id INTEGER PRIMARY KEY,
                group_id TEXT,
                title TEXT,
                description TEXT,
                price TEXT,
                date_create TEXT
            )
        """)

        # --- Habr Posts ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS habr_posts (
                id INTEGER PRIMARY KEY,
                title TEXT,
                url TEXT,
                date_create TEXT
            )
        """)

        # --- Habr Vacancies ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS habr_vacancies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                company TEXT,
                salary TEXT,
                city TEXT,
                tags TEXT,
                link TEXT,
                date_create TEXT
            )
        """)

        # --- Settings ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS parser_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parser_name TEXT UNIQUE NOT NULL,
                message_interval INTEGER DEFAULT 120
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS parser_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parser_name TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                keywords TEXT,
                minus_words TEXT,
                min_price INTEGER,
                max_price INTEGER,
                UNIQUE(parser_name, channel_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                chat_id INTEGER PRIMARY KEY,
                title TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS gpt_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL DEFAULT "stopped"
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT NOT NULL,
                send_to TEXT NOT NULL,
                send_to_gpt TEXT,
                from_out TEXT NOT NULL,
                white_list TEXT NOT NULL,
                black_list TEXT NOT NULL,
                status INTEGER DEFAULT 0,
                type TEXT,
                use_from_out INTEGER DEFAULT 1,
                is_test INTEGER DEFAULT 0,
                last_check_gpt_at TEXT,
                last_msg_id TEXT
            )
        """)
        # check if there is a record in gpt_settings, if not, create one
        self.cursor.execute("SELECT * FROM gpt_settings")
        if self.cursor.fetchone() is None:
            self.cursor.execute("INSERT INTO gpt_settings (status) VALUES (?)", ("stopped",))
        self.conn.commit()

    # ----------- Parser settings (каналы + интервалы) --------
    def get_parser_settings(self, parser_name: str) -> Optional[Dict]:
        """Получить настройки парсера"""
        row = self.cursor.execute(
            "SELECT message_interval FROM parser_settings WHERE parser_name = ?",
            (parser_name,)
        ).fetchone()
        if row:
            return {"message_interval": row[0]}
        return None

    def set_parser_interval(self, parser_name: str, interval: int):
        """Установить интервал для парсера"""
        self.cursor.execute(
            "INSERT INTO parser_settings(parser_name, message_interval) VALUES (?, ?) "
            "ON CONFLICT(parser_name) DO UPDATE SET message_interval=excluded.message_interval",
            (parser_name, interval)
        )
        self.conn.commit()

    def add_parser_channel(self, parser_name: str, channel_id: int, keywords: str = '', minus_words: str = '', min_price: int = None, max_price: int = None):
        """Добавить канал для парсера"""
        self.cursor.execute(
            "INSERT INTO parser_channels(parser_name, channel_id, keywords, minus_words, min_price, max_price) VALUES (?, ?, ?, ?, ?, ?)",
            (parser_name, channel_id, keywords, minus_words, min_price, max_price)
        )
        self.conn.commit()

    def get_parser_channels(self, parser_name: str) -> List[Dict]:
        """Получить все каналы для парсера"""
        rows = self.cursor.execute(
            "SELECT id, channel_id, keywords, minus_words, min_price, max_price FROM parser_channels WHERE parser_name = ?",
            (parser_name,)
        ).fetchall()
        return [{"id": row[0], "channel_id": row[1], "keywords": row[2], "minus_words": row[3], "min_price": row[4], "max_price": row[5]} for row in rows]

    def get_parser_channel_settings(self, parser_name: str, channel_id: int) -> Optional[Dict]:
        """Получить настройки канала для парсера"""
        row = self.cursor.execute(
            "SELECT id, keywords, minus_words, min_price, max_price FROM parser_channels WHERE parser_name = ? AND channel_id = ?",
            (parser_name, channel_id)
        ).fetchone()
        if row:
            return {"id": row[0], "keywords": row[1], "minus_words": row[2], "min_price": row[3], "max_price": row[4]}
        return None

    def update_parser_channel_price_range(self, id: int, min_price: int, max_price: int):
        """Обновить ценовой диапазон для канала парсера"""
        self.cursor.execute(
            "UPDATE parser_channels SET min_price = ?, max_price = ? WHERE id = ?",
            (min_price, max_price, id)
        )
        self.conn.commit()

    def update_parser_channel_keywords(self, id: int, keywords: str):
        """Обновить ключевые слова для канала парсера"""
        self.cursor.execute(
            "UPDATE parser_channels SET keywords = ? WHERE id = ?",
            (keywords, id)
        )
        self.conn.commit()

    def update_parser_channel_minus_words(self, id: int, minus_words: str):
        """Обновить минус-слова для канала парсера"""
        self.cursor.execute(
            "UPDATE parser_channels SET minus_words = ? WHERE id = ?",
            (minus_words, id)
        )
        self.conn.commit()

    def delete_parser_channel(self, parser_name: str, channel_id: int):
        """Удалить канал для парсера"""
        self.cursor.execute(
            "DELETE FROM parser_channels WHERE parser_name = ? AND channel_id = ?",
            (parser_name, channel_id)
        )
        self.conn.commit()

    def upsert_channel(self, chat_id: int, title: str):
        self.cursor.execute(
            "INSERT INTO channels(chat_id, title) VALUES (?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET title=excluded.title",
            (chat_id, title)
        )
        self.conn.commit()

    def delete_channel_entry(self, chat_id: int):
        self.cursor.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))
        self.conn.commit()

    def list_channels(self) -> List[Tuple[int, str]]:
        return list(self.cursor.execute("SELECT chat_id, title FROM channels ORDER BY title ASC").fetchall())

    # ----------- WEBLANCER -----------
    def save_weblancer_project(self, project: dict) -> None:
        self.cursor.execute(
            "INSERT OR IGNORE INTO weblancer_projects VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                project.get("id"),
                project.get("title"),
                project.get("description"),
                project.get("price"),
                project.get("url"),
                project.get("date_create"),
                project.get("username"),
            ),
        )
        self.conn.commit()

    def get_latest_weblancer_projects(self, limit: int = 5):
        self.cursor.execute(
            "SELECT * FROM weblancer_projects ORDER BY date_create DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_total_weblancer_projects_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM weblancer_projects")
        row = self.cursor.fetchone()
        return row[0] if row else 0

    def get_weblancer_settings(self) -> dict:
        return self.get_settings("weblancer")

    def save_weblancer_settings(self, keywords, min_price, max_price):
        self.save_settings(keywords, min_price, max_price, "weblancer")

    # ----------- Work-Zilla -----------
    def save_workzilla_vacancy(self, vacancy: dict) -> None:
        self.cursor.execute(
            "INSERT OR IGNORE INTO workzilla_vacancies VALUES (?, ?, ?, ?, ?, ?)",
            (
                vacancy.get("id"),
                vacancy.get("title"),
                vacancy.get("description"),
                vacancy.get("price"),
                vacancy.get("url"),
                vacancy.get("date_create"),
            ),
        )
        self.conn.commit()

    def get_latest_workzilla_vacancies(self, limit: int = 5):
        self.cursor.execute(
            "SELECT * FROM workzilla_vacancies ORDER BY date_create DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_total_workzilla_vacancies_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM workzilla_vacancies")
        row = self.cursor.fetchone()
        return row[0] if row else 0

    def get_workzilla_settings(self) -> dict:
        return self.get_settings("workzilla")

    def save_workzilla_settings(self, keywords, min_price, max_price):
        self.save_settings(keywords, min_price, max_price, "workzilla")

    # ----------- KWORK -----------
    def save_project(self, project: dict) -> None:
        self.cursor.execute(
            "INSERT OR IGNORE INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                project.get("id"),
                project.get("title"),
                project.get("description"),
                project.get("price"),
                project.get("url"),
                project.get("date_create"),
                project.get("username"),
                project.get("category_id"),
            ),
        )
        self.conn.commit()

    def get_latest_projects(self, limit: int = 5):
        self.cursor.execute(
            "SELECT * FROM projects ORDER BY date_create DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_total_projects_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM projects")
        row = self.cursor.fetchone()
        return row[0] if row else 0

    # ----------- HABR POSTS ------------
    def save_habr_post(self, post: dict) -> None:
        self.cursor.execute(
            "INSERT OR IGNORE INTO habr_posts VALUES (?, ?, ?, ?)",
            (
                post.get("id"),
                post.get("title"),
                post.get("url"),
                post.get("date_create"),
            ),
        )
        self.conn.commit()

    def get_latest_habr_posts(self, limit: int = 5):
        self.cursor.execute(
            "SELECT * FROM habr_posts ORDER BY date_create DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_total_habr_posts_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM habr_posts")
        row = self.cursor.fetchone()
        return row[0] if row else 0

    # ----------- HABR VACANCIES ------------
    def save_habr_vacancy(self, vacancy: dict) -> None:
        self.cursor.execute(
            "INSERT INTO habr_vacancies (title, company, salary, city, tags, link, date_create) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                vacancy.get("title"),
                vacancy.get("company"),
                vacancy.get("salary"),
                vacancy.get("city"),
                ",".join(vacancy.get("tags", [])),
                vacancy.get("link"),
                vacancy.get("date_create"),
            ),
        )
        self.conn.commit()

    def get_latest_habr_vacancies(self, limit: int = 5):
        self.cursor.execute(
            "SELECT * FROM habr_vacancies ORDER BY date_create DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_total_habr_vacancies_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM habr_vacancies")
        row = self.cursor.fetchone()
        return row[0] if row else 0

    # ----------- FL --------------
    def save_fl_project(self, project: dict) -> None:
        self.cursor.execute(
            "INSERT OR IGNORE INTO fl_projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                project.get("id"),
                project.get("title"),
                project.get("description"),
                project.get("price"),
                project.get("url"),
                project.get("date_create"),
                project.get("username"),
                project.get("category_id"),
            ),
        )
        self.conn.commit()

    def get_latest_fl_projects(self, limit: int = 5):
        self.cursor.execute(
            "SELECT * FROM fl_projects ORDER BY date_create DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_total_fl_projects_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM fl_projects")
        row = self.cursor.fetchone()
        return row[0] if row else 0

    # ----------- GURU --------------
    def save_guru_project(self, project: dict) -> None:
        self.cursor.execute(
            "INSERT OR IGNORE INTO guru_projects VALUES (?, ?, ?, ?, ?, ?)",
            (
                project.get("id"),
                project.get("title"),
                project.get("description"),
                project.get("price"),
                project.get("url"),
                project.get("date_create"),
            ),
        )
        self.conn.commit()

    def get_latest_guru_projects(self, limit: int = 5):
        self.cursor.execute(
            "SELECT * FROM guru_projects ORDER BY date_create DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_total_guru_projects_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM guru_projects")
        row = self.cursor.fetchone()
        return row[0] if row else 0

    # ----------- YOUDO --------------
    def save_youdo_task(self, task: dict) -> None:
        self.cursor.execute(
            "INSERT OR IGNORE INTO youdo_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                task.get("id"),
                task.get("title"),
                task.get("description"),
                task.get("address"),
                task.get("budget"),
                task.get("date"),
                task.get("url"),
                task.get("date_create"),
            ),
        )
        self.conn.commit()

    def get_latest_youdo_tasks(self, limit: int = 5):
        self.cursor.execute(
            "SELECT * FROM youdo_tasks ORDER BY date_create DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_total_youdo_tasks_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM youdo_tasks")
        row = self.cursor.fetchone()
        return row[0] if row else 0

    # ----------- VK --------------
    def save_vk_post(self, post: dict) -> None:
        self.cursor.execute(
            "INSERT OR IGNORE INTO vk_posts VALUES (?, ?, ?, ?, ?, ?)",
            (
                post.get("id"),
                post.get("group_id"),
                post.get("title"),
                post.get("description"),
                post.get("price"),
                post.get("date_create"),
            ),
        )
        self.conn.commit()

    def get_latest_vk_posts(self, limit: int = 5):
        self.cursor.execute(
            "SELECT * FROM vk_posts ORDER BY date_create DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_total_vk_posts_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM vk_posts")
        row = self.cursor.fetchone()
        return row[0] if row else 0

    # ----------- SETTINGS --------
    def get_settings(self, key: str = "kwork") -> dict:
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = self.cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return {"keywords": [], "min_price": None, "max_price": None}

    def save_settings(self, keywords, min_price, max_price, key: str = "kwork"):
        settings = {"keywords": keywords, "min_price": min_price, "max_price": max_price}
        self.cursor.execute(
            "REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, json.dumps(settings))
        )
        self.conn.commit()

    # --- Для FL ---
    def get_fl_settings(self) -> dict:
        return self.get_settings("fl")

    def save_fl_settings(self, keywords, min_price, max_price):
        self.save_settings(keywords, min_price, max_price, "fl")

    # --- Для Guru ---
    def get_guru_settings(self) -> dict:
        return self.get_settings("guru")

    def save_guru_settings(self, keywords, min_price, max_price):
        self.save_settings(keywords, min_price, max_price, "guru")

    # --- Для Habr Career ---
    def get_habr_settings(self) -> dict:
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", ('habr',))
        row = self.cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return {"keywords": [], "min_salary": None, "max_salary": None, "cities": [], "employment_types": []}

    def save_habr_settings(self, keywords, min_salary, max_salary, cities, employment_types):
        settings = {
            "keywords": keywords,
            "min_salary": min_salary,
            "max_salary": max_salary,
            "cities": cities,
            "employment_types": employment_types
        }
        self.cursor.execute(
            "REPLACE INTO settings (key, value) VALUES (?, ?)",
            ('habr', json.dumps(settings))
        )
        self.conn.commit()

    # --- Для YouDo ---
    def get_youdo_settings(self) -> dict:
        return self.get_settings("youdo")

    def save_youdo_settings(self, keywords, min_price, max_price):
        self.save_settings(keywords, min_price, max_price, "youdo")

    # --- Для VK ---
    def get_vk_settings(self) -> dict:
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", ('vk',))
        row = self.cursor.fetchone()
        if row and row[0]:
            settings = json.loads(row[0])
            if 'group_ids' not in settings:
                settings['group_ids'] = []
            return settings
        return {"keywords": [], "min_price": None, "max_price": None, "group_ids": []}

    def save_vk_settings(self, keywords, min_price, max_price):
        settings = {"keywords": keywords, "min_price": min_price, "max_price": max_price}
        self.cursor.execute(
            "REPLACE INTO settings (key, value) VALUES (?, ?)",
            ('vk', json.dumps(settings))
        )
        self.conn.commit()

    def add_source(self, link: str):
        """Добавить новый источник"""
        self.cursor.execute(
            "INSERT INTO sources (link, send_to, from_out, white_list, black_list) VALUES (?, ?, ?, ?, ?)",
            (link, "-1001234567890", "-1001234567890", "", "")
        )
        self.conn.commit()

    def get_all_sources(self) -> List[Source]:
        """Получить все источники"""
        self.cursor.execute("SELECT * FROM sources")
        rows = self.cursor.fetchall()
        return [Source(*row) for row in rows]

    def update_source_gpt_data(self, source_id: int, last_check_gpt_at: datetime, last_msg_id: str):
        """Обновить данные GPT для источника"""
        self.cursor.execute(
            "UPDATE sources SET last_check_gpt_at = ?, last_msg_id = ? WHERE id = ?",
            (last_check_gpt_at.isoformat(), last_msg_id, source_id)
        )
        self.conn.commit()

    # --- GPT Settings ---
    def get_gpt_status(self) -> str:
        """Получить статус GPT"""
        row = self.cursor.execute(
            "SELECT status FROM gpt_settings"
        ).fetchone()
        if row:
            return row[0]
        return "stopped"

    def set_gpt_status(self, status: str):
        """Установить статус GPT"""
        self.cursor.execute(
            "UPDATE gpt_settings SET status = ?",
            (status,)
        )
        self.conn.commit()

    def get_gpt_prompt(self) -> str:
        """Получить промпт GPT"""
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", ("gpt_prompt",))
        row = self.cursor.fetchone()
        if row and row[0]:
            return row[0]
        return "Твоя задача:\n1. Отфильтровать только те сообщения, у которых тема — \"вакансия\".\n2. Оценить каждое сообщение по качеству и соответствию теме. \n   - Самые лучшие сообщения: чётко сформулированы, содержат ключевые детали (зарплата, обязанности, требования и контакты).\n   - Хорошие сообщения: качественные, но менее подробные или содержат незначительные излишества.\n3. Выбрать максимум 2 записи из списка (1 или 2, но не больше), которые лучше всего соответствуют этим критериям.\n\nВернуть результат в формате JSON. Каждый объект должен содержать:\n- \"id\" сообщения.\n- Поле \"good\", принимающее значение:\n  - True для самых лучших сообщений.\n  - False для сообщений второй категории.\n\nЕсли тема сообщения не \"вакансия\", пропустить его."

    def set_gpt_prompt(self, prompt: str):
        """Установить промпт GPT"""
        self.cursor.execute(
            "REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("gpt_prompt", prompt)
        )
        self.conn.commit()

    def save_vk_full_settings(self, settings: dict):
        self.cursor.execute(
            "REPLACE INTO settings (key, value) VALUES (?, ?)",
            ('vk', json.dumps(settings))
        )
        self.conn.commit()
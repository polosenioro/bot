import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "db.sqlite3")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# создание таблиц, если не существуют
# создание таблиц, если не существуют
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ref_id TEXT,
    user_id INTEGER UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    city TEXT,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS rates (
    id INTEGER PRIMARY KEY,
    city TEXT UNIQUE,
    walk INTEGER,
    bike INTEGER,
    car INTEGER
)
""")
conn.commit()


def insert_user_if_not_exists(user_id, username, ref_id=None, city=None, first_name=None, last_name=None):
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        created_at = datetime.now().strftime("%d-%m-%Y %H:%M")
        cursor.execute(
            """
            INSERT INTO users (ref_id, user_id, username, first_name, last_name, city, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ref_id, user_id, username, first_name, last_name, city, created_at)
        )
        conn.commit()


def get_user_by_id(user_id: int):
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()


def load_rates_from_file(path: str):
    if not os.path.exists(path):
        print(f"[!] Файл не найден: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    city, walk, bike, car = [x.strip() for x in line.split("/")]
                    cursor.execute(
                        "INSERT OR REPLACE INTO rates (city, walk, bike, car) VALUES (?, ?, ?, ?)",
                        (city, int(walk), int(bike), int(car))
                    )
                except Exception as e:
                    print(f"[!] Ошибка в строке: {line.strip()} → {e}")
    conn.commit()
    print("✅ Ставки успешно загружены в базу данных.")


# автоинициализация ставок, если таблица пуста
cursor.execute("SELECT COUNT(*) FROM rates")
if cursor.fetchone()[0] == 0:
    load_rates_from_file(os.path.join(os.path.dirname(__file__), "ставки_курьеров.txt"))

def get_used_city_letters():
    cursor.execute("SELECT DISTINCT SUBSTR(city, 1, 1) FROM rates")
    return sorted(set(row[0].upper() for row in cursor.fetchall()))

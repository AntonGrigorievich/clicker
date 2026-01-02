import sqlite3

DB_NAME = "bot.db"

def get_conn():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        skills_count INTEGER,
        repair_min INTEGER,
        repair_max INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS algorithms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS algorithm_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        algorithm_id INTEGER,
        step_order INTEGER,
        battle_type TEXT,
        count INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS battle_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        algorithm_id INTEGER,
        battle_type TEXT,
        result INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def drop_table(table):
    conn = get_conn()
    c = conn.cursor()

    c.execute(f"""
    DROP TABLE {table}
    """)
    print(f"Таблица {table} удалена.")

    conn.commit()
    conn.close()
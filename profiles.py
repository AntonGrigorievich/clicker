from db import get_conn
import sqlite3
from utils import input_str, input_int, UI

def create_profile():
    name = input_str("Имя профиля: ")
    if name is None:
        return

    skills = input_int("Количество скиллов: ", min_value=0)
    if skills is None:
        return

    repair_min = input_int("Починка ОТ: ", min_value=1)
    if repair_min is None:
        return

    repair_max = input_int("Починка ДО: ", min_value=1)
    if repair_max is None:
        return

    if repair_min > repair_max:
        UI.error("Починка ОТ не может быть больше Починка ДО")
        return

    conn = get_conn()
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO profiles
            (name, skills_count, repair_min, repair_max)
            VALUES (?, ?, ?, ?)
        """, (name, skills, repair_min, repair_max))
        conn.commit()
        UI.success("Профиль успешно создан")
    except sqlite3.IntegrityError:
        UI.error("Ошибка: профиль с таким именем уже существует")
    finally:
        conn.close()

def select_profile():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM profiles")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    for i, (id, _, _, _, _) in enumerate(rows, 1):
        UI.info("--------------------")
        UI.info(f"{i} - Профиль:")
        display_profile(id)
    UI.info("--------------------")

    UI.info("0 - Назад")
    ch = int(input("> "))
    if ch == 0:
        return None

    return rows[ch - 1]

def get_profile(profile_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT skills_count, max_energy, repair_min, repair_max, boosters_enabled
        FROM profiles
        WHERE id = ?
    """, (profile_id,))
    row = c.fetchone()
    conn.close()
    return row


def display_profile(profile_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, skills_count, repair_min, repair_max FROM profiles WHERE id = ?", (profile_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        UI.warning(f"Профиль {profile_id} не найден.")
        return

    UI.info(f"ID: {row[0]}")
    UI.success(f"Имя: {row[1]}")
    UI.info(f"Кол-во скиллов: {row[2]}\nПочинка: {row[3]}-{row[4]}")

def edit_profile(profile_id):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT name, skills_count, repair_min, repair_max
        FROM profiles
        WHERE id = ?
    """, (profile_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        UI.warning("Профиль не найден")
        return

    name, skills, r_min, r_max = row

    UI.info("Редактирование профиля (Enter - оставить без изменений)")
    new_name = input(f"Имя [{name}]: ") or name
    new_skills = input(f"Кол-во скиллов [{skills}]: ")
    new_rmin = input(f"Починка ОТ [{r_min}]: ")
    new_rmax = input(f"Починка ДО [{r_max}]: ")

    c.execute("""
        UPDATE profiles
        SET name = ?, skills_count = ?, repair_min = ?, repair_max = ?
        WHERE id = ?
    """, (
        new_name,
        int(new_skills) if new_skills else skills,
        int(new_rmin) if new_rmin else r_min,
        int(new_rmax) if new_rmax else r_max,
        profile_id
    ))

    conn.commit()
    conn.close()
    UI.success("Профиль обновлён")

def get_all_profiles():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, skills_count, repair_min, repair_max
        FROM profiles
        ORDER BY id
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def delete_profile(profile_id):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT name FROM profiles WHERE id = ?", (profile_id,))
    row = c.fetchone()

    if not row:
        UI.error("Профиль не найден")
        conn.close()
        return

    name = row[0]
    UI.warning(f"Вы уверены, что хотите удалить профиль «{name}»?")
    UI.warning("Связанная статистика сохранится без привязки к профилю.")
    UI.warning("Введите ДА для подтверждения: ")
    confirm = input().strip().lower()

    if confirm != "да":
        UI.info("Удаление отменено")
        conn.close()
        return

    try:
        c.execute("""
            UPDATE battle_stats
            SET profile_id = NULL
            WHERE profile_id = ?
        """, (profile_id,))

        c.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.commit()

        UI.success(f"Профиль «{name}» удалён")

    except Exception as e:
        conn.rollback()
        UI.error(f"Ошибка удаления профиля: {e}")

    finally:
        conn.close()

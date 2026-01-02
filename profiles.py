from db import get_conn

def create_profile():
    name = input("Имя профиля: ")
    skills = int(input("Количество скиллов: "))
    repair_min = int(input("Починка ОТ: "))
    repair_max = int(input("Починка ДО: "))

    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO profiles
        (name, skills_count, repair_min, repair_max)
        VALUES (?, ?, ?, ?)
    """, (name, skills, repair_min, repair_max))
    conn.commit()
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
        print("--------------------")
        print(f"{i} - Профиль:")
        display_profile(id)
    print("--------------------")

    print("0 - Назад")
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
        print(f"Профиль {profile_id} не найден.")
        return

    print(f"ID: {row[0]}\nИмя: {row[1]}\nКол-во скиллов: {row[2]}\nПочинка: {row[3]}-{row[4]}")


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
        print("Профиль не найден")
        return

    name, skills, r_min, r_max = row

    print("Редактирование профиля (Enter - оставить без изменений)")
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
    print("Профиль обновлён")

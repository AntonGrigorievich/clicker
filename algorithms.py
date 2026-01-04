from db import get_conn
from utils import input_str, input_int, UI

BATTLE_TYPES = {
    "1": "3x3",
    "2": "1x1",
    "3": "dungeon",
}

def create_algorithm():
    name = input_str("Имя алгоритма: ")
    if name is None:
        return

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM algorithms WHERE name = ?", (name,))
    if c.fetchone():
        UI.error(f"Алгоритм с именем '{name}' уже существует")
        conn.close()
        return

    c.execute(
        "INSERT INTO algorithms (name) VALUES (?)",
        (name,)
    )
    alg_id = c.lastrowid

    order = 1
    steps_added = False
    while True:
        UI.info("""
1 - 3x3
2 - 1x1
3 - Подземелье
0 - Сохранить
""")
        ch = input("> ")

        if ch == "0":
            break

        if ch not in BATTLE_TYPES:
            UI.error("Неверный тип боя")
            continue

        count = input_int("Количество боёв: ", min_value=1)
        if count is None:
            continue

        c.execute("""
            INSERT INTO algorithm_steps
            (algorithm_id, step_order, battle_type, count)
            VALUES (?, ?, ?, ?)
        """, (alg_id, order, BATTLE_TYPES[ch], count))

        steps_added = True
        order += 1
    
    if not steps_added:
        UI.error("Алгоритм не содержит шагов и не будет сохранён")
        conn.rollback()
        conn.close()
        return

    conn.commit()
    conn.close()

def run_algorithm(clicker, algorithm_id):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT battle_type, count
        FROM algorithm_steps
        WHERE algorithm_id=?
        ORDER BY step_order
    """, (algorithm_id,))
    steps = c.fetchall()
    conn.close()

    for battle_type, count in steps:
        for _ in range(count):
            clicker.run_battle(battle_type)


def select_algorithm():
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT id, name FROM algorithms ORDER BY id")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    UI.info("Выберите алгоритм:")
    for i, (alg_id, _) in enumerate(rows, start=1):
        UI.info("--------------------")
        UI.info(f"{i} - Алгоритм:")
        display_algorithm(alg_id)
    UI.info("--------------------")

    UI.info("0 - Назад")

    while True:
        try:
            choice = int(input("> "))

            if choice == 0:
                return None

            if 1 <= choice <= len(rows):
                return rows[choice - 1]

        except ValueError:
            pass

        UI.error("Неверный ввод")


def display_algorithm(algorithm_id):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT name FROM algorithms WHERE id = ?", (algorithm_id,))
    alg = c.fetchone()

    if not alg:
        conn.close()
        UI.error("Алгоритм не найден")
        return

    UI.info(f"«{alg[0]}»")
    UI.info("Шаги:")
    c.execute("""

        SELECT step_order, battle_type, count
        FROM algorithm_steps
        WHERE algorithm_id = ?
        ORDER BY step_order
    """, (algorithm_id,))

    steps = c.fetchall()
    conn.close()

    for order, btype, count in steps:
        UI.info(f"  {order}. {btype} × {count}")
    UI.info()


def clear_algorithm_steps(algorithm_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM algorithm_steps WHERE algorithm_id = ?", (algorithm_id,))
    conn.commit()
    conn.close()


def edit_algorithm(algorithm_id):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT name FROM algorithms WHERE id = ?", (algorithm_id,))
    alg = c.fetchone()

    if not alg:
        conn.close()
        UI.error("Алгоритм не найден")
        return

    name = alg[0]

    UI.info("Редактирование алгоритма (Enter — оставить)")
    new_name = input_str(f"Имя [{name}]: ", allow_empty=True)

    if new_name:
        c.execute(
            "SELECT 1 FROM algorithms WHERE name = ? AND id != ?",
            (new_name, algorithm_id)
        )
        if c.fetchone():
            UI.error("Алгоритм с таким именем уже существует")
            conn.close()
            return

        c.execute(
            "UPDATE algorithms SET name = ? WHERE id = ?",
            (new_name, algorithm_id)
        )

    conn.commit()
    conn.close()

    clear_algorithm_steps(algorithm_id)

    UI.info("\nВведите новые шаги алгоритма")
    order = 1
    steps_added = False

    while True:
        UI.info("""
1 - 3x3
2 - 1x1
3 - Подземелье
0 - Сохранить
""")
        ch = input("> ").strip()

        if ch == "0":
            break

        if ch not in BATTLE_TYPES:
            UI.error("Неверный тип боя")
            continue

        count = input_int("Количество боёв: ", min_value=1)
        if count is None:
            continue

        c.execute("""
            INSERT INTO algorithm_steps
            (algorithm_id, step_order, battle_type, count)
            VALUES (?, ?, ?, ?)
        """, (algorithm_id, order, BATTLE_TYPES[ch], count))

        steps_added = True
        order += 1

    if not steps_added:
        UI.error("Алгоритм без шагов не может быть сохранён")
        conn.rollback()
        conn.close()
        return

    conn.commit()
    conn.close()
    UI.success("Алгоритм успешно обновлён")
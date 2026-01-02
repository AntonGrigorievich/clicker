from db import get_conn

def create_algorithm():
    name = input("Имя алгоритма: ")

    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO algorithms (name) VALUES (?)",
        (name,)
    )
    alg_id = c.lastrowid

    order = 1
    while True:
        print("""
1 - 3x3
2 - 1x1
3 - Подземелье
0 - Сохранить
""")
        ch = input("> ")

        if ch == "0":
            break

        battle_type = {"1": "3x3", "2": "1x1", "3": "dungeon"}[ch]
        count = int(input("Количество боёв: "))

        c.execute("""
            INSERT INTO algorithm_steps
            (algorithm_id, step_order, battle_type, count)
            VALUES (?, ?, ?, ?)
        """, (alg_id, order, battle_type, count))

        order += 1

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

    print("Выберите алгоритм:")
    for i, (alg_id, _) in enumerate(rows, start=1):
        print("--------------------")
        print(f"{i} - Алгоритм:")
        display_algorithm(alg_id)
    print("--------------------")

    print("0 - Назад")

    while True:
        try:
            choice = int(input("> "))

            if choice == 0:
                return None

            if 1 <= choice <= len(rows):
                return rows[choice - 1]

        except ValueError:
            pass

        print("Неверный ввод")


def display_algorithm(algorithm_id):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT name FROM algorithms WHERE id = ?", (algorithm_id,))
    alg = c.fetchone()

    if not alg:
        conn.close()
        print("Алгоритм не найден")
        return

    print(f"«{alg[0]}»")
    print("Шаги:")
    c.execute("""

        SELECT step_order, battle_type, count
        FROM algorithm_steps
        WHERE algorithm_id = ?
        ORDER BY step_order
    """, (algorithm_id,))

    steps = c.fetchall()
    conn.close()

    for order, btype, count in steps:
        print(f"  {order}. {btype} × {count}")
    print()


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
        print("Алгоритм не найден")
        return

    name = alg[0]

    print("Редактирование алгоритма (Enter — оставить)")
    new_name = input(f"Имя [{name}]: ") or name

    c.execute("""
        UPDATE algorithms
        SET name = ?
        WHERE id = ?
    """, (
        new_name,
        algorithm_id
    ))

    conn.commit()
    conn.close()

    clear_algorithm_steps(algorithm_id)

    print("Введите новые шаги алгоритма:")

    conn = get_conn()
    c = conn.cursor()
    order = 1

    while True:
        print("""
1 - 3x3
2 - 1x1
3 - Подземелье
0 - Сохранить
""")
        ch = input("> ")
        if ch == "0":
            break

        battle_type = {"1": "3x3", "2": "1x1", "3": "dungeon"}[ch]
        count = int(input("Количество боёв: "))

        c.execute("""
            INSERT INTO algorithm_steps
            (algorithm_id, step_order, battle_type, count)
            VALUES (?, ?, ?, ?)
        """, (algorithm_id, order, battle_type, count))
        order += 1

    conn.commit()
    conn.close()
    print("Алгоритм обновлён")

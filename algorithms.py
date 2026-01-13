from db import get_conn
from utils import input_str, input_int, UI

BATTLE_TYPES = {
    "1": "3x3",
    "2": "1x1",
    "3": "Подземелье",
}

def create_algorithm():
    name = input_str("Имя алгоритма: ")
    use_boosts = input("Использовать боевые усилители? (1/0): ") == "1"
    no_energy = input("Режим игры без энергии? (1/0): ") == "1"

    if name is None:
        return

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM algorithms WHERE name = ?", (name,))
    if c.fetchone():
        UI.error(f"Алгоритм с именем '{name}' уже существует")
        conn.close()
        return

    c.execute("""
    INSERT INTO algorithms (name, use_boosts, no_energy_mode)
    VALUES (?, ?, ?)
    """, (name, int(use_boosts), int(no_energy)))
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
            if clicker.stop_event.is_set():
                return
            res = clicker.run_battle(battle_type)

            if res == 0:
                return


def select_algorithm():
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT id, name, use_boosts, no_energy_mode FROM algorithms ORDER BY id")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    UI.info("Выберите алгоритм:")
    for i, (alg_id, _, _, _) in enumerate(rows, start=1):
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

    c.execute("""
    SELECT name, use_boosts, no_energy_mode
    FROM algorithms
    WHERE id = ?
    """, (algorithm_id,))
    alg = c.fetchone()

    if not alg:
        conn.close()
        UI.error("Алгоритм не найден")
        return

    name, use_boosts, no_energy_mode = alg
    UI.info(f"«{name}»")
    UI.info(f"Боевые усилители: {'вкл' if use_boosts else 'выкл'}")
    UI.info(f"Режим без энергии: {'вкл' if no_energy_mode else 'выкл'}")

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

    c.execute("""SELECT name, use_boosts, no_energy_mode
    FROM algorithms
    WHERE id = ?""", (algorithm_id,))
    alg = c.fetchone()

    if not alg:
        conn.close()
        UI.error("Алгоритм не найден")
        return

    name, use_boosts, no_energy_mode = alg

    UI.info("Редактирование алгоритма (Enter — оставить)")
    new_name = input_str(f"Имя [{name}]: ", allow_empty=True)

    boosts_in = input(
        f"Боевые усилители (1/0) [{1 if use_boosts else 0}]: "
    ).strip()

    energy_in = input(
        f"Режим без энергии (1/0) [{1 if no_energy_mode else 0}]: "
    ).strip()
    new_use_boosts = use_boosts if boosts_in == "" else boosts_in == "1"
    new_no_energy = no_energy_mode if energy_in == "" else energy_in == "1"

    if new_name:
        c.execute(
            "SELECT 1 FROM algorithms WHERE name = ? AND id != ?",
            (new_name, algorithm_id)
        )
        if c.fetchone():
            UI.error("Алгоритм с таким именем уже существует")
            conn.close()
            return

        c.execute("""
        UPDATE algorithms
        SET name = ?, use_boosts = ?, no_energy_mode = ?
        WHERE id = ?
        """, (
            new_name,
            int(new_use_boosts),
            int(new_no_energy),
            algorithm_id
        ))


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

def delete_algorithm(algorithm_id):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT name FROM algorithms WHERE id = ?", (algorithm_id,))
    row = c.fetchone()

    if not row:
        UI.error("Алгоритм не найден")
        conn.close()
        return

    name = row[0]
    UI.warning(f"Вы уверены, что хотите удалить алгоритм «{name}»?")
    UI.warning("Связанная статистика сохранится без привязки к алгоритму.")
    UI.warning("Введите ДА для подтверждения: ")
    confirm = input().strip().lower()

    if confirm != "да":
        UI.info("Удаление отменено")
        conn.close()
        return

    try:
        c.execute("""
            UPDATE battle_stats
            SET algorithm_id = NULL
            WHERE algorithm_id = ?
        """, (algorithm_id,))

        c.execute("DELETE FROM algorithms WHERE id = ?", (algorithm_id,))

        conn.commit()
        UI.success(f"Алгоритм «{name}» удалён")

    except Exception as e:
        conn.rollback()
        UI.error(f"Ошибка удаления алгоритма: {e}")

    finally:
        conn.close()

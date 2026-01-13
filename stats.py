from db import get_conn


def save_battle_stat(profile_id, algorithm_id, battle_type, win):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO battle_stats
        (profile_id, algorithm_id, battle_type, result)
        VALUES (?, ?, ?, ?)
    """, (profile_id, algorithm_id, battle_type, int(win)))
    conn.commit()
    conn.close()

def _apply_period_filter(query, params, date_from, date_to):
    if date_from:
        query += " AND bs.created_at >= ?"
        params.append(date_from)
    if date_to:
        query += " AND bs.created_at <= ?"
        params.append(date_to)
    return query, params


def stats_overall(date_from=None, date_to=None):
    conn = get_conn()
    c = conn.cursor()

    query = """
        SELECT
            COUNT(bs.id) AS games,
            COALESCE(SUM(bs.result), 0) AS wins,
            COUNT(bs.id) - COALESCE(SUM(bs.result), 0) AS losses,
            CASE
                WHEN COUNT(bs.id) = 0 THEN 0
                ELSE ROUND(
                    COALESCE(SUM(bs.result), 0) * 100.0 / COUNT(bs.id),
                    2
                )
            END AS winrate
        FROM battle_stats bs
        WHERE 1=1
    """
    params = []

    query, params = _apply_period_filter(query, params, date_from, date_to)

    c.execute(query, params)
    row = c.fetchone()
    conn.close()

    return row


def stats_by_profiles(date_from=None, date_to=None):
    conn = get_conn()
    c = conn.cursor()

    query = """
        SELECT
            COALESCE(p.name, 'ANY') AS profile,
            COUNT(bs.id) AS games,
            SUM(bs.result) AS wins,
            COUNT(bs.id) - SUM(bs.result) AS losses,
            CASE
                WHEN COUNT(bs.id) = 0 THEN 0
                ELSE ROUND(SUM(bs.result) * 100.0 / COUNT(bs.id), 2)
            END AS winrate
        FROM battle_stats bs
        LEFT JOIN profiles p ON p.id = bs.profile_id
        WHERE 1=1
    """
    params = []

    query, params = _apply_period_filter(query, params, date_from, date_to)

    query += """
        GROUP BY bs.profile_id
        ORDER BY winrate DESC, games DESC
    """

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows


def stats_by_algorithms(date_from=None, date_to=None):
    conn = get_conn()
    c = conn.cursor()

    query = """
        SELECT
            COALESCE(a.name, 'ANY') AS algorithm,
            COUNT(bs.id) AS games,
            SUM(bs.result) AS wins,
            COUNT(bs.id) - SUM(bs.result) AS losses,
            CASE
                WHEN COUNT(bs.id) = 0 THEN 0
                ELSE ROUND(SUM(bs.result) * 100.0 / COUNT(bs.id), 2)
            END AS winrate
        FROM battle_stats bs
        LEFT JOIN algorithms a ON a.id = bs.algorithm_id
        WHERE 1=1
    """
    params = []

    query, params = _apply_period_filter(query, params, date_from, date_to)

    query += """
        GROUP BY bs.algorithm_id
        ORDER BY winrate DESC, games DESC
    """

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows


def stats_profile_algorithms(profile_id=None, date_from=None, date_to=None):
    conn = get_conn()
    c = conn.cursor()

    query = """
        SELECT
            COALESCE(a.name, 'ANY') AS algorithm,
            COUNT(bs.id) AS games,
            SUM(bs.result) AS wins,
            COUNT(bs.id) - SUM(bs.result) AS losses,
            CASE
                WHEN COUNT(bs.id) = 0 THEN 0
                ELSE ROUND(SUM(bs.result) * 100.0 / COUNT(bs.id), 2)
            END AS winrate
        FROM battle_stats bs
        LEFT JOIN algorithms a ON a.id = bs.algorithm_id
        WHERE 1=1
    """
    params = []

    if profile_id is not None:
        query += " AND bs.profile_id = ?"
        params.append(profile_id)

    query, params = _apply_period_filter(query, params, date_from, date_to)

    query += """
        GROUP BY bs.algorithm_id
        ORDER BY winrate DESC, games DESC
    """

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows



def stats_by_battle_type(date_from=None, date_to=None):
    conn = get_conn()
    c = conn.cursor()

    query = """
        SELECT
            battle_type,
            COUNT(*) AS games,
            SUM(result) AS wins,
            COUNT(*) - SUM(result) AS losses,
            CASE
                WHEN COUNT(*) = 0 THEN 0
                ELSE ROUND(SUM(result) * 100.0 / COUNT(*), 2)
            END AS winrate
        FROM battle_stats bs
        WHERE 1=1
    """
    params = []

    query, params = _apply_period_filter(query, params, date_from, date_to)

    query += """
        GROUP BY battle_type
        ORDER BY winrate DESC, games DESC
    """

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def stats_for_run(profile_id, algorithm_id, started_at):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT
            COUNT(*) as games,
            SUM(CASE WHEN result = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN result = 0 THEN 1 ELSE 0 END) as losses
        FROM battle_stats
        WHERE
            (? IS NULL OR profile_id = ?)
            AND (? IS NULL OR algorithm_id = ?)
            AND created_at >= ?
    """, (
        profile_id, profile_id,
        algorithm_id, algorithm_id,
        started_at
    ))

    games, wins, losses = c.fetchone()
    conn.close()

    games = games or 0
    wins = wins or 0
    losses = losses or 0
    winrate = round((wins / games) * 100, 2) if games else 0.0

    return games, wins, losses, winrate

def reset_stats():
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM battle_stats")
    conn.commit()
    conn.close()

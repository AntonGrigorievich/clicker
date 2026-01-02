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

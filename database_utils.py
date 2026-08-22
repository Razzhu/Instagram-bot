# database_utils.py
from database import get_db
from datetime import datetime

def get_user_xp(user_id, thread_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT xp, level, coins, reputation, daily_streak FROM xp WHERE user_id = ? AND thread_id = ?", (user_id, thread_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"xp": 0, "level": 1, "coins": 0, "reputation": 50, "daily_streak": 0}

def update_user_xp(user_id, thread_id, xp_delta):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO xp (user_id, thread_id, xp) 
        VALUES (?, ?, ?) 
        ON CONFLICT(user_id, thread_id) 
        DO UPDATE SET xp = xp + excluded.xp
    """, (user_id, thread_id, xp_delta))
    conn.commit()
    conn.close()

def add_coins(user_id, thread_id, amount):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO xp (user_id, thread_id, coins) 
        VALUES (?, ?, ?) 
        ON CONFLICT(user_id, thread_id) 
        DO UPDATE SET coins = coins + excluded.coins
    """, (user_id, thread_id, amount))
    conn.commit()
    conn.close()

def get_setting(thread_id, key):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT {key} FROM settings WHERE thread_id = ?", (thread_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(thread_id, key, value):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO settings (thread_id, {key}) VALUES (?, ?)
        ON CONFLICT(thread_id) DO UPDATE SET {key} = excluded.{key}
    """, (thread_id, value))
    conn.commit()
    conn.close()

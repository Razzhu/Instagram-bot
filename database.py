import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "bot_data.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            thread_id TEXT
        )
    """)
    
    # XP/Levels/Coins
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xp (
            user_id TEXT,
            thread_id TEXT,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            coins INTEGER DEFAULT 0,
            reputation INTEGER DEFAULT 50,
            daily_streak INTEGER DEFAULT 0,
            last_daily TIMESTAMP,
            PRIMARY KEY (user_id, thread_id)
        )
    """)
    
    # Memory
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            thread_id TEXT,
            text TEXT,
            importance REAL DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP
        )
    """)
    
    # Settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            thread_id TEXT PRIMARY KEY,
            welcome_message TEXT,
            rules TEXT,
            chaos_level INTEGER DEFAULT 50,
            ai_enabled BOOLEAN DEFAULT 1
        )
    """)
    
    # Achievements
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            thread_id TEXT,
            name TEXT,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Inventory
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            user_id TEXT,
            thread_id TEXT,
            item_name TEXT,
            quantity INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, thread_id, item_name)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

def migrate_json_to_sqlite(json_file="bot_data.json"):
    if not os.path.exists(json_file):
        print("📂 No JSON file to migrate")
        return
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Migrate XP
    for user_id, xp in data.get('xp', {}).items():
        cursor.execute("""
            INSERT OR REPLACE INTO xp (user_id, thread_id, xp)
            VALUES (?, 'DEFAULT', ?)
        """, (user_id, xp))
    
    # Migrate coins
    for user_id, coins in data.get('coins', {}).items():
        cursor.execute("""
            UPDATE xp SET coins = ? WHERE user_id = ? AND thread_id = 'DEFAULT'
        """, (coins, user_id))
    
    # Migrate scores
    for user_id, score in data.get('scores', {}).items():
        # Scores are separate from XP
        pass
    
    conn.commit()
    conn.close()
    print("✅ Data migrated from JSON to SQLite!")

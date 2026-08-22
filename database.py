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
    
    # Personality per GC
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personality (
            thread_id TEXT PRIMARY KEY,
            mood TEXT DEFAULT 'chill',
            energy INTEGER DEFAULT 70,
            sarcasm INTEGER DEFAULT 60,
            friendliness INTEGER DEFAULT 70,
            chaos INTEGER DEFAULT 50,
            confidence INTEGER DEFAULT 70,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            ai_enabled BOOLEAN DEFAULT 1,
            custom_personality TEXT
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
    
    # Roast Battle
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roast_battles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT,
            user1 TEXT,
            user2 TEXT,
            winner TEXT,
            roasts TEXT,
            votes TEXT,
            status TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP
        )
    """)
    
    # Mysteries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mysteries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT,
            topic TEXT,
            culprit TEXT,
            suspects TEXT,
            clues TEXT,
            status TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # XP History (for leaderboard)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xp_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            thread_id TEXT,
            amount INTEGER,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

def migrate_json_to_sqlite(json_file="bot_data.json"):
    if not os.path.exists(json_file):
        print("📂 No JSON file to migrate")
        return
    
    try:
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
        
        conn.commit()
        conn.close()
        print("✅ Data migrated from JSON to SQLite!")
    except Exception as e:
        print(f"⚠️ Migration error: {e}")

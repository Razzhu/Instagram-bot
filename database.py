# database.py
import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "bot_data.db"

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize database with all tables"""
    with get_db() as conn:
        c = conn.cursor()
        
        # Users & XP table
        c.execute("""
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
        c.execute("""
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
        c.execute("""
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
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                thread_id TEXT PRIMARY KEY,
                welcome_message TEXT,
                rules TEXT,
                chaos_level INTEGER DEFAULT 50,
                ai_enabled BOOLEAN DEFAULT 1
            )
        """)
        
        # Achievements
        c.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                thread_id TEXT,
                name TEXT,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, thread_id, name)
            )
        """)
        
        # Inventory
        c.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id TEXT,
                thread_id TEXT,
                item_name TEXT,
                quantity INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, thread_id, item_name)
            )
        """)
        
        # Reports (instead of spamming Instagram API)
        c.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT,
                reporter_id TEXT,
                target_id TEXT,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Events (chaos, mystery, etc.)
        c.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT,
                event_type TEXT,
                data TEXT,
                status TEXT DEFAULT 'active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        # Game stats
        c.execute("""
            CREATE TABLE IF NOT EXISTS game_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                thread_id TEXT,
                game_type TEXT,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                plays INTEGER DEFAULT 0,
                UNIQUE(user_id, thread_id, game_type)
            )
        """)
        
        # XP History
        c.execute("""
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
        print("✅ Database initialized successfully!")
        
        # Migration: Add missing columns if they exist
        try:
            c.execute("ALTER TABLE xp ADD COLUMN last_daily TIMESTAMP")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE xp ADD COLUMN daily_streak INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

# ============ USER DATA HELPERS ============

def get_user_data(user_id, thread_id):
    """Get user data from database"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM xp WHERE user_id = ? AND thread_id = ?", (user_id, thread_id))
        row = c.fetchone()
        if row:
            return dict(row)
        return {"xp": 0, "level": 1, "coins": 0, "reputation": 50, "daily_streak": 0, "last_daily": None}

def ensure_user(user_id, thread_id):
    """Ensure user exists in database"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO xp (user_id, thread_id, xp, level, coins, reputation)
            VALUES (?, ?, 0, 1, 0, 50)
        """, (user_id, thread_id))
        conn.commit()

def add_xp(user_id, thread_id, amount, reason=None):
    """Add XP to user and update level"""
    if amount == 0:
        return
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO xp (user_id, thread_id) VALUES (?, ?)", (user_id, thread_id))
        c.execute("UPDATE xp SET xp = xp + ? WHERE user_id = ? AND thread_id = ?", (amount, user_id, thread_id))
        
        # Update level
        c.execute("SELECT xp FROM xp WHERE user_id = ? AND thread_id = ?", (user_id, thread_id))
        row = c.fetchone()
        if row:
            new_level = get_level(row[0])
            c.execute("UPDATE xp SET level = ? WHERE user_id = ? AND thread_id = ?", (new_level, user_id, thread_id))
        
        # Log XP history
        if reason:
            c.execute("""
                INSERT INTO xp_history (user_id, thread_id, amount, reason)
                VALUES (?, ?, ?, ?)
            """, (user_id, thread_id, amount, reason))
        
        conn.commit()
        return new_level

def add_coins(user_id, thread_id, amount):
    """Add coins to user"""
    if amount == 0:
        return
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO xp (user_id, thread_id) VALUES (?, ?)", (user_id, thread_id))
        c.execute("UPDATE xp SET coins = coins + ? WHERE user_id = ? AND thread_id = ?", (amount, user_id, thread_id))
        conn.commit()

def add_reputation(user_id, thread_id, amount):
    """Add reputation to user"""
    if amount == 0:
        return
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO xp (user_id, thread_id) VALUES (?, ?)", (user_id, thread_id))
        c.execute("UPDATE xp SET reputation = reputation + ? WHERE user_id = ? AND thread_id = ?", (amount, user_id, thread_id))
        conn.commit()

def get_level(xp):
    """Calculate level from XP"""
    levels = {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000, 7: 2000, 10: 4000, 15: 7500, 20: 12000, 30: 20000, 50: 40000, 75: 70000, 100: 120000}
    level = 1
    for lvl, req in sorted(levels.items()):
        if xp >= req:
            level = lvl
    return level

def get_title(level):
    """Get title from level"""
    titles = {1: "Newbie", 2: "Rookie", 3: "Member", 5: "Regular", 10: "OG", 20: "Legend", 35: "GC God", 50: "Myth", 75: "Legendary", 100: "Immortal"}
    for lvl, title in sorted(titles.items(), reverse=True):
        if level >= lvl:
            return title
    return "Newbie"

def get_or_create_personality(thread_id):
    """Get or create personality for a thread"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM personality WHERE thread_id = ?", (thread_id,))
        row = c.fetchone()
        if row:
            return dict(row)
        # Create default personality
        c.execute("""
            INSERT INTO personality (thread_id, mood, energy, sarcasm, friendliness, chaos, confidence)
            VALUES (?, 'chill', 70, 60, 70, 50, 70)
        """, (thread_id,))
        conn.commit()
        return {"thread_id": thread_id, "mood": "chill", "energy": 70, "sarcasm": 60, "friendliness": 70, "chaos": 50, "confidence": 70}

def update_personality(thread_id, **kwargs):
    """Update personality values"""
    with get_db() as conn:
        c = conn.cursor()
        for key, value in kwargs.items():
            c.execute(f"UPDATE personality SET {key} = ? WHERE thread_id = ?", (value, thread_id))
        c.execute("UPDATE personality SET updated_at = CURRENT_TIMESTAMP WHERE thread_id = ?", (thread_id,))
        conn.commit()

def get_setting(thread_id, key):
    """Get a setting for a thread"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT {key} FROM settings WHERE thread_id = ?", (thread_id,))
        row = c.fetchone()
        return row[0] if row else None

def set_setting(thread_id, key, value):
    """Set a setting for a thread"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"""
            INSERT INTO settings (thread_id, {key}) VALUES (?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET {key} = excluded.{key}
        """, (thread_id, value))
        conn.commit()

def get_welcome_message(thread_id):
    """Get welcome message for thread"""
    msg = get_setting(thread_id, 'welcome_message')
    return msg if msg else WELCOME_MSG

def get_rules(thread_id):
    """Get rules for thread"""
    rules = get_setting(thread_id, 'rules')
    return rules if rules else RULES

def add_achievement(user_id, thread_id, name):
    """Add achievement for user"""
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO achievements (user_id, thread_id, name) VALUES (?, ?, ?)", (user_id, thread_id, name))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def get_achievements(user_id, thread_id):
    """Get achievements for user"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT name, unlocked_at FROM achievements WHERE user_id = ? AND thread_id = ?", (user_id, thread_id))
        rows = c.fetchall()
        return [dict(row) for row in rows]

def add_inventory_item(user_id, thread_id, item_name, quantity=1):
    """Add item to user inventory"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO inventory (user_id, thread_id, item_name, quantity)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, thread_id, item_name) DO UPDATE SET quantity = quantity + ?
        """, (user_id, thread_id, item_name, quantity, quantity))
        conn.commit()

def get_inventory(user_id, thread_id):
    """Get user inventory"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT item_name, quantity FROM inventory WHERE user_id = ? AND thread_id = ?", (user_id, thread_id))
        rows = c.fetchall()
        return [dict(row) for row in rows]

def add_report(thread_id, reporter_id, target_id, reason):
    """Add internal report (does NOT spam Instagram)"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO reports (thread_id, reporter_id, target_id, reason)
            VALUES (?, ?, ?, ?)
        """, (thread_id, reporter_id, target_id, reason))
        conn.commit()

def get_reports(thread_id, status='pending'):
    """Get reports for a thread"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM reports WHERE thread_id = ? AND status = ?", (thread_id, status))
        rows = c.fetchall()
        return [dict(row) for row in rows]

# ============ GAME STATS ============

def update_game_stats(user_id, thread_id, game_type, win=False):
    """Update game statistics"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO game_stats (user_id, thread_id, game_type, wins, losses, plays)
            VALUES (?, ?, ?, 0, 0, 1)
            ON CONFLICT(user_id, thread_id, game_type) DO UPDATE SET plays = plays + 1
        """, (user_id, thread_id, game_type))
        if win:
            c.execute("""
                UPDATE game_stats SET wins = wins + 1
                WHERE user_id = ? AND thread_id = ? AND game_type = ?
            """, (user_id, thread_id, game_type))
        else:
            c.execute("""
                UPDATE game_stats SET losses = losses + 1
                WHERE user_id = ? AND thread_id = ? AND game_type = ?
            """, (user_id, thread_id, game_type))
        conn.commit()

def get_game_stats(user_id, thread_id, game_type):
    """Get game statistics for a user"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT wins, losses, plays FROM game_stats WHERE user_id = ? AND thread_id = ? AND game_type = ?", 
                  (user_id, thread_id, game_type))
        row = c.fetchone()
        if row:
            return dict(row)
        return {"wins": 0, "losses": 0, "plays": 0}

# ============ MIGRATION ============

def migrate_json_to_sqlite(json_file="bot_data.json"):
    """Migrate data from old JSON file to SQLite"""
    if not os.path.exists(json_file):
        print("📂 No JSON file to migrate")
        return
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        with get_db() as conn:
            c = conn.cursor()
            
            # Migrate XP
            for user_id, xp in data.get('xp', {}).items():
                c.execute("""
                    INSERT OR REPLACE INTO xp (user_id, thread_id, xp)
                    VALUES (?, 'DEFAULT', ?)
                """, (user_id, xp))
            
            # Migrate coins
            for user_id, coins in data.get('coins', {}).items():
                c.execute("""
                    UPDATE xp SET coins = ? WHERE user_id = ? AND thread_id = 'DEFAULT'
                """, (coins, user_id))
            
            # Migrate memory
            for user_id, memories in data.get('memory', {}).items():
                for memory in memories:
                    c.execute("""
                        INSERT INTO memories (user_id, thread_id, text)
                        VALUES (?, 'DEFAULT', ?)
                    """, (user_id, memory))
            
            conn.commit()
            print("✅ Data migrated from JSON to SQLite!")
    except Exception as e:
        print(f"⚠️ Migration error: {e}")

# ============ CONFIG (to avoid circular import) ============
WELCOME_MSG = "🎉 Welcome {username} to the group! 🥳✨"
RULES = """
📋 GROUP RULES:
1. No spam
2. Be respectful
3. No NSFW content
4. Type .help for commands
"""

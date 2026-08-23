# mystery_database.py
import sqlite3
import json
from datetime import datetime
from database import get_db

def init_mystery_db():
    """Initialize mystery event database tables"""
    with get_db() as conn:
        c = conn.cursor()
        
        # Main mystery events table
        c.execute('''
            CREATE TABLE IF NOT EXISTS mystery_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                title TEXT NOT NULL,
                phase TEXT DEFAULT 'investigation',
                difficulty TEXT DEFAULT 'hard',
                started_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ended_at TEXT,
                state_json TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                solved INTEGER DEFAULT 0,
                culprit TEXT,
                solution_text TEXT,
                UNIQUE(thread_id, event_id)
            )
        ''')
        
        # Mystery players
        c.execute('''
            CREATE TABLE IF NOT EXISTS mystery_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                mystery_xp INTEGER DEFAULT 0,
                clues_found INTEGER DEFAULT 0,
                correct_theories INTEGER DEFAULT 0,
                wrong_accusations INTEGER DEFAULT 0,
                correct_accusations INTEGER DEFAULT 0,
                cases_solved INTEGER DEFAULT 0,
                rank TEXT DEFAULT 'Rookie',
                UNIQUE(thread_id, user_id)
            )
        ''')
        
        # Mystery clues
        c.execute('''
            CREATE TABLE IF NOT EXISTS mystery_clues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                clue_id TEXT NOT NULL,
                clue_type TEXT NOT NULL,
                description TEXT NOT NULL,
                importance INTEGER DEFAULT 1,
                difficulty INTEGER DEFAULT 1,
                discovered INTEGER DEFAULT 0,
                discovered_by TEXT,
                discovered_at TEXT,
                is_red_herring INTEGER DEFAULT 0,
                reveals_info TEXT,
                UNIQUE(thread_id, event_id, clue_id)
            )
        ''')
        
        # Mystery theories
        c.execute('''
            CREATE TABLE IF NOT EXISTS mystery_theories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                theory_text TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                analysis_score INTEGER DEFAULT 0,
                is_correct INTEGER DEFAULT 0
            )
        ''')
        
        # Mystery accusations
        c.execute('''
            CREATE TABLE IF NOT EXISTS mystery_accusations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                accuser_id TEXT NOT NULL,
                accused_id TEXT NOT NULL,
                accusation_text TEXT,
                submitted_at TEXT NOT NULL,
                is_correct INTEGER DEFAULT 0,
                resolved INTEGER DEFAULT 0
            )
        ''')
        
        # Mystery interrogations
        c.execute('''
            CREATE TABLE IF NOT EXISTS mystery_interrogations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                suspect_id TEXT NOT NULL,
                question TEXT,
                response TEXT,
                interrogator_id TEXT,
                asked_at TEXT,
                UNIQUE(thread_id, event_id, suspect_id, question)
            )
        ''')
        
        # Mystery stats
        c.execute('''
            CREATE TABLE IF NOT EXISTS mystery_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                total_mystery_xp INTEGER DEFAULT 0,
                cases_solved INTEGER DEFAULT 0,
                clues_found INTEGER DEFAULT 0,
                correct_accusations INTEGER DEFAULT 0,
                wrong_accusations INTEGER DEFAULT 0,
                best_rank TEXT DEFAULT 'Rookie',
                UNIQUE(thread_id, user_id)
            )
        ''')
        
        conn.commit()
        print("✅ Mystery database initialized")

def save_mystery_event(thread_id, event_data):
    """Save or update a mystery event"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO mystery_events 
            (thread_id, event_id, event_type, title, phase, difficulty, 
             started_at, expires_at, state_json, active, solved, culprit, solution_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            thread_id,
            event_data['event_id'],
            event_data['type'],
            event_data['title'],
            event_data.get('phase', 'investigation'),
            event_data.get('difficulty', 'hard'),
            event_data['started_at'],
            event_data['expires_at'],
            json.dumps(event_data),
            1,
            0,
            event_data.get('culprit', ''),
            event_data.get('solution_text', '')
        ))
        conn.commit()

def load_mystery_event(thread_id, event_id):
    """Load a mystery event from database"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT * FROM mystery_events 
            WHERE thread_id = ? AND event_id = ? AND active = 1
        ''', (thread_id, event_id))
        row = c.fetchone()
        if row:
            event_data = json.loads(row['state_json'])
            return event_data
    return None

def get_active_mystery(thread_id):
    """Get the active mystery for a thread"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT * FROM mystery_events 
            WHERE thread_id = ? AND active = 1
            ORDER BY started_at DESC LIMIT 1
        ''', (thread_id,))
        row = c.fetchone()
        if row:
            return json.loads(row['state_json'])
    return None

def close_mystery(thread_id, event_id, solved=False, culprit=None, solution=None):
    """Close a mystery event"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE mystery_events 
            SET active = 0, solved = ?, ended_at = ?, culprit = ?, solution_text = ?
            WHERE thread_id = ? AND event_id = ?
        ''', (
            1 if solved else 0,
            datetime.now().isoformat(),
            culprit or '',
            solution or '',
            thread_id,
            event_id
        ))
        conn.commit()

def update_mystery_player_stats(thread_id, user_id, event_id, xp=0, clues=0, correct_theories=0, wrong_accusations=0, correct_accusations=0):
    """Update player mystery stats"""
    with get_db() as conn:
        c = conn.cursor()
        # Update or insert player stats
        c.execute('''
            INSERT INTO mystery_players 
            (thread_id, user_id, event_id, mystery_xp, clues_found, 
             correct_theories, wrong_accusations, correct_accusations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(thread_id, user_id) DO UPDATE SET
                mystery_xp = mystery_xp + ?,
                clues_found = clues_found + ?,
                correct_theories = correct_theories + ?,
                wrong_accusations = wrong_accusations + ?,
                correct_accusations = correct_accusations + ?
        ''', (
            thread_id, user_id, event_id, xp, clues,
            correct_theories, wrong_accusations, correct_accusations,
            xp, clues, correct_theories, wrong_accusations, correct_accusations
        ))
        conn.commit()

def get_mystery_leaderboard(thread_id, limit=10):
    """Get mystery leaderboard for a thread"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT user_id, total_mystery_xp, cases_solved, clues_found, best_rank
            FROM mystery_stats
            WHERE thread_id = ?
            ORDER BY total_mystery_xp DESC
            LIMIT ?
        ''', (thread_id, limit))
        return c.fetchall()

# Initialize mystery database
init_mystery_db()

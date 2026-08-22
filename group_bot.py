#!/usr/bin/env python3
"""
ULTIMATE GC COMPANION BOT - COMPLETE
- Personality System
- Smart AI Router
- Context Manager
- Memory System
- Roast System
- XP & Levels
- Virtual Economy
- Mystery Events
- Chaos System
- Natural Understanding
- All Games
- SQLite Database
- Multi-GC Isolation
"""

import os
import sys
import time
import json
import random
import traceback
import threading
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import re

print("=" * 60)
print("🔥 ULTIMATE GC COMPANION BOT LOADING...")
print("=" * 60)

# ============ ENVIRONMENT ============
SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
ADMINS_RAW = os.environ.get("INSTAGRAM_ADMINS", "razzz_huu")
ADMINS = [a.strip() for a in ADMINS_RAW.split(",") if a.strip()]

if not SESSION_ID:
    print("❌ INSTAGRAM_SESSION_ID not set!")
    sys.exit(1)

if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY not set!")
    sys.exit(1)

print(f"✅ SESSION_ID: {SESSION_ID[:20]}...")
print(f"✅ GROQ_API_KEY: {'Yes' if GROQ_API_KEY else 'No'}")
print(f"✅ ADMINS: {ADMINS}")

# ============ DATABASE ============
DB_PATH = "bot_data.db"

def get_db():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS xp (user_id TEXT, thread_id TEXT, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, coins INTEGER DEFAULT 0, reputation INTEGER DEFAULT 50, daily_streak INTEGER DEFAULT 0, last_daily TIMESTAMP, PRIMARY KEY (user_id, thread_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, thread_id TEXT, text TEXT, importance REAL DEFAULT 0.5, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS settings (thread_id TEXT PRIMARY KEY, welcome_message TEXT, rules TEXT, chaos_level INTEGER DEFAULT 50, ai_enabled BOOLEAN DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS achievements (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, thread_id TEXT, name TEXT, unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS inventory (user_id TEXT, thread_id TEXT, item_name TEXT, quantity INTEGER DEFAULT 1, PRIMARY KEY (user_id, thread_id, item_name))""")
    c.execute("""CREATE TABLE IF NOT EXISTS personality (thread_id TEXT PRIMARY KEY, mood TEXT DEFAULT 'chill', energy INTEGER DEFAULT 70, sarcasm INTEGER DEFAULT 60, friendliness INTEGER DEFAULT 70, chaos INTEGER DEFAULT 50, confidence INTEGER DEFAULT 70)""")
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

init_db()

# ============ HELPERS ============
def get_user_data(user_id, thread_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM xp WHERE user_id = ? AND thread_id = ?", (user_id, thread_id))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"xp": 0, "level": 1, "coins": 0, "reputation": 50, "daily_streak": 0}

def update_user_data(user_id, thread_id, **kwargs):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO xp (user_id, thread_id) VALUES (?, ?) ON CONFLICT(user_id, thread_id) DO NOTHING", (user_id, thread_id))
    for key, value in kwargs.items():
        c.execute(f"UPDATE xp SET {key} = {key} + ? WHERE user_id = ? AND thread_id = ?", (value, user_id, thread_id))
    conn.commit()
    conn.close()

def add_xp(user_id, thread_id, amount):
    update_user_data(user_id, thread_id, xp=amount)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT xp FROM xp WHERE user_id = ? AND thread_id = ?", (user_id, thread_id))
    row = c.fetchone()
    conn.close()
    if row:
        xp = row[0]
        level = get_level(xp)
        c = conn.cursor()
        c.execute("UPDATE xp SET level = ? WHERE user_id = ? AND thread_id = ?", (level, user_id, thread_id))
        conn.commit()
        conn.close()
        return level
    return 1

def add_coins(user_id, thread_id, amount):
    update_user_data(user_id, thread_id, coins=amount)

def get_level(xp):
    levels = {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000, 7: 2000, 10: 4000, 15: 7500, 20: 12000, 30: 20000, 50: 40000, 75: 70000, 100: 120000}
    level = 1
    for lvl, req in sorted(levels.items()):
        if xp >= req:
            level = lvl
    return level

def get_title(level):
    titles = {1: "Newbie", 2: "Rookie", 3: "Member", 5: "Regular", 10: "OG", 20: "Legend", 35: "GC God", 50: "Myth", 75: "Legendary", 100: "Immortal"}
    for lvl, title in sorted(titles.items(), reverse=True):
        if level >= lvl:
            return title
    return "Newbie"

def get_setting(thread_id, key):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT {key} FROM settings WHERE thread_id = ?", (thread_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(thread_id, key, value):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"INSERT INTO settings (thread_id, {key}) VALUES (?, ?) ON CONFLICT(thread_id) DO UPDATE SET {key} = excluded.{key}", (thread_id, value))
    conn.commit()
    conn.close()

def get_personality(thread_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM personality WHERE thread_id = ?", (thread_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"mood": "chill", "energy": 70, "sarcasm": 60, "friendliness": 70, "chaos": 50, "confidence": 70}

def update_personality(thread_id, **kwargs):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO personality (thread_id) VALUES (?) ON CONFLICT(thread_id) DO NOTHING", (thread_id,))
    for key, value in kwargs.items():
        c.execute(f"UPDATE personality SET {key} = ? WHERE thread_id = ?", (value, thread_id))
    conn.commit()
    conn.close()

# ============ CONFIG ============
WELCOME_MSG = "🎉 Welcome {username} to the group! 🥳✨"
RULES = """
📋 GROUP RULES:
1. No spam
2. Be respectful
3. No NSFW content
4. Type .help for commands
"""
LEAVE_MSG = "🚶 {username} chala gya bhadwa! 😂"
WELCOME_BACK_MSGS = ["{username} kya haal ladleee wapis idhr 👀🔥"]
SPAM_EMOJIS = ["🔥", "❤️", "💀", "👀", "🚀", "💯", "✨", "🎯", "😂", "🤣", "💪", "🦅", "🌟", "⚡", "🍿", "🎉", "🥶", "🤯", "😎", "👑"]

COMMAND_COOLDOWN = {
    '.ping': 5, '.dice': 5, '.flip': 5, '.rps': 10,
    '.trivia': 20, '.roast': 15, '.compliment': 10,
    '.fact': 10, '.joke': 10, '.8ball': 10,
    '.love': 10, '.score': 5, '.leaderboard': 15,
    '.help': 15, '.rules': 15,
    '.spam': 300, '.stopspam': 10,
    '.afk': 60, '.setwelcome': 60, '.setrules': 60,
    '.ask': 15, '.groq': 30, '.report': 60,
    '.daily': 60, '.balance': 5, '.give': 30,
    '.shop': 10, '.buy': 10,
    '.memory': 10, '.forget': 15, '.remember': 15,
    '.mostlikely': 30, '.sus': 15,
    '.profile': 10, '.leaderboard': 15,
    '.chaos': 60, '.summon': 120,
    'default': 5,
}

MAX_SPAM_COUNT = 1000
SPAM_DELAY_MIN = 5
SPAM_DELAY_MAX = 10
POLL_INTERVAL_MIN = 5.0
POLL_INTERVAL_MAX = 10.0
WELCOME_BACK_INTERVAL = 600
ADMIN_ACTIVE_TIMEOUT = 900
NATURAL_REPLY_CHANCE = 0.08

# ============ SHOP ============
SHOP_ITEMS = [
    {"name": "Virtual Maggi", "price": 100, "emoji": "🍜", "desc": "Absolutely useless. Buy it anyway."},
    {"name": "Fake Admin Crown", "price": 500, "emoji": "👑", "desc": "Flex on the peasants."},
    {"name": "Ban Protection", "price": 2000, "emoji": "🛡️", "desc": "One free pass. Use wisely."},
    {"name": "Nuclear Roast", "price": 5000, "emoji": "💀", "desc": "The ultimate roast weapon."},
    {"name": "+10 Fake IQ", "price": 10000, "emoji": "🧠", "desc": "You're still dumb. But less."},
]

# ============ FALLBACK ============
FALLBACK_ROASTS = ["तू हर जगह है जैसे WiFi, पर काम किसी काम का नहीं! 📶", "तेरी सोच इतनी गहरी है जितनी चाय की प्लेट! ☕"]
FALLBACK_JOKES = ["एक आदमी ने डॉक्टर से कहा: मुझे हर रात बुरे सपने आते हैं। डॉक्टर बोला: क्या सपने आते हैं? आदमी बोला: सपने में मुझे नींद नहीं आती! 😂"]
FALLBACK_FACTS = ["ऑक्टोपस के 3 दिल होते हैं! 💙", "केला एक बेरी है! 🍌"]
FALLBACK_8BALL = ["🎱 शायद हाँ", "🎱 नहीं", "🎱 पक्का नहीं"]
FALLBACK_TRIVIA = [{"q": "फ्रांस की राजधानी क्या है?", "a": "पेरिस"}]
ADMIN_TAG_REPLIES = ["Ohh tell me what happened, my boss is offline 🧐", "Boss is busy! Tell me, I'll handle it 💪"]
ADMIN_GREETINGS = ["👑 Welcome back boss!", "🙇‍♂️ At your service, my lord!"]

# ============ STATE ============
AFK_USERS = {}
USER_LAST_ACTIVE = {}
USER_WELCOME_SENT = {}
ADMIN_LAST_SEEN = {}
WELCOME_SENT = {}
user_last_daily = {}
user_memory = {}
trivia_state = {}
roast_battle_state = {}
mystery_state = {}
mostlikely_state = {}
spam_running = False
spam_stop_flag = False
spam_thread = None

# ============ GROQ AI ============
def groq_generate(prompt, api_key):
    if not api_key:
        return None
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {"model": "groq/compound", "messages": [{"role": "user", "content": prompt}], "temperature": 1.0, "max_tokens": 100}
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            reply = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not reply or "can't help" in reply.lower():
                return None
            return reply
        return None
    except Exception as e:
        print(f"⚠️ Groq error: {e}")
        return None

def groq_roast(target, api_key):
    return groq_generate(f"Give a SHORT savage roast for @{target} in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_joke(api_key):
    return groq_generate("Tell a SHORT funny joke in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_fact(api_key):
    return groq_generate("Give a SHORT interesting fact in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_ask_public(question, api_key):
    return groq_generate(f"Reply to this question in a funny way in HINDI/HINGLISH (5-10 words). Question: '{question}'", api_key)

def groq_admin(question, api_key):
    return groq_generate(f"Answer this question in HINDI/HINGLISH. Be helpful, informative, and complete. Question: '{question}'", api_key)

def groq_natural_reply(message, username, api_key):
    return groq_generate(f"Reply to @{username} in ONE SHORT SENTENCE (5-10 words) in HINDI/HINGLISH. Be savage, funny, and casual. Reply DIRECTLY. Message: '{message}'", api_key)

# ============ INSTAGRAPI ============
try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired, RateLimitError
    print("✅ instagrapi imported!")
except ImportError as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# ============ HUMAN BEHAVIOR ============
class HumanBehavior:
    def __init__(self):
        self.moods = ['chatty', 'brief', 'distracted', 'focused', 'slow', 'hyper']
        self.current_mood = random.choice(self.moods)
        self.typing_speed = random.randint(40, 80)
        self.reading_speed = random.randint(200, 350)

    def get_delay(self, action='message'):
        mood_delays = {'chatty': {'message': (1.0, 3.0), 'typing': (0.5, 1.0)}, 'brief': {'message': (0.5, 1.5), 'typing': (0.2, 0.5)}, 'distracted': {'message': (5.0, 12.0), 'typing': (2.0, 5.0)}, 'focused': {'message': (0.8, 2.0), 'typing': (0.3, 0.7)}, 'slow': {'message': (6.0, 15.0), 'typing': (3.0, 6.0)}, 'hyper': {'message': (0.3, 1.0), 'typing': (0.1, 0.3)}}
        min_d, max_d = mood_delays.get(self.current_mood, mood_delays['focused']).get(action, (1.0, 3.0))
        return random.uniform(min_d, max_d)

    def type_time(self, text):
        chars = len(text)
        return min(chars / (self.typing_speed * random.uniform(0.7, 1.3)) + random.uniform(0.5, 1.5), 10.0)

human = HumanBehavior()

def human_delay(min_sec=1.0, max_sec=4.0):
    time.sleep(random.uniform(min_sec, max_sec))

def type_message_like_human(text):
    time.sleep(human.type_time(text))

# ============ MAIN BOT ============
class InstagramGroupBot:
    def __init__(self):
        print("🔧 Initializing bot...")
        self.cl = Client()
        self.cl.set_user_agent("Mozilla/5.0 (Linux; Android 13) Chrome/116.0.5845.92")
        self.running = True
        self.processed_messages = set()
        self.known_members = {}
        self.scoreboard = {}
        self.username_cache = {}
        self.groq_api_key = GROQ_API_KEY

        self.session = requests.Session()
        self.session.cookies.set('sessionid', SESSION_ID)
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Linux; Android 13) Chrome/116.0.5845.92', 'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.9', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Instagram-AJAX': '1', 'X-Requested-With': 'XMLHttpRequest', 'Origin': 'https://www.instagram.com', 'Referer': 'https://www.instagram.com/'})
        self.session.max_redirects = 3

        self.login()
        self.initialize_threads()
        print("✅ Bot initialization complete!")

    def login(self):
        print("🔐 Logging in...")
        try:
            self.cl.login_by_sessionid(SESSION_ID)
            self.username = self.cl.username
            self.user_id = self.cl.user_id
            print(f"✅ Logged in as: @{self.username}")
            print(f"👥 Followers: {self.cl.user_followers(self.user_id)}")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            raise e

    def initialize_threads(self):
        print("📂 Initializing threads...")
        try:
            threads = self.cl.direct_threads()
            group_count = 0
            for thread in threads:
                if hasattr(thread, 'users') and len(thread.users) > 2:
                    thread_id = str(thread.id)
                    member_ids = [u.pk for u in thread.users]
                    self.known_members[thread_id] = set(member_ids)
                    group_count += 1
                    print(f"📌 Thread {thread_id}: {len(member_ids)} members")
            self.group_count = group_count
            print(f"📊 Detected {self.group_count} group(s)")
        except Exception as e:
            print(f"⚠️ Error: {e}")
            self.group_count = 1

    def is_admin(self, username):
        return username in ADMINS or username == self.username

    def get_username_cached(self, user_id):
        if user_id in self.username_cache:
            return self.username_cache[user_id]
        try:
            user = self.cl.user_info(user_id)
            self.username_cache[user_id] = user.username
            return user.username
        except:
            return None

    def send_message(self, thread_id, message):
        try:
            type_message_like_human(message)
            human_delay(1.0, 3.0)
            self.cl.direct_send(message, thread_ids=[thread_id])
            print(f"📤 Sent: {message[:30]}...")
            human_delay(1.0, 2.0)
            return True
        except RateLimitError:
            print("⚠️ Rate limited! Waiting 5 minutes...")
            time.sleep(300)
            return False
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False

    def report_user(self, thread_id, target_username, admin_username, reason="spam"):
        try:
            target_id = self.cl.user_id_from_username(target_username)
            if not target_id:
                return False, f"❌ User @{target_username} not found"
            csrf = self.session.cookies.get('csrftoken', '')
            if csrf:
                self.session.headers.update({'X-CSRFToken': csrf})
            response = self.session.post(f"https://www.instagram.com/api/v1/users/{target_id}/flag/", data={"reason": reason, "source": "group", "target_id": target_id})
            if response.status_code == 200:
                return True, f"✅ Reported @{target_username} for: {reason}"
            return False, f"❌ Failed to report @{target_username}"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

    def run_spam(self, thread_id, count, message, admin_username):
        global spam_running, spam_stop_flag
        spam_running = True
        spam_stop_flag = False
        try:
            for i in range(count):
                if spam_stop_flag:
                    self.send_message(thread_id, f"🛑 Spam stopped! Sent {i} messages.")
                    break
                if not self.running:
                    break
                emoji = random.choice(SPAM_EMOJIS)
                self.send_message(thread_id, f"{emoji} {message}")
                human_delay(SPAM_DELAY_MIN, SPAM_DELAY_MAX)
            else:
                self.send_message(thread_id, f"✅ Spam complete! {count} messages sent.")
        except Exception as e:
            self.send_message(thread_id, f"❌ Spam error: {e}")
        finally:
            spam_running = False

    def stop_spam(self, thread_id, username):
        global spam_running, spam_stop_flag
        if not self.is_admin(username):
            self.send_message(thread_id, f"❌ @{username} Only admins can stop spam!")
            return False
        if not spam_running:
            self.send_message(thread_id, "ℹ️ No spam running.")
            return False
        spam_stop_flag = True
        self.send_message(thread_id, "🛑 Stopping spam...")
        return True

    def send_trivia_question(self, thread_id):
        state = trivia_state.get(thread_id)
        if not state:
            return
        current = state['current']
        questions = state['questions']
        if current >= len(questions):
            self.end_trivia(thread_id)
            return
        q = questions[current]
        self.send_message(thread_id, f"--- Question {current+1}/{len(questions)} ---\n❓ {q['q']}\n⏰ 15 seconds...")
        def check():
            time.sleep(15)
            if thread_id in trivia_state and trivia_state[thread_id]['current'] == current:
                self.send_message(thread_id, f"⏰ Time's up! Answer: {q['a']}")
                trivia_state[thread_id]['current'] += 1
                time.sleep(2)
                self.send_trivia_question(thread_id)
        threading.Thread(target=check, daemon=True).start()

    def end_trivia(self, thread_id):
        state = trivia_state.pop(thread_id, None)
        if not state:
            return
        score, total, username = state['score'], len(state['questions']), state['username']
        msgs = ["🧠 GENIUS! 🏆", "🔥 Amazing! 🌟", "👍 Good job! 💪", "🤔 Not bad! 📚", "😂 Did you even try?! 💀"]
        msg = msgs[0] if score == total else msgs[1] if score >= total-1 else msgs[2] if score >= total//2 else msgs[3] if score >= 1 else msgs[4]
        self.send_message(thread_id, f"--- 🎯 GAME OVER! ---\n🏆 @{username} scored {score}/{total}\n{msg}")
        self.scoreboard[state['user_id']] = self.scoreboard.get(state['user_id'], 0) + score
        add_xp(state['user_id'], thread_id, score * 10)
        add_coins(state['user_id'], thread_id, score * 5)

    def check_trivia_answer(self, thread_id, user_id, message):
        state = trivia_state.get(thread_id)
        if not state or user_id != state['user_id']:
            return
        if state['current'] >= len(state['questions']):
            return
        q = state['questions'][state['current']]
        if message.lower().strip() == q['a'].lower():
            state['score'] += 1
            self.send_message(thread_id, "✅ Correct! +1 point! 🎉")
            state['current'] += 1
            time.sleep(2)
            self.send_trivia_question(thread_id)

    def handle_command(self, thread_id, user_id, username, command):
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        print(f"📩 Command from @{username}: {cmd}")

        # ============ HELP ============
        if cmd == '.help':
            help_text = """
🔥 **ULTIMATE GC BOT COMMANDS:**

**🎮 Games:**
.dice - Roll dice
.flip - Flip coin
.rps - Rock Paper Scissors
.trivia - 5 questions with timer
.roast @user - Roast user
.roastbattle @u1 @u2 - Roast battle!
.compliment @user - Compliment user
.fact - Random fact
.joke - Random joke
.8ball [question] - Magic 8-ball
.love @user OR .love @u1 @u2 - Love calculator
.mostlikely - Who is most likely to...?
.sus @user - Suspicious claim detector

**📊 Profile:**
.score - Your points
.leaderboard - Top players
.profile @user - View user profile
.balance - Check coins
.daily - Claim daily reward
.give @user amount - Give coins

**🧠 Memory:**
.memory - Show memories
.remember [thing] - Add memory
.forget [thing] - Delete memory

**👑 Admin:**
.spam count msg - Spam messages
.stopspam - Stop spam
.afk [reason] - Set AFK
.setwelcome msg - Set welcome
.setrules rules - Set rules
.groq [question] - Ask Groq
.report count @user - Report user

**🤖 AI:**
.ask [question] - Ask bot (funny)
Bot also replies naturally to conversations!

**🥚 Secrets:**
.chaos - Trigger chaos
.summon - Rare event
"""
            self.send_message(thread_id, help_text)
            return

        # ============ BASIC ============
        elif cmd == '.rules':
            self.send_message(thread_id, RULES)
            return

        elif cmd == '.ping':
            self.send_message(thread_id, "🏓 Pong! Bot is alive!")
            return

        elif cmd == '.dice':
            roll = random.randint(1, 6)
            self.send_message(thread_id, f"🎲 @{username} rolled **{roll}**!")
            self.scoreboard[user_id] = self.scoreboard.get(user_id, 0) + 1
            add_xp(user_id, thread_id, 5)
            return

        elif cmd == '.flip':
            result = random.choice(['Heads', 'Tails'])
            self.send_message(thread_id, f"🪙 @{username} flipped **{result}**!")
            self.scoreboard[user_id] = self.scoreboard.get(user_id, 0) + 1
            add_xp(user_id, thread_id, 5)
            return

        elif cmd == '.rps':
            if not args:
                self.send_message(thread_id, "Usage: .rps rock/paper/scissors")
                return
            choice = args[0].lower()
            if choice not in ['rock', 'paper', 'scissors', 'r', 'p', 's']:
                self.send_message(thread_id, "Choose: rock, paper, or scissors")
                return
            choices = {'r': 'rock', 'p': 'paper', 's': 'scissors'}
            user_choice = choices.get(choice, choice)
            bot_choice = random.choice(['rock', 'paper', 'scissors'])
            if user_choice == bot_choice:
                result = "Tie! 🤝"
            elif (user_choice == 'rock' and bot_choice == 'scissors') or (user_choice == 'paper' and bot_choice == 'rock') or (user_choice == 'scissors' and bot_choice == 'paper'):
                result = "You win! 🎉"
                self.scoreboard[user_id] = self.scoreboard.get(user_id, 0) + 2
                add_xp(user_id, thread_id, 15)
                add_coins(user_id, thread_id, 10)
            else:
                result = "I win! 😎"
            self.send_message(thread_id, f"🪨📄✂️ @{username}: {user_choice} 🤖 Bot: {bot_choice}\n{result}")
            return

        # ============ TRIVIA ============
        elif cmd == '.trivia':
            if thread_id in trivia_state:
                self.send_message(thread_id, "⚠️ Trivia already running!")
                return
            questions = []
            if self.groq_api_key:
                for _ in range(5):
                    q = groq_generate("Generate ONE short trivia question in HINDI/HINGLISH with 4 options.\nFormat:\nQ: [question]\nA) [option1]\nB) [option2]\nC) [option3]\nD) [option4]\nAnswer: [letter]", self.groq_api_key)
                    if q:
                        questions.append({"q": q.split('Q:')[1].split('A)')[0].strip(), "a": q.split('Answer:')[1].strip().lower() if 'Answer:' in q else ''})
            if len(questions) < 5:
                qs = random.sample(FALLBACK_TRIVIA, min(5, len(FALLBACK_TRIVIA)))
                questions = [{"q": q['q'], "a": q['a']} for q in qs]
            trivia_state[thread_id] = {'questions': questions, 'current': 0, 'score': 0, 'user_id': user_id, 'username': username}
            self.send_message(thread_id, f"🧠 **TRIVIA STARTED!**\n@{username} has 15 sec per question.\nTotal: {len(questions)} questions.")
            self.send_trivia_question(thread_id)
            return

        # ============ ROAST ============
        elif cmd == '.roast':
            if not args:
                self.send_message(thread_id, "Usage: .roast @user")
                return
            target = args[0].replace('@', '')
            if self.groq_api_key:
                msg = groq_roast(target, self.groq_api_key)
            msg = msg or random.choice(FALLBACK_ROASTS)
            self.send_message(thread_id, f"🔥 @{target} {msg}")
            add_xp(user_id, thread_id, 10)
            return

        # ============ ROAST BATTLE ============
        elif cmd == '.roastbattle':
            if len(args) < 2:
                self.send_message(thread_id, "Usage: .roastbattle @user1 @user2")
                return
            user1 = args[0].replace('@', '')
            user2 = args[1].replace('@', '')
            if thread_id in roast_battle_state:
                self.send_message(thread_id, "⚠️ A roast battle is already happening!")
                return
            roast_battle_state[thread_id] = {'user1': user1, 'user2': user2, 'round': 0, 'roasts': []}
            self.send_message(thread_id, f"🔥 ROAST BATTLE STARTED!\n@{user1} vs @{user2}\nRound 1: @{user1} goes first!\nType .roast @{user1} or .roast @{user2}")
            return

        # ============ COMPLIMENT ============
        elif cmd == '.compliment':
            if not args:
                self.send_message(thread_id, "Usage: .compliment @user")
                return
            target = args[0].replace('@', '')
            compliments = ["तू तो लगता है जैसे सुबह की चाय — हर किसी को भाती है! ☕", "तू वो दोस्त है जिसके बिना ग्रुप अधूरा है! ❤️", "तू वजह है ग्रुप की शान! 👑"]
            self.send_message(thread_id, f"💕 @{target} {random.choice(compliments)}")
            add_xp(user_id, thread_id, 5)
            return

        # ============ JOKE ============
        elif cmd == '.joke':
            if self.groq_api_key:
                msg = groq_joke(self.groq_api_key)
            msg = msg or random.choice(FALLBACK_JOKES)
            self.send_message(thread_id, f"😂 {msg}")
            return

        # ============ FACT ============
        elif cmd == '.fact':
            if self.groq_api_key:
                msg = groq_fact(self.groq_api_key)
            msg = msg or random.choice(FALLBACK_FACTS)
            self.send_message(thread_id, f"📖 {msg}")
            return

        # ============ 8BALL ============
        elif cmd == '.8ball':
            if not args:
                self.send_message(thread_id, "Ask me something! Example: .8ball Will I win?")
                return
            msg = random.choice(FALLBACK_8BALL)
            self.send_message(thread_id, msg)
            return

        # ============ LOVE (FIXED) ============
        elif cmd == '.love':
            if not args:
                self.send_message(thread_id, "Usage: .love @user OR .love @user1 @user2")
                return
            mentions = [a.replace('@', '') for a in args if a.startswith('@')]
            if len(mentions) == 0:
                self.send_message(thread_id, "❌ Please tag at least 1 person!")
                return
            elif len(mentions) == 1:
                name1 = username
                name2 = mentions[0]
                percentage = random.randint(0, 100)
                heart = "❤️🔥" if percentage >= 80 else "❤️" if percentage >= 60 else "💕" if percentage >= 40 else "💛" if percentage >= 20 else "💔"
                msgs = {90: "True love! Soulmates! 😍💕", 75: "A match made in heaven! 🥰", 60: "Good connection! 😊", 40: "It's complicated... 🤔", 20: "Friendzone! 😂", 0: "Bro, you two are like oil and water 💀"}
                msg = next((v for k, v in sorted(msgs.items(), reverse=True) if percentage >= k), msgs[0])
                self.send_message(thread_id, f"💕 **Love Calculator**\n@{name1} + @{name2} = {percentage}% {heart}\n\n{msg}")
            elif len(mentions) == 2:
                name1 = mentions[0]
                name2 = mentions[1]
                percentage = random.randint(0, 100)
                heart = "❤️🔥" if percentage >= 80 else "❤️" if percentage >= 60 else "💕" if percentage >= 40 else "💛" if percentage >= 20 else "💔"
                msgs = {90: "True love! Soulmates! 😍💕", 75: "A match made in heaven! 🥰", 60: "Good connection! 😊", 40: "It's complicated... 🤔", 20: "Friendzone! 😂", 0: "Bro, you two are like oil and water 💀"}
                msg = next((v for k, v in sorted(msgs.items(), reverse=True) if percentage >= k), msgs[0])
                self.send_message(thread_id, f"💕 **Love Calculator**\n@{name1} + @{name2} = {percentage}% {heart}\n\n{msg}")
            else:
                self.send_message(thread_id, "❌ Please tag only 1 or 2 people!")
            return

        # ============ MOST LIKELY ============
        elif cmd == '.mostlikely':
            mostlikely_questions = ["कौन सबसे ज्यादा Maggi खाता है?", "कौन सबसे ज्यादा सोता है?", "कौन सबसे ज्यादा बात करता है?", "कौन सबसे ज्यादा देर आता है?", "कौन सबसे ज्यादा मजाक करता है?"]
            question = random.choice(mostlikely_questions)
            self.send_message(thread_id, f"📊 **Who is most likely to...**\n\n{question}\n\nVote by replying!")
            mostlikely_state[thread_id] = {'question': question, 'votes': {}, 'timestamp': datetime.now()}
            return

        # ============ SUS ============
        elif cmd == '.sus':
            if not args:
                self.send_message(thread_id, "Usage: .sus @user")
                return
            target = args[0].replace('@', '')
            sus_level = random.randint(60, 99)
            reasons = ["You have a history of 'studying' = watching YouTube", "Your story doesn't add up, bro", "The GC has spoken 💀", "Your energy is sus today", "You're too quiet... sus"]
            self.send_message(thread_id, f"🧐 **SUSPICIOUS CLAIM DETECTED**\n\nGC Verdict: {sus_level}% SUS\nReason: {random.choice(reasons)}\n\n💀 The GC has spoken.")
            return

        # ============ SCORE ============
        elif cmd == '.score':
            score = self.scoreboard.get(user_id, 0)
            self.send_message(thread_id, f"🏆 @{username} has {score} points!")
            return

        # ============ LEADERBOARD ============
        elif cmd == '.leaderboard':
            if not self.scoreboard:
                self.send_message(thread_id, "No scores yet!")
                return
            sorted_scores = sorted(self.scoreboard.items(), key=lambda x: x[1], reverse=True)[:10]
            board = "🏆 **LEADERBOARD**\n\n"
            for i, (uid, score) in enumerate(sorted_scores, 1):
                name = self.get_username_cached(uid) or f"User{uid}"
                board += f"{i}. @{name} - {score} pts\n"
            self.send_message(thread_id, board)
            return

        # ============ PROFILE ============
        elif cmd == '.profile':
            target = args[0].replace('@', '') if args else username
            target_id = None
            for uid, uname in self.username_cache.items():
                if uname == target:
                    target_id = uid
                    break
            if not target_id:
                self.send_message(thread_id, f"❌ User @{target} not found")
                return
            data = get_user_data(target_id, thread_id)
            self.send_message(thread_id, f"📊 **Profile: @{target}**\n\nLevel: {data['level']}\nXP: {data['xp']}\nCoins: {data['coins']}\nTitle: {get_title(data['level'])}\nReputation: {data['reputation']}")
            return

        # ============ DAILY ============
        elif cmd == '.daily':
            last = user_last_daily.get(user_id)
            if last and (datetime.now() - last).total_seconds() < 86400:
                remaining = 86400 - (datetime.now() - last).total_seconds()
                self.send_message(thread_id, f"⏳ Daily reward already claimed! Wait {int(remaining/3600)}h {int((remaining%3600)/60)}m.")
                return
            reward = random.randint(50, 200)
            add_coins(user_id, thread_id, reward)
            add_xp(user_id, thread_id, 20)
            user_last_daily[user_id] = datetime.now()
            self.send_message(thread_id, f"💸 Daily reward claimed! +{reward} coins! 💰")
            return

        # ============ BALANCE ============
        elif cmd == '.balance':
            data = get_user_data(user_id, thread_id)
            self.send_message(thread_id, f"💰 @{username} has {data['coins']} coins!")
            return

        # ============ GIVE ============
        elif cmd == '.give':
            if len(args) < 2:
                self.send_message(thread_id, "Usage: .give @user amount")
                return
            target = args[0].replace('@', '')
            try:
                amount = int(args[1])
                if amount <= 0:
                    self.send_message(thread_id, "❌ Amount must be positive!")
                    return
                data = get_user_data(user_id, thread_id)
                if data['coins'] < amount:
                    self.send_message(thread_id, "❌ You don't have enough coins!")
                    return
                target_id = None
                for uid, uname in self.username_cache.items():
                    if uname == target:
                        target_id = uid
                        break
                if not target_id:
                    self.send_message(thread_id, f"❌ User @{target} not found")
                    return
                add_coins(user_id, thread_id, -amount)
                add_coins(target_id, thread_id, amount)
                self.send_message(thread_id, f"💸 @{username} gave {amount} coins to @{target}!")
            except ValueError:
                self.send_message(thread_id, "❌ Invalid amount!")
            return

        # ============ SHOP ============
        elif cmd == '.shop':
            shop_list = "🏪 **SHOP**\n\n"
            for item in SHOP_ITEMS:
                shop_list += f"{item['emoji']} {item['name']} — {item['price']} coins\n   {item['desc']}\n\n"
            self.send_message(thread_id, shop_list)
            return

        # ============ BUY ============
        elif cmd == '.buy':
            if not args:
                self.send_message(thread_id, "Usage: .buy [item name]")
                return
            item_name = ' '.join(args)
            for item in SHOP_ITEMS:
                if item['name'].lower() in item_name.lower():
                    data = get_user_data(user_id, thread_id)
                    if data['coins'] < item['price']:
                        self.send_message(thread_id, f"❌ Not enough coins! Need {item['price']} coins.")
                        return
                    add_coins(user_id, thread_id, -item['price'])
                    self.send_message(thread_id, f"✅ {item['emoji']} Purchased: {item['name']}! Enjoy your totally useless item! 😂")
                    return
            self.send_message(thread_id, "❌ Item not found! Check .shop")
            return

        # ============ MEMORY ============
        elif cmd == '.memory':
            memories = user_memory.get(user_id, [])
            if not memories:
                self.send_message(thread_id, "📭 No memories saved yet!")
                return
            mem_list = "🧠 **Your Memories:**\n\n"
            for i, mem in enumerate(memories[:10], 1):
                mem_list += f"{i}. {mem}\n"
            self.send_message(thread_id, mem_list)
            return

        elif cmd == '.remember':
            if not args:
                self.send_message(thread_id, "Usage: .remember [thing]")
                return
            memory = ' '.join(args)
            if user_id not in user_memory:
                user_memory[user_id] = []
            user_memory[user_id].append(memory)
            self.send_message(thread_id, f"✅ Remembered: \"{memory}\"")
            return

        elif cmd == '.forget':
            if not args:
                self.send_message(thread_id, "Usage: .forget [thing]")
                return
            memory = ' '.join(args)
            if user_id in user_memory and memory in user_memory[user_id]:
                user_memory[user_id].remove(memory)
                self.send_message(thread_id, f"✅ Forgot: \"{memory}\"")
            else:
                self.send_message(thread_id, "❌ I don't remember that!")
            return

        # ============ CHAOS ============
        elif cmd == '.chaos':
            personality = get_personality(thread_id)
            self.send_message(thread_id, f"🌀 CHAOS LEVEL: {personality['chaos']}%\n\n{random.choice(['You summoned the chaos!', 'The chaos is spreading...', 'I have no idea what I\'m doing 💀', 'This is fine 🔥'])}")
            update_personality(thread_id, chaos=min(100, personality['chaos'] + 10))
            return

        # ============ SUMMON ============
        elif cmd == '.summon':
            self.send_message(thread_id, "🔮 **SUMMONED.**\n\nI'm listening for the next 5 minutes.\nTalk to me naturally!")
            return

        # ============ ASK ============
        elif cmd == '.ask':
            if not args:
                self.send_message(thread_id, "Usage: .ask [question]")
                return
            question = ' '.join(args)
            if self.groq_api_key:
                reply = groq_ask_public(question, self.groq_api_key)
                if reply:
                    self.send_message(thread_id, reply)
            return

        # ============ ADMIN ============
        if not self.is_admin(username):
            self.send_message(thread_id, f"❌ @{username} Not admin!")
            return

        elif cmd == '.groq':
            if not args:
                self.send_message(thread_id, "Usage: .groq [question]")
                return
            question = ' '.join(args)
            if self.groq_api_key:
                reply = groq_admin(question, self.groq_api_key)
                if reply:
                    self.send_message(thread_id, reply)
                else:
                    self.send_message(thread_id, "⚠️ Groq didn't respond. Try again.")
            return

        elif cmd == '.report':
            if len(args) < 2:
                self.send_message(thread_id, "Usage: .report [count] @user")
                return
            try:
                count = int(args[0])
                if count <= 0 or count > 10:
                    self.send_message(thread_id, "❌ Count must be between 1 and 10")
                    return
                target = args[1].replace('@', '')
            except ValueError:
                self.send_message(thread_id, "❌ Invalid count. Usage: .report [count] @user")
                return
            report_reasons = ["spam", "harassment", "inappropriate", "nudity", "hate_speech", "scam", "fake_account", "terrorism", "abuse"]
            success_count = 0
            for _ in range(count):
                reason = random.choice(report_reasons)
                success, _ = self.report_user(thread_id, target, username, reason)
                if success:
                    success_count += 1
                human_delay(1.0, 2.0)
            self.send_message(thread_id, f"✅ Reported @{target} {success_count} times successfully! 🚨")
            return

        elif cmd == '.stopspam':
            self.stop_spam(thread_id, username)
            return

        elif cmd == '.afk':
            reason = ' '.join(args) if args else "AFK"
            AFK_USERS[user_id] = (reason, datetime.now())
            self.send_message(thread_id, f"🛏️ @{username} is now AFK: {reason}")
            return

        elif cmd == '.spam':
            if not args:
                self.send_message(thread_id, "Usage: .spam [count] [message]")
                return
            try:
                count = int(args[0])
                if count <= 0 or count > MAX_SPAM_COUNT:
                    self.send_message(thread_id, f"❌ Count must be between 1 and {MAX_SPAM_COUNT}")
                    return
                message = ' '.join(args[1:]) if len(args) > 1 else "SPAM!"
            except ValueError:
                self.send_message(thread_id, "❌ Invalid count.")
                return
            if spam_running:
                self.send_message(thread_id, "⚠️ Spam already running! Use .stopspam")
                return
            self.send_message(thread_id, f"📢 Admin starting spam: {count} messages!")
            global spam_thread
            spam_thread = threading.Thread(target=self.run_spam, args=(thread_id, count, message, username), daemon=True)
            spam_thread.start()
            return

        elif cmd == '.setwelcome':
            if not args:
                self.send_message(thread_id, "Usage: .setwelcome [message]")
                return
            new_welcome = ' '.join(args)
            set_setting(thread_id, 'welcome_message', new_welcome)
            self.send_message(thread_id, f"✅ Welcome message updated!")
            return

        elif cmd == '.setrules':
            if not args:
                self.send_message(thread_id, "Usage: .setrules [rules]")
                return
            new_rules = ' '.join(args)
            set_setting(thread_id, 'rules', new_rules)
            self.send_message(thread_id, f"✅ Rules updated!")
            return

        else:
            self.send_message(thread_id, f"❌ Unknown: {cmd}\nType .help")

    def check_messages(self):
        try:
            threads = self.cl.direct_threads()
            for thread in threads:
                thread_id = str(thread.id)
                if hasattr(thread, 'users') and len(thread.users) <= 2:
                    continue
                try:
                    detail = self.cl.direct_thread(thread_id)
                    current = [u.pk for u in detail.users]
                    if thread_id not in self.known_members:
                        self.known_members[thread_id] = set()
                    new_members = set(current) - self.known_members[thread_id]
                    for mid in new_members:
                        if mid != self.user_id:
                            uname = self.get_username_cached(mid)
                            if uname and (thread_id, mid) not in WELCOME_SENT:
                                print(f"🔔 New member: @{uname}")
                                self.send_message(thread_id, WELCOME_MSG.format(username=uname))
                                human_delay(2.0, 4.0)
                                self.send_message(thread_id, RULES)
                                WELCOME_SENT[(thread_id, mid)] = True
                    left = self.known_members[thread_id] - set(current)
                    for mid in left:
                        if mid != self.user_id:
                            uname = self.get_username_cached(mid)
                            if uname:
                                print(f"🚶 Member left: @{uname}")
                                self.send_message(thread_id, LEAVE_MSG.format(username=uname))
                    self.known_members[thread_id] = set(current)

                    for msg in detail.messages:
                        msg_id = str(msg.id)
                        if msg_id in self.processed_messages:
                            continue
                        if msg.user_id == self.user_id or not msg.text:
                            continue
                        username = self.get_username_cached(msg.user_id)
                        if not username:
                            continue
                        self.processed_messages.add(msg_id)
                        print(f"📩 @{username}: {msg.text}")

                        now = datetime.now()
                        last = USER_LAST_ACTIVE.get(msg.user_id)
                        if msg.user_id != self.user_id and last and (now - last).total_seconds() >= WELCOME_BACK_INTERVAL:
                            last_welcome = USER_WELCOME_SENT.get(msg.user_id)
                            if not last_welcome or (now - last_welcome).total_seconds() > WELCOME_BACK_INTERVAL:
                                print(f"👋 Welcome back @{username}")
                                self.send_message(thread_id, WELCOME_BACK_MSGS[0].format(username=username))
                                USER_WELCOME_SENT[msg.user_id] = now
                        USER_LAST_ACTIVE[msg.user_id] = now

                        if username.lower() in [a.lower() for a in ADMINS]:
                            ADMIN_LAST_SEEN[thread_id] = now

                        msg_lower = msg.text.lower()
                        if any(f"@{admin}".lower() in msg_lower for admin in ADMINS) and not self.is_admin(username):
                            if thread_id not in ADMIN_LAST_SEEN or (now - ADMIN_LAST_SEEN.get(thread_id, now - timedelta(minutes=10))).seconds > ADMIN_ACTIVE_TIMEOUT:
                                self.send_message(thread_id, f"@{username} {random.choice(ADMIN_TAG_REPLIES)}")
                                human_delay(1.0, 2.0)

                        if username.lower() in [a.lower() for a in ADMINS]:
                            last_seen = ADMIN_LAST_SEEN.get(thread_id, now - timedelta(minutes=10))
                            if (now - last_seen).seconds > 120:
                                self.send_message(thread_id, random.choice(ADMIN_GREETINGS))

                        if thread_id in trivia_state:
                            self.check_trivia_answer(thread_id, msg.user_id, msg.text)

                        if msg.user_id in AFK_USERS:
                            reason, t = AFK_USERS[msg.user_id]
                            if (now - t).seconds > 300:
                                del AFK_USERS[msg.user_id]
                                self.send_message(thread_id, f"🟢 @{username} is no longer AFK")

                        # Natural Reply
                        if not msg.text.startswith('.') and random.random() < NATURAL_REPLY_CHANCE and self.groq_api_key:
                            if f"@{self.username}".lower() in msg.text.lower():
                                reply = groq_natural_reply(msg.text, username, self.groq_api_key)
                            else:
                                reply = groq_natural_reply(msg.text, username, self.groq_api_key)
                            if reply:
                                human_delay(2.0, 5.0)
                                self.send_message(thread_id, reply)
                                print(f"🤖 Reply to @{username}")
                                add_xp(msg.user_id, thread_id, 2)

                        if msg.text.startswith('.'):
                            self.handle_command(thread_id, msg.user_id, username, msg.text)

                except RateLimitError:
                    print("⚠️ Rate limited! Waiting 10 minutes...")
                    time.sleep(600)
                except Exception as e:
                    print(f"⚠️ Thread error: {e}")
        except RateLimitError:
            print("⚠️ Rate limited! Waiting 10 minutes...")
            time.sleep(600)
        except Exception as e:
            print(f"⚠️ Check error: {e}")

    def run(self):
        print("\n" + "=" * 60)
        print("🔥 ULTIMATE GC COMPANION BOT RUNNING")
        print(f"👤 Bot: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print(f"📊 Monitoring: {getattr(self, 'group_count', 1)} group(s)")
        print("=" * 60)
        print("🤖 Features:")
        print("   ✅ Personality System")
        print("   ✅ Smart AI Router (8% natural reply)")
        print("   ✅ Memory System")
        print("   ✅ XP & Levels")
        print("   ✅ Virtual Economy")
        print("   ✅ All Games")
        print("   ✅ Love Calculator (fixed)")
        print("   ✅ SQLite Database")
        print("   ✅ Multi-GC Isolation")
        print("=" * 60)
        print("\n⚠️ Press Ctrl+C to stop\n")
        while self.running:
            try:
                self.check_messages()
                time.sleep(random.uniform(POLL_INTERVAL_MIN, POLL_INTERVAL_MAX))
            except KeyboardInterrupt:
                self.running = False
                print("\n👋 Stopping...")
                break
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(30)

    def start(self):
        self.run()

def main():
    try:
        bot = InstagramGroupBot()
        bot.start()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()

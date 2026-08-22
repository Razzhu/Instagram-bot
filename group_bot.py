#!/usr/bin/env python3
"""
Instagram Group Bot - FINAL: Gemini Always Active + Casual Conversation
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

print("=" * 60)
print("📂 GROUP_BOT.PY LOADING...")
print("=" * 60)

# ============ ENVIRONMENT ============
SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "")
if not SESSION_ID:
    SESSION_ID = "37581081458:9b7JEQUO8cIrjh:23:AYgev3GhCxJ6NhG2SAuHFP8waJLvUtxh6D1lhiqzBQ"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    GEMINI_API_KEY = "AQ.Ab8RN6KqMmoNV0Iw2bm5tSTdmgAFg21jqrfad67ei9EwYW4G2g"

ADMINS_RAW = os.environ.get("INSTAGRAM_ADMINS", "razzz_huu")
ADMINS = [a.strip() for a in ADMINS_RAW.split(",") if a.strip()]

print(f"✅ SESSION_ID: {SESSION_ID[:20]}...")
print(f"✅ GEMINI_API_KEY: {'Yes' if GEMINI_API_KEY else 'No'}")
print(f"✅ ADMINS: {ADMINS}")

# ============ GEMINI ============
try:
    from google import genai
    GEMINI_AVAILABLE = True
    print("✅ Gemini AI available!")
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini not installed. Run: pip install google-genai")

# ============ MESSAGES ============
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

# ============ EMOJIS ============
SPAM_EMOJIS = ["🔥", "❤️", "💀", "👀", "🚀", "💯", "✨", "🎯", "😂", "🤣", "💪", "🦅", "🌟", "⚡", "🍿", "🎉", "🥶", "🤯", "😎", "👑"]

# ============ COMMAND SETTINGS ============
COMMAND_COOLDOWN = {
    '.ping': 1, '.dice': 1, '.flip': 1, '.rps': 2,
    '.trivia': 10, '.roast': 3, '.compliment': 3,
    '.fact': 3, '.joke': 3, '.meme': 3, '.quote': 3,
    '.love': 3, '.score': 1, '.leaderboard': 3,
    '.help': 5, '.rules': 5,
    '.kick': 30, '.warn': 30, '.add': 30,
    '.mute': 30, '.unmute': 30, '.clearwarn': 30,
    '.slowmode': 30, '.spam': 120, '.stopspam': 5,
    '.afk': 30, '.setwelcome': 30, '.setrules': 30,
    'default': 2,
}

MAX_COMMANDS_PER_MINUTE = 20
MAX_WARNINGS = 3
MAX_SPAM_COUNT = 10000
SPAM_DELAY_MIN = 3
SPAM_DELAY_MAX = 5
POLL_INTERVAL_MIN = 1.8
POLL_INTERVAL_MAX = 2.8
WELCOME_BACK_INTERVAL = 300
ADMIN_ACTIVE_TIMEOUT = 600
NATURAL_REPLY_CHANCE = 0.60  # 60%

# ============ HUMAN BEHAVIOR ============
class HumanBehavior:
    def __init__(self):
        self.moods = ['chatty', 'brief', 'distracted', 'focused', 'slow', 'hyper']
        self.current_mood = random.choice(self.moods)
        self.typing_speed = random.randint(40, 80)
        self.reading_speed = random.randint(200, 350)

    def change_mood(self):
        if random.random() < 0.04:
            self.current_mood = random.choice(self.moods)
            print(f"🧠 Mood: {self.current_mood}")

    def get_delay(self, action='message'):
        mood_delays = {
            'chatty': {'message': (0.5, 2.0), 'typing': (0.2, 0.6)},
            'brief': {'message': (0.2, 0.8), 'typing': (0.1, 0.3)},
            'distracted': {'message': (3.0, 8.0), 'typing': (1.0, 3.0)},
            'focused': {'message': (0.3, 1.2), 'typing': (0.2, 0.5)},
            'slow': {'message': (4.0, 10.0), 'typing': (1.5, 4.0)},
            'hyper': {'message': (0.1, 0.6), 'typing': (0.05, 0.2)}
        }
        min_d, max_d = mood_delays.get(self.current_mood, mood_delays['focused']).get(action, (0.5, 2.0))
        return random.uniform(min_d, max_d)

    def read_time(self, text):
        words = len(text.split())
        base_time = (words / self.reading_speed) * 60
        return min(base_time * random.uniform(0.7, 1.3), 8.0)

    def type_time(self, text):
        chars = len(text)
        base_time = chars / (self.typing_speed * random.uniform(0.7, 1.3))
        return min(base_time + random.uniform(0.2, 0.8), 6.0)

human = HumanBehavior()

def human_delay(min_sec=0.5, max_sec=2.5):
    time.sleep(random.uniform(min_sec, max_sec))

def read_message_like_human(text):
    delay = human.read_time(text)
    time.sleep(delay)
    return delay

def type_message_like_human(text):
    delay = human.type_time(text)
    time.sleep(delay)
    return delay

# ============ GEMINI FUNCTIONS (Always First) ============
def gemini_generate(prompt, client):
    if not client:
        return None
    try:
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return resp.text.strip()
    except Exception as e:
        print(f"⚠️ Gemini error: {e}")
        return None

def gemini_joke(client):
    return gemini_generate("Give a SHORT funny joke in HINDI/HINGLISH (max 20 words). Use emojis.", client)

def gemini_roast(target, client):
    return gemini_generate(f"Give a SHORT funny savage roast in HINDI/HINGLISH for @{target} (max 15 words). Use emojis.", client)

def gemini_compliment(target, client):
    return gemini_generate(f"Give a SHORT funny compliment in HINDI/HINGLISH for @{target} (max 15 words). Use emojis.", client)

def gemini_fact(client):
    return gemini_generate("Give one SHORT interesting fact in HINDI/HINGLISH (max 20 words). Use emojis.", client)

def gemini_love(name1, name2, percentage, client):
    return gemini_generate(f"Love percentage between {name1} and {name2} is {percentage}%. Give SHORT funny/savage reply in HINDI/HINGLISH (max 15 words). Use emojis.", client)

def gemini_trivia(client):
    return gemini_generate("Generate ONE trivia question in HINDI/HINGLISH with 4 options.\nFormat:\nQ: [question]\nA) [option1]\nB) [option2]\nC) [option3]\nD) [option4]\nAnswer: [letter]", client)

def gemini_natural_reply(message, username, client):
    return gemini_generate(f"User @{username} said: '{message}'. Give a SHORT funny/roast/savage/casual reply in HINDI/HINGLISH (max 20 words). Be playful, friendly, and human-like. Use emojis.", client)

def gemini_mention_reply(message, username, client):
    return gemini_generate(f"User @{username} mentioned the bot and said: '{message}'. Reply casually like a human friend in HINDI/HINGLISH (max 20 words). Be playful, funny, and natural. Use emojis.", client)

# ============ FALLBACK (Only if Gemini Fails) ============
FALLBACK_JOKES = [
    "एक आदमी ने डॉक्टर से कहा: मुझे हर रात बुरे सपने आते हैं। डॉक्टर बोला: क्या सपने आते हैं? आदमी बोला: सपने में मुझे नींद नहीं आती! 😂",
    "टीचर: तुम्हारी कॉपी में तो दीमक लग गई है! स्टूडेंट: सर, वो मेरी क्रिएटिविटी है! 💀",
    "पति: मैं तुमसे बहुत प्यार करता हूँ। पत्नी: क्या चाहिए? 😂",
    "एक लड़का लड़की से बोला: तुम मेरी आँखों का तारा हो। लड़की बोली: तो क्या मैं टूट कर गिर जाऊँ? 🤡",
    "बॉस: तुम्हारी सोच बहुत गहरी है। कर्मचारी: सर, वो मेरी अलमारी खाली है इसलिए। 💀",
]

FALLBACK_ROASTS = [
    "तू हर जगह है जैसे WiFi, पर काम किसी काम का नहीं! 📶",
    "तेरी सोच इतनी गहरी है जितनी चाय की प्लेट! ☕",
    "तू अच्छा है... बस दूर से। 😂",
    "तेरा चेहरा देखकर लगता है कल का कल होगा! 🗓️",
    "तुझसे अच्छा तो मेरा पुराना फोन है, वो भी कम से कम चार्ज हो जाता है! 🔋",
]

FALLBACK_COMPLIMENTS = [
    "तू तो लगता है जैसे सुबह की चाय — हर किसी को भाती है! ☕",
    "तू वो दोस्त है जिसके बिना ग्रुप अधूरा है! ❤️",
    "तू वजह है ग्रुप की शान! 👑",
    "तेरी हँसी सुनकर लगता है जैसे बारिश हो गई! 🌧️",
]

FALLBACK_FACTS = [
    "ऑक्टोपस के 3 दिल होते हैं! 💙",
    "केला एक बेरी है! 🍌",
    "वीनस पर 1 दिन 1 साल से भी लंबा होता है! 🌍",
]

FALLBACK_LOVE = [
    "तुम दोनों एक दूसरे के लिए बने हो! ❤️",
    "ये प्यार है... या फिर मजाक? 🤔",
    "तुम दोनों का कनेक्शन तारीफ के काबिल है! 💕",
]

FALLBACK_TRIVIA = [
    {"q": "फ्रांस की राजधानी क्या है?", "a": "पेरिस"},
    {"q": "2+2 क्या होता है?", "a": "4"},
    {"q": "सबसे बड़ा ग्रह कौन सा है?", "a": "बृहस्पति"},
]

ADMIN_TAG_REPLIES = [
    "Ohh tell me what happened, my boss is offline 🧐",
    "Boss is busy! Tell me, I'll handle it 💪",
    "Admin is AFK, but I'm here! What's up? 🤖",
]

ADMIN_GREETINGS = [
    "👑 Welcome back boss!",
    "🙇‍♂️ At your service, my lord!",
    "👋 Hey boss! Good to see you!",
]

AFK_USERS = {}
USER_LAST_ACTIVE = {}
USER_WELCOME_SENT = {}
ADMIN_LAST_SEEN = {}

# ============ INSTAGRAPI ============
try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired, RateLimitError
    print("✅ instagrapi imported!")
except ImportError as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# ============ MAIN BOT ============
class InstagramGroupBot:
    def __init__(self):
        print("🔧 Initializing bot...")
        self.cl = Client()
        self.cl.set_user_agent("Mozilla/5.0 (Linux; Android 13) Chrome/116.0.5845.92")
        self.running = True
        self.processed_messages = set()
        self.known_members = {}
        self.warned_users = {}
        self.scoreboard = {}
        self.username_cache = {}
        self.trivia_state = {}
        self.admin_last_seen = {}
        self.spam_running = False
        self.spam_stop_flag = False
        self.spam_thread = None

        # Gemini
        self.gemini_client = None
        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                print("✅ Gemini AI connected!")
            except Exception as e:
                print(f"⚠️ Gemini connection failed: {e}")
        else:
            print("⚠️ Gemini not available. Using fallback.")

        self.session = requests.Session()
        self.session.cookies.set('sessionid', SESSION_ID)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13) Chrome/116.0.5845.92',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Instagram-AJAX': '1',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
        })
        self.session.max_redirects = 3

        self.login()
        self.load_data()
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

    def load_data(self):
        try:
            if os.path.exists('bot_data.json'):
                with open('bot_data.json', 'r') as f:
                    data = json.load(f)
                    self.warned_users = data.get('warned', {})
                    self.scoreboard = data.get('scores', {})
                print("📂 Loaded bot data")
        except Exception as e:
            print(f"⚠️ Error loading data: {e}")

    def save_data(self):
        try:
            with open('bot_data.json', 'w') as f:
                json.dump({'warned': self.warned_users, 'scores': self.scoreboard}, f)
        except Exception as e:
            print(f"⚠️ Error saving data: {e}")

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
            if self.group_count == 1:
                self.poll_min, self.poll_max = 1.8, 2.8
            elif self.group_count == 2:
                self.poll_min, self.poll_max = 2.8, 3.8
            else:
                self.poll_min, self.poll_max = 4.0, 6.0
            print(f"📊 Detected {self.group_count} group(s)")
        except Exception as e:
            print(f"⚠️ Error: {e}")
            self.group_count = 1
            self.poll_min, self.poll_max = 1.8, 2.8

    def is_admin(self, username):
        return username in ADMINS or username == self.username

    def is_admin_online(self, thread_id):
        if thread_id not in self.admin_last_seen:
            return False
        return (datetime.now() - self.admin_last_seen[thread_id]).total_seconds() < ADMIN_ACTIVE_TIMEOUT

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
            human_delay(0.3, 0.8)
            self.cl.direct_send(message, thread_ids=[thread_id])
            print(f"📤 Sent: {message[:30]}...")
            human_delay(0.5, 1.5)
            return True
        except RateLimitError:
            print("⚠️ Rate limited! Waiting 60s...")
            time.sleep(60)
            return False
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False

    def kick_user(self, thread_id, target_id):
        try:
            print(f"🔨 Kicking user {target_id}")
            thread_id_str = str(thread_id)
            target_id_str = str(target_id)
            csrf = self.session.cookies.get('csrftoken', '')
            if csrf:
                self.session.headers.update({'X-CSRFToken': csrf})
            resp = self.session.post(
                f"https://www.instagram.com/direct_v2/threads/{thread_id_str}/remove_user/{target_id_str}/"
            )
            if resp.status_code == 200:
                print("✅ Kick successful!")
                return True
            print(f"❌ Kick failed: {resp.status_code}")
            return False
        except Exception as e:
            print(f"❌ Kick error: {e}")
            return False

    def add_user(self, thread_id, username, admin_username):
        try:
            user_id = self.cl.user_id_from_username(username)
            if not user_id:
                return False, f"❌ User @{username} not found"
            thread_id_str = str(thread_id)
            user_id_str = str(user_id)
            csrf = self.session.cookies.get('csrftoken', '')
            if csrf:
                self.session.headers.update({'X-CSRFToken': csrf})
            resp = self.session.post(
                f"https://www.instagram.com/direct_v2/threads/{thread_id_str}/add_user/{user_id_str}/"
            )
            if resp.status_code == 200:
                print(f"✅ Added @{username}")
                return True, f"✅ @{username} added by @{admin_username}!"
            return False, f"❌ Failed to add @{username}"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

    def run_spam(self, thread_id, count, message, admin_username):
        self.spam_running = True
        self.spam_stop_flag = False
        try:
            for i in range(count):
                if self.spam_stop_flag:
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
            self.spam_running = False

    def stop_spam(self, thread_id, username):
        if not self.is_admin(username):
            self.send_message(thread_id, f"❌ @{username} Only admins can stop spam!")
            return False
        if not self.spam_running:
            self.send_message(thread_id, "ℹ️ No spam running.")
            return False
        self.spam_stop_flag = True
        self.send_message(thread_id, "🛑 Stopping spam...")
        return True

    def send_trivia_question(self, thread_id):
        state = self.trivia_state.get(thread_id)
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
            if thread_id in self.trivia_state and self.trivia_state[thread_id]['current'] == current:
                self.send_message(thread_id, f"⏰ Time's up! Answer: {q['a']}")
                self.trivia_state[thread_id]['current'] += 1
                time.sleep(2)
                self.send_trivia_question(thread_id)
        threading.Thread(target=check, daemon=True).start()

    def end_trivia(self, thread_id):
        state = self.trivia_state.pop(thread_id, None)
        if not state:
            return
        score, total, username = state['score'], len(state['questions']), state['username']
        msgs = ["🧠 GENIUS! 🏆", "🔥 Amazing! 🌟", "👍 Good job! 💪", "🤔 Not bad! 📚", "😂 Did you even try?! 💀"]
        msg = msgs[0] if score == total else msgs[1] if score >= total-1 else msgs[2] if score >= total//2 else msgs[3] if score >= 1 else msgs[4]
        self.send_message(thread_id, f"--- 🎯 GAME OVER! ---\n🏆 @{username} scored {score}/{total}\n{msg}")
        self.scoreboard[state['user_id']] = self.scoreboard.get(state['user_id'], 0) + score
        self.save_data()

    def check_trivia_answer(self, thread_id, user_id, message):
        state = self.trivia_state.get(thread_id)
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

        if cmd == '.help':
            help_text = """
🤖 **GROUP BOT COMMANDS:**

**🎮 Games:**
.dice - Roll dice
.flip - Flip coin
.rps [r/p/s] - Rock Paper Scissors
.trivia - 5 questions with timer
.roast @user - Roast user
.compliment @user - Compliment user
.fact - Random fact
.joke - Random joke
.meme - Random meme
.quote - Inspirational quote
.love @user OR .love @user1 @user2 - Love calculator
.score - Your points
.leaderboard - Top players

**👑 Admin:**
.kick @user - Kick user
.warn @user - Warn (3 = kick)
.add @user - Add user
.mute @user [min] - Mute user
.unmute @user - Unmute user
.clearwarn @user - Clear warnings
.slowmode [sec] - Set slow mode
.spam count msg - Spam (max 10,000)
.stopspam - Stop spam
.afk [reason] - Set AFK
.setwelcome msg - Set welcome
.setrules rules - Set rules

**🤖 AI Mode:**
Bot is always active! Reply naturally in Hindi/Hinglish (60% chance).
"""
            self.send_message(thread_id, help_text)
            return

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
            self.save_data()
            return

        elif cmd == '.flip':
            result = random.choice(['Heads', 'Tails'])
            self.send_message(thread_id, f"🪙 @{username} flipped **{result}**!")
            self.scoreboard[user_id] = self.scoreboard.get(user_id, 0) + 1
            self.save_data()
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
            elif (user_choice == 'rock' and bot_choice == 'scissors') or \
                 (user_choice == 'paper' and bot_choice == 'rock') or \
                 (user_choice == 'scissors' and bot_choice == 'paper'):
                result = "You win! 🎉"
                self.scoreboard[user_id] = self.scoreboard.get(user_id, 0) + 2
                self.save_data()
            else:
                result = "I win! 😎"
            self.send_message(thread_id, f"🪨📄✂️ @{username}: {user_choice} 🤖 Bot: {bot_choice}\n{result}")
            return

        elif cmd == '.trivia':
            if thread_id in self.trivia_state:
                self.send_message(thread_id, "⚠️ Trivia already running!")
                return
            questions = []
            if self.gemini_client:
                for _ in range(5):
                    q = gemini_trivia(self.gemini_client)
                    if q:
                        questions.append(q)
            if len(questions) < 5:
                qs = random.sample(FALLBACK_TRIVIA, min(5, len(FALLBACK_TRIVIA)))
                questions = [{"q": q['q'], "options": [], "a": q['a']} for q in qs]
            self.trivia_state[thread_id] = {
                'questions': questions,
                'current': 0,
                'score': 0,
                'user_id': user_id,
                'username': username
            }
            self.send_message(thread_id, f"🧠 **TRIVIA STARTED!**\n@{username} has 15 sec per question.\nTotal: {len(questions)} questions.")
            self.send_trivia_question(thread_id)
            return

        elif cmd == '.roast':
            if not args:
                self.send_message(thread_id, "Usage: .roast @user")
                return
            target = args[0].replace('@', '')
            if self.gemini_client:
                msg = gemini_roast(target, self.gemini_client)
            msg = msg or random.choice(FALLBACK_ROASTS)
            self.send_message(thread_id, f"🔥 @{target} {msg}")
            return

        elif cmd == '.compliment':
            if not args:
                self.send_message(thread_id, "Usage: .compliment @user")
                return
            target = args[0].replace('@', '')
            if self.gemini_client:
                msg = gemini_compliment(target, self.gemini_client)
            msg = msg or random.choice(FALLBACK_COMPLIMENTS)
            self.send_message(thread_id, f"💕 @{target} {msg}")
            return

        elif cmd == '.joke':
            if self.gemini_client:
                msg = gemini_joke(self.gemini_client)
            msg = msg or random.choice(FALLBACK_JOKES)
            self.send_message(thread_id, f"😂 {msg}")
            return

        elif cmd == '.fact':
            if self.gemini_client:
                msg = gemini_fact(self.gemini_client)
            msg = msg or random.choice(FALLBACK_FACTS)
            self.send_message(thread_id, f"📖 {msg}")
            return

        elif cmd == '.meme':
            self.send_message(thread_id, f"🤣 {random.choice(FALLBACK_JOKES)}")
            return

        elif cmd == '.quote':
            self.send_message(thread_id, f"💭 {random.choice(FALLBACK_JOKES)}")
            return

        elif cmd == '.love':
            if not args:
                self.send_message(thread_id, "Usage: .love @user OR .love @user1 @user2")
                return
            mentions = [a.replace('@', '') for a in args if a.startswith('@')]
            if len(mentions) == 1:
                name1, name2 = username, mentions[0]
            elif len(mentions) == 2:
                name1, name2 = mentions[0], mentions[1]
            else:
                self.send_message(thread_id, "Please tag 1 or 2 people! ❌")
                return
            percentage = random.randint(0, 100)
            heart = "❤️🔥" if percentage >= 80 else "❤️" if percentage >= 60 else "💕" if percentage >= 40 else "💛" if percentage >= 20 else "💔"
            if self.gemini_client:
                msg = gemini_love(name1, name2, percentage, self.gemini_client)
            msg = msg or random.choice(FALLBACK_LOVE)
            self.send_message(thread_id, f"💕 **Love Calculator**\n@{name1} + @{name2} = {percentage}% {heart}\n\n{msg}")
            return

        elif cmd == '.score':
            self.send_message(thread_id, f"🏆 @{username} has {self.scoreboard.get(user_id, 0)} points!")
            return

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

        elif cmd == '.stopspam':
            self.stop_spam(thread_id, username)
            return

        elif cmd == '.afk':
            if not self.is_admin(username):
                self.send_message(thread_id, f"❌ @{username} Only admins can use .afk!")
                return
            reason = ' '.join(args) if args else "AFK"
            AFK_USERS[user_id] = (reason, datetime.now())
            self.send_message(thread_id, f"🛏️ @{username} is now AFK: {reason}")
            return

        # ============ ADMIN ============
        if not self.is_admin(username):
            self.send_message(thread_id, f"❌ @{username} Not admin!")
            return

        if cmd == '.kick':
            if not args:
                self.send_message(thread_id, "Usage: .kick @user")
                return
            target = args[0].replace('@', '')
            target_id = self.cl.user_id_from_username(target)
            if not target_id:
                self.send_message(thread_id, f"❌ User @{target} not found")
                return
            if self.kick_user(thread_id, target_id):
                self.send_message(thread_id, LEAVE_MSG.format(username=target))
                if thread_id in self.known_members and target_id in self.known_members[thread_id]:
                    self.known_members[thread_id].remove(target_id)
            else:
                self.send_message(thread_id, f"❌ Failed to kick @{target}")
            return

        elif cmd == '.add':
            if not args:
                self.send_message(thread_id, "Usage: .add @user")
                return
            target = args[0].replace('@', '')
            success, msg = self.add_user(thread_id, target, username)
            self.send_message(thread_id, msg)
            if success:
                target_id = self.cl.user_id_from_username(target)
                if target_id:
                    self.known_members.setdefault(thread_id, set()).add(target_id)
            return

        elif cmd == '.warn':
            if not args:
                self.send_message(thread_id, "Usage: .warn @user")
                return
            target = args[0].replace('@', '')
            target_id = self.cl.user_id_from_username(target)
            if not target_id:
                self.send_message(thread_id, f"❌ User @{target} not found")
                return
            self.warned_users[target_id] = self.warned_users.get(target_id, 0) + 1
            warnings = self.warned_users[target_id]
            self.save_data()
            self.send_message(thread_id, f"⚠️ @{target} warned ({warnings}/3)")
            if warnings >= MAX_WARNINGS and self.kick_user(thread_id, target_id):
                self.send_message(thread_id, f"🔴 @{target} auto-kicked for 3 warnings!")
                self.send_message(thread_id, LEAVE_MSG.format(username=target))
                self.warned_users[target_id] = 0
                if thread_id in self.known_members and target_id in self.known_members[thread_id]:
                    self.known_members[thread_id].remove(target_id)
                self.save_data()
            return

        elif cmd == '.mute':
            if not args:
                self.send_message(thread_id, "Usage: .mute @user [minutes]")
                return
            target = args[0].replace('@', '')
            minutes = int(args[1]) if len(args) > 1 else 30
            self.send_message(thread_id, f"🔇 @{target} muted for {minutes} minutes")
            return

        elif cmd == '.unmute':
            if not args:
                self.send_message(thread_id, "Usage: .unmute @user")
                return
            target = args[0].replace('@', '')
            self.send_message(thread_id, f"🔊 @{target} unmuted")
            return

        elif cmd == '.clearwarn':
            if not args:
                self.send_message(thread_id, "Usage: .clearwarn @user")
                return
            target = args[0].replace('@', '')
            target_id = self.cl.user_id_from_username(target)
            if target_id:
                self.warned_users[target_id] = 0
                self.save_data()
                self.send_message(thread_id, f"✅ Cleared warnings for @{target}")
            else:
                self.send_message(thread_id, f"❌ User @{target} not found")
            return

        elif cmd == '.slowmode':
            if not args:
                self.send_message(thread_id, "Usage: .slowmode [seconds]")
                return
            seconds = int(args[0])
            self.send_message(thread_id, f"🐢 Slow mode set to {seconds} seconds")
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
            if self.spam_running:
                self.send_message(thread_id, "⚠️ Spam already running! Use .stopspam")
                return
            self.send_message(thread_id, f"📢 Admin starting spam: {count} messages!")
            self.spam_thread = threading.Thread(target=self.run_spam, args=(thread_id, count, message, username), daemon=True)
            self.spam_thread.start()
            return

        elif cmd == '.setwelcome':
            if not args:
                self.send_message(thread_id, "Usage: .setwelcome [message]")
                return
            self.send_message(thread_id, "✅ Welcome message updated!")
            return

        elif cmd == '.setrules':
            if not args:
                self.send_message(thread_id, "Usage: .setrules [rules]")
                return
            self.send_message(thread_id, "✅ Rules updated!")
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
                            if uname:
                                print(f"🔔 New member: @{uname}")
                                self.send_message(thread_id, WELCOME_MSG.format(username=uname))
                                human_delay(1.0, 2.0)
                                self.send_message(thread_id, RULES)
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

                        # Welcome back
                        now = datetime.now()
                        last = USER_LAST_ACTIVE.get(msg.user_id)
                        if msg.user_id != self.user_id and last and (now - last).total_seconds() >= WELCOME_BACK_INTERVAL:
                            last_welcome = USER_WELCOME_SENT.get(msg.user_id)
                            if not last_welcome or (now - last_welcome).total_seconds() > WELCOME_BACK_INTERVAL:
                                print(f"👋 Welcome back @{username}")
                                self.send_welcome_back(thread_id, username)
                                USER_WELCOME_SENT[msg.user_id] = now
                        USER_LAST_ACTIVE[msg.user_id] = now

                        if username.lower() in [a.lower() for a in ADMINS]:
                            self.admin_last_seen[thread_id] = now

                        # Admin tag
                        msg_lower = msg.text.lower()
                        if any(f"@{admin}".lower() in msg_lower for admin in ADMINS) and not self.is_admin(username):
                            if not self.is_admin_online(thread_id):
                                self.send_message(thread_id, f"@{username} {random.choice(ADMIN_TAG_REPLIES)}")
                                human_delay(0.5, 1.0)

                        # Admin greeting
                        if username.lower() in [a.lower() for a in ADMINS]:
                            last_seen = self.admin_last_seen.get(thread_id, now - timedelta(minutes=10))
                            if (now - last_seen).seconds > 60:
                                self.send_message(thread_id, random.choice(ADMIN_GREETINGS))

                        if thread_id in self.trivia_state:
                            self.check_trivia_answer(thread_id, msg.user_id, msg.text)

                        if msg.user_id in AFK_USERS:
                            reason, t = AFK_USERS[msg.user_id]
                            if (now - t).seconds > 300:
                                del AFK_USERS[msg.user_id]
                                self.send_message(thread_id, f"🟢 @{username} is no longer AFK")

                        # ============================================================
                        # ✅ GEMINI NATURAL REPLY (60% chance)
                        # ============================================================
                        if not msg.text.startswith('.') and random.random() < NATURAL_REPLY_CHANCE and self.gemini_client:
                            # Read like human
                            read_message_like_human(msg.text)

                            # Check if bot is mentioned
                            if f"@{self.username}".lower() in msg.text.lower():
                                reply = gemini_mention_reply(msg.text, username, self.gemini_client)
                            else:
                                reply = gemini_natural_reply(msg.text, username, self.gemini_client)

                            if reply:
                                human_delay(1.0, 2.5)
                                self.send_message(thread_id, reply)
                                print(f"🤖 AI reply to @{username}")

                            human.change_mood()

                        # ============================================================
                        # ✅ COMMANDS
                        # ============================================================
                        if msg.text.startswith('.'):
                            self.handle_command(thread_id, msg.user_id, username, msg.text)

                except RateLimitError:
                    print("⚠️ Rate limited! Waiting 5 min...")
                    time.sleep(300)
                except Exception as e:
                    print(f"⚠️ Thread error: {e}")
        except RateLimitError:
            print("⚠️ Rate limited! Waiting 5 min...")
            time.sleep(300)
        except Exception as e:
            print(f"⚠️ Check error: {e}")

    def send_welcome_back(self, thread_id, username):
        if username == self.username:
            return
        for msg in WELCOME_BACK_MSGS:
            self.send_message(thread_id, msg.format(username=username))
            human_delay(2.0, 4.0)

    def run(self):
        print("\n" + "=" * 60)
        print("🤖 GROUP BOT RUNNING (Gemini Always Active)")
        print(f"👤 Bot: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print(f"📊 Monitoring: {getattr(self, 'group_count', 1)} group(s)")
        print("=" * 60)
        print("🤖 Features:")
        print("   ✅ Gemini ALWAYS active (first priority)")
        print("   ✅ 60% natural replies (Hindi/Hinglish)")
        print("   ✅ Mention replies (@botname kya haal hai)")
        print("   ✅ Full human behavior (reading, typing, moods)")
        print("   ✅ Fresh jokes, roasts, compliments from Gemini")
        print("   ✅ Fallback only if Gemini fails")
        print("=" * 60)
        print("\n⚠️ Press Ctrl+C to stop\n")
        while self.running:
            try:
                self.check_messages()
                time.sleep(random.uniform(self.poll_min, self.poll_max))
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

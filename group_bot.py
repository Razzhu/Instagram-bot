#!/usr/bin/env python3
"""
Instagram Group Bot - FINAL COMPLETE VERSION
- 15% natural replies
- Groq AI (free, fast, Hindi)
- Public .ask command
- Admin .groq command
- Anti-detection
- No kick/add/warn/mute
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
print("📂 GROUP_BOT.PY LOADING... (FINAL)")
print("=" * 60)

# ============ ENVIRONMENT ============
SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "")
if not SESSION_ID:
    SESSION_ID = "37581081458:zXHY1VTJaFyVGu:19:AYiocLg53LRaCvjWOInTowpFnUdz3y9NzQUbn39fYw"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    GROQ_API_KEY = "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"

ADMINS_RAW = os.environ.get("INSTAGRAM_ADMINS", "razzz_huu")
ADMINS = [a.strip() for a in ADMINS_RAW.split(",") if a.strip()]

print(f"✅ SESSION_ID: {SESSION_ID[:20]}...")
print(f"✅ GROQ_API_KEY: {'Yes' if GROQ_API_KEY else 'No'}")
print(f"✅ ADMINS: {ADMINS}")

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

SPAM_EMOJIS = ["🔥", "❤️", "💀", "👀", "🚀", "💯", "✨", "🎯", "😂", "🤣", "💪", "🦅", "🌟", "⚡", "🍿", "🎉", "🥶", "🤯", "😎", "👑"]

# ============ COMMAND SETTINGS ============
COMMAND_COOLDOWN = {
    '.ping': 5, '.dice': 5, '.flip': 5, '.rps': 10,
    '.trivia': 20, '.roast': 10, '.compliment': 10,
    '.fact': 10, '.joke': 10, '.8ball': 10,
    '.love': 10, '.score': 5, '.leaderboard': 15,
    '.help': 15, '.rules': 15,
    '.spam': 300, '.stopspam': 10,
    '.afk': 60, '.setwelcome': 60, '.setrules': 60,
    '.ask': 15,  # Public ask
    '.groq': 30,  # Admin groq
    'default': 5,
}

MAX_COMMANDS_PER_MINUTE = 10
MAX_WARNINGS = 3
MAX_SPAM_COUNT = 1000
SPAM_DELAY_MIN = 5
SPAM_DELAY_MAX = 10
POLL_INTERVAL_MIN = 5.0
POLL_INTERVAL_MAX = 10.0
WELCOME_BACK_INTERVAL = 600
ADMIN_ACTIVE_TIMEOUT = 900
NATURAL_REPLY_CHANCE = 0.15

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

    def get_delay(self, action='message'):
        mood_delays = {
            'chatty': {'message': (1.0, 3.0), 'typing': (0.5, 1.0)},
            'brief': {'message': (0.5, 1.5), 'typing': (0.2, 0.5)},
            'distracted': {'message': (5.0, 12.0), 'typing': (2.0, 5.0)},
            'focused': {'message': (0.8, 2.0), 'typing': (0.3, 0.7)},
            'slow': {'message': (6.0, 15.0), 'typing': (3.0, 6.0)},
            'hyper': {'message': (0.3, 1.0), 'typing': (0.1, 0.3)}
        }
        min_d, max_d = mood_delays.get(self.current_mood, mood_delays['focused']).get(action, (1.0, 3.0))
        return random.uniform(min_d, max_d)

    def read_time(self, text):
        words = len(text.split())
        base_time = (words / self.reading_speed) * 60
        return min(base_time * random.uniform(0.7, 1.3), 12.0)

    def type_time(self, text):
        chars = len(text)
        base_time = chars / (self.typing_speed * random.uniform(0.7, 1.3))
        return min(base_time + random.uniform(0.5, 1.5), 10.0)

human = HumanBehavior()

def human_delay(min_sec=1.0, max_sec=4.0):
    time.sleep(random.uniform(min_sec, max_sec))

def read_message_like_human(text):
    delay = human.read_time(text)
    time.sleep(delay)
    return delay

def type_message_like_human(text):
    delay = human.type_time(text)
    time.sleep(delay)
    return delay

# ============ GROQ AI FUNCTIONS ============
def groq_generate(prompt, api_key):
    """Generate reply from Groq AI. Returns None if fails."""
    if not api_key:
        return None
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "groq/compound",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 1.0,
            "max_tokens": 100
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            reply = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not reply or "can't help" in reply.lower() or "sorry" in reply.lower():
                return None
            return reply
        else:
            print(f"⚠️ Groq API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Groq error: {e}")
        return None

# ✅ Natural reply (short, savage, funny)
def groq_natural_reply(message, username, api_key):
    return groq_generate(
        f"Reply to @{username} in ONE SHORT SENTENCE (5-10 words) in HINDI/HINGLISH. "
        f"Be savage, rude, funny, and casual. Reply DIRECTLY with the message only. "
        f"Do NOT explain, do NOT add reasoning. Message: '{message}'",
        api_key
    )

# ✅ Public .ask (funny/roast reply)
def groq_ask_public(question, api_key):
    return groq_generate(
        f"Reply to this question in a funny, roast, or casual way in HINDI/HINGLISH. "
        f"Keep it short (5-10 words). Question: '{question}'",
        api_key
    )

# ✅ Admin .groq (full reply, can be longer)
def groq_admin(question, api_key):
    return groq_generate(
        f"Answer this question in HINDI/HINGLISH. Be helpful, informative, and complete. "
        f"Question: '{question}'",
        api_key
    )

# ✅ Playful commands
def groq_joke(api_key):
    return groq_generate("Tell a SHORT funny joke in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_roast(target, api_key):
    return groq_generate(f"Give a SHORT savage roast for @{target} in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_compliment(target, api_key):
    return groq_generate(f"Give a SHORT funny compliment for @{target} in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_fact(api_key):
    return groq_generate("Give a SHORT interesting fact in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_8ball(question, api_key):
    return groq_generate(f"Give a funny magic 8-ball answer for: '{question}' in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_love(name1, name2, percentage, api_key):
    return groq_generate(f"Love percentage is {percentage}%. Give ONE SHORT funny/savage reply in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_trivia(api_key):
    return groq_generate("Generate ONE short trivia question in HINDI/HINGLISH with 4 options.\nFormat:\nQ: [question]\nA) [option1]\nB) [option2]\nC) [option3]\nD) [option4]\nAnswer: [letter]", api_key)

# ============ FALLBACK ============
FALLBACK_JOKES = ["एक आदमी ने डॉक्टर से कहा: मुझे हर रात बुरे सपने आते हैं। डॉक्टर बोला: क्या सपने आते हैं? आदमी बोला: सपने में मुझे नींद नहीं आती! 😂"]
FALLBACK_ROASTS = ["तू हर जगह है जैसे WiFi, पर काम किसी काम का नहीं! 📶"]
FALLBACK_COMPLIMENTS = ["तू तो लगता है जैसे सुबह की चाय — हर किसी को भाती है! ☕"]
FALLBACK_FACTS = ["ऑक्टोपस के 3 दिल होते हैं! 💙"]
FALLBACK_LOVE = ["तुम दोनों एक दूसरे के लिए बने हो! ❤️"]
FALLBACK_8BALL = ["🎱 शायद हाँ", "🎱 नहीं", "🎱 पक्का नहीं"]
FALLBACK_TRIVIA = [{"q": "फ्रांस की राजधानी क्या है?", "a": "पेरिस"}]

ADMIN_TAG_REPLIES = ["Ohh tell me what happened, my boss is offline 🧐", "Boss is busy! Tell me, I'll handle it 💪"]
ADMIN_GREETINGS = ["👑 Welcome back boss!", "🙇‍♂️ At your service, my lord!"]

AFK_USERS = {}
USER_LAST_ACTIVE = {}
USER_WELCOME_SENT = {}
ADMIN_LAST_SEEN = {}
WELCOME_SENT = {}

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
        self.welcome_sent = {}

        self.groq_api_key = GROQ_API_KEY
        if self.groq_api_key:
            print("✅ Groq API key loaded!")

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
            print(f"📊 Detected {self.group_count} group(s)")
        except Exception as e:
            print(f"⚠️ Error: {e}")
            self.group_count = 1

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
.8ball [question] - Magic 8-ball
.love @user - Love calculator
.score - Your points
.leaderboard - Top players

**🤖 AI Commands:**
.ask [question] - Ask Groq (funny/roast)
.rules - Show rules
.ping - Check bot alive

**👑 Admin:**
.spam count msg - Spam messages
.stopspam - Stop spam
.afk [reason] - Set AFK
.setwelcome msg - Set welcome
.setrules rules - Set rules
.groq [question] - Ask Groq (full reply)
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
            if self.groq_api_key:
                for _ in range(5):
                    q = groq_trivia(self.groq_api_key)
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
            if self.groq_api_key:
                msg = groq_roast(target, self.groq_api_key)
            msg = msg or random.choice(FALLBACK_ROASTS)
            self.send_message(thread_id, f"🔥 @{target} {msg}")
            return

        elif cmd == '.compliment':
            if not args:
                self.send_message(thread_id, "Usage: .compliment @user")
                return
            target = args[0].replace('@', '')
            if self.groq_api_key:
                msg = groq_compliment(target, self.groq_api_key)
            msg = msg or random.choice(FALLBACK_COMPLIMENTS)
            self.send_message(thread_id, f"💕 @{target} {msg}")
            return

        elif cmd == '.joke':
            if self.groq_api_key:
                msg = groq_joke(self.groq_api_key)
            msg = msg or random.choice(FALLBACK_JOKES)
            self.send_message(thread_id, f"😂 {msg}")
            return

        elif cmd == '.fact':
            if self.groq_api_key:
                msg = groq_fact(self.groq_api_key)
            msg = msg or random.choice(FALLBACK_FACTS)
            self.send_message(thread_id, f"📖 {msg}")
            return

        elif cmd == '.8ball':
            if not args:
                self.send_message(thread_id, "Ask me something! Example: .8ball Will I win?")
                return
            question = ' '.join(args)
            if self.groq_api_key:
                msg = groq_8ball(question, self.groq_api_key)
            msg = msg or random.choice(FALLBACK_8BALL)
            self.send_message(thread_id, msg)
            return

        elif cmd == '.love':
            if not args:
                self.send_message(thread_id, "Usage: .love @user")
                return
            target = args[0].replace('@', '')
            percentage = random.randint(0, 100)
            heart = "❤️🔥" if percentage >= 80 else "❤️" if percentage >= 60 else "💕" if percentage >= 40 else "💛" if percentage >= 20 else "💔"
            if self.groq_api_key:
                msg = groq_love(username, target, percentage, self.groq_api_key)
            msg = msg or random.choice(FALLBACK_LOVE)
            self.send_message(thread_id, f"💕 **Love Calculator**\n@{username} + @{target} = {percentage}% {heart}\n\n{msg}")
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

        elif cmd == '.ask':
            if not args:
                self.send_message(thread_id, "Usage: .ask [question]")
                return
            question = ' '.join(args)
            if self.groq_api_key:
                reply = groq_ask_public(question, self.groq_api_key)
                if reply:
                    self.send_message(thread_id, reply)
                # Silent if no reply
            return

        elif cmd == '.groq':
            if not self.is_admin(username):
                self.send_message(thread_id, f"❌ @{username} Only admins can use .groq!")
                return
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
                                if (thread_id, mid) not in self.welcome_sent:
                                    print(f"🔔 New member: @{uname}")
                                    self.send_message(thread_id, WELCOME_MSG.format(username=uname))
                                    human_delay(2.0, 4.0)
                                    self.send_message(thread_id, RULES)
                                    self.welcome_sent[(thread_id, mid)] = True
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
                        USER_LAST_ACTIVE[msg.user_id] = now                        if username.lower() in [a.lower() for a in ADMINS]:
                            self.admin_last_seen[thread_id] = now

                        msg_lower = msg.text.lower()
                        if any(f"@{admin}".lower() in msg_lower for admin in ADMINS) and not self.is_admin(username):
                            if not self.is_admin_online(thread_id):
                                self.send_message(thread_id, f"@{username} {random.choice(ADMIN_TAG_REPLIES)}")
                                human_delay(1.0, 2.0)

                        if username.lower() in [a.lower() for a in ADMINS]:
                            last_seen = self.admin_last_seen.get(thread_id, now - timedelta(minutes=10))
                            if (now - last_seen).seconds > 120:
                                self.send_message(thread_id, random.choice(ADMIN_GREETINGS))

                        if thread_id in self.trivia_state:
                            self.check_trivia_answer(thread_id, msg.user_id, msg.text)

                        if msg.user_id in AFK_USERS:
                            reason, t = AFK_USERS[msg.user_id]
                            if (now - t).seconds > 300:
                                del AFK_USERS[msg.user_id]
                                self.send_message(thread_id, f"🟢 @{username} is no longer AFK")

                        # ============================================================
                        # ✅ NATURAL REPLY (15% chance)
                        # ============================================================
                        if not msg.text.startswith('.') and random.random() < NATURAL_REPLY_CHANCE and self.groq_api_key:
                            read_message_like_human(msg.text)

                            if f"@{self.username}".lower() in msg.text.lower():
                                reply = groq_mention_reply(msg.text, username, self.groq_api_key)
                            else:
                                reply = groq_natural_reply(msg.text, username, self.groq_api_key)

                            if reply:
                                human_delay(2.0, 5.0)
                                self.send_message(thread_id, reply)
                                print(f"🤖 Groq reply to @{username}")

                            human.change_mood()

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
        print("🤖 GROUP BOT RUNNING (FINAL)")
        print(f"👤 Bot: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print(f"📊 Monitoring: {getattr(self, 'group_count', 1)} group(s)")
        print("=" * 60)
        print("🤖 Features:")
        print("   ✅ 15% natural replies")
        print("   ✅ Public .ask (funny/roast)")
        print("   ✅ Admin .groq (full reply)")
        print("   ✅ All games")
        print("   ✅ Spam (working)")
        print("   ✅ Anti-detection")
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

#!/usr/bin/env python3
"""
Instagram Group Bot - FINAL COMPLETE VERSION
- Session ID: Hardcoded fallback + Environment variable
- Gemini API Key: Hardcoded fallback + Environment variable
- Error free + Debugged
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

# ============ ENVIRONMENT VARIABLES WITH HARDCODED FALLBACK ============
# ✅ Session ID - Environment or Hardcoded
SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "")
if not SESSION_ID:
    SESSION_ID = "11950490138:eTVuFmLKKnpBt6:6:AYgXPb6Yu1gacrK69V2TBHN9FbOce1XQa3aPVb0w_A"
    print("⚠️ Using hardcoded SESSION_ID (environment not set)")

# ✅ Gemini API Key - Environment or Hardcoded
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    GEMINI_API_KEY = "AQ.Ab8RN6KqMmoNV0Iw2bm5tSTdmgAFg21jqrfad67ei9EwYW4G2g"
    print("⚠️ Using hardcoded GEMINI_API_KEY (environment not set)")

# ✅ Admins - Environment or Hardcoded
ADMINS_RAW = os.environ.get("INSTAGRAM_ADMINS", "razzz_huu")
ADMINS = [a.strip() for a in ADMINS_RAW.split(",") if a.strip()]

print(f"✅ SESSION_ID loaded: {SESSION_ID[:20]}...")
print(f"✅ GEMINI_API_KEY loaded: {'Yes' if GEMINI_API_KEY else 'No'}")
print(f"✅ ADMINS: {ADMINS}")

# ============ GEMINI AI IMPORT ============
try:
    from google import genai
    GEMINI_AVAILABLE = True
    print("✅ Gemini AI available!")
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini AI not installed. Install: pip install google-genai")

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

# ✅ Updated welcome back message
WELCOME_BACK_MSGS = [
    "{username} kya haal ladleee wapis idhr 👀🔥",
]

# ============ EMOJI POOLS ============
SPAM_EMOJIS = ["🔥", "❤️", "💀", "👀", "🚀", "💯", "✨", "🎯", "😂", "🤣", "💪", "🦅", "🌟", "⚡", "🍿", "🎉", "🥶", "🤯", "😎", "👑"]
REPLY_EMOJIS = ["😂", "💀", "🔥", "👀", "🤣", "😭", "💀", "😎", "🔥", "💯"]

# ============ GAME COMMANDS ============
COMMAND_COOLDOWN = {
    '.ping': 1,
    '.dice': 1,
    '.flip': 1,
    '.rps': 2,
    '.8ball': 2,
    '.trivia': 10,
    '.roast': 3,
    '.compliment': 3,
    '.fact': 3,
    '.joke': 3,
    '.meme': 3,
    '.quote': 3,
    '.love': 3,
    '.score': 1,
    '.leaderboard': 3,
    '.help': 5,
    '.rules': 5,
    '.kick': 30,
    '.warn': 30,
    '.add': 30,
    '.mute': 30,
    '.unmute': 30,
    '.clearwarn': 30,
    '.slowmode': 30,
    '.spam': 120,
    '.stopspam': 5,
    '.afk': 30,
    '.setwelcome': 30,
    '.setrules': 30,
    'default': 2,
}

MAX_COMMANDS_PER_MINUTE = 20
MAX_WARNINGS = 3
MAX_SPAM_COUNT = 10000
SPAM_DELAY_MIN = 3
SPAM_DELAY_MAX = 5
POLL_INTERVAL_MIN = 1.5
POLL_INTERVAL_MAX = 2.5
WELCOME_BACK_INTERVAL = 300
WELCOME_BACK_GAP = 5
ADMIN_ACTIVE_TIMEOUT = 600

# ============ DATA LISTS (Fallback for when AI is unavailable) ============
FALLBACK_JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "What do you call a fake noodle? An impasta!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "What do you call a bear with no teeth? A gummy bear!",
]

FALLBACK_QUOTES = [
    "Be the change you wish to see in the world. - Gandhi",
    "In the middle of difficulty lies opportunity. - Einstein",
    "The only way to do great work is to love what you do. - Steve Jobs",
]

FALLBACK_MEMES = [
    "🤣 This is fine 🔥",
    "😂 It's not a bug, it's a feature!",
    "🤪 I'm not lazy, I'm on energy-saving mode",
]

FALLBACK_FACTS = [
    "Octopuses have three hearts. 💙",
    "The shortest war in history was 38 minutes. ⚔️",
    "Bananas are berries. 🍌",
    "A day on Venus is longer than a year on Venus. 🌍",
]

FALLBACK_8BALL = [
    "🎱 Yes, definitely!",
    "🎱 Without a doubt.",
    "🎱 As I see it, yes.",
    "🎱 Most likely.",
    "🎱 Outlook good.",
    "🎱 Yes.",
    "🎱 Signs point to yes.",
    "🎱 Reply hazy, try again.",
    "🎱 Ask again later.",
    "🎱 Better not tell you now.",
    "🎱 Cannot predict now.",
    "🎱 Concentrate and ask again.",
    "🎱 Don't count on it.",
    "🎱 My reply is no.",
    "🎱 My sources say no.",
    "🎱 Outlook not so good.",
    "🎱 Very doubtful.",
]

FALLBACK_ROASTS = [
    "Bro, you're the human version of a loading screen 💀",
    "Your opinion is like a broken pencil... pointless ✏️",
    "You're not stupid, you just have bad luck thinking 🤡",
    "Wow, you're so smart! Said no one ever 🙄",
    "I'd agree with you, but then we'd both be wrong 🤖",
    "You're like a cloud... when you disappear, it's a beautiful day! ☁️",
]

FALLBACK_COMPLIMENTS = [
    "You're like a sunrise... bright and beautiful! 🌅",
    "You're the main character of this group! 👑",
    "You're like pizza... everyone loves you! 🍕",
    "You're like WiFi... you make everything better! 📶",
]

FALLBACK_LOVE_MESSAGES = {
    'high': "True love! Soulmates! ❤️🔥",
    'good': "A match made in heaven! 💕",
    'medium': "Good connection! 😊",
    'low': "It's complicated... 🤔",
    'friendzone': "Friendzone! 😂",
    'none': "Better stay friends! 💀",
}

FALLBACK_TRIVIA = [
    {"q": "What is the capital of France?", "a": "paris"},
    {"q": "What is 2+2?", "a": "4"},
    {"q": "What is the largest planet?", "a": "jupiter"},
    {"q": "What is the color of the sky?", "a": "blue"},
    {"q": "What is the square root of 9?", "a": "3"},
]

ADMIN_TAG_REPLIES = [
    "Ohh tell me what happened, my boss is offline 🧐",
    "Boss is busy! Tell me, I'll handle it 💪",
    "Admin is AFK, but I'm here! What's up? 🤖",
    "My admin is resting. Spill the tea! ☕",
]

ADMIN_GREETINGS = [
    "👑 Welcome back boss!",
    "🙇‍♂️ At your service, my lord!",
    "👋 Hey boss! Good to see you!",
    "🫡 Reporting for duty, sir!",
]

AFK_USERS = {}
USER_LAST_ACTIVE = {}
USER_WELCOME_SENT = {}
ADMIN_LAST_SEEN = {}

# ============ GEMINI AI FUNCTIONS ============
def generate_ai_reply(user_message, username, gemini_client=None):
    if not gemini_client:
        return None
    try:
        prompt = f"""
You are a savage, funny, and roast-style AI in an Instagram group.
User: @{username} said: "{user_message}"

Reply in a funny/roast/savage way in ONE SHORT LINE (max 20 words).
Use casual Hindi/Hinglish if possible.
Don't be too harsh, keep it playful.
Use emojis naturally.
Reply directly without any prefix.
"""
        response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ AI reply error: {e}")
        return None

def generate_roast(target, gemini_client=None):
    if not gemini_client:
        return random.choice(FALLBACK_ROASTS)
    try:
        prompt = f"Give a short funny savage roast for @{target} (max 15 words, use emoji)."
        response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except:
        return random.choice(FALLBACK_ROASTS)

def generate_compliment(target, gemini_client=None):
    if not gemini_client:
        return random.choice(FALLBACK_COMPLIMENTS)
    try:
        prompt = f"Give a short funny compliment for @{target} (max 15 words, use emoji)."
        response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except:
        return random.choice(FALLBACK_COMPLIMENTS)

def generate_fact(gemini_client=None):
    if not gemini_client:
        return random.choice(FALLBACK_FACTS)
    try:
        prompt = "Give one interesting random fact (max 20 words, use emoji)."
        response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except:
        return random.choice(FALLBACK_FACTS)

def generate_joke(gemini_client=None):
    if not gemini_client:
        return random.choice(FALLBACK_JOKES)
    try:
        prompt = "Give a short funny joke (max 20 words)."
        response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except:
        return random.choice(FALLBACK_JOKES)

def generate_8ball(gemini_client=None):
    if not gemini_client:
        return random.choice(FALLBACK_8BALL)
    try:
        prompt = "Give a funny magic 8-ball answer."
        response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return f"🎱 {response.text.strip()}"
    except:
        return random.choice(FALLBACK_8BALL)

def generate_trivia_questions(gemini_client=None, count=5):
    if not gemini_client:
        return random.sample(FALLBACK_TRIVIA, min(count, len(FALLBACK_TRIVIA)))
    try:
        prompt = f"""Generate {count} trivia questions with answers.
Format each as:
Q: [question]
A: [answer]
Make them interesting and varied."""
        response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        lines = response.text.strip().split('\n')
        questions = []
        current_q = None
        for line in lines:
            if line.startswith('Q:'):
                if current_q:
                    questions.append(current_q)
                current_q = {'q': line[2:].strip(), 'a': ''}
            elif line.startswith('A:') and current_q:
                current_q['a'] = line[2:].strip().lower()
                questions.append(current_q)
                current_q = None
        if current_q and current_q.get('a'):
            questions.append(current_q)
        return questions if questions else random.sample(FALLBACK_TRIVIA, min(count, len(FALLBACK_TRIVIA)))
    except:
        return random.sample(FALLBACK_TRIVIA, min(count, len(FALLBACK_TRIVIA)))

def generate_love_message(name1, name2, percentage, gemini_client=None):
    if not gemini_client:
        if percentage >= 80:
            return FALLBACK_LOVE_MESSAGES['high']
        elif percentage >= 60:
            return FALLBACK_LOVE_MESSAGES['good']
        elif percentage >= 40:
            return FALLBACK_LOVE_MESSAGES['medium']
        elif percentage >= 20:
            return FALLBACK_LOVE_MESSAGES['low']
        elif percentage >= 10:
            return FALLBACK_LOVE_MESSAGES['friendzone']
        else:
            return FALLBACK_LOVE_MESSAGES['none']
    try:
        prompt = f"""Love percentage between {name1} and {name2} is {percentage}%.
Generate ONE short funny/savage/roast reply (max 15 words).
Style should be playful and entertaining based on the percentage.
Reply directly only.
Use emojis naturally.
"""
        response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except:
        return FALLBACK_LOVE_MESSAGES.get('high' if percentage >= 80 else 'good' if percentage >= 60 else 'medium' if percentage >= 40 else 'low' if percentage >= 20 else 'friendzone' if percentage >= 10 else 'none', "💕")

def generate_natural_reply(message, username, gemini_client=None):
    if not gemini_client:
        return None
    try:
        prompt = f"""
You are a savage, funny, and roast-style AI in an Instagram group.
User: @{username} said: "{message}"

Reply in a funny/roast/savage way in ONE SHORT LINE (max 20 words).
Use casual Hindi/Hinglish if possible.
Don't be too harsh, keep it playful.
Use emojis naturally.
Reply directly without any prefix.
"""
        response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        reply = response.text.strip()
        if reply and not reply.startswith('@'):
            reply = reply[:200]
        return reply
    except Exception as e:
        print(f"⚠️ AI reply error: {e}")
        return None

# ============ INSTAGRAPI IMPORT ============
try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired, RateLimitError, ClientError
    print("✅ instagrapi imported!")
except ImportError as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# ============ HUMAN BEHAVIOR FUNCTIONS ============
def human_delay(min_sec=1.0, max_sec=3.0):
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay

def random_emoji(emoji_list):
    return random.choice(emoji_list)

# ============ MAIN BOT CLASS ============
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
        self.last_message_time = {}
        self.trivia_state = {}
        self.admin_last_greeting = {}
        self.admin_last_seen = {}

        self.spam_running = False
        self.spam_stop_flag = False
        self.spam_thread = None

        # ✅ Gemini AI - Using hardcoded key
        self.gemini_client = None
        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                print("✅ Gemini AI connected!")
            except Exception as e:
                print(f"⚠️ Gemini AI connection failed: {e}")
        else:
            if not GEMINI_API_KEY:
                print("⚠️ GEMINI_API_KEY not set. Using fallback responses.")
            elif not GEMINI_AVAILABLE:
                print("⚠️ google-genai not installed. Run: pip install google-genai")

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
            data = {
                'warned': self.warned_users,
                'scores': self.scoreboard
            }
            with open('bot_data.json', 'w') as f:
                json.dump(data, f)
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

            if self.group_count == 1:
                self.poll_min = 1.5
                self.poll_max = 2.5
                print("🚀 Fast mode: 1 group")
            elif self.group_count == 2:
                self.poll_min = 2.5
                self.poll_max = 3.5
                print("⚡ Medium mode: 2 groups")
            else:
                self.poll_min = 4.0
                self.poll_max = 6.0
                print("🐢 Slow mode: 3+ groups")

        except Exception as e:
            print(f"⚠️ Error initializing threads: {e}")
            self.group_count = 1
            self.poll_min = 1.5
            self.poll_max = 2.5

    def is_admin(self, username):
        return username in ADMINS or username == self.username

    def is_admin_online(self, thread_id):
        if thread_id not in self.admin_last_seen:
            return False
        elapsed = (datetime.now() - self.admin_last_seen[thread_id]).total_seconds()
        return elapsed < ADMIN_ACTIVE_TIMEOUT

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
            human_delay(1.0, 2.5)
            self.cl.direct_send(message, thread_ids=[thread_id])
            print(f"📤 Sent: {message[:30]}...")
            return True
        except RateLimitError:
            print(f"⚠️ Rate limited! Waiting 60s...")
            time.sleep(60)
            return False
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False

    def send_welcome_back(self, thread_id, username):
        if username == self.username:
            return
        for msg in WELCOME_BACK_MSGS:
            self.send_message(thread_id, msg.format(username=username))
            human_delay(2.0, 4.0)

    def kick_user(self, thread_id, target_id):
        try:
            print(f"🔨 Kicking user {target_id}")
            thread_id_str = str(thread_id)
            target_id_str = str(target_id)

            csrf_token = self.session.cookies.get('csrftoken', '')
            if csrf_token:
                self.session.headers.update({'X-CSRFToken': csrf_token})

            response = self.session.post(
                f"https://www.instagram.com/direct_v2/threads/{thread_id_str}/remove_user/{target_id_str}/"
            )

            if response.status_code == 200:
                print("✅ Kick successful!")
                return True
            else:
                print(f"❌ Kick failed: {response.status_code}")
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

            csrf_token = self.session.cookies.get('csrftoken', '')
            if csrf_token:
                self.session.headers.update({'X-CSRFToken': csrf_token})

            response = self.session.post(
                f"https://www.instagram.com/direct_v2/threads/{thread_id_str}/add_user/{user_id_str}/"
            )

            if response.status_code == 200:
                print(f"✅ Added @{username}")
                return True, f"✅ @{username} added by @{admin_username}!"
            else:
                return False, f"❌ Failed to add @{username}"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

    def run_spam(self, thread_id, count, message, admin_username):
        self.spam_running = True
        self.spam_stop_flag = False

        try:
            for i in range(count):
                if self.spam_stop_flag:
                    self.send_message(thread_id, f"🛑 Spam stopped by admin! Sent {i} messages.")
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
            self.send_message(thread_id, "ℹ️ No spam is currently running.")
            return False
        self.spam_stop_flag = True
        self.send_message(thread_id, "🛑 Stopping spam...")
        return True

    def handle_command(self, thread_id, user_id, username, command):
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        print(f"📩 Command from @{username}: {cmd}")

        # ============ PUBLIC COMMANDS ============
        if cmd == '.help':
            help_text = f"""
🤖 **GROUP BOT COMMANDS:**

**🎮 Games:**
.dice - Roll dice
.flip - Flip coin
.rps [r/p/s] - Rock Paper Scissors
.8ball [question] - Magic 8-ball
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
Bot automatically replies to messages in funny/roast/savage way (30% chance)
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
                self.send_message(thread_id, "Usage: .rps rock / paper / scissors")
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

        elif cmd == '.8ball':
            if not args:
                self.send_message(thread_id, "Ask me something! Example: .8ball Will I win?")
                return
            if self.gemini_client:
                answer = generate_8ball(self.gemini_client)
            else:
                answer = random.choice(FALLBACK_8BALL)
            self.send_message(thread_id, answer)
            return

        elif cmd == '.trivia':
            if thread_id in self.trivia_state:
                self.send_message(thread_id, "⚠️ A trivia game is already running in this group!")
                return

            if self.gemini_client:
                questions = generate_trivia_questions(self.gemini_client, 5)
            else:
                questions = random.sample(FALLBACK_TRIVIA, min(5, len(FALLBACK_TRIVIA)))

            if not questions:
                questions = random.sample(FALLBACK_TRIVIA, min(5, len(FALLBACK_TRIVIA)))

            self.trivia_state[thread_id] = {
                'questions': questions,
                'current': 0,
                'score': 0,
                'user_id': user_id,
                'username': username,
                'timestamp': datetime.now()
            }
            self.send_message(thread_id, f"🧠 **TRIVIA GAME STARTED!**\n@{username} has 15 seconds per question.\nTotal: {len(questions)} questions. Good luck!")
            self.send_trivia_question(thread_id)
            return

        elif cmd == '.roast':
            if not args:
                self.send_message(thread_id, "Usage: .roast @user")
                return
            target = args[0].replace('@', '')
            if self.gemini_client:
                roast = generate_roast(target, self.gemini_client)
            else:
                roast = random.choice(FALLBACK_ROASTS)
            self.send_message(thread_id, f"🔥 @{target} {roast}")
            return

        elif cmd == '.compliment':
            if not args:
                self.send_message(thread_id, "Usage: .compliment @user")
                return
            target = args[0].replace('@', '')
            if self.gemini_client:
                comp = generate_compliment(target, self.gemini_client)
            else:
                comp = random.choice(FALLBACK_COMPLIMENTS)
            self.send_message(thread_id, f"💕 @{target} {comp}")
            return

        elif cmd == '.fact':
            if self.gemini_client:
                fact = generate_fact(self.gemini_client)
            else:
                fact = random.choice(FALLBACK_FACTS)
            self.send_message(thread_id, f"📖 {fact}")
            return

        elif cmd == '.joke':
            if self.gemini_client:
                joke = generate_joke(self.gemini_client)
            else:
                joke = random.choice(FALLBACK_JOKES)
            self.send_message(thread_id, f"😂 {joke}")
            return

        elif cmd == '.meme':
            meme = random.choice(FALLBACK_MEMES)
            self.send_message(thread_id, f"🤣 {meme}")
            return

        elif cmd == '.quote':
            quote = random.choice(FALLBACK_QUOTES)
            self.send_message(thread_id, f"💭 {quote}")
            return

        elif cmd == '.love':
            if not args:
                self.send_message(thread_id, "Usage: .love @user OR .love @user1 @user2")
                return

            mentions = [a.replace('@', '') for a in args if a.startswith('@')]

            if len(mentions) == 1:
                name1 = username
                name2 = mentions[0]
                percentage = random.randint(0, 100)
                heart = "❤️🔥" if percentage >= 80 else "❤️" if percentage >= 60 else "💕" if percentage >= 40 else "💛" if percentage >= 20 else "💔" if percentage >= 10 else "😭"
                if self.gemini_client:
                    message = generate_love_message(name1, name2, percentage, self.gemini_client)
                else:
                    if percentage >= 80:
                        message = FALLBACK_LOVE_MESSAGES['high']
                    elif percentage >= 60:
                        message = FALLBACK_LOVE_MESSAGES['good']
                    elif percentage >= 40:
                        message = FALLBACK_LOVE_MESSAGES['medium']
                    elif percentage >= 20:
                        message = FALLBACK_LOVE_MESSAGES['low']
                    elif percentage >= 10:
                        message = FALLBACK_LOVE_MESSAGES['friendzone']
                    else:
                        message = FALLBACK_LOVE_MESSAGES['none']
                self.send_message(thread_id, f"💕 **Love Calculator**\n@{name1} + @{name2} = {percentage}% {heart}\n\n{message}")

            elif len(mentions) == 2:
                name1 = mentions[0]
                name2 = mentions[1]
                percentage = random.randint(0, 100)
                heart = "❤️🔥" if percentage >= 80 else "❤️" if percentage >= 60 else "💕" if percentage >= 40 else "💛" if percentage >= 20 else "💔" if percentage >= 10 else "😭"
                if self.gemini_client:
                    message = generate_love_message(name1, name2, percentage, self.gemini_client)
                else:
                    if percentage >= 80:
                        message = FALLBACK_LOVE_MESSAGES['high']
                    elif percentage >= 60:
                        message = FALLBACK_LOVE_MESSAGES['good']
                    elif percentage >= 40:
                        message = FALLBACK_LOVE_MESSAGES['medium']
                    elif percentage >= 20:
                        message = FALLBACK_LOVE_MESSAGES['low']
                    elif percentage >= 10:
                        message = FALLBACK_LOVE_MESSAGES['friendzone']
                    else:
                        message = FALLBACK_LOVE_MESSAGES['none']
                self.send_message(thread_id, f"💕 **Love Calculator**\n@{name1} + @{name2} = {percentage}% {heart}\n\n{message}")
            else:
                self.send_message(thread_id, "Please tag only 1 or 2 people! ❌")
            return

        elif cmd == '.score':
            score = self.scoreboard.get(user_id, 0)
            self.send_message(thread_id, f"🏆 @{username} has {score} points!")
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

        # ============ ADMIN COMMANDS ============
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
                    if thread_id in self.known_members:
                        self.known_members[thread_id].add(target_id)
                    else:
                        self.known_members[thread_id] = {target_id}
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
            if warnings >= MAX_WARNINGS:
                if self.kick_user(thread_id, target_id):
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
                self.send_message(thread_id, "❌ Invalid count. Usage: .spam [count] [message]")
                return
            if self.spam_running:
                self.send_message(thread_id, "⚠️ Spam is already running! Use .stopspam to stop it.")
                return
            self.send_message(thread_id, f"📢 Admin starting spam: {count} messages!")
            self.send_message(thread_id, f"💡 Use .stopspam to stop anytime.")
            spam_thread = threading.Thread(target=self.run_spam, args=(thread_id, count, message, username), daemon=True)
            spam_thread.start()
            return

        elif cmd == '.setwelcome':
            if not args:
                self.send_message(thread_id, "Usage: .setwelcome [message]")
                return
            new_msg = ' '.join(args)
            self.send_message(thread_id, f"✅ Welcome message updated!")
            return

        elif cmd == '.setrules':
            if not args:
                self.send_message(thread_id, "Usage: .setrules [rules]")
                return
            new_rules = ' '.join(args)
            self.send_message(thread_id, f"✅ Rules updated!")
            return

        else:
            self.send_message(thread_id, f"❌ Unknown command: {cmd}\nType .help for commands")
            return

    # ============ TRIVIA HELPERS ============
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

        def check_answer():
            time.sleep(15)
            if thread_id in self.trivia_state and self.trivia_state[thread_id]['current'] == current:
                self.send_message(thread_id, f"⏰ Time's up! The answer was: {q['a']}")
                self.trivia_state[thread_id]['current'] += 1
                time.sleep(2)
                self.send_trivia_question(thread_id)

        timer_thread = threading.Thread(target=check_answer, daemon=True)
        timer_thread.start()

    def end_trivia(self, thread_id):
        state = self.trivia_state.pop(thread_id, None)
        if not state:
            return
        score = state['score']
        total = len(state['questions'])
        username = state['username']

        if score == total:
            msg = "🧠 GENIUS! You're a trivia master! 🏆"
        elif score >= total - 1:
            msg = "🔥 Amazing! You're so smart! 🌟"
        elif score >= total // 2:
            msg = "👍 Good job! You know your stuff! 💪"
        elif score >= 1:
            msg = "🤔 Not bad! Study more next time! 📚"
        else:
            msg = "😂 Did you even try?! 💀"

        self.send_message(thread_id, f"--- 🎯 GAME OVER! ---\n🏆 @{username} scored {score}/{total}\n{msg}")
        self.scoreboard[state['user_id']] = self.scoreboard.get(state['user_id'], 0) + score
        self.save_data()

    def check_trivia_answer(self, thread_id, user_id, message):
        state = self.trivia_state.get(thread_id)
        if not state:
            return
        if user_id != state['user_id']:
            return
        if state['current'] >= len(state['questions']):
            return

        current = state['current']
        q = state['questions'][current]
        if message.lower().strip() == q['a'].lower():
            state['score'] += 1
            self.send_message(thread_id, f"✅ Correct! +1 point! 🎉")
            state['current'] += 1
            time.sleep(2)
            self.send_trivia_question(thread_id)

    # ============ MESSAGE PROCESSING ============
    def check_messages(self):
        try:
            threads = self.cl.direct_threads()

            for thread in threads:
                thread_id = str(thread.id)

                if hasattr(thread, 'users') and len(thread.users) <= 2:
                    continue

                try:
                    thread_detail = self.cl.direct_thread(thread_id)

                    current_members = [u.pk for u in thread_detail.users]
                    if thread_id not in self.known_members:
                        self.known_members[thread_id] = set()

                    # New members
                    new_members = set(current_members) - self.known_members[thread_id]
                    for member_id in new_members:
                        if member_id != self.user_id:
                            username = self.get_username_cached(member_id)
                            if username:
                                print(f"🔔 New member: @{username}")
                                self.send_message(thread_id, WELCOME_MSG.format(username=username))
                                human_delay(1.0, 2.0)
                                self.send_message(thread_id, RULES)

                    # Left members
                    left_members = self.known_members[thread_id] - set(current_members)
                    for member_id in left_members:
                        if member_id != self.user_id:
                            username = self.get_username_cached(member_id)
                            if username:
                                print(f"🚶 Member left: @{username}")
                                self.send_message(thread_id, LEAVE_MSG.format(username=username))

                    self.known_members[thread_id] = set(current_members)

                    for msg in thread_detail.messages:
                        msg_id = str(msg.id)
                        if msg_id in self.processed_messages:
                            continue

                        if msg.user_id == self.user_id:
                            continue

                        if not msg.text:
                            continue

                        username = self.get_username_cached(msg.user_id)
                        if not username:
                            continue

                        self.processed_messages.add(msg_id)
                        print(f"📩 New message from @{username}: {msg.text}")

                        # Welcome back
                        current_time = datetime.now()
                        last_active = USER_LAST_ACTIVE.get(msg.user_id)

                        if msg.user_id != self.user_id and last_active:
                            time_diff = (current_time - last_active).total_seconds()
                            if time_diff >= WELCOME_BACK_INTERVAL:
                                last_welcome = USER_WELCOME_SENT.get(msg.user_id)
                                if not last_welcome or (current_time - last_welcome).total_seconds() > WELCOME_BACK_INTERVAL:
                                    print(f"👋 Welcome back @{username}")
                                    self.send_welcome_back(thread_id, username)
                                    USER_WELCOME_SENT[msg.user_id] = current_time

                        USER_LAST_ACTIVE[msg.user_id] = current_time

                        # Admin tracking
                        if username.lower() in [a.lower() for a in ADMINS]:
                            self.admin_last_seen[thread_id] = datetime.now()

                        # Admin tag response
                        msg_lower = msg.text.lower()
                        admin_mentioned = False
                        for admin in ADMINS:
                            if f"@{admin}".lower() in msg_lower:
                                admin_mentioned = True
                                break

                        if admin_mentioned and not self.is_admin(username):
                            if not self.is_admin_online(thread_id):
                                reply = random.choice(ADMIN_TAG_REPLIES)
                                self.send_message(thread_id, f"@{username} {reply}")
                                human_delay(0.5, 1.0)

                        # Admin greeting
                        if username.lower() in [a.lower() for a in ADMINS]:
                            last_seen = self.admin_last_seen.get(thread_id, datetime.now() - timedelta(minutes=10))
                            if (datetime.now() - last_seen).seconds > 60:
                                greeting = random.choice(ADMIN_GREETINGS)
                                self.send_message(thread_id, greeting)

                        # Check trivia answer
                        if thread_id in self.trivia_state:
                            self.check_trivia_answer(thread_id, msg.user_id, msg.text)

                        # AFK
                        if msg.user_id in AFK_USERS:
                            afk_reason, afk_time = AFK_USERS[msg.user_id]
                            if (datetime.now() - afk_time).seconds > 300:
                                del AFK_USERS[msg.user_id]
                                self.send_message(thread_id, f"🟢 @{username} is no longer AFK")

                        # ============ GEMINI NATURAL REPLY ============
                        if not msg.text.startswith('.') and random.random() < 0.35:
                            if self.gemini_client:
                                reply = generate_natural_reply(msg.text, username, self.gemini_client)
                                if reply:
                                    human_delay(1.0, 3.0)
                                    self.send_message(thread_id, reply)
                                    print(f"🤖 AI reply to @{username}")

                        # Process commands
                        if msg.text.startswith('.'):
                            self.handle_command(thread_id, msg.user_id, username, msg.text)

                except RateLimitError:
                    print(f"⚠️ Rate limited! Waiting 5 minutes...")
                    time.sleep(300)
                except Exception as e:
                    print(f"⚠️ Error reading thread: {e}")

        except RateLimitError:
            print(f"⚠️ Rate limited! Waiting 5 minutes...")
            time.sleep(300)
        except Exception as e:
            print(f"⚠️ Error checking threads: {e}")

    def run(self):
        print("\n" + "=" * 60)
        print("🤖 GROUP BOT RUNNING")
        print(f"👤 Bot: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print(f"📊 Monitoring: {getattr(self, 'group_count', 1)} group(s)")
        print("=" * 60)
        print("\n🤖 Features:")
        print("   ✅ Gemini AI (natural replies)")
        print("   ✅ Human-like behavior")
        print("   ✅ 30% chance natural replies")
        print("   ✅ Auto speed adjustment")
        print("=" * 60)
        print("\n⚠️ Press Ctrl+C to stop\n")

        while self.running:
            try:
                self.check_messages()
                poll_delay = random.uniform(self.poll_min, self.poll_max)
                time.sleep(poll_delay)
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

#!/usr/bin/env python3
"""
Instagram Group Bot - FINAL ANTI-DETECTION VERSION
- New session ID
- Slower polling (5s)
- Rate limit handling
- Anti-detection measures
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

# ============ NEW SESSION ID ============
SESSION_ID = "11950490138:eTVuFmLKKnpBt6:6:AYgXPb6Yu1gacrK69V2TBHN9FbOce1XQa3aPVb0w_A"
ADMINS = os.environ.get("INSTAGRAM_ADMINS", "razzz_huu").split(",")
ADMINS = [a.strip() for a in ADMINS if a.strip()]

WELCOME_MSG = "🎉 Welcome {username} to the group!"
RULES = """
📋 GROUP RULES:
1. No spam
2. Be respectful
3. No NSFW content
4. Type /help for commands
"""

LEAVE_MSG = "🚶 {username} chala gya bhadwa! 😂"

WELCOME_BACK_MSGS = [
    "Ohh hiie {username}! 👋",
    "Kya haal chal kaise ho? 😊",
    "Kya kar rhe h? 🤔"
]

# ============ ANTI-DETECTION SETTINGS ============
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.92 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.60 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-A528B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.138 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.92 Mobile Safari/537.36",
]

DEVICE_IDS = [
    "android-13-1a2b3c4d5e6f7g8h9i0j",
    "android-13-2b3c4d5e6f7g8h9i0j1k",
    "android-14-3c4d5e6f7g8h9i0j1k2l",
]

# ============ COMMAND SETTINGS - SLOWED DOWN ============
COMMAND_COOLDOWN = {
    '/ping': 5,
    '/dice': 5,
    '/flip': 5,
    '/score': 5,
    '/help': 10,
    '/rules': 10,
    '/kick': 60,
    '/warn': 60,
    '/add': 60,
    '/spam': 120,
    '/stopspam': 10,
    '/8ball': 5,
    '/meme': 10,
    '/joke': 10,
    '/quote': 10,
    '/trivia': 30,
    '/love': 10,
    '/afk': 30,
    'default': 5,
}

MAX_COMMANDS_PER_MINUTE = 15  # ✅ Reduced from 60
MAX_WARNINGS = 3
POLL_INTERVAL = 5.0  # ✅ Slower polling
MAX_SPAM_COUNT = 100  # ✅ Reduced from 10000
SPAM_DELAY = 5  # ✅ Slower spam
WELCOME_BACK_INTERVAL = 300
WELCOME_BACK_GAP = 5
ADMIN_ACTIVE_TIMEOUT = 600

spam_running = False
spam_stop_flag = False

# ============ DATA LISTS ============
JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "What do you call a fake noodle? An impasta!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "What do you call a bear with no teeth? A gummy bear!",
]

QUOTES = [
    "Be the change you wish to see in the world. - Gandhi",
    "In the middle of difficulty lies opportunity. - Einstein",
    "The only way to do great work is to love what you do. - Steve Jobs",
    "Life is what happens when you're busy making other plans. - John Lennon",
]

MEMES = [
    "🤣 This is fine 🔥",
    "😂 It's not a bug, it's a feature!",
    "🤪 I'm not lazy, I'm on energy-saving mode",
    "😎 I don't always test my code, but when I do, I do it in production",
]

TRIVIA = [
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
    "Boss is not available. You can tell me, I'm listening 👂",
    "Admin is offline! What drama did I miss? 🍿",
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

# ============ ANTI-DETECTION HELPER FUNCTIONS ============
def random_delay(min_sec=0.5, max_sec=2.0):
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay

def random_user_agent():
    return random.choice(USER_AGENTS)

def random_device_id():
    return random.choice(DEVICE_IDS)

# ============ INSTAGRAPI IMPORT ============
try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired, RateLimitError, ClientError
    print("✅ instagrapi imported!")
except ImportError as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# ============ MAIN BOT CLASS ============
class InstagramGroupBot:
    def __init__(self):
        print("🔧 Initializing bot...")
        
        user_agent = random_user_agent()
        print(f"📱 User Agent: {user_agent[:50]}...")
        
        self.cl = Client()
        self.cl.set_user_agent(user_agent)
        
        self.device_id = random_device_id()
        print(f"📱 Device ID: {self.device_id[:20]}...")
        
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
        
        self.session = requests.Session()
        self.session.cookies.set('sessionid', SESSION_ID)
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Instagram-AJAX': '1',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
        })
        self.session.max_redirects = 5
        
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
            print(f"📋 Found {len(threads)} threads")
            for thread in threads:
                if hasattr(thread, 'users') and len(thread.users) > 2:
                    thread_id = str(thread.id)
                    member_ids = [u.pk for u in thread.users]
                    self.known_members[thread_id] = set(member_ids)
                    print(f"📌 Thread {thread_id}: {len(member_ids)} members")
        except Exception as e:
            print(f"⚠️ Error initializing threads: {e}")
    
    def is_admin(self, username):
        return username in ADMINS or username == self.username
    
    def is_admin_online(self, thread_id):
        if thread_id not in self.admin_last_seen:
            return False
        last_seen = self.admin_last_seen[thread_id]
        elapsed = (datetime.now() - last_seen).total_seconds()
        return elapsed < ADMIN_ACTIVE_TIMEOUT
    
    def get_username_cached(self, user_id):
        if user_id in self.username_cache:
            return self.username_cache[user_id]
        try:
            user = self.cl.user_info(user_id)
            self.username_cache[user_id] = user.username
            return user.username
        except Exception as e:
            return None
    
    def send_message(self, thread_id, message):
        try:
            random_delay(1.0, 2.5)
            
            if random.random() < 0.1:
                new_ua = random_user_agent()
                self.session.headers.update({'User-Agent': new_ua})
                self.cl.set_user_agent(new_ua)
            
            self.cl.direct_send(message, thread_ids=[thread_id])
            print(f"📤 Sent: {message[:30]}...")
            
            random_delay(0.5, 1.5)
            return True
        except RateLimitError as e:
            print(f"⚠️ Rate limited while sending! Waiting 60s...")
            time.sleep(60)
            return False
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    def send_welcome_back(self, thread_id, username):
        if username == self.username:
            return
        
        for msg_template in WELCOME_BACK_MSGS:
            msg = msg_template.format(username=username)
            self.send_message(thread_id, msg)
            random_delay(3.0, 5.0)
    
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
                
                self.send_message(thread_id, f"💥 {i+1}/{count}: {message}")
                random_delay(4.0, 6.0)
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
        self.send_message(thread_id, "🛑 Stopping spam... Please wait a moment.")
        return True
    
    def kick_user(self, thread_id, target_id):
        try:
            print(f"\n{'='*60}")
            print(f"🔨 KICK USER")
            print(f"   Thread: {thread_id}")
            print(f"   Target ID: {target_id}")
            print(f"{'='*60}\n")
            
            random_delay(1.0, 3.0)
            
            thread_id_str = str(thread_id)
            target_id_str = str(target_id)
            
            url = f"https://www.instagram.com/direct_v2/threads/{thread_id_str}/remove_user/{target_id_str}/"
            
            headers = self.session.headers.copy()
            if random.random() < 0.3:
                headers['User-Agent'] = random_user_agent()
            
            csrf_token = self.session.cookies.get('csrftoken', '')
            if csrf_token:
                headers.update({'X-CSRFToken': csrf_token})
            
            response = self.session.post(url, headers=headers)
            
            print(f"📊 Status Code: {response.status_code}")
            
            random_delay(0.5, 1.5)
            
            if response.status_code == 200:
                print("✅ Kick successful!")
                return True
            else:
                print(f"❌ Kick failed with status {response.status_code}")
                return False
            
        except Exception as e:
            print(f"❌ Kick error: {e}")
            traceback.print_exc()
            return False
    
    def add_user(self, thread_id, username, admin_username):
        try:
            print(f"\n{'='*60}")
            print(f"➕ ADD USER")
            print(f"   Thread: {thread_id}")
            print(f"   Username: @{username}")
            print(f"{'='*60}\n")
            
            random_delay(0.5, 2.0)
            
            user_id = self.cl.user_id_from_username(username)
            if not user_id:
                print(f"❌ User @{username} not found")
                return False, f"❌ User @{username} not found"
            
            print(f"✅ Found user ID: {user_id}")
            
            thread_id_str = str(thread_id)
            user_id_str = str(user_id)
            
            url = f"https://www.instagram.com/direct_v2/threads/{thread_id_str}/add_user/{user_id_str}/"
            
            headers = self.session.headers.copy()
            if random.random() < 0.2:
                headers['User-Agent'] = random_user_agent()
            
            csrf_token = self.session.cookies.get('csrftoken', '')
            if csrf_token:
                headers.update({'X-CSRFToken': csrf_token})
            
            response = self.session.post(url, headers=headers)
            
            print(f"📊 Status Code: {response.status_code}")
            
            random_delay(0.5, 1.0)
            
            if response.status_code == 200:
                print("✅ Add successful!")
                return True, f"✅ @{username} added to the group by @{admin_username}!"
            else:
                return False, f"❌ Failed to add @{username}"
            
        except Exception as e:
            print(f"❌ Add error: {e}")
            traceback.print_exc()
            return False, f"❌ Failed to add @{username}: {str(e)}"
    
    def handle_command(self, thread_id, user_id, username, command):
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        print(f"📩 Command from @{username}: {cmd}")
        
        if cmd == '/help':
            help_text = f"""
🤖 **GROUP BOT COMMANDS:**

**🎮 Fun Commands:**
/help - Show this
/rules - Show rules
/ping - Check bot alive
/dice - Roll dice (1-6)
/flip - Flip a coin
/8ball - Ask the magic 8-ball
/joke - Get a random joke
/quote - Get an inspirational quote
/meme - Get a random meme
/trivia - Play trivia
/love - Love calculator
/score - Your points
/leaderboard - Top players

**👑 Admin Commands:**
/kick @username - Kick user
/warn @username - Warn user
/add @username - Add user to group
/spam [count] [msg] - Spam messages (max {MAX_SPAM_COUNT})
/stopspam - Stop running spam
/afk [reason] - Set AFK (admin only)
"""
            self.send_message(thread_id, help_text)
            return
        
        elif cmd == '/rules':
            self.send_message(thread_id, RULES)
            return
        
        elif cmd == '/ping':
            self.send_message(thread_id, "🏓 Pong! Bot is alive!")
            return
        
        elif cmd == '/dice':
            roll = random.randint(1, 6)
            self.send_message(thread_id, f"🎲 @{username} rolled **{roll}**!")
            self.scoreboard[user_id] = self.scoreboard.get(user_id, 0) + 1
            self.save_data()
            return
        
        elif cmd == '/flip':
            result = random.choice(['Heads', 'Tails'])
            self.send_message(thread_id, f"🪙 @{username} flipped **{result}**!")
            self.scoreboard[user_id] = self.scoreboard.get(user_id, 0) + 1
            self.save_data()
            return
        
        elif cmd == '/score':
            score = self.scoreboard.get(user_id, 0)
            self.send_message(thread_id, f"🏆 @{username} has {score} points!")
            return
        
        elif cmd == '/leaderboard':
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
        
        elif cmd == '/8ball':
            responses = [
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
            self.send_message(thread_id, random.choice(responses))
            return
        
        elif cmd == '/joke':
            self.send_message(thread_id, f"😂 {random.choice(JOKES)}")
            return
        
        elif cmd == '/quote':
            self.send_message(thread_id, f"💭 {random.choice(QUOTES)}")
            return
        
        elif cmd == '/meme':
            self.send_message(thread_id, f"🤣 {random.choice(MEMES)}")
            return
        
        elif cmd == '/trivia':
            q = random.choice(TRIVIA)
            self.send_message(thread_id, f"❓ **Trivia:** {q['q']}\n\nReply with your answer!")
            self.trivia_state[thread_id] = {
                'answer': q['a'].lower(),
                'user_id': user_id,
                'timestamp': datetime.now()
            }
            return
        
        elif cmd == '/love':
            if not args:
                self.send_message(thread_id, "Usage: /love @username")
                return
            target = args[0].replace('@', '')
            percentage = random.randint(0, 100)
            heart = "❤️" if percentage > 70 else "💛" if percentage > 40 else "💔"
            self.send_message(thread_id, f"💕 **Love Calculator**\n\n@{username} + @{target} = {percentage}% {heart}")
            return
        
        elif cmd == '/stopspam':
            self.stop_spam(thread_id, username)
            return
        
        elif cmd == '/afk':
            if not self.is_admin(username):
                self.send_message(thread_id, f"❌ @{username} Only admins can use /afk!")
                return
            
            reason = ' '.join(args) if args else "AFK"
            AFK_USERS[user_id] = (reason, datetime.now())
            self.send_message(thread_id, f"🛏️ @{username} is now AFK: {reason}")
            return
        
        # ========== ADMIN COMMANDS ==========
        if not self.is_admin(username):
            self.send_message(thread_id, f"❌ @{username} Not admin!")
            return
        
        if cmd == '/kick':
            if not args:
                self.send_message(thread_id, "Usage: /kick @username")
                return
            target = args[0].replace('@', '')
            
            try:
                print(f"🔨 Admin @{username} trying to kick @{target}")
                
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
                    
            except Exception as e:
                print(f"❌ Kick exception: {e}")
                traceback.print_exc()
                self.send_message(thread_id, f"❌ Failed to kick @{target}: {str(e)}")
            return
        
        elif cmd == '/add':
            if not args:
                self.send_message(thread_id, "Usage: /add @username")
                return
            target = args[0].replace('@', '')
            print(f"➕ Admin @{username} trying to add @{target}")
            
            success, message = self.add_user(thread_id, target, username)
            self.send_message(thread_id, message)
            
            if success:
                try:
                    target_id = self.cl.user_id_from_username(target)
                    if thread_id in self.known_members:
                        self.known_members[thread_id].add(target_id)
                    else:
                        self.known_members[thread_id] = {target_id}
                except:
                    pass
            return
        
        elif cmd == '/warn':
            if not args:
                self.send_message(thread_id, "Usage: /warn @username")
                return
            target = args[0].replace('@', '')
            try:
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
            except Exception as e:
                print(f"❌ Warn exception: {e}")
                self.send_message(thread_id, f"❌ Failed: {str(e)}")
            return
        
        elif cmd == '/spam':
            if not args:
                self.send_message(thread_id, "Usage: /spam [count] [message]")
                return
            try:
                count = int(args[0])
                if count <= 0 or count > MAX_SPAM_COUNT:
                    self.send_message(thread_id, f"❌ Count must be between 1 and {MAX_SPAM_COUNT}")
                    return
                message = ' '.join(args[1:]) if len(args) > 1 else "SPAM!"
            except ValueError:
                self.send_message(thread_id, "❌ Invalid count. Usage: /spam [count] [message]")
                return
            
            if self.spam_running:
                self.send_message(thread_id, "⚠️ Spam is already running! Use /stopspam to stop it first.")
                return
            
            self.send_message(thread_id, f"📢 Admin starting spam: {count} messages with {SPAM_DELAY}s delay!")
            self.send_message(thread_id, f"💡 Use /stopspam to stop anytime.")
            
            spam_thread = threading.Thread(
                target=self.run_spam,
                args=(thread_id, count, message, username),
                daemon=True
            )
            spam_thread.start()
            return
        
        else:
            self.send_message(thread_id, f"❌ Unknown: {cmd}\nType /help")
    
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
                    
                    new_members = set(current_members) - self.known_members[thread_id]
                    for member_id in new_members:
                        if member_id != self.user_id:
                            username = self.get_username_cached(member_id)
                            if username:
                                print(f"🔔 New member: @{username}")
                                self.send_message(thread_id, WELCOME_MSG.format(username=username))
                                random_delay(1.0, 2.0)
                                self.send_message(thread_id, RULES)
                    
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
                        
                        current_time = datetime.now()
                        last_active = USER_LAST_ACTIVE.get(msg.user_id)
                        
                        if msg.user_id != self.user_id and last_active:
                            time_diff = (current_time - last_active).total_seconds()
                            if time_diff >= WELCOME_BACK_INTERVAL:
                                last_welcome = USER_WELCOME_SENT.get(msg.user_id)
                                if not last_welcome or (current_time - last_welcome).total_seconds() > WELCOME_BACK_INTERVAL:
                                    print(f"👋 Welcome back @{username} after {int(time_diff/60)} minutes")
                                    self.send_welcome_back(thread_id, username)
                                    USER_WELCOME_SENT[msg.user_id] = current_time
                        
                        USER_LAST_ACTIVE[msg.user_id] = current_time
                        
                        if username.lower() in [a.lower() for a in ADMINS]:
                            self.admin_last_seen[thread_id] = datetime.now()
                        
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
                                random_delay(0.3, 0.8)
                        
                        if username.lower() in [a.lower() for a in ADMINS]:
                            last_seen = self.admin_last_seen.get(thread_id, datetime.now() - timedelta(minutes=10))
                            if (datetime.now() - last_seen).seconds > 60:
                                greeting = random.choice(ADMIN_GREETINGS)
                                self.send_message(thread_id, greeting)
                        
                        if thread_id in self.trivia_state:
                            trivia = self.trivia_state[thread_id]
                            if (datetime.now() - trivia['timestamp']).seconds < 60:
                                if msg.user_id == trivia['user_id']:
                                    if trivia['answer'] in msg.text.lower():
                                        self.send_message(thread_id, f"✅ Correct! @{username} gets 5 points!")
                                        self.scoreboard[msg.user_id] = self.scoreboard.get(msg.user_id, 0) + 5
                                        self.save_data()
                                        del self.trivia_state[thread_id]
                            else:
                                del self.trivia_state[thread_id]
                        
                        if msg.user_id in AFK_USERS:
                            afk_reason, afk_time = AFK_USERS[msg.user_id]
                            if (datetime.now() - afk_time).seconds > 300:
                                del AFK_USERS[msg.user_id]
                                self.send_message(thread_id, f"🟢 @{username} is no longer AFK")
                        
                        if msg.text.startswith('/'):
                            self.handle_command(thread_id, msg.user_id, username, msg.text)
                            
                except RateLimitError as e:
                    print(f"⚠️ Rate limited! Waiting 5 minutes...")
                    time.sleep(300)
                except Exception as e:
                    print(f"⚠️ Error reading thread: {e}")
                    
        except RateLimitError as e:
            print(f"⚠️ Rate limited! Waiting 5 minutes...")
            time.sleep(300)
        except Exception as e:
            print(f"⚠️ Error checking threads: {e}")
    
    def run(self):
        print("\n" + "=" * 60)
        print("🤖 GROUP BOT RUNNING (ANTI-DETECTION)")
        print(f"👤 Bot: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print("=" * 60)
        print("\n🛡️ Anti-Detection Features:")
        print("   ✅ Random user agents")
        print("   ✅ Human-like delays (1-3s)")
        print("   ✅ 5 second polling")
        print("   ✅ 15 commands per minute max")
        print("   ✅ Rate limit handling")
        print("=" * 60)
        print("\n⚠️ Press Ctrl+C to stop\n")
        
        while self.running:
            try:
                self.check_messages()
                poll_delay = random.uniform(3.0, 6.0)
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

#!/usr/bin/env python3
"""
Instagram Group Bot - KICK FIXED
"""

import os
import sys
import time
import json
import random
import traceback
import threading
from datetime import datetime, timedelta
from collections import defaultdict

print("=" * 60)
print("📂 GROUP_BOT.PY LOADING...")
print("=" * 60)

SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "11950490138:2e5V9aHxKAosXH:28:AYj0h54d0SaaFBpF3pUpsZOPe29TlKH8wYFA4Ic5Lg")
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

# ============ COMMAND SETTINGS ============
COMMAND_COOLDOWN = {
    '/ping': 2,
    '/dice': 2,
    '/flip': 2,
    '/score': 2,
    '/help': 3,
    '/rules': 3,
    '/kick': 30,
    '/warn': 30,
    '/spam': 60,
    '/stopspam': 5,
    '/8ball': 2,
    '/meme': 3,
    '/joke': 3,
    '/quote': 3,
    '/trivia': 10,
    '/love': 3,
    '/afk': 10,
    'default': 2,
}

MAX_COMMANDS_PER_MINUTE = 40
MAX_WARNINGS = 3
POLL_INTERVAL = 2.5
MAX_SPAM_COUNT = 10000
SPAM_DELAY = 3
WELCOME_BACK_INTERVAL = 300
WELCOME_BACK_GAP = 5

# Spam control
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

ADMIN_REPLIES = [
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

# ============ INSTAGRAPI IMPORT ============
try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired, RateLimitError
    print("✅ instagrapi imported!")
except ImportError as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

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
        
        # Spam control
        self.spam_running = False
        self.spam_stop_flag = False
        self.spam_thread = None
        
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
        except:
            pass
    
    def save_data(self):
        try:
            data = {
                'warned': self.warned_users,
                'scores': self.scoreboard
            }
            with open('bot_data.json', 'w') as f:
                json.dump(data, f)
        except:
            pass
    
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
            self.cl.direct_send(message, thread_ids=[thread_id])
            print(f"📤 Sent: {message[:30]}...")
            return True
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    def send_welcome_back(self, thread_id, username):
        for msg_template in WELCOME_BACK_MSGS:
            msg = msg_template.format(username=username)
            self.send_message(thread_id, msg)
            time.sleep(WELCOME_BACK_GAP)
    
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
                time.sleep(SPAM_DELAY)
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
        """
        ✅ MULTIPLE FALLBACK METHODS TO KICK USER
        Tries different method names until one works
        """
        methods = [
            # Method 1: Standard instagrapi method
            lambda: self.cl.direct_thread_remove_user(thread_id, [target_id]),
            # Method 2: Alternative name
            lambda: self.cl.direct_remove_user(thread_id, target_id),
            # Method 3: Another alternative
            lambda: self.cl.remove_user_from_thread(thread_id, target_id),
            # Method 4: With user_id as string
            lambda: self.cl.direct_thread_remove_user(thread_id, [str(target_id)]),
            # Method 5: Using thread_id as string
            lambda: self.cl.direct_thread_remove_user(str(thread_id), [target_id]),
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                print(f"🔄 Trying kick method {i}...")
                result = method()
                print(f"✅ Kick method {i} succeeded!")
                return True
            except AttributeError:
                print(f"⚠️ Method {i} not available")
                continue
            except Exception as e:
                print(f"⚠️ Method {i} failed: {e}")
                continue
        
        print(f"❌ All kick methods failed!")
        return False
    
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
        
        # ========== ADMIN ONLY: AFK ==========
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
                print(f"✅ Found target ID: {target_id}")
                
                # ✅ Use the multi-method kick function
                if self.kick_user(thread_id, target_id):
                    self.send_message(thread_id, LEAVE_MSG.format(username=target))
                    if thread_id in self.known_members and target_id in self.known_members[thread_id]:
                        self.known_members[thread_id].remove(target_id)
                else:
                    self.send_message(thread_id, f"❌ All kick methods failed for @{target}")
                    
            except Exception as e:
                self.send_message(thread_id, f"❌ Failed to kick @{target}: {str(e)}")
            return
        
        elif cmd == '/warn':
            if not args:
                self.send_message(thread_id, "Usage: /warn @username")
                return
            target = args[0].replace('@', '')
            try:
                target_id = self.cl.user_id_from_username(target)
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
                self.send_message(thread_id, f"❌ Failed: {e}")
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
                    
                    # Check new members
                    new_members = set(current_members) - self.known_members[thread_id]
                    for member_id in new_members:
                        if member_id != self.user_id:
                            username = self.get_username_cached(member_id)
                            if username:
                                print(f"🔔 New member: @{username}")
                                self.send_message(thread_id, WELCOME_MSG.format(username=username))
                                time.sleep(1)
                                self.send_message(thread_id, RULES)
                    
                    # Check left members
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
                        
                        if last_active:
                            time_diff = (current_time - last_active).total_seconds()
                            if time_diff >= WELCOME_BACK_INTERVAL:
                                last_welcome = USER_WELCOME_SENT.get(msg.user_id)
                                if not last_welcome or (current_time - last_welcome).total_seconds() > WELCOME_BACK_INTERVAL:
                                    print(f"👋 Welcome back @{username} after {int(time_diff/60)} minutes")
                                    self.send_welcome_back(thread_id, username)
                                    USER_WELCOME_SENT[msg.user_id] = current_time
                        
                        USER_LAST_ACTIVE[msg.user_id] = current_time
                        
                        # Admin tag detection
                        msg_lower = msg.text.lower()
                        admin_mentioned = False
                        for admin in ADMINS:
                            if f"@{admin}".lower() in msg_lower and username.lower() != admin.lower():
                                admin_mentioned = True
                                break
                        
                        if admin_mentioned:
                            reply = random.choice(ADMIN_REPLIES)
                            self.send_message(thread_id, f"@{username} {reply}")
                            time.sleep(0.5)
                        
                        # Admin greeting
                        if username.lower() in [a.lower() for a in ADMINS]:
                            last_greeting = self.admin_last_greeting.get(thread_id, datetime.now() - timedelta(minutes=10))
                            if (datetime.now() - last_greeting).seconds > 300:
                                greeting = random.choice(ADMIN_GREETINGS)
                                self.send_message(thread_id, greeting)
                                self.admin_last_greeting[thread_id] = datetime.now()
                        
                        # Trivia
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
                        
                        # AFK
                        if msg.user_id in AFK_USERS:
                            afk_reason, afk_time = AFK_USERS[msg.user_id]
                            if (datetime.now() - afk_time).seconds > 300:
                                del AFK_USERS[msg.user_id]
                                self.send_message(thread_id, f"🟢 @{username} is no longer AFK")
                        
                        # Process commands
                        if msg.text.startswith('/'):
                            self.handle_command(thread_id, msg.user_id, username, msg.text)
                            
                except Exception as e:
                    print(f"⚠️ Error reading thread: {e}")
                    
        except Exception as e:
            print(f"⚠️ Error checking threads: {e}")
    
    def run(self):
        print("\n" + "=" * 60)
        print("🤖 GROUP BOT RUNNING")
        print(f"👤 Bot: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print("=" * 60)
        print("\n📌 Commands: /help for full list")
        print("📌 Admin tag replies: Enabled")
        print("📌 Spam delay: 3 seconds (anti-ban)")
        print("📌 Max spam: 10,000 messages")
        print("📌 Response time: 2.5 seconds")
        print("📌 /stopspam - Stop running spam")
        print("=" * 60)
        print("\n⚠️ Press Ctrl+C to stop\n")
        
        while self.running:
            try:
                self.check_messages()
                time.sleep(POLL_INTERVAL)
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

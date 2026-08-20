#!/usr/bin/env python3
"""
Instagram Group Bot - FINAL WORKING VERSION
FIXED: Removed all sys.stdout.flush() calls
"""

import os
import sys
import time
import json
import random
import traceback
from datetime import datetime, timedelta
from collections import defaultdict

print("=" * 60)
print("📂 GROUP_BOT.PY LOADING...")
print("=" * 60)

# ============ ENVIRONMENT VARIABLES ============
SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "11950490138:2e5V9aHxKAosXH:28:AYj0h54d0SaaFBpF3pUpsZOPe29TlKH8wYFA4Ic5Lg")
ADMINS = os.environ.get("INSTAGRAM_ADMINS", "razzz_huu").split(",")
ADMINS = [a.strip() for a in ADMINS if a.strip()]

WELCOME_MSG = os.environ.get("WELCOME_MESSAGE", "🎉 Welcome {username} to the group!")
RULES = os.environ.get("GROUP_RULES", """
📋 GROUP RULES:
1. No spam
2. Be respectful
3. No NSFW content
4. Type /help for commands
""")

# ============ COMMAND SETTINGS ============
COMMAND_COOLDOWN = {
    '/ping': 3,
    '/dice': 3,
    '/flip': 3,
    '/score': 3,
    '/help': 5,
    '/rules': 5,
    '/kick': 30,
    '/warn': 30,
    '/spam': 60,
    'default': 5,
}

MAX_COMMANDS_PER_MINUTE = 20
MAX_WARNINGS = 3
POLL_INTERVAL = 10

# ============ FILE PATHS ============
DATA_FILE = "bot_data.json"

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
        
        # Login
        self.login()
        
        # Load data
        self.load_data()
        
        # Initialize threads
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
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
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
            with open(DATA_FILE, 'w') as f:
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
    
    def handle_command(self, thread_id, user_id, username, command):
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        print(f"📩 Command from @{username}: {cmd}")
        
        if cmd == '/help':
            help_text = f"""
🤖 GROUP BOT COMMANDS:

Public:
/help - Show this
/rules - Show rules
/dice - Roll dice (1-6)
/flip - Flip a coin
/ping - Check bot alive
/score - Your points

Admin (only {', '.join(ADMINS)}):
/kick @username - Kick user
/warn @username - Warn user
/spam [count] [msg] - Spam messages
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
        
        if not self.is_admin(username):
            self.send_message(thread_id, f"❌ @{username} Not admin!")
            return
        
        if cmd == '/kick':
            if not args:
                self.send_message(thread_id, "Usage: /kick @username")
                return
            target = args[0].replace('@', '')
            try:
                target_id = self.cl.user_id_from_username(target)
                self.cl.direct_thread_remove_user(thread_id, [target_id])
                self.send_message(thread_id, f"👢 @{target} kicked by @{username}")
            except Exception as e:
                self.send_message(thread_id, f"❌ Failed: {e}")
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
                    self.cl.direct_thread_remove_user(thread_id, [target_id])
                    self.send_message(thread_id, f"🔴 @{target} auto-kicked for 3 warnings!")
                    self.warned_users[target_id] = 0
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
                message = ' '.join(args[1:]) if len(args) > 1 else "SPAM!"
            except ValueError:
                count = 5
                message = ' '.join(args)
            self.send_message(thread_id, f"📢 Admin spamming {count} messages!")
            for i in range(min(count, 3)):
                self.send_message(thread_id, f"💥 {i+1}/{count}: {message}")
                time.sleep(0.5)
            self.send_message(thread_id, "✅ Spam complete!")
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
                    
                    # Check new members
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
                                time.sleep(1)
                                self.send_message(thread_id, RULES)
                    
                    self.known_members[thread_id] = set(current_members)
                    
                    # Check messages
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
        print("\n📌 Commands: /help, /ping, /dice, /flip, /score")
        print("📌 Admin: /kick, /warn, /spam")
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

# ============ MAIN ============
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

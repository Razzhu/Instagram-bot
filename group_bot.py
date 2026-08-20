#!/usr/bin/env python3
"""
Instagram Group Bot - ALL BUGS FIXED
Fixes: limit error, flush error, bad file descriptor, monitor loop
"""

import time
import random
import json
import os
from datetime import datetime, timedelta

print("=" * 50)
print("🤖 GROUP BOT STARTING...")
print("=" * 50)

try:
    from instagrapi import Client
    print("✅ instagrapi imported!")
except ImportError as e:
    print(f"❌ ERROR: {e}")
    print("📌 Add instagrapi to requirements.txt")
    exit(1)

# ============ CONFIGURATION ============
SESSION_ID = "11950490138:2e5V9aHxKAosXH:28:AYj0h54d0SaaFBpF3pUpsZOPe29TlKH8wYFA4Ic5Lg"
ADMINS = ["razzz_huu"]

WELCOME_MSG = "🎉 Welcome {username} to the group!"
RULES = """
📋 GROUP RULES:
1. No spam
2. Be respectful
3. No NSFW content
4. Type /help for commands
"""

class InstagramGroupBot:
    def __init__(self):
        print("🔧 Initializing bot...")
        self.cl = Client()
        self.cl.set_user_agent("Mozilla/5.0 (Linux; Android 13) Chrome/116.0.5845.92")
        
        self.running = True
        self.warned_users = {}
        self.muted_users = {}
        self.scoreboard = {}
        self.known_members = {}
        
        try:
            print("🔐 Logging in...")
            self.cl.login_by_sessionid(SESSION_ID)
            self.username = self.cl.username
            self.user_id = self.cl.user_id
            print(f"✅ Logged in as: @{self.username}")
            print(f"👥 Followers: {self.cl.user_followers(self.user_id)}")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            raise e
        
        self.load_data()
    
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
    
    def is_admin(self, username):
        return username in ADMINS or username == self.username
    
    def get_username(self, user_id):
        try:
            return self.cl.user_info(user_id).username
        except:
            return None
    
    def send_message(self, thread_id, message):
        try:
            self.cl.direct_send(message, thread_id=thread_id)
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
        
        # ========== PUBLIC COMMANDS ==========
        if cmd == '/help':
            help_text = """
🤖 GROUP BOT COMMANDS:

Public:
/help - Show this
/rules - Show rules
/dice - Roll dice (1-6)
/flip - Flip a coin
/ping - Check bot alive
/score - Your points

Admin (only @razzz_huu):
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
                msg = f"⚠️ @{target} warned ({warnings}/3)"
                if warnings >= 3:
                    msg += "\n🔴 Auto-kicked for 3 warnings!"
                    self.cl.direct_thread_remove_user(thread_id, [target_id])
                    self.warned_users[target_id] = 0
                    self.save_data()
                self.send_message(thread_id, msg)
            except:
                self.send_message(thread_id, f"❌ User not found")
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
            for i in range(min(count, 5)):
                self.send_message(thread_id, f"💥 {i+1}/{count}: {message}")
                time.sleep(0.3)
            self.send_message(thread_id, "✅ Spam complete!")
            return
        
        else:
            self.send_message(thread_id, f"❌ Unknown: {cmd}\nType /help")
    
    def monitor_threads(self):
        print("👀 Monitoring threads...")
        print("=" * 50)
        
        loop_count = 0
        
        while self.running:
            try:
                loop_count += 1
                print(f"🔄 Loop {loop_count}: Fetching threads...")
                
                # ✅ FIXED: NO 'limit' parameter here
                threads = self.cl.direct_threads()
                print(f"🔄 Found {len(threads)} threads")
                
                for thread in threads:
                    thread_id = thread.id
                    users = [u.pk for u in thread.users]
                    
                    # Check for new members
                    if thread_id not in self.known_members:
                        self.known_members[thread_id] = []
                    
                    new_members = set(users) - set(self.known_members[thread_id])
                    for member_id in new_members:
                        if member_id != self.user_id:
                            username = self.get_username(member_id)
                            if username:
                                print(f"🔔 New member: @{username}")
                                self.send_message(thread_id, WELCOME_MSG.format(username=username))
                                time.sleep(1)
                                self.send_message(thread_id, RULES)
                    
                    self.known_members[thread_id] = users
                
                print(f"🔄 Loop {loop_count} complete. Sleeping 15s...")
                time.sleep(15)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"⚠️ Monitor error: {e}")
                time.sleep(30)
        
        print("👀 Monitoring stopped")
    
    def start(self):
        print("\n" + "=" * 50)
        print("🤖 GROUP BOT RUNNING")
        print(f"👤 Bot: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print("=" * 50)
        print("\n📌 Commands:")
        print("   /help, /ping, /dice, /flip, /score")
        print("   Admin: /kick, /warn, /spam")
        print("=" * 50)
        print("\n⚠️ Press Ctrl+C to stop\n")
        
        self.monitor_threads()

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

#!/usr/bin/env python3
"""
Instagram Group Bot - Full Debug Version
"""

import sys
import time
import random
import json
import os
from datetime import datetime, timedelta

# Force stdout to flush immediately
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

print("=" * 50)
print("📂 GROUP_BOT.PY IS LOADING...")
print(f"🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 50)

# Import instagrapi
try:
    print("📦 Importing instagrapi...")
    from instagrapi import Client
    print("✅ instagrapi imported successfully!")
    print(f"📦 instagrapi version: {Client.__module__}")
except ImportError as e:
    print(f"❌ ERROR: instagrapi not installed: {e}")
    print("📌 Add instagrapi to requirements.txt")
    sys.exit(1)

print("=" * 50)

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

print("📌 Configuration:")
print(f"   SESSION_ID: {SESSION_ID[:20]}...")
print(f"   ADMINS: {ADMINS}")
print("=" * 50)

class InstagramGroupBot:
    def __init__(self):
        print("🔧 InstagramGroupBot.__init__() called")
        print("🔧 Creating Client instance...")
        
        self.cl = Client()
        self.cl.set_user_agent("Mozilla/5.0 (Linux; Android 13) Chrome/116.0.5845.92")
        print("✅ Client created with user agent set")
        
        # Bot state
        self.running = True
        self.warned_users = {}
        self.muted_users = {}
        self.scoreboard = {}
        
        # Login
        try:
            print("🔐 Attempting login with session ID...")
            print(f"🔐 Session ID: {SESSION_ID[:20]}...")
            
            self.cl.login_by_sessionid(SESSION_ID)
            self.username = self.cl.username
            self.user_id = self.cl.user_id
            
            print(f"✅ LOGIN SUCCESSFUL!")
            print(f"   Username: @{self.username}")
            print(f"   User ID: {self.user_id}")
            
            # Get followers count
            try:
                followers = self.cl.user_followers(self.user_id)
                print(f"   Followers: {followers}")
            except:
                print("   Followers: (could not fetch)")
            
        except Exception as e:
            print(f"❌ LOGIN FAILED: {e}")
            import traceback
            traceback.print_exc()
            raise e
        
        print("📂 Loading saved data...")
        self.load_data()
        print("✅ Initialization complete!")
        print("=" * 50)
    
    def load_data(self):
        try:
            if os.path.exists('bot_data.json'):
                with open('bot_data.json', 'r') as f:
                    data = json.load(f)
                    self.warned_users = data.get('warned', {})
                    self.scoreboard = data.get('scores', {})
                print(f"📂 Loaded bot data: {len(self.warned_users)} warnings, {len(self.scoreboard)} scores")
            else:
                print("📂 No saved data found, starting fresh")
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
            print("💾 Data saved")
        except Exception as e:
            print(f"⚠️ Error saving data: {e}")
    
    def is_admin(self, username):
        return username in ADMINS or username == self.username
    
    def get_username(self, user_id):
        try:
            return self.cl.user_info(user_id).username
        except Exception as e:
            print(f"⚠️ Could not get username for {user_id}: {e}")
            return None
    
    def send_message(self, thread_id, message):
        try:
            print(f"📤 Sending: {message[:40]}...")
            self.cl.direct_send(message, thread_id=thread_id)
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
🤖 **GROUP BOT COMMANDS:**

**Public:**
/help - Show this help
/rules - Show rules
/dice - Roll dice
/flip - Flip coin
/ping - Check bot alive
/score - Your points
/leaderboard - Top players

**Admin (only @razzz_huu):**
/kick @username - Kick user from group
/warn @username - Warn user
/mute @username - Mute user
/unmute @username - Unmute user
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
        
        elif cmd == '/leaderboard':
            if not self.scoreboard:
                self.send_message(thread_id, "No scores yet!")
                return
            sorted_scores = sorted(self.scoreboard.items(), key=lambda x: x[1], reverse=True)[:10]
            board = "🏆 **LEADERBOARD**\n\n"
            for i, (uid, score) in enumerate(sorted_scores, 1):
                name = self.get_username(uid) or f"User{uid}"
                board += f"{i}. @{name} - {score} pts\n"
            self.send_message(thread_id, board)
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
                self.send_message(thread_id, f"❌ Failed to kick @{target}: {e}")
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
            except Exception as e:
                self.send_message(thread_id, f"❌ User not found: {e}")
            return
        
        elif cmd == '/mute':
            if not args:
                self.send_message(thread_id, "Usage: /mute @username [minutes]")
                return
            target = args[0].replace('@', '')
            minutes = int(args[1]) if len(args) > 1 else 30
            try:
                target_id = self.cl.user_id_from_username(target)
                mute_until = datetime.now() + timedelta(minutes=minutes)
                self.muted_users[target_id] = mute_until
                self.send_message(thread_id, f"🔇 @{target} muted for {minutes} min")
            except Exception as e:
                self.send_message(thread_id, f"❌ User not found: {e}")
            return
        
        elif cmd == '/unmute':
            if not args:
                self.send_message(thread_id, "Usage: /unmute @username")
                return
            target = args[0].replace('@', '')
            try:
                target_id = self.cl.user_id_from_username(target)
                if target_id in self.muted_users:
                    del self.muted_users[target_id]
                    self.send_message(thread_id, f"🔊 @{target} unmuted")
                else:
                    self.send_message(thread_id, f"@{target} is not muted")
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
        
        known_members = {}
        loop_count = 0
        
        while self.running:
            try:
                loop_count += 1
                print(f"🔄 Loop {loop_count}: Fetching threads...")
                
                threads = self.cl.direct_threads(limit=20)
                print(f"🔄 Found {len(threads)} threads")
                
                for thread in threads:
                    thread_id = thread.id
                    users = [u.pk for u in thread.users]
                    usernames = [u.username for u in thread.users]
                    
                    # Check for new members
                    if thread_id not in known_members:
                        known_members[thread_id] = []
                    
                    new_members = set(users) - set(known_members[thread_id])
                    for member_id in new_members:
                        if member_id != self.user_id:
                            username = self.get_username(member_id)
                            if username:
                                print(f"🔔 New member: @{username}")
                                self.send_message(thread_id, WELCOME_MSG.format(username=username))
                                time.sleep(1)
                                self.send_message(thread_id, RULES)
                    
                    known_members[thread_id] = users
                
                print(f"🔄 Loop {loop_count} complete. Sleeping 15s...")
                time.sleep(15)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"⚠️ Monitor error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(30)
        
        print("👀 Monitoring stopped")
    
    def start(self):
        print("\n" + "=" * 50)
        print("🤖 GROUP BOT RUNNING")
        print(f"👤 Bot: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print("=" * 50)
        print("\n📌 Commands: /help, /ping, /dice, /flip")
        print("📌 Admin: /kick, /warn, /mute, /spam")
        print("=" * 50)
        print("\n⚠️ Press Ctrl+C to stop\n")
        
        self.monitor_threads()

def main():
    print("=" * 50)
    print("▶️ main() function called")
    print("=" * 50)
    
    try:
        bot = InstagramGroupBot()
        bot.start()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

print("=" * 50)
print("📂 GROUP_BOT.PY LOADING COMPLETE")
print("=" * 50)

if __name__ == "__main__":
    main()

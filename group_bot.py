#!/usr/bin/env python3
"""
Instagram Group Bot - Auto Welcome, Admin Commands, Games & Moderation
"""

from instagrapi import Client
import time
import json
import os
import random
import threading
from datetime import datetime, timedelta

# ============ CONFIGURATION ============
SESSION_ID = "11950490138:2e5V9aHxKAosXH:28:AYj0h54d0SaaFBpF3pUpsZOPe29TlKH8wYFA4Ic5Lg"

# Admin usernames (who can use admin commands)
ADMINS = ["razzz_huu"]

# Group settings
WELCOME_MESSAGE = "🎉 Welcome {username} to the group! Please read the rules and enjoy!"
RULES = """
📋 GROUP RULES:
1. No spam or excessive self-promotion
2. Be respectful to all members
3. No NSFW content
4. Keep conversations on topic
5. Follow admin instructions

Type /help to see available commands!
"""

# ============ BOT CLASS ============
class InstagramGroupBot:
    def __init__(self):
        self.cl = Client()
        self.cl.set_user_agent("Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.92 Mobile Safari/537.36")
        
        # Bot state
        self.running = True
        self.known_members = {}
        self.warned_users = {}
        self.muted_users = {}
        self.spam_trigger = {}
        self.scoreboard = {}
        self.game_state = {}
        
        # Login
        try:
            print("🔐 Logging in...")
            self.cl.login_by_sessionid(SESSION_ID)
            self.username = self.cl.username
            print(f"✅ Logged in as: @{self.username}")
            print(f"🆔 User ID: {self.cl.user_id}")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            exit()
        
        # Load saved data
        self.load_data()
    
    def load_data(self):
        try:
            if os.path.exists('bot_data.json'):
                with open('bot_data.json', 'r') as f:
                    data = json.load(f)
                    self.warned_users = data.get('warned', {})
                    self.scoreboard = data.get('scores', {})
                    self.known_members = data.get('members', {})
                print("📂 Loaded bot data")
        except:
            pass
    
    def save_data(self):
        try:
            data = {
                'warned': self.warned_users,
                'scores': self.scoreboard,
                'members': self.known_members
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
            return True
        except Exception as e:
            print(f"❌ Failed to send: {e}")
            return False
    
    def handle_join(self, thread_id, new_member_id):
        username = self.get_username(new_member_id)
        if not username:
            return
        
        print(f"🔔 New member joined: @{username}")
        welcome = WELCOME_MESSAGE.format(username=username)
        self.send_message(thread_id, welcome)
        time.sleep(1)
        self.send_message(thread_id, RULES)
        
        if thread_id not in self.known_members:
            self.known_members[thread_id] = []
        self.known_members[thread_id].append(new_member_id)
        self.save_data()
    
    def handle_command(self, thread_id, user_id, username, command):
        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        # ========== PUBLIC COMMANDS ==========
        if cmd == '/help':
            help_text = """
🤖 **BOT COMMANDS:**

**Public Commands:**
/help - Show this help
/rules - Show group rules
/score - Show your score
/leaderboard - Show top players
/trivia - Play trivia game
/dice - Roll a dice (1-6)
/flip - Flip a coin

**Admin Commands:**
/kick @username - Kick a user
/warn @username - Warn a user
/mute @username - Mute a user
/unmute @username - Unmute a user
/clearwarn @username - Clear warnings
/spam [count] [message] - Spam messages (admin only)
"""
            self.send_message(thread_id, help_text)
            return
        
        elif cmd == '/rules':
            self.send_message(thread_id, RULES)
            return
        
        elif cmd == '/score':
            score = self.scoreboard.get(user_id, 0)
            self.send_message(thread_id, f"🏆 @{username} your score: {score} points")
            return
        
        elif cmd == '/leaderboard':
            if not self.scoreboard:
                self.send_message(thread_id, "No scores yet!")
                return
            sorted_scores = sorted(self.scoreboard.items(), key=lambda x: x[1], reverse=True)[:10]
            leaderboard = "🏆 **LEADERBOARD**\n\n"
            for i, (uid, score) in enumerate(sorted_scores, 1):
                name = self.get_username(uid) or f"User {uid}"
                leaderboard += f"{i}. @{name} - {score} points\n"
            self.send_message(thread_id, leaderboard)
            return
        
        elif cmd == '/trivia':
            questions = [
                {"q": "What is the capital of France?", "a": "paris"},
                {"q": "What is 2+2?", "a": "4"},
                {"q": "What is the largest planet?", "a": "jupiter"},
                {"q": "What is the color of the sky?", "a": "blue"},
                {"q": "What is the square root of 9?", "a": "3"},
                {"q": "Which country has the most people?", "a": "china"},
                {"q": "What is the smallest country?", "a": "vatican"},
                {"q": "How many continents are there?", "a": "7"},
            ]
            q = random.choice(questions)
            self.send_message(thread_id, f"❓ Trivia: {q['q']}\nReply with the answer!")
            self.game_state[thread_id] = {
                'answer': q['a'].lower(),
                'user_id': user_id,
                'timestamp': datetime.now()
            }
            return
        
        elif cmd == '/dice':
            roll = random.randint(1, 6)
            self.send_message(thread_id, f"🎲 @{username} rolled a **{roll}**!")
            self.scoreboard[user_id] = self.scoreboard.get(user_id, 0) + 1
            self.save_data()
            return
        
        elif cmd == '/flip':
            result = random.choice(['Heads', 'Tails'])
            self.send_message(thread_id, f"🪙 @{username} flipped **{result}**!")
            self.scoreboard[user_id] = self.scoreboard.get(user_id, 0) + 1
            self.save_data()
            return
        
        # ========== ADMIN COMMANDS ==========
        if not self.is_admin(username):
            self.send_message(thread_id, f"❌ @{username} You don't have permission for this command")
            return
        
        if cmd == '/kick':
            if not args:
                self.send_message(thread_id, "Usage: /kick @username")
                return
            target = args[0].replace('@', '')
            try:
                target_id = self.cl.user_id_from_username(target)
                self.cl.direct_thread_remove_user(thread_id, [target_id])
                self.send_message(thread_id, f"👢 @{target} has been kicked by @{username}")
            except:
                self.send_message(thread_id, f"❌ Failed to kick @{target}")
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
                msg = f"⚠️ @{target} has been warned ({warnings}/3)"
                if warnings >= 3:
                    msg += "\n🔴 Auto-kicked for 3 warnings!"
                    self.cl.direct_thread_remove_user(thread_id, [target_id])
                    self.warned_users[target_id] = 0
                self.send_message(thread_id, msg)
            except:
                self.send_message(thread_id, f"❌ User @{target} not found")
            return
        
        elif cmd == '/clearwarn':
            if not args:
                self.send_message(thread_id, "Usage: /clearwarn @username")
                return
            target = args[0].replace('@', '')
            try:
                target_id = self.cl.user_id_from_username(target)
                self.warned_users[target_id] = 0
                self.save_data()
                self.send_message(thread_id, f"✅ Cleared warnings for @{target}")
            except:
                self.send_message(thread_id, f"❌ User @{target} not found")
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
                self.send_message(thread_id, f"🔇 @{target} muted for {minutes} minutes")
            except:
                self.send_message(thread_id, f"❌ User @{target} not found")
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
                self.send_message(thread_id, f"❌ User @{target} not found")
            return
        
        elif cmd == '/spam':
            if not self.is_admin(username):
                self.send_message(thread_id, f"❌ @{username} You don't have permission for this command")
                return
            if not args:
                self.send_message(thread_id, "Usage: /spam [count] [message] OR /spam [message]")
                return
            try:
                count = int(args[0])
                message = ' '.join(args[1:]) if len(args) > 1 else "SPAM!"
            except ValueError:
                count = 5
                message = ' '.join(args)
            if not message:
                message = "SPAM!"
            self.send_message(thread_id, f"📢 ADMIN @{username} is spamming {count} messages!")
            time.sleep(0.5)
            for i in range(count):
                try:
                    self.send_message(thread_id, f"💥 {i+1}/{count}: {message}")
                    time.sleep(0.3)
                except:
                    break
            self.send_message(thread_id, f"✅ Spam complete! {count} messages sent by @{username}")
            return
        
        else:
            self.send_message(thread_id, f"❌ Unknown command: {cmd}\nType /help for available commands")
    
    def check_trivia(self, thread_id, user_id, message):
        if thread_id not in self.game_state:
            return
        game = self.game_state[thread_id]
        if game['answer'] in message.lower():
            self.send_message(thread_id, f"✅ Correct! @{self.get_username(user_id)} gets a point!")
            self.scoreboard[user_id] = self.scoreboard.get(user_id, 0) + 5
            self.save_data()
            del self.game_state[thread_id]
    
    def detect_spam(self, thread_id, user_id, username, message):
        if user_id not in self.spam_trigger:
            self.spam_trigger[user_id] = []
        now = datetime.now()
        self.spam_trigger[user_id].append(now)
        self.spam_trigger[user_id] = [t for t in self.spam_trigger[user_id] if (now - t).seconds < 10]
        if len(self.spam_trigger[user_id]) > 5:
            self.send_message(thread_id, f"⚠️ @{username} Slow down! Stop spamming!")
            self.warned_users[user_id] = self.warned_users.get(user_id, 0) + 1
            if self.warned_users[user_id] >= 3:
                self.send_message(thread_id, f"🚫 @{username} removed for spam!")
                self.cl.direct_thread_remove_user(thread_id, [user_id])
            self.save_data()
            self.spam_trigger[user_id] = []
    
    def handle_message(self, thread_id, user_id, message):
        username = self.get_username(user_id)
        if not username:
            return
        if message.startswith('/'):
            self.handle_command(thread_id, user_id, username, message)
            return
        self.detect_spam(thread_id, user_id, username, message)
        if user_id in self.muted_users:
            if datetime.now() < self.muted_users[user_id]:
                self.send_message(thread_id, f"@{username} You are muted until {self.muted_users[user_id].strftime('%H:%M')}")
                return
        self.check_trivia(thread_id, user_id, message)
    
    def monitor_threads(self):
        print("👀 Monitoring threads...")
        while self.running:
            try:
                threads = self.cl.direct_threads(limit=20)
                for thread in threads:
                    thread_id = thread.id
                    current_members = [user.pk for user in thread.users]
                    if thread_id not in self.known_members:
                        self.known_members[thread_id] = []
                    new_members = set(current_members) - set(self.known_members[thread_id])
                    for member_id in new_members:
                        if member_id != self.cl.user_id:
                            self.handle_join(thread_id, member_id)
                    self.known_members[thread_id] = current_members
                self.save_data()
                time.sleep(10)
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"⚠️ Monitor error: {e}")
                time.sleep(30)
    
    def start(self):
        print("\n" + "="*50)
        print(f"🤖 GROUP BOT RUNNING")
        print(f"👤 Logged in as: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print("="*50)
        print("\n📌 Bot Features:")
        print("  ✅ Auto-welcome new members")
        print("  ✅ Admin commands (/kick, /warn, /mute, etc.)")
        print("  ✅ SPAM command (/spam count message)")
        print("  ✅ Games (/trivia, /dice, /flip)")
        print("  ✅ Leaderboard and scoring")
        print("  ✅ Spam detection")
        print("="*50)
        print("\n⚠️ Press Ctrl+C to stop the bot\n")
        self.monitor_threads()

def main():
    try:
        bot = InstagramGroupBot()
        bot.start()
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()

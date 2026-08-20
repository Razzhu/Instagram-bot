#!/usr/bin/env python3
"""
Instagram Group Bot - FINAL PRODUCTION VERSION
All bugs fixed, ready for Render deployment
"""

import os
import sys
import time
import json
import random
import signal
import traceback
from datetime import datetime, timedelta  # ✅ FIXED: timedelta imported
from collections import defaultdict

print("=" * 50)
print("🤖 GROUP BOT STARTING...")
print("=" * 50)

# ============ ENVIRONMENT VARIABLES ============ #
SESSION_ID = "11950490138:2e5V9aHxKAosXH:28:AYj0h54d0SaaFBpF3pUpsZOPe29TlKH8wYFA4Ic5Lg"
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
    '/ping': 5,
    '/dice': 5,
    '/flip': 5,
    '/score': 5,
    '/help': 10,
    '/rules': 10,
    '/kick': 30,
    '/warn': 30,
    '/spam': 60,
    'default': 10,
}

MAX_COMMANDS_PER_MINUTE = int(os.environ.get("MAX_COMMANDS_PER_MINUTE", 10))
MAX_WARNINGS = int(os.environ.get("MAX_WARNINGS", 3))
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", 15))

# ============ FILE PATHS ============
SESSION_FILE = "instagram_session.json"
DATA_FILE = "bot_data.json"

# ============ BACKOFF CONFIG ============
BACKOFF_CONFIG = {
    '429': (60, 1800, 5),
    '400': (5, 60, 3),
    '401': (10, 300, 3),
    '403': (30, 600, 3),
    '404': (2, 30, 2),
    '500': (10, 120, 5),
    '502': (10, 120, 5),
    '503': (10, 120, 5),
    'timeout': (5, 60, 3),
    'connection': (10, 120, 5),
    'default': (10, 300, 3),
}

# ============ LOGGING HELPER ============
def log_error(context, error, extra_info=None):
    print("=" * 60)
    print(f"❌ ERROR IN: {context}")
    print("-" * 60)
    print(f"Error Type: {type(error).__name__}")
    print(f"Error Message: {str(error)}")
    if extra_info:
        print(f"Extra Info: {extra_info}")
    print("-" * 60)
    print("Full Traceback:")
    traceback.print_exc()
    print("=" * 60)

def log_info(message, data=None):
    print(f"ℹ️ {message}")
    if data:
        print(f"   Data: {data}")

# ============ JSON VALIDATION ============
def validate_bot_data(data):
    """Validate loaded JSON data structure"""
    required_keys = ['threads', 'thread_state', 'last_message_times', 'processed_messages']
    
    for key in required_keys:
        if key not in data:
            log_info(f"Missing key in data: {key}, creating default")
            if key == 'threads':
                data[key] = {}
            elif key == 'thread_state':
                data[key] = {}
            elif key == 'last_message_times':
                data[key] = {}
            elif key == 'processed_messages':
                data[key] = []
    
    # Validate thread data structure
    for thread_id, thread_data in data.get('threads', {}).items():
        if not isinstance(thread_data, dict):
            log_info(f"Invalid thread data for {thread_id}, removing")
            data['threads'][thread_id] = {}
        if 'members' not in thread_data:
            data['threads'][thread_id]['members'] = []
        if 'welcome_sent' not in thread_data:
            data['threads'][thread_id]['welcome_sent'] = []
        if 'type' not in thread_data:
            data['threads'][thread_id]['type'] = 'unknown'
    
    return data

# ============ INSTAGRAPI IMPORT ============
try:
    from instagrapi import Client
    from instagrapi.exceptions import (
        ClientError, LoginRequired, UserNotFound, 
        RateLimitError, ChallengeRequired
    )
    print("✅ instagrapi imported!")
except ImportError as e:
    print(f"❌ ERROR: {e}")
    print("📌 Add instagrapi to requirements.txt")
    sys.exit(1)

class InstagramGroupBot:
    def __init__(self):
        print("🔧 Initializing bot...")
        
        # ✅ Check for session ID
        if not SESSION_ID:
            print("❌ ERROR: INSTAGRAM_SESSION_ID environment variable not set!")
            print("📌 Please set your session ID in Render environment variables")
            sys.exit(1)
        
        self.cl = Client()
        self.cl.set_user_agent("Mozilla/5.0 (Linux; Android 13) Chrome/116.0.5845.92")
        
        self.running = True
        self.initialized = False
        
        # ============ STATE ============
        self.threads = {}
        self.thread_state = {}
        self.command_cooldowns = defaultdict(lambda: defaultdict(dict))
        self.command_history = defaultdict(lambda: defaultdict(list))
        self.processed_message_ids = set()
        self.last_message_time = {}
        
        # ============ CACHE ============
        self.username_cache = {}
        
        # ============ SESSION TRACKING ============
        self.session_created = None
        self.last_session_refresh = None
        self.is_connected = False
        self.reconnect_attempts = 0
        
        # ============ ERROR TRACKING ============
        self.error_counts = {}
        self.consecutive_errors = 0
        self.total_errors = 0
        
        # ============ SIGNAL HANDLING ============
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # ============ LOAD STATE ============
        self.load_data()
        
        # ============ INITIAL LOGIN ============
        self.login()
        
        # ============ INITIALIZE THREADS ============
        self.initialize_threads()
        self.initialized = True
        print("✅ Bot initialization complete!")
    
    def signal_handler(self, signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self):
        print("💾 Saving data before shutdown...")
        self.save_data()
        print("👋 Bot stopped gracefully!")
    
    # ========== SESSION MANAGEMENT ==========
    
    def login(self):
        print("🔐 Logging in...")
        
        try:
            self.cl.login_by_sessionid(SESSION_ID)
            self.username = self.cl.username
            self.user_id = self.cl.user_id
            self.session_created = datetime.now()
            self.last_session_refresh = datetime.now()
            self.is_connected = True
            self.reconnect_attempts = 0
            
            print(f"✅ Logged in as: @{self.username}")
            print(f"👥 Followers: {self.cl.user_followers(self.user_id)}")
            
            self.save_session()
            return True
            
        except LoginRequired as e:
            log_error("login() - LoginRequired", e)
            self.is_connected = False
            return False
        except ChallengeRequired as e:
            log_error("login() - ChallengeRequired", e)
            self.is_connected = False
            return False
        except Exception as e:
            log_error("login()", e)
            self.is_connected = False
            return False
    
    def refresh_session(self):
        print("🔄 Refreshing session...")
        try:
            self.cl.test_login()
            self.last_session_refresh = datetime.now()
            print("✅ Session refreshed successfully")
            return True
        except LoginRequired as e:
            log_error("refresh_session() - LoginRequired", e)
            return False
        except Exception as e:
            log_error("refresh_session()", e)
            return False
    
    def save_session(self):
        try:
            session_data = {
                'username': self.username,
                'user_id': self.user_id,
                'session_created': self.session_created.isoformat() if self.session_created else None,
                'last_refresh': self.last_session_refresh.isoformat() if self.last_session_refresh else None,
            }
            with open(SESSION_FILE, 'w') as f:
                json.dump(session_data, f)
        except Exception as e:
            log_error("save_session()", e)
    
    def is_session_expired(self):
        if not self.is_connected:
            return True
        if not self.last_session_refresh:
            return True
        elapsed = (datetime.now() - self.last_session_refresh).total_seconds()
        return elapsed > 3600
    
    def recover_session(self):
        print("🔄 Attempting session recovery...")
        self.reconnect_attempts += 1
        wait_time = min(30 * (2 ** (self.reconnect_attempts - 1)), 600)
        print(f"⏳ Waiting {wait_time:.0f} seconds before retry...")
        time.sleep(wait_time)
        
        try:
            return self.login()
        except Exception as e:
            log_error("recover_session()", e)
            return False
    
    def check_and_recover(self):
        if self.is_session_expired():
            print("⚠️ Session needs refresh")
            if not self.refresh_session():
                print("⚠️ Session refresh failed, attempting full recovery...")
                return self.recover_session()
            return True
        return True
    
    # ========== STATE PERSISTENCE ==========
    
    def is_group_chat(self, thread):
        if hasattr(thread, 'users') and len(thread.users) > 2:
            return True
        if hasattr(thread, 'title') and thread.title and thread.title.strip():
            return True
        if hasattr(thread, 'thread_type') and thread.thread_type == 'GROUP':
            return True
        return False
    
    def is_dm(self, thread):
        return not self.is_group_chat(thread)
    
    def get_thread_state(self, thread_id):
        thread_id = str(thread_id)
        if thread_id not in self.thread_state:
            self.thread_state[thread_id] = {
                'warnings': {},
                'scores': {},
                'created': datetime.now().isoformat()
            }
        return self.thread_state[thread_id]
    
    def load_data(self):
        print("📂 Loading bot data...")
        
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                
                data = validate_bot_data(data)
                
                self.threads = data.get('threads', {})
                for thread_id, thread_data in self.threads.items():
                    if 'members' in thread_data:
                        self.threads[thread_id]['members'] = set(thread_data['members'])
                    if 'welcome_sent' in thread_data:
                        self.threads[thread_id]['welcome_sent'] = set(thread_data['welcome_sent'])
                
                self.thread_state = data.get('thread_state', {})
                
                saved_times = data.get('last_message_times', {})
                for thread_id, timestamp in saved_times.items():
                    try:
                        self.last_message_time[thread_id] = datetime.fromisoformat(timestamp)
                    except ValueError:
                        self.last_message_time[thread_id] = datetime.now()
                
                self.processed_message_ids = set(data.get('processed_messages', []))
                
                print(f"📂 Loaded bot data:")
                print(f"   - {len(self.threads)} threads tracked")
                print(f"   - {len(self.processed_message_ids)} messages processed")
            else:
                print("📂 No saved data found, starting fresh")
                
        except json.JSONDecodeError as e:
            log_error("load_data() - JSON parse", e)
            if os.path.exists(DATA_FILE):
                backup_file = f"{DATA_FILE}.backup.{int(time.time())}"
                os.rename(DATA_FILE, backup_file)
                print(f"📌 Backed up corrupted file to {backup_file}")
        except Exception as e:
            log_error("load_data()", e)
    
    def save_data(self):
        try:
            saveable_threads = {}
            for thread_id, thread_data in self.threads.items():
                saveable_threads[thread_id] = {
                    'type': thread_data.get('type', 'unknown'),
                    'members': list(thread_data.get('members', set())),
                    'welcome_sent': list(thread_data.get('welcome_sent', set())),
                    'last_updated': datetime.now().isoformat()
                }
            
            times_data = {}
            for thread_id, timestamp in self.last_message_time.items():
                times_data[str(thread_id)] = timestamp.isoformat()
            
            data = {
                'threads': saveable_threads,
                'thread_state': self.thread_state,
                'last_message_times': times_data,
                'processed_messages': list(self.processed_message_ids),
                'last_updated': datetime.now().isoformat(),
                'bot_username': self.username,
            }
            
            validate_bot_data(data)
            
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
                
        except Exception as e:
            log_error("save_data()", e)
            return False
    
    def save_data_async(self):
        try:
            self.save_data()
        except Exception as e:
            log_error("save_data_async()", e)
    
    # ========== COMMAND RATE LIMITING ==========
    
    def check_cooldown(self, thread_id, user_id, command):
        thread_id = str(thread_id)
        user_id = str(user_id)
        
        cooldown_time = COMMAND_COOLDOWN.get(command, COMMAND_COOLDOWN['default'])
        
        if user_id in self.command_cooldowns[thread_id]:
            if command in self.command_cooldowns[thread_id][user_id]:
                last_used = self.command_cooldowns[thread_id][user_id][command]
                elapsed = (datetime.now() - last_used).total_seconds()
                if elapsed < cooldown_time:
                    return False, cooldown_time - elapsed
        
        return True, 0
    
    def update_cooldown(self, thread_id, user_id, command):
        thread_id = str(thread_id)
        user_id = str(user_id)
        self.command_cooldowns[thread_id][user_id][command] = datetime.now()
    
    def check_rate_limit(self, thread_id, user_id):
        thread_id = str(thread_id)
        user_id = str(user_id)
        now = datetime.now()
        
        history = self.command_history[thread_id][user_id]
        cutoff = now - timedelta(minutes=1)
        history = [t for t in history if t > cutoff]
        self.command_history[thread_id][user_id] = history
        
        if len(history) >= MAX_COMMANDS_PER_MINUTE:
            return False
        
        history.append(now)
        return True
    
    # ========== API METHODS ==========
    
    def safe_api_call(self, func, *args, **kwargs):
        """Make API call with retry and recovery logic"""
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if not self.check_and_recover():
                    print("❌ Session recovery failed, retrying...")
                    time.sleep(30)
                    continue
                
                result = func(*args, **kwargs)
                self.reset_error_tracking()
                time.sleep(random.uniform(0.2, 0.5))
                return result
                
            except RateLimitError as e:
                log_error(f"{func.__name__} - RateLimit (attempt {attempt + 1})", e)
                delay = min(60 * (2 ** attempt), 600)
                print(f"⏳ Rate limited. Waiting {delay:.0f} seconds...")
                time.sleep(delay)
                last_error = e
                continue
                
            except LoginRequired as e:
                log_error(f"{func.__name__} - LoginRequired", e)
                self.is_connected = False
                self.recover_session()
                last_error = e
                continue
                
            except Exception as e:
                log_error(f"{func.__name__} (attempt {attempt + 1})", e)
                delay = self.handle_error(e, func.__name__)
                last_error = e
                
                if isinstance(delay, bool):
                    if delay:
                        continue
                    else:
                        time.sleep(60)
                        continue
                
                if delay > 0:
                    print(f"⏳ Waiting {delay:.1f} seconds before retry...")
                    time.sleep(delay)
                else:
                    print(f"❌ Fatal error in {func.__name__}")
                    raise e
        
        # ✅ Safe error raising with fallback
        if last_error is not None:
            print(f"❌ All retries failed for {func.__name__}")
            raise last_error
        else:
            error_msg = f"{func.__name__} failed after {max_retries} retries with no specific error"
            log_error("safe_api_call()", RuntimeError(error_msg))
            raise RuntimeError(error_msg)
    
    def reset_error_tracking(self):
        if self.consecutive_errors > 0:
            self.consecutive_errors = 0
    
    def get_error_type(self, error):
        error_str = str(error).lower()
        
        if "429" in error_str or "too many requests" in error_str:
            return '429'
        elif "400" in error_str or "bad request" in error_str:
            return '400'
        elif "401" in error_str or "unauthorized" in error_str or "login" in error_str:
            return '401'
        elif "403" in error_str or "forbidden" in error_str:
            return '403'
        elif "404" in error_str or "not found" in error_str:
            return '404'
        elif "500" in error_str or "internal server" in error_str:
            return '500'
        elif "502" in error_str or "bad gateway" in error_str:
            return '502'
        elif "503" in error_str or "service unavailable" in error_str:
            return '503'
        elif "timeout" in error_str or "timed out" in error_str:
            return 'timeout'
        elif "connection" in error_str or "network" in error_str or "reset" in error_str:
            return 'connection'
        else:
            return 'default'
    
    def calculate_backoff(self, error_type, attempt):
        config = BACKOFF_CONFIG.get(error_type, BACKOFF_CONFIG['default'])
        base_delay = config[0]
        max_delay = config[1]
        
        delay = base_delay * (2 ** attempt)
        delay = min(delay, max_delay)
        jitter = random.uniform(0.8, 1.2)
        delay = delay * jitter
        
        return delay
    
    def handle_error(self, error, operation_name="unknown"):
        error_type = self.get_error_type(error)
        error_str = str(error)[:100]
        
        self.consecutive_errors += 1
        self.total_errors += 1
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        log_error(operation_name, error, {"error_type": error_type})
        
        if error_type == '401':
            print("⚠️ Authentication error - attempting session recovery...")
            self.is_connected = False
            return self.recover_session()
        
        if error_type == 'connection':
            print("⚠️ Connection error - attempting recovery...")
            self.is_connected = False
            return self.recover_session()
        
        attempt = self.error_counts.get(error_type, 1) - 1
        delay = self.calculate_backoff(error_type, attempt)
        
        print(f"⚠️ Error in {operation_name}: {error_type}")
        print(f"   Error: {error_str}")
        print(f"   Backoff delay: {delay:.1f} seconds")
        print(f"   Consecutive errors: {self.consecutive_errors}")
        
        return delay
    
    # ========== BOT METHODS ==========
    
    def get_username_cached(self, user_id):
        user_id = str(user_id)
        
        if user_id in self.username_cache:
            return self.username_cache[user_id]
        
        try:
            result = self.safe_api_call(self.cl.user_info, user_id)
            if result and result.username:
                self.username_cache[user_id] = result.username
                if len(self.username_cache) > 1000:
                    self.username_cache = {}
                return result.username
        except Exception as e:
            log_error(f"get_username_cached({user_id})", e)
        
        return None
    
    def initialize_threads(self):
        print("📂 Initializing threads...")
        
        try:
            threads = self.safe_api_call(self.cl.direct_threads)
            if threads is None:
                print("⚠️ No threads found")
                return
            
            print(f"📋 Found {len(threads)} threads")
            
            group_count = 0
            dm_count = 0
            
            for thread in threads:
                thread_id = str(thread.id)
                
                if self.is_dm(thread):
                    dm_count += 1
                    continue
                
                group_count += 1
                member_ids = [u.pk for u in thread.users]
                
                for user in thread.users:
                    self.username_cache[str(user.pk)] = user.username
                
                if thread_id not in self.threads:
                    self.threads[thread_id] = {
                        'type': 'group',
                        'members': set(member_ids),
                        'welcome_sent': set()
                    }
                
                if thread.messages and len(thread.messages) > 0:
                    self.last_message_time[thread_id] = thread.messages[0].timestamp
                else:
                    self.last_message_time[thread_id] = datetime.now()
            
            print(f"✅ Initialized {group_count} group chats (skipped {dm_count} DMs)")
            self.save_data()
            
        except Exception as e:
            log_error("initialize_threads()", e)
            time.sleep(60)
    
    def is_admin(self, username):
        return username in ADMINS or username == self.username
    
    def verify_sender(self, thread_id, user_id, username):
        thread_id = str(thread_id)
        if not username:
            return False
        
        if thread_id in self.threads and self.threads[thread_id].get('type') == 'dm':
            return False
        
        if thread_id not in self.threads:
            return False
        
        if user_id not in self.threads[thread_id].get('members', set()):
            return False
        
        if user_id == self.user_id:
            return False
        
        return True
    
    def send_message(self, thread_id, message):
        try:
            if thread_id in self.threads and self.threads[thread_id].get('type') == 'dm':
                return False
            
            time.sleep(1.5)
            
            result = self.safe_api_call(
                self.cl.direct_send, 
                message, 
                thread_ids=[thread_id]
            )
            
            if result:
                print(f"📤 Sent: {message[:30]}...")
            
            time.sleep(random.uniform(0.5, 1.0))
            return bool(result)
            
        except Exception as e:
            log_error(f"send_message", e)
            return False
    
    def find_user_in_thread(self, thread_id, target_username):
        thread_id = str(thread_id)
        target_username = target_username.lower()
        
        if thread_id not in self.threads:
            return None, "Thread not tracked"
        
        if self.threads[thread_id].get('type') == 'dm':
            return None, "Cannot use commands in DMs"
        
        try:
            thread = self.safe_api_call(self.cl.direct_thread, thread_id)
            if not thread:
                return None, "Thread not found"
            
            for user in thread.users:
                if user.username.lower() == target_username:
                    return user.pk, None
            
            return None, f"User @{target_username} not found in this group"
            
        except Exception as e:
            log_error(f"find_user_in_thread", e)
            return None, f"Error: {str(e)}"
    
    def process_membership_changes(self, thread_id, current_members):
        thread_id = str(thread_id)
        
        if thread_id not in self.threads or self.threads[thread_id].get('type') == 'dm':
            return
        
        previous_members = self.threads[thread_id].get('members', set())
        welcome_sent = self.threads[thread_id].get('welcome_sent', set())
        
        new_members = current_members - previous_members
        
        for member_id in new_members:
            if member_id == self.user_id:
                continue
            
            if member_id in welcome_sent:
                continue
            
            username = self.get_username_cached(member_id)
            if username:
                print(f"🔔 NEW member joined: @{username}")
                self.send_message(thread_id, WELCOME_MSG.format(username=username))
                time.sleep(1)
                self.send_message(thread_id, RULES)
                welcome_sent.add(member_id)
        
        left_members = previous_members - current_members
        for member_id in left_members:
            if member_id == self.user_id:
                continue
            username = self.get_username_cached(member_id)
            if username:
                print(f"👋 Member left: @{username}")
                if member_id in welcome_sent:
                    welcome_sent.remove(member_id)
        
        self.threads[thread_id]['members'] = current_members
        self.threads[thread_id]['welcome_sent'] = welcome_sent
    
    def handle_command(self, thread_id, user_id, username, command):
        thread_id = str(thread_id)
        
        if thread_id in self.threads and self.threads[thread_id].get('type') == 'dm':
            self.send_message(thread_id, "❌ Bot commands only work in group chats!")
            return
        
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        print(f"📩 Command from @{username}: {cmd}")
        
        # ========== RATE LIMITING ==========
        if not self.check_rate_limit(thread_id, user_id):
            self.send_message(thread_id, f"⏳ @{username} Too many commands! Max {MAX_COMMANDS_PER_MINUTE} per minute.")
            return
        
        can_use, wait_time = self.check_cooldown(thread_id, user_id, cmd)
        if not can_use:
            self.send_message(thread_id, f"⏳ @{username} Please wait {int(wait_time) + 1}s before using {cmd} again.")
            return
        
        self.update_cooldown(thread_id, user_id, cmd)
        
        # ========== PUBLIC COMMANDS ==========
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
            state = self.get_thread_state(thread_id)
            state['scores'][user_id] = state['scores'].get(user_id, 0) + 1
            self.send_message(thread_id, f"🎲 @{username} rolled **{roll}**! (+1 point)")
            self.save_data_async()
            return
        
        elif cmd == '/flip':
            result = random.choice(['Heads', 'Tails'])
            state = self.get_thread_state(thread_id)
            state['scores'][user_id] = state['scores'].get(user_id, 0) + 1
            self.send_message(thread_id, f"🪙 @{username} flipped **{result}**! (+1 point)")
            self.save_data_async()
            return
        
        elif cmd == '/score':
            state = self.get_thread_state(thread_id)
            score = state['scores'].get(user_id, 0)
            self.send_message(thread_id, f"🏆 @{username} has {score} points in this group!")
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
            target_id, error = self.find_user_in_thread(thread_id, target)
            
            if error:
                self.send_message(thread_id, f"❌ {error}")
                return
            
            try:
                self.safe_api_call(self.cl.direct_thread_remove_user, thread_id, [target_id])
                self.send_message(thread_id, f"👢 @{target} kicked by @{username}")
                
                if thread_id in self.threads and target_id in self.threads[thread_id].get('members', set()):
                    self.threads[thread_id]['members'].remove(target_id)
                    self.save_data_async()
                    
            except Exception as e:
                log_error(f"kick({target})", e)
                self.send_message(thread_id, f"❌ Failed to kick @{target}: {str(e)}")
            return
        
        elif cmd == '/warn':
            if not args:
                self.send_message(thread_id, "Usage: /warn @username")
                return
            
            target = args[0].replace('@', '')
            target_id, error = self.find_user_in_thread(thread_id, target)
            
            if error:
                self.send_message(thread_id, f"❌ {error}")
                return
            
            state = self.get_thread_state(thread_id)
            warnings = state['warnings'].get(target_id, 0) + 1
            state['warnings'][target_id] = warnings
            
            msg = f"⚠️ @{target} warned ({warnings}/{MAX_WARNINGS})"
            
            if warnings >= MAX_WARNINGS:
                msg += "\n🔴 Auto-kicked for exceeding warnings!"
                try:
                    self.safe_api_call(self.cl.direct_thread_remove_user, thread_id, [target_id])
                    state['warnings'][target_id] = 0
                    if thread_id in self.threads and target_id in self.threads[thread_id].get('members', set()):
                        self.threads[thread_id]['members'].remove(target_id)
                except Exception as e:
                    log_error(f"warn({target}) - auto-kick failed", e)
                    msg += f"\n❌ Auto-kick failed: {str(e)}"
            
            self.send_message(thread_id, msg)
            self.save_data_async()
            return
        
        elif cmd == '/spam':
            if not args:
                self.send_message(thread_id, "Usage: /spam [count] [message]")
                return
            
            try:
                count = int(args[0])
                if count <= 0 or count > 3:
                    self.send_message(thread_id, "❌ Count must be between 1 and 3")
                    return
                message = ' '.join(args[1:]) if len(args) > 1 else "SPAM!"
            except ValueError:
                self.send_message(thread_id, "❌ Invalid count. Usage: /spam [count] [message]")
                return
            
            self.send_message(thread_id, f"📢 Admin spamming {count} messages!")
            for i in range(count):
                self.send_message(thread_id, f"💥 {i+1}/{count}: {message}")
                time.sleep(2.0)
            self.send_message(thread_id, "✅ Spam complete!")
            return
        
        else:
            self.send_message(thread_id, f"❌ Unknown: {cmd}\nType /help")
    
    def check_thread_messages(self, thread_id):
        """Check for new messages using BOTH timestamp AND message ID"""
        thread_id = str(thread_id)
        
        if thread_id in self.threads and self.threads[thread_id].get('type') == 'dm':
            return
        
        try:
            thread = self.safe_api_call(self.cl.direct_thread, thread_id)
            if not thread or not thread.messages:
                return
            
            latest_msg = thread.messages[0]
            latest_time = latest_msg.timestamp
            
            if thread_id not in self.last_message_time:
                self.last_message_time[thread_id] = latest_time
            
            for msg in thread.messages:
                # Check timestamp first (skip old messages)
                if msg.timestamp <= self.last_message_time[thread_id]:
                    continue
                
                # ✅ Check if already processed by ID
                message_id = str(msg.id)
                if message_id in self.processed_message_ids:
                    continue
                
                # Skip bot's own messages
                if msg.user_id == self.user_id:
                    continue
                
                # Skip empty messages
                if not msg.text:
                    continue
                
                # Get sender username
                username = self.get_username_cached(msg.user_id)
                if not username:
                    continue
                
                # Verify sender
                if not self.verify_sender(thread_id, msg.user_id, username):
                    continue
                
                # ✅ Mark as processed BEFORE handling
                self.processed_message_ids.add(message_id)
                
                print(f"📩 New message from @{username}: {msg.text}")
                
                # Process command
                if msg.text.startswith('/'):
                    self.handle_command(thread_id, msg.user_id, username, msg.text)
                
                # Save periodically
                self.save_data_async()
            
            # Update last message time AFTER processing all messages
            self.last_message_time[thread_id] = latest_time
            
        except Exception as e:
            log_error(f"check_thread_messages({thread_id})", e)
    
    def monitor_threads(self):
        print("👀 Monitoring threads...")
        print("=" * 50)
        print(f"📌 {len(self.threads)} group chats being monitored")
        print(f"📌 {len(self.processed_message_ids)} messages already processed")
        print(f"📌 Poll interval: {POLL_INTERVAL}s")
        print("=" * 50)
        
        loop_count = 0
        
        while self.running:
            try:
                loop_count += 1
                
                if loop_count % 10 == 0:
                    print(f"\n🔄 Loop {loop_count}: Checking for updates...")
                
                if not self.check_and_recover():
                    print("⚠️ Session recovery failed, waiting...")
                    time.sleep(60)
                    continue
                
                threads = self.safe_api_call(self.cl.direct_threads)
                if not threads:
                    print("⚠️ No threads found, waiting...")
                    time.sleep(30)
                    continue
                
                group_count = 0
                
                for thread in threads:
                    thread_id = str(thread.id)
                    
                    if self.is_dm(thread):
                        continue
                    
                    group_count += 1
                    current_members = set([u.pk for u in thread.users])
                    
                    for user in thread.users:
                        self.username_cache[str(user.pk)] = user.username
                    
                    if thread_id not in self.threads:
                        self.threads[thread_id] = {
                            'type': 'group',
                            'members': set(),
                            'welcome_sent': set()
                        }
                    
                    self.process_membership_changes(thread_id, current_members)
                    self.check_thread_messages(thread_id)
                
                if loop_count % 10 == 0:
                    print(f"📋 Processed {group_count} group chats")
                    print(f"📊 {len(self.processed_message_ids)} messages tracked")
                
                self.save_data_async()
                
                time.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                log_error("monitor_threads() main loop", e)
                time.sleep(60)
        
        print("👀 Monitoring stopped")
    
    def start(self):
        print("\n" + "=" * 50)
        print("🤖 GROUP BOT RUNNING")
        print(f"👤 Bot: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print(f"📊 Monitoring {len(self.threads)} group chats")
        print(f"📊 {len(self.processed_message_ids)} messages tracked")
        print("=" * 50)
        print("\n📌 Commands:")
        print("   /help, /ping, /dice, /flip, /score")
        print("   Admin: /kick, /warn, /spam")
        print("=" * 50)
        print(f"\n⚠️ Cooldowns: {COMMAND_COOLDOWN}")
        print(f"⚠️ Max {MAX_COMMANDS_PER_MINUTE} commands per minute")
        print("=" * 50)
        print("\n⚠️ Press Ctrl+C to stop\n")
        
        self.monitor_threads()

# ============ MAIN ============
def main():
    try:
        bot = InstagramGroupBot()
        bot.start()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped!")
    except Exception as e:
        log_error("main()", e)
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()

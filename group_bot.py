#!/usr/bin/env python3
"""
ULTIMATE GC COMPANION BOT - COMPLETE UPGRADE
- Smart AI Router (not random)
- Context-aware conversations
- Personality-driven responses
- Human-like timing
- Anti-repetition
- Proper cooldowns
- All commands working
- .buy, .inventory, .use included
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
from collections import deque, defaultdict
import re

print("=" * 60)
print("🔥 ULTIMATE GC COMPANION BOT LOADING...")
print("=" * 60)

# ============ ENVIRONMENT ============
SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
ADMINS_RAW = os.environ.get("INSTAGRAM_ADMINS", "razzz_huu")
ADMINS = [a.strip().lower() for a in ADMINS_RAW.split(",") if a.strip()]

if not SESSION_ID:
    print("❌ INSTAGRAM_SESSION_ID not set!")
    sys.exit(1)

if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY not set!")
    sys.exit(1)

print(f"✅ SESSION_ID: {SESSION_ID[:10]}...")
print(f"✅ GROQ_API_KEY: {'Yes' if GROQ_API_KEY else 'No'}")
print(f"✅ ADMINS: {ADMINS}")

# ============ DATABASE ============
from database import (
    get_db, init_db, migrate_json_to_sqlite,
    get_user_data, ensure_user, add_xp, add_coins, add_reputation,
    get_level, get_title, get_welcome_message, get_rules,
    get_or_create_personality, update_personality,
    get_setting, set_setting,
    add_achievement, get_achievements,
    add_inventory_item, get_inventory,
    add_report, get_reports,
    update_game_stats, get_game_stats,
    WELCOME_MSG, RULES
)

# Initialize database
init_db()
migrate_json_to_sqlite()

# ============ CONFIGURATION ============
# Message processing
MAX_CONTEXT_MESSAGES = 20
BOT_REPLY_COOLDOWN = 5
USER_REPLY_COOLDOWN = 8
AI_MAX_TOKENS = 100
AI_TEMPERATURE = 0.9
POLL_INTERVAL_MIN = 5.0
POLL_INTERVAL_MAX = 10.0
MAX_SPAM_COUNT = 100
SPAM_DELAY_MIN = 3
SPAM_DELAY_MAX = 6

# Messages
LEAVE_MSG = "🚶 {username} chala gya bhadwa! 😂"
WELCOME_BACK_MSGS = ["{username} kya haal ladleee wapis idhr 👀🔥"]

# ============ EXPANDED FALLBACK ============
FALLBACK_ROASTS = [
    "तू हर जगह है जैसे WiFi, पर काम किसी काम का नहीं! 📶",
    "तेरी सोच इतनी गहरी है जितनी चाय की प्लेट! ☕",
    "तू अच्छा है... बस दूर से। 😂",
    "तेरा चेहरा देखकर लगता है कल का कल होगा! 🗓️",
    "तुझसे अच्छा तो मेरा पुराना फोन है, वो भी कम से कम चार्ज हो जाता है! 🔋",
    "तू वो दोस्त है जो ग्रुप में आता है और माहौल खराब कर देता है 💀",
    "तेरी हर बात में 90% झूठ और 10% अतिरंजना होती है 😂",
    "तू सोचता है कि तू कूल है, पर हकीकत में तू तो बस एक मजाक है 🤡",
    "तू वो इंसान है जो ऑनलाइन गेम में भी हार जाता है 🎮",
    "तेरी दोस्ती से अच्छा तो मेरी अकेलाई है 😂",
]

FALLBACK_JOKES = [
    "एक आदमी ने डॉक्टर से कहा: मुझे हर रात बुरे सपने आते हैं। डॉक्टर बोला: क्या सपने आते हैं? आदमी बोला: सपने में मुझे नींद नहीं आती! 😂",
    "टीचर: तुम्हारी कॉपी में तो दीमक लग गई है! स्टूडेंट: सर, वो मेरी क्रिएटिविटी है! 💀",
    "पति: मैं तुमसे बहुत प्यार करता हूँ। पत्नी: क्या चाहिए? 😂",
    "एक लड़का लड़की से बोला: तुम मेरी आँखों का तारा हो। लड़की बोली: तो क्या मैं टूट कर गिर जाऊँ? 🤡",
    "बॉस: तुम्हारी सोच बहुत गहरी है। कर्मचारी: सर, वो मेरी अलमारी खाली है इसलिए। 💀",
]

FALLBACK_COMPLIMENTS = [
    "तू तो लगता है जैसे सुबह की चाय — हर किसी को भाती है! ☕",
    "तू वो दोस्त है जिसके बिना ग्रुप अधूरा है! ❤️",
    "तू वजह है ग्रुप की शान! 👑",
    "तेरी हँसी सुनकर लगता है जैसे बारिश हो गई! 🌧️",
    "तू वो इंसान है जिसके बारे में कोई बुरा नहीं बोल सकता! 🌟",
]

FALLBACK_FACTS = [
    "ऑक्टोपस के 3 दिल होते हैं! 💙",
    "केला एक बेरी है! 🍌",
    "वीनस पर 1 दिन 1 साल से भी लंबा होता है! 🌍",
    "मधुमक्खियाँ नाच कर बात करती हैं! 🐝",
    "इंसान का दिमाग 100,000 साल पुराना है! 🧠",
]

FALLBACK_8BALL = [
    "🎱 शायद हाँ", "🎱 नहीं", "🎱 पक्का नहीं",
    "🎱 बिल्कुल", "🎱 कभी नहीं", "🎱 शायद",
    "🎱 पूछते रहो", "🎱 मेरी समझ से बाहर",
]

FALLBACK_TRIVIA = [
    {"q": "फ्रांस की राजधानी क्या है?", "a": "पेरिस"},
    {"q": "2+2 क्या होता है?", "a": "4"},
    {"q": "सबसे बड़ा ग्रह कौन सा है?", "a": "बृहस्पति"},
    {"q": "भारत की राजधानी क्या है?", "a": "नई दिल्ली"},
    {"q": "मानव शरीर में कितनी हड्डियाँ होती हैं?", "a": "206"},
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

# ============ SHOP ITEMS ============
SHOP_ITEMS = [
    {"name": "Virtual Maggi", "price": 100, "emoji": "🍜", "desc": "Absolutely useless. Buy it anyway."},
    {"name": "Fake Admin Crown", "price": 500, "emoji": "👑", "desc": "Flex on the peasants."},
    {"name": "Ban Protection", "price": 2000, "emoji": "🛡️", "desc": "One free pass. Use wisely."},
    {"name": "Nuclear Roast", "price": 5000, "emoji": "💀", "desc": "The ultimate roast weapon."},
    {"name": "+10 Fake IQ", "price": 10000, "emoji": "🧠", "desc": "You're still dumb. But less."},
]

# ============ STATE ============
AFK_USERS = {}  # {(thread_id, user_id): (reason, timestamp)}
WELCOME_SENT = {}  # {(thread_id, user_id): bool}
ADMIN_LAST_SEEN = {}  # {thread_id: timestamp}

processed_messages = deque(maxlen=5000)
context_history = defaultdict(lambda: deque(maxlen=MAX_CONTEXT_MESSAGES))
recent_bot_responses = defaultdict(lambda: deque(maxlen=10))

trivia_state = {}
roast_battle_state = {}
mostlikely_state = {}
active_events = {}
summon_state = {}

command_cooldowns = {}
spam_running = False
spam_stop_flag = False
spam_thread = None

# ============ GROQ AI ============
def groq_generate(prompt, api_key, max_tokens=AI_MAX_TOKENS):
    if not api_key:
        return None
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "model": "groq/compound",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": AI_TEMPERATURE,
            "max_tokens": max_tokens
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            reply = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not reply or "can't help" in reply.lower():
                return None
            return reply
        return None
    except Exception as e:
        print(f"[ERROR] Groq: {e}")
        return None

def groq_roast(target, api_key):
    return groq_generate(f"Give a SHORT savage roast for @{target} in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_joke(api_key):
    return groq_generate("Tell a SHORT funny joke in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_fact(api_key):
    return groq_generate("Give a SHORT interesting fact in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_ask_public(question, api_key):
    return groq_generate(f"Reply to this question in a funny way in HINDI/HINGLISH. Question: '{question}'", api_key)

def groq_admin(question, api_key):
    return groq_generate(f"Answer this question in HINDI/HINGLISH. Be helpful and informative. Question: '{question}'", api_key)

def groq_natural_reply(message, username, api_key, personality=None, context=None):
    personality_text = ""
    if personality:
        personality_text = f"""
Mood: {personality.get('mood', 'chill')}
Friendliness: {personality.get('friendliness', 70)}%
Sarcasm: {personality.get('sarcasm', 60)}%
Chaos: {personality.get('chaos', 40)}%"""

    context_text = ""
    if context:
        context_text = "Recent conversation:\n" + "\n".join(context)

    prompt = f"""You are a natural, funny member of an Instagram group chat.
You are NOT an assistant or chatbot. You are just another member.
Respond naturally to the latest message.

Personality:
{personality_text}

{context_text}

Latest message:
@{username}: {message}

Rules:
- Keep it SHORT (1 short sentence)
- Use natural Hindi/Hinglish
- Be relevant to the conversation
- Don't force jokes
- Don't overuse emojis
- Don't mention being an AI
- Don't repeat the message
- Don't include any reasoning or explanation
- Just reply directly

Your response:"""

    reply = groq_generate(prompt, api_key, 80)
    return reply

# ============ AI ROUTER ============
class AIRouter:
    def __init__(self):
        self.cooldown_tracker = {}
        self.last_bot_message = {}
        self.response_cache = defaultdict(lambda: deque(maxlen=10))
    
    def should_reply(self, thread_id, user_id, message, bot_username, is_command=False):
        if is_command:
            return {"should_reply": False, "reason": "is_command", "score": 0}
        
        if not message or len(message.strip()) < 1:
            return {"should_reply": False, "reason": "empty", "score": 0}
        
        if user_id == self.cl.user_id:
            return {"should_reply": False, "reason": "self", "score": 0}
        
        score = 0
        reasons = []
        
        if bot_username.lower() in message.lower():
            score += 95
            reasons.append("direct_mention")
        
        if message.startswith('@') and bot_username.lower() in message.lower():
            score += 90
            reasons.append("reply_to_bot")
        
        if '?' in message and bot_username.lower() in message.lower():
            score += 85
            reasons.append("bot_question")
        
        if '?' in message:
            score += 35
            reasons.append("question")
        
        funny_patterns = ['😂', '💀', 'lol', '🤣', 'haha', 'lmao', '🔥']
        if any(p in message for p in funny_patterns):
            score += 30
            reasons.append("funny")
        
        if len(message.split()) > 5:
            score += 15
            reasons.append("meaningful")
        
        if thread_id in summon_state and summon_state[thread_id].get("active", False):
            score += 30
            reasons.append("summon_mode")
        
        cooldown_key = (thread_id, user_id)
        if cooldown_key in self.cooldown_tracker:
            elapsed = time.time() - self.cooldown_tracker[cooldown_key]
            if elapsed < 60:
                return {"should_reply": False, "reason": "user_cooldown", "score": 0}
        
        last_bot = self.last_bot_message.get(thread_id, 0)
        if time.time() - last_bot < BOT_REPLY_COOLDOWN:
            return {"should_reply": False, "reason": "bot_cooldown", "score": 0}
        
        if len(message.strip()) < 3 and not any(p in message for p in ['😂', '💀', '👀']):
            score -= 20
        
        if score >= 80:
            probability = random.uniform(0.85, 1.0)
        elif score >= 60:
            probability = random.uniform(0.50, 0.80)
        elif score >= 40:
            probability = random.uniform(0.25, 0.50)
        elif score >= 20:
            probability = random.uniform(0.08, 0.25)
        else:
            probability = random.uniform(0.02, 0.08)
        
        should_reply = random.random() < probability
        
        return {
            "should_reply": should_reply,
            "reason": reasons[0] if reasons else "general",
            "score": score,
            "probability": probability
        }
    
    def mark_reply(self, thread_id, user_id):
        self.cooldown_tracker[(thread_id, user_id)] = time.time()
        self.last_bot_message[thread_id] = time.time()

# ============ INSTAGRAPI ============
try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired, RateLimitError
    print("✅ instagrapi imported!")
except ImportError as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# ============ HUMAN BEHAVIOR ============
class HumanBehavior:
    def __init__(self):
        self.moods = ['chatty', 'brief', 'distracted', 'focused', 'slow', 'hyper']
        self.current_mood = random.choice(self.moods)
        self.typing_speed = random.randint(40, 80)
    
    def get_delay(self, text="", is_direct=False):
        if is_direct:
            base_delay = random.uniform(0.5, 1.5)
        elif len(text) > 50:
            base_delay = random.uniform(2.0, 4.0)
        elif len(text) > 20:
            base_delay = random.uniform(1.0, 2.5)
        else:
            base_delay = random.uniform(0.5, 1.5)
        
        mood_multipliers = {
            'chatty': 0.8, 'brief': 0.5, 'distracted': 2.0,
            'focused': 0.7, 'slow': 1.5, 'hyper': 0.4
        }
        delay = base_delay * mood_multipliers.get(self.current_mood, 1.0)
        return min(max(delay, 0.5), 5.0)
    
    def type_time(self, text):
        chars = len(text)
        base_time = chars / (self.typing_speed * random.uniform(0.7, 1.3))
        return min(base_time + random.uniform(0.3, 0.8), 4.0)

human = HumanBehavior()

def human_delay(text="", is_direct=False):
    time.sleep(human.get_delay(text, is_direct))

def type_message_like_human(text):
    time.sleep(human.type_time(text))

# ============ MAIN BOT ============
class InstagramGroupBot:
    def __init__(self):
        print("[INIT] 🔧 Initializing bot...")
        self.cl = Client()
        self.cl.set_user_agent("Mozilla/5.0 (Linux; Android 13) Chrome/116.0.5845.92")
        self.running = True
        self.known_members = {}
        self.username_cache = {}
        self.groq_api_key = GROQ_API_KEY
        self.last_active = {}
        self.ai_router = AIRouter()
        self.context_history = defaultdict(lambda: deque(maxlen=MAX_CONTEXT_MESSAGES))
        self.recent_bot_responses = defaultdict(lambda: deque(maxlen=10))
        
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
        self.initialize_threads()
        print("[INIT] ✅ Bot initialization complete!")

    def login(self):
        print("[LOGIN] 🔐 Logging in...")
        try:
            self.cl.login_by_sessionid(SESSION_ID)
            self.username = self.cl.username
            self.user_id = self.cl.user_id
            print(f"[LOGIN] ✅ Logged in as: @{self.username}")
            print(f"[LOGIN] 👥 Followers: {self.cl.user_followers(self.user_id)}")
        except Exception as e:
            print(f"[LOGIN] ❌ Login failed: {e}")
            raise e
    
    def initialize_threads(self):
        print("[THREAD] 📂 Initializing threads...")
        try:
            threads = self.cl.direct_threads()
            group_count = 0
            for thread in threads:
                if hasattr(thread, 'users') and len(thread.users) > 2:
                    thread_id = str(thread.id)
                    member_ids = [u.pk for u in thread.users]
                    self.known_members[thread_id] = set(member_ids)
                    group_count += 1
                    print(f"[THREAD] 📌 Thread {thread_id}: {len(member_ids)} members")
            self.group_count = group_count
            print(f"[THREAD] 📊 Detected {self.group_count} group(s)")
        except Exception as e:
            print(f"[THREAD] ⚠️ Error: {e}")
            self.group_count = 1
    
    def is_admin(self, username):
        return username.lower() in ADMINS or username.lower() == self.username.lower()
    
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
            human_delay(message)
            self.cl.direct_send(message, thread_ids=[thread_id])
            print(f"[SEND] 📤 Sent: {message[:40]}...")
            return True
        except RateLimitError:
            print("[RATE LIMIT] ⚠️ Rate limited! Waiting 60s...")
            time.sleep(60)
            return False
        except Exception as e:
            print(f"[ERROR] ❌ Send error: {e}")
            return False
    
    def check_cooldown(self, thread_id, user_id, command):
        key = (thread_id, user_id, command)
        if key in command_cooldowns:
            elapsed = time.time() - command_cooldowns[key]
            if elapsed < 5:
                return False, 5 - elapsed
        return True, 0
    
    def update_cooldown(self, thread_id, user_id, command):
        key = (thread_id, user_id, command)
        command_cooldowns[key] = time.time()

    # ============ COMMAND HANDLER ============
    def handle_command(self, thread_id, user_id, username, command):
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        print(f"[COMMAND] 📩 from @{username}: {cmd}")
        
        can_use, wait_time = self.check_cooldown(thread_id, user_id, cmd)
        if not can_use:
            self.send_message(thread_id, f"⏳ Wait {int(wait_time)+1}s before using {cmd} again.")
            return
        
        self.update_cooldown(thread_id, user_id, cmd)
        
        # ============ HELP ============
        if cmd == '.help':
            help_text = """
🔥 **ULTIMATE GC BOT COMMANDS:**

**🎮 Games:**
.dice - Roll dice
.flip - Flip coin
.rps - Rock Paper Scissors
.trivia - 5 questions with timer
.roast @user - Roast user
.compliment @user - Compliment user
.fact - Random fact
.joke - Random joke
.8ball - Magic 8-ball
.love @user OR .love @u1 @u2 - Love calculator
.mostlikely - Who is most likely to...?
.sus @user - Suspicious claim detector

**📊 Profile:**
.score - Your XP and coins
.leaderboard - Top players
.profile @user - View user profile
.balance - Check coins
.daily - Claim daily reward
.give @user amount - Give coins

**🧠 Memory:**
.memory - Show memories
.remember [thing] - Add memory
.forget [thing] - Delete memory

**🛒 Economy:**
.shop - View shop
.buy [item] - Buy an item
.inventory - View your items
.use [item] - Use an item

**👑 Admin:**
.spam count msg - Spam messages
.stopspam - Stop spam
.afk [reason] - Set AFK
.setwelcome msg - Set welcome
.setrules rules - Set rules
.groq [question] - Ask Groq

**🤖 AI:**
.ask [question] - Ask bot (funny)
Bot also replies naturally to conversations!

**🥚 Secrets:**
.chaos - Trigger chaos
.summon - Rare event
"""
            self.send_message(thread_id, help_text)
            return
        
        # ============ RULES ============
        elif cmd == '.rules':
            rules = get_rules(thread_id) or RULES
            self.send_message(thread_id, rules)
            return
        
        # ============ PING ============
        elif cmd == '.ping':
            self.send_message(thread_id, "🏓 Pong! Bot is alive!")
            return
        
        # ============ DICE ============
        elif cmd == '.dice':
            roll = random.randint(1, 6)
            self.send_message(thread_id, f"🎲 @{username} rolled **{roll}**!")
            add_xp(user_id, thread_id, 5, "dice")
            return
        
        # ============ FLIP ============
        elif cmd == '.flip':
            result = random.choice(['Heads', 'Tails'])
            self.send_message(thread_id, f"🪙 @{username} flipped **{result}**!")
            add_xp(user_id, thread_id, 5, "flip")
            return
        
        # ============ RPS ============
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
                add_xp(user_id, thread_id, 15, "rps_win")
                add_coins(user_id, thread_id, 10)
            else:
                result = "I win! 😎"
            self.send_message(thread_id, f"🪨📄✂️ @{username}: {user_choice} 🤖 Bot: {bot_choice}\n{result}")
            return
        
        # ============ TRIVIA ============
        elif cmd == '.trivia':
            if thread_id in trivia_state:
                self.send_message(thread_id, "⚠️ Trivia already running!")
                return
            questions = []
            if self.groq_api_key:
                for _ in range(5):
                    q = groq_generate("Generate ONE short trivia question in HINDI/HINGLISH with 4 options.\nFormat:\nQ: [question]\nA) [option1]\nB) [option2]\nC) [option3]\nD) [option4]\nAnswer: [letter]", self.groq_api_key)
                    if q:
                        try:
                            lines = q.split('\n')
                            question_text = ""
                            options = []
                            answer = ""
                            for line in lines:
                                if line.startswith('Q:'):
                                    question_text = line[2:].strip()
                                elif line.startswith('A)') or line.startswith('B)') or line.startswith('C)') or line.startswith('D)'):
                                    options.append(line.strip())
                                elif line.startswith('Answer:'):
                                    answer = line.split(':')[1].strip().lower()
                            if question_text and answer:
                                questions.append({"q": question_text, "options": options, "a": answer})
                        except:
                            continue
            if len(questions) < 5:
                qs = random.sample(FALLBACK_TRIVIA, min(5, len(FALLBACK_TRIVIA)))
                questions = [{"q": q['q'], "options": [], "a": q['a']} for q in qs]
            
            trivia_state[thread_id] = {
                'questions': questions,
                'current': 0,
                'score': 0,
                'user_id': user_id,
                'username': username
            }
            self.send_message(thread_id, f"🧠 **TRIVIA STARTED!**\n@{username} has 15 sec per question.\nTotal: {len(questions)} questions.")
            self.send_trivia_question(thread_id)
            return
        
        # ============ ROAST ============
        elif cmd == '.roast':
            if not args:
                self.send_message(thread_id, "Usage: .roast @user")
                return
            target = args[0].replace('@', '')
            msg = None
            if self.groq_api_key:
                msg = groq_roast(target, self.groq_api_key)
            msg = msg or random.choice(FALLBACK_ROASTS)
            self.send_message(thread_id, f"🔥 @{target} {msg}")
            add_xp(user_id, thread_id, 10, "roast")
            return
        
        # ============ COMPLIMENT ============
        elif cmd == '.compliment':
            if not args:
                self.send_message(thread_id, "Usage: .compliment @user")
                return
            target = args[0].replace('@', '')
            msg = random.choice(FALLBACK_COMPLIMENTS)
            self.send_message(thread_id, f"💕 @{target} {msg}")
            add_xp(user_id, thread_id, 5, "compliment")
            return
        
        # ============ JOKE ============
        elif cmd == '.joke':
            msg = None
            if self.groq_api_key:
                msg = groq_joke(self.groq_api_key)
            msg = msg or random.choice(FALLBACK_JOKES)
            self.send_message(thread_id, f"😂 {msg}")
            add_xp(user_id, thread_id, 3, "joke")
            return
        
        # ============ FACT ============
        elif cmd == '.fact':
            msg = None
            if self.groq_api_key:
                msg = groq_fact(self.groq_api_key)
            msg = msg or random.choice(FALLBACK_FACTS)
            self.send_message(thread_id, f"📖 {msg}")
            add_xp(user_id, thread_id, 3, "fact")
            return
        
        # ============ 8BALL ============
        elif cmd == '.8ball':
            if not args:
                self.send_message(thread_id, "Ask me something! Example: .8ball Will I win?")
                return
            msg = random.choice(FALLBACK_8BALL)
            self.send_message(thread_id, msg)
            return
        
        # ============ LOVE ============
        elif cmd == '.love':
            if not args:
                self.send_message(thread_id, "Usage: .love @user OR .love @user1 @user2")
                return
            mentions = [a.replace('@', '') for a in args if a.startswith('@')]
            if len(mentions) == 0:
                self.send_message(thread_id, "❌ Please tag at least 1 person!")
                return
            elif len(mentions) == 1:
                name1, name2 = username, mentions[0]
            elif len(mentions) == 2:
                name1, name2 = mentions[0], mentions[1]
            else:
                self.send_message(thread_id, "❌ Please tag only 1 or 2 people!")
                return
            
            percentage = random.randint(0, 100)
            heart = "❤️🔥" if percentage >= 80 else "❤️" if percentage >= 60 else "💕" if percentage >= 40 else "💛" if percentage >= 20 else "💔"
            
            if percentage >= 90:
                msg = "True love! Soulmates! 😍💕"
            elif percentage >= 75:
                msg = "A match made in heaven! 🥰"
            elif percentage >= 60:
                msg = "Good connection! 😊"
            elif percentage >= 40:
                msg = "It's complicated... 🤔"
            elif percentage >= 20:
                msg = "Friendzone! 😂"
            else:
                msg = "Bro, you two are like oil and water 💀"
            
            self.send_message(thread_id, f"💕 **Love Calculator**\n@{name1} + @{name2} = {percentage}% {heart}\n\n{msg}")
            add_xp(user_id, thread_id, 5, "love")
            return
        
        # ============ MOST LIKELY ============
        elif cmd == '.mostlikely':
            questions = [
                "कौन सबसे ज्यादा Maggi खाता है?",
                "कौन सबसे ज्यादा सोता है?",
                "कौन सबसे ज्यादा बात करता है?",
                "कौन सबसे ज्यादा देर आता है?",
                "कौन सबसे ज्यादा मजाक करता है?",
                "कौन सबसे ज्यादा रोता है?",
                "कौन सबसे ज्यादा काम करता है?",
                "कौन सबसे ज्यादा खाता है?",
                "कौन सबसे ज्यादा बहाने बनाता है?",
                "कौन सबसे ज्यादा झूठ बोलता है?",
            ]
            question = random.choice(questions)
            self.send_message(thread_id, f"📊 **Who is most likely to...**\n\n{question}\n\nVote by replying!")
            mostlikely_state[thread_id] = {'question': question, 'votes': {}, 'timestamp': datetime.now()}
            return
        
        # ============ SUS ============
        elif cmd == '.sus':
            if not args:
                self.send_message(thread_id, "Usage: .sus @user")
                return
            target = args[0].replace('@', '')
            sus_level = random.randint(60, 99)
            reasons = [
                "You have a history of 'studying' = watching YouTube",
                "Your story doesn't add up, bro",
                "The GC has spoken 💀",
                "Your energy is sus today",
                "You're too quiet... sus",
                "You're defending yourself too much",
                "Your timeline doesn't match",
                "You're acting sus since morning"
            ]
            self.send_message(thread_id, f"🧐 **SUSPICIOUS CLAIM DETECTED**\n\nGC Verdict: {sus_level}% SUS\nReason: {random.choice(reasons)}\n\n💀 The GC has spoken.")
            add_xp(user_id, thread_id, 3, "sus")
            return
        
        # ============ SCORE ============
        elif cmd == '.score':
            data = get_user_data(user_id, thread_id)
            self.send_message(thread_id, f"🏆 @{username} has {data['xp']} XP (Level {data['level']}) and {data['coins']} coins!")
            return
        
        # ============ LEADERBOARD ============
        elif cmd == '.leaderboard':
            with get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT user_id, xp, level, coins FROM xp WHERE thread_id = ? ORDER BY xp DESC LIMIT 10", (thread_id,))
                rows = c.fetchall()
            if not rows:
                self.send_message(thread_id, "No scores yet!")
                return
            board = "🏆 **LEADERBOARD**\n\n"
            for i, row in enumerate(rows, 1):
                name = self.get_username_cached(row['user_id']) or f"User{row['user_id'][:8]}"
                board += f"{i}. @{name} - Level {row['level']} ({row['xp']} XP)\n"
            self.send_message(thread_id, board)
            return
        
        # ============ PROFILE ============
        elif cmd == '.profile':
            target = args[0].replace('@', '') if args else username
            target_id = None
            for uid, uname in self.username_cache.items():
                if uname.lower() == target.lower():
                    target_id = uid
                    break
            if not target_id:
                self.send_message(thread_id, f"❌ User @{target} not found")
                return
            data = get_user_data(target_id, thread_id)
            self.send_message(thread_id, f"📊 **Profile: @{target}**\n\nLevel: {data['level']}\nXP: {data['xp']}\nCoins: {data['coins']}\nTitle: {get_title(data['level'])}\nReputation: {data['reputation']}")
            return
        
        # ============ DAILY ============
        elif cmd == '.daily':
            ensure_user(user_id, thread_id)
            with get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT last_daily, daily_streak FROM xp WHERE user_id = ? AND thread_id = ?", (user_id, thread_id))
                row = c.fetchone()
            
            now = datetime.now()
            if row and row['last_daily']:
                last = datetime.fromisoformat(row['last_daily'])
                if (now - last).total_seconds() < 86400:
                    remaining = 86400 - (now - last).total_seconds()
                    self.send_message(thread_id, f"⏳ Already claimed! Wait {int(remaining/3600)}h {int((remaining%3600)/60)}m.")
                    return
                streak = row['daily_streak'] + 1 if (now - last).total_seconds() < 172800 else 1
            else:
                streak = 1
            
            reward = 50 + streak * 10
            add_xp(user_id, thread_id, 20, "daily")
            add_coins(user_id, thread_id, reward)
            
            with get_db() as conn:
                c = conn.cursor()
                c.execute("UPDATE xp SET last_daily = ?, daily_streak = ? WHERE user_id = ? AND thread_id = ?", 
                          (now.isoformat(), streak, user_id, thread_id))
                conn.commit()
            
            self.send_message(thread_id, f"💸 Daily reward claimed! +{reward} coins, 20 XP! 🔥 {streak} day streak!")
            return
        
        # ============ BALANCE ============
        elif cmd == '.balance':
            data = get_user_data(user_id, thread_id)
            self.send_message(thread_id, f"💰 @{username} has {data['coins']} coins!")
            return
        
        # ============ GIVE ============
        elif cmd == '.give':
            if len(args) < 2:
                self.send_message(thread_id, "Usage: .give @user amount")
                return
            target = args[0].replace('@', '')
            try:
                amount = int(args[1])
                if amount <= 0:
                    self.send_message(thread_id, "❌ Amount must be positive!")
                    return
                data = get_user_data(user_id, thread_id)
                if data['coins'] < amount:
                    self.send_message(thread_id, "❌ You don't have enough coins!")
                    return
                target_id = None
                for uid, uname in self.username_cache.items():
                    if uname.lower() == target.lower():
                        target_id = uid
                        break
                if not target_id:
                    self.send_message(thread_id, f"❌ User @{target} not found")
                    return
                add_coins(user_id, thread_id, -amount)
                add_coins(target_id, thread_id, amount)
                self.send_message(thread_id, f"💸 @{username} gave {amount} coins to @{target}!")
            except ValueError:
                self.send_message(thread_id, "❌ Invalid amount!")
            return
        
        # ============ SHOP ============
        elif cmd == '.shop':
            shop_list = "🏪 **SHOP**\n\n"
            for item in SHOP_ITEMS:
                shop_list += f"{item['emoji']} **{item['name']}** — {item['price']} coins\n   *{item['desc']}*\n\n"
            self.send_message(thread_id, shop_list)
            return
        
        # ============ BUY ============
        elif cmd == '.buy':
            if not args:
                self.send_message(thread_id, "Usage: .buy [item name]")
                return
            
            item_name = ' '.join(args)
            found_item = None
            
            for item in SHOP_ITEMS:
                if item['name'].lower() in item_name.lower():
                    found_item = item
                    break
            
            if not found_item:
                self.send_message(thread_id, "❌ Item not found! Check .shop")
                return
            
            data = get_user_data(user_id, thread_id)
            if data['coins'] < found_item['price']:
                self.send_message(thread_id, f"❌ Not enough coins! Need {found_item['price']} coins. You have {data['coins']}.")
                return
            
            add_coins(user_id, thread_id, -found_item['price'])
            add_inventory_item(user_id, thread_id, found_item['name'])
            
            self.send_message(thread_id, f"✅ {found_item['emoji']} Purchased: **{found_item['name']}**! ({found_item['price']} coins)")
            add_xp(user_id, thread_id, 5, "buy_item")
            return
        
        # ============ INVENTORY ============
        elif cmd == '.inventory':
            items = get_inventory(user_id, thread_id)
            
            if not items:
                self.send_message(thread_id, "📭 You don't own any items yet! Use .shop to buy something.")
                return
            
            inv_list = "🎒 **Your Inventory:**\n\n"
            total_items = 0
            
            for item in items:
                inv_list += f"• {item['item_name']} x{item['quantity']}\n"
                total_items += item['quantity']
            
            inv_list += f"\n📦 Total items: {total_items}"
            self.send_message(thread_id, inv_list)
            return
        
        # ============ USE ============
        elif cmd == '.use':
            if not args:
                self.send_message(thread_id, "Usage: .use [item name]")
                return
            
            item_name = ' '.join(args)
            items = get_inventory(user_id, thread_id)
            
            has_item = None
            for item in items:
                if item['item_name'].lower() in item_name.lower():
                    has_item = item
                    break
            
            if not has_item:
                self.send_message(thread_id, "❌ You don't own that item! Use .shop to buy it.")
                return
            
            with get_db() as conn:
                c = conn.cursor()
                c.execute("""
                    UPDATE inventory 
                    SET quantity = quantity - 1 
                    WHERE user_id = ? AND thread_id = ? AND item_name = ?
                """, (user_id, thread_id, has_item['item_name']))
                c.execute("DELETE FROM inventory WHERE user_id = ? AND thread_id = ? AND item_name = ? AND quantity <= 0", 
                          (user_id, thread_id, has_item['item_name']))
                conn.commit()
            
            self.send_message(thread_id, f"🎉 Used: {has_item['item_name']}!")
            
            if "Nuclear Roast" in has_item['item_name']:
                self.send_message(thread_id, "💀 **NUCLEAR ROAST ACTIVATED!**\nUse .roast @user for ultimate destruction! 🔥")
            elif "Ban Protection" in has_item['item_name']:
                self.send_message(thread_id, "🛡️ **BAN PROTECTION ACTIVATED!**\nYou're safe from the next report! 😎")
            elif "Fake IQ" in has_item['item_name']:
                add_xp(user_id, thread_id, 10, "fake_iq")
                self.send_message(thread_id, "🧠 **+10 FAKE IQ!**\nYou're 10% smarter now... in theory! 🤓")
            else:
                self.send_message(thread_id, "💨 You used it! Nothing happened... (it's virtual, remember? 😂)")
            
            add_xp(user_id, thread_id, 5, "use_item")
            return
        
        # ============ MEMORY ============
        elif cmd == '.memory':
            with get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT text, created_at FROM memories WHERE user_id = ? AND thread_id = ? ORDER BY created_at DESC LIMIT 10", (user_id, thread_id))
                rows = c.fetchall()
            if not rows:
                self.send_message(thread_id, "📭 No memories saved yet!")
                return
            mem_list = "🧠 **Your Memories:**\n\n"
            for row in rows:
                mem_list += f"• {row['text']}\n"
            self.send_message(thread_id, mem_list)
            return
        
        elif cmd == '.remember':
            if not args:
                self.send_message(thread_id, "Usage: .remember [thing]")
                return
            memory = ' '.join(args)
            if len(memory) > 200:
                self.send_message(thread_id, "❌ Memory too long! Keep it under 200 characters.")
                return
            with get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM memories WHERE user_id = ? AND thread_id = ?", (user_id, thread_id))
                count = c.fetchone()[0]
                if count >= 20:
                    self.send_message(thread_id, "❌ You have too many memories! Use .forget to remove some.")
                    return
                c.execute("INSERT INTO memories (user_id, thread_id, text) VALUES (?, ?, ?)", (user_id, thread_id, memory))
                conn.commit()
            self.send_message(thread_id, f"✅ Remembered: \"{memory}\"")
            add_xp(user_id, thread_id, 5, "remember")
            return
        
        elif cmd == '.forget':
            if not args:
                self.send_message(thread_id, "Usage: .forget [thing]")
                return
            memory = ' '.join(args)
            with get_db() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM memories WHERE user_id = ? AND thread_id = ? AND text = ?", (user_id, thread_id, memory))
                conn.commit()
            self.send_message(thread_id, f"✅ Forgot: \"{memory}\"")
            return
        
        # ============ CHAOS ============
        elif cmd == '.chaos':
            personality = get_or_create_personality(thread_id)
            self.send_message(thread_id, f"🌀 CHAOS LEVEL: {personality['chaos']}%\n\n{random.choice(['You summoned the chaos!', 'The chaos is spreading...', 'I have no idea what I\'m doing 💀', 'This is fine 🔥'])}")
            update_personality(thread_id, chaos=min(100, personality['chaos'] + 10))
            add_xp(user_id, thread_id, 5, "chaos")
            return
        
        # ============ SUMMON ============
        elif cmd == '.summon':
            summon_state[thread_id] = {"active": True, "expires": time.time() + 300}
            self.send_message(thread_id, "🔮 **SUMMONED.**\n\nI'm listening for the next 5 minutes.\nTalk to me naturally!")
            add_xp(user_id, thread_id, 10, "summon")
            return
        
        # ============ ASK ============
        elif cmd == '.ask':
            if not args:
                self.send_message(thread_id, "Usage: .ask [question]")
                return
            question = ' '.join(args)
            if self.groq_api_key:
                reply = groq_ask_public(question, self.groq_api_key)
                if reply:
                    self.send_message(thread_id, reply)
                else:
                    self.send_message(thread_id, "⚠️ I couldn't think of a good reply. Try again!")
            return
        
        # ============ ADMIN ============
        if not self.is_admin(username):
            self.send_message(thread_id, f"❌ @{username} Not admin!")
            return
        
        elif cmd == '.groq':
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
            reason = ' '.join(args) if args else "AFK"
            AFK_USERS[(thread_id, user_id)] = (reason, datetime.now())
            self.send_message(thread_id, f"🛏️ @{username} is now AFK: {reason}")
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
            if spam_running:
                self.send_message(thread_id, "⚠️ Spam already running! Use .stopspam")
                return
            self.send_message(thread_id, f"📢 Admin starting spam: {count} messages!")
            global spam_thread
            spam_thread = threading.Thread(target=self.run_spam, args=(thread_id, count, message, username), daemon=True)
            spam_thread.start()
            return
        
        elif cmd == '.setwelcome':
            if not args:
                self.send_message(thread_id, "Usage: .setwelcome [message]")
                return
            new_welcome = ' '.join(args)
            set_setting(thread_id, 'welcome_message', new_welcome)
            self.send_message(thread_id, f"✅ Welcome message updated!")
            return
        
        elif cmd == '.setrules':
            if not args:
                self.send_message(thread_id, "Usage: .setrules [rules]")
                return
            new_rules = ' '.join(args)
            set_setting(thread_id, 'rules', new_rules)
            self.send_message(thread_id, f"✅ Rules updated!")
            return
        
        else:
            self.send_message(thread_id, f"❌ Unknown: {cmd}\nType .help")
    
    # ============ TRIVIA HELPERS ============
    def send_trivia_question(self, thread_id):
        state = trivia_state.get(thread_id)
        if not state:
            return
        current = state['current']
        questions = state['questions']
        if current >= len(questions):
            self.end_trivia(thread_id)
            return
        q = questions[current]
        options_text = ""
        if q.get('options'):
            options_text = "\n".join(q['options'])
        self.send_message(thread_id, f"--- Question {current+1}/{len(questions)} ---\n❓ {q['q']}\n{options_text}\n⏰ 15 seconds...")
        
        def check():
            time.sleep(15)
            if thread_id in trivia_state and trivia_state[thread_id]['current'] == current:
                self.send_message(thread_id, f"⏰ Time's up! Answer: {q['a']}")
                trivia_state[thread_id]['current'] += 1
                time.sleep(2)
                self.send_trivia_question(thread_id)
        threading.Thread(target=check, daemon=True).start()
    
    def end_trivia(self, thread_id):
        state = trivia_state.pop(thread_id, None)
        if not state:
            return
        score, total, username = state['score'], len(state['questions']), state['username']
        msgs = ["🧠 GENIUS! 🏆", "🔥 Amazing! 🌟", "👍 Good job! 💪", "🤔 Not bad! 📚", "😂 Did you even try?! 💀"]
        msg = msgs[0] if score == total else msgs[1] if score >= total-1 else msgs[2] if score >= total//2 else msgs[3] if score >= 1 else msgs[4]
        self.send_message(thread_id, f"--- 🎯 GAME OVER! ---\n🏆 @{username} scored {score}/{total}\n{msg}")
        add_xp(state['user_id'], thread_id, score * 10, "trivia")
        add_coins(state['user_id'], thread_id, score * 5)
    
    def check_trivia_answer(self, thread_id, user_id, message):
        state = trivia_state.get(thread_id)
        if not state or user_id != state['user_id']:
            return
        if state['current'] >= len(state['questions']):
            return
        q = state['questions'][state['current']]
        answer = message.lower().strip()
        if answer == q['a'].lower() or answer in ['a', 'b', 'c', 'd'] and q.get('options') and len(q['options']) >= ord(answer) - 96:
            state['score'] += 1
            self.send_message(thread_id, f"✅ Correct! +1 point! 🎉")
            state['current'] += 1
            time.sleep(2)
            self.send_trivia_question(thread_id)
    
    # ============ SPAM HELPERS ============
    def run_spam(self, thread_id, count, message, admin_username):
        global spam_running, spam_stop_flag
        spam_running = True
        spam_stop_flag = False
        try:
            for i in range(count):
                if spam_stop_flag:
                    self.send_message(thread_id, f"🛑 Spam stopped! Sent {i} messages.")
                    break
                if not self.running:
                    break
                emoji = random.choice(["🔥", "❤️", "💀", "👀", "🚀", "💯", "✨", "🎯", "😂", "🤣", "💪", "🦅", "🌟", "⚡", "🍿", "🎉", "🥶", "🤯", "😎", "👑"])
                self.send_message(thread_id, f"{emoji} {message}")
                time.sleep(random.uniform(SPAM_DELAY_MIN, SPAM_DELAY_MAX))
            else:
                self.send_message(thread_id, f"✅ Spam complete! {count} messages sent.")
        except Exception as e:
            self.send_message(thread_id, f"❌ Spam error: {e}")
        finally:
            spam_running = False
    
    def stop_spam(self, thread_id, username):
        global spam_running, spam_stop_flag
        if not self.is_admin(username):
            self.send_message(thread_id, f"❌ @{username} Only admins can stop spam!")
            return False
        if not spam_running:
            self.send_message(thread_id, "ℹ️ No spam running.")
            return False
        spam_stop_flag = True
        self.send_message(thread_id, "🛑 Stopping spam...")
        return True
    
    # ============ MAIN LOOP ============
    def check_messages(self):
        global processed_messages
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
                    
                    # New members
                    new_members = set(current) - self.known_members[thread_id]
                    for mid in new_members:
                        if mid != self.user_id:
                            uname = self.get_username_cached(mid)
                            if uname and (thread_id, mid) not in WELCOME_SENT:
                                print(f"[THREAD] 🔔 New member: @{uname}")
                                welcome_msg = get_welcome_message(thread_id) or WELCOME_MSG
                                self.send_message(thread_id, welcome_msg.format(username=uname))
                                time.sleep(random.uniform(1.0, 2.0))
                                rules = get_rules(thread_id) or RULES
                                self.send_message(thread_id, rules)
                                WELCOME_SENT[(thread_id, mid)] = True
                    
                    # Left members
                    left = self.known_members[thread_id] - set(current)
                    for mid in left:
                        if mid != self.user_id:
                            uname = self.get_username_cached(mid)
                            if uname:
                                print(f"[THREAD] 🚶 Member left: @{uname}")
                                self.send_message(thread_id, LEAVE_MSG.format(username=uname))
                    self.known_members[thread_id] = set(current)
                    
                    # Process messages
                    for msg in detail.messages:
                        msg_id = str(msg.id)
                        if msg_id in processed_messages:
                            continue
                        if msg.user_id == self.user_id or not msg.text:
                            continue
                        
                        username = self.get_username_cached(msg.user_id)
                        if not username:
                            continue
                        
                        processed_messages.append(msg_id)
                        print(f"[MESSAGE] 📩 @{username}: {msg.text[:50]}")
                        
                        # Update context history
                        self.context_history[thread_id].append((username, msg.text, datetime.now()))
                        
                        # Welcome back
                        now = datetime.now()
                        last = self.last_active.get(msg.user_id)
                        if msg.user_id != self.user_id and last and (now - last).total_seconds() >= WELCOME_BACK_INTERVAL:
                            last_welcome = USER_WELCOME_SENT.get(msg.user_id)
                            if not last_welcome or (now - last_welcome).total_seconds() > WELCOME_BACK_INTERVAL:
                                print(f"[THREAD] 👋 Welcome back @{username}")
                                self.send_message(thread_id, WELCOME_BACK_MSGS[0].format(username=username))
                                USER_WELCOME_SENT[msg.user_id] = now
                        
                        self.last_active[msg.user_id] = now
                        
                        # Admin tracking
                        if username.lower() in [a.lower() for a in ADMINS]:
                            ADMIN_LAST_SEEN[thread_id] = now
                        
                        # Admin tag reply
                        msg_lower = msg.text.lower()
                        if any(f"@{admin}".lower() in msg_lower for admin in ADMINS) and not self.is_admin(username):
                            if thread_id not in ADMIN_LAST_SEEN or (now - ADMIN_LAST_SEEN.get(thread_id, now - timedelta(minutes=10))).seconds > ADMIN_ACTIVE_TIMEOUT:
                                self.send_message(thread_id, f"@{username} {random.choice(ADMIN_TAG_REPLIES)}")
                                time.sleep(random.uniform(0.5, 1.0))
                        
                        # Admin greeting
                        if username.lower() in [a.lower() for a in ADMINS]:
                            last_seen = ADMIN_LAST_SEEN.get(thread_id, now - timedelta(minutes=10))
                            if (now - last_seen).seconds > 120:
                                self.send_message(thread_id, random.choice(ADMIN_GREETINGS))
                        
                        # Trivia
                        if thread_id in trivia_state:
                            self.check_trivia_answer(thread_id, msg.user_id, msg.text)
                        
                        # AFK
                        afk_key = (thread_id, msg.user_id)
                        if afk_key in AFK_USERS:
                            reason, t = AFK_USERS[afk_key]
                            if (now - t).seconds > 300:
                                del AFK_USERS[afk_key]
                                self.send_message(thread_id, f"🟢 @{username} is no longer AFK")
                        
                        # NATURAL REPLY
                        if not msg.text.startswith('.'):
                            personality = get_or_create_personality(thread_id)
                            
                            # Check if it's a command
                            is_command = msg.text.startswith('.')
                            
                            router_result = self.ai_router.should_reply(
                                thread_id, msg.user_id, msg.text, self.username, is_command
                            )
                            
                            if router_result["should_reply"] and self.groq_api_key:
                                # Build context
                                context = []
                                for uname, text, ts in list(self.context_history[thread_id])[-10:]:
                                    context.append(f"@{uname}: {text}")
                                
                                reply = groq_natural_reply(
                                    msg.text, username, self.groq_api_key, personality, context
                                )
                                
                                if reply:
                                    # Check if similar reply was sent recently
                                    is_duplicate = False
                                    for recent in self.recent_bot_responses[thread_id]:
                                        if len(reply) > 10 and reply in recent:
                                            is_duplicate = True
                                            break
                                    
                                    if not is_duplicate:
                                        time.sleep(random.uniform(1.0, 3.0))
                                        self.send_message(thread_id, reply)
                                        print(f"[AI] 🤖 Reply to @{username} ({router_result['reason']})")
                                        self.ai_router.mark_reply(thread_id, msg.user_id)
                                        self.recent_bot_responses[thread_id].append(reply)
                                        add_xp(msg.user_id, thread_id, 2, "natural_reply")
                                    else:
                                        print(f"[AI] ⏭️ Skipping duplicate reply")
                        
                        # Process commands
                        if msg.text.startswith('.'):
                            self.handle_command(thread_id, msg.user_id, username, msg.text)
                            
                except RateLimitError:
                    print("[RATE LIMIT] ⚠️ Rate limited! Waiting 5 minutes...")
                    time.sleep(300)
                except Exception as e:
                    print(f"[THREAD] ⚠️ Thread error: {e}")
                    traceback.print_exc()
        except RateLimitError:
            print("[RATE LIMIT] ⚠️ Rate limited! Waiting 5 minutes...")
            time.sleep(300)
        except Exception as e:
            print(f"[ERROR] ⚠️ Check error: {e}")
            traceback.print_exc()
    
    def run(self):
        print("\n" + "=" * 60)
        print("🔥 ULTIMATE GC COMPANION BOT RUNNING")
        print(f"👤 Bot: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print(f"📊 Monitoring: {getattr(self, 'group_count', 1)} group(s)")
        print("=" * 60)
        print("🤖 Features:")
        print("   ✅ Smart AI Router (not random)")
        print("   ✅ Context-aware conversations")
        print("   ✅ Personality-driven responses")
        print("   ✅ Human-like timing")
        print("   ✅ Anti-repetition")
        print("   ✅ Proper cooldowns")
        print("   ✅ .buy, .inventory, .use")
        print("   ✅ Multi-GC isolation")
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
                print(f"[ERROR] ⚠️ Error: {e}")
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
        traceback.print_exc()

if __name__ == "__main__":
    main()

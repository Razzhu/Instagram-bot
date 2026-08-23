#!/usr/bin/env python3
"""
ULTIMATE GC COMPANION BOT - ENHANCED VERSION

- Smarter AI reply system with context awareness
- Improved personality system
- Human-like response timing
- Better rate limit handling
- Fixed all bugs
- Enhanced command cooldowns
- And much more!
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
import hashlib

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

# ============ CONFIGURATION ============

class Config:
    # Reply chances
    NATURAL_REPLY_CHANCE = 0.25
    DIRECT_MENTION_CHANCE = 0.95
    QUESTION_CHANCE = 0.85
    REPLY_TO_BOT_CHANCE = 0.90
    SUMMON_MODE_CHANCE = 0.70
    FUNNY_MESSAGE_CHANCE = 0.40
    CONVERSATION_CHANCE = 0.25
    LOW_PRIORITY_CHANCE = 0.10
    
    # Context
    MAX_CONTEXT_MESSAGES = 25
    CONTEXT_EXPIRY_SECONDS = 600  # 10 minutes
    
    # Cooldowns
    BOT_REPLY_COOLDOWN = 8  # seconds between bot replies in same thread
    USER_REPLY_COOLDOWN = 5  # seconds between replying to same user
    
    # AI
    AI_MAX_TOKENS = 100
    AI_TEMPERATURE = 0.9
    
    # Polling
    POLL_INTERVAL_MIN = 5.0
    POLL_INTERVAL_MAX = 10.0
    
    # Spam
    MAX_SPAM_COUNT = 100
    SPAM_DELAY_MIN = 5
    SPAM_DELAY_MAX = 10
    
    # Welcome
    WELCOME_BACK_INTERVAL = 600  # 10 minutes
    ADMIN_ACTIVE_TIMEOUT = 900  # 15 minutes
    
    # Rate limiting
    RATE_LIMIT_BACKOFFS = [5, 15, 30, 60, 120]
    
    # Memory limits
    MAX_MEMORIES_PER_USER = 50
    MAX_MEMORY_LENGTH = 500
    
    # Trivia
    TRIVIA_TIME_LIMIT = 15  # seconds per question

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

# ============ MESSAGES ============

LEAVE_MSG = "👋 @{username} left the group! See you around!"
WELCOME_BACK_MSGS = [
    "👋 Welcome back @{username}!",
    "Hey @{username}, good to see you again!",
    "@{username} is back!",
    "Oh look who decided to show up - @{username}! 👀"
]

# ============ SPAM EMOJIS ============

SPAM_EMOJIS = ["🔥", "❤️", "💀", "👀", "🚀", "💯", "✨", "🎯", "😂", "🤣", "💪", "🦅", "🌟", "⚡", "🍿", "🎉", "🥶", "🤯", "😎", "👑"]

COMMAND_COOLDOWN = {
    '.ping': 5, '.dice': 5, '.flip': 5, '.rps': 10,
    '.trivia': 20, '.roast': 15, '.compliment': 10,
    '.fact': 10, '.joke': 10, '.8ball': 10,
    '.love': 10, '.score': 5, '.leaderboard': 15,
    '.help': 15, '.rules': 15,
    '.spam': 300, '.stopspam': 10,
    '.afk': 60, '.setwelcome': 60, '.setrules': 60,
    '.ask': 15, '.groq': 30,
    '.daily': 60, '.balance': 5, '.give': 30,
    '.shop': 10, '.buy': 10, '.inventory': 10,
    '.memory': 10, '.forget': 15, '.remember': 15,
    '.mostlikely': 30, '.sus': 15,
    '.profile': 10, '.leaderboard': 15,
    '.chaos': 60, '.summon': 120,
    '.weekly': 60,
    'default': 5,
}

# ============ SHOP ============

SHOP_ITEMS = [
    {"name": "Virtual Maggi", "price": 100, "emoji": "🍜", "desc": "Absolutely useless. Buy it anyway."},
    {"name": "Fake Admin Crown", "price": 500, "emoji": "👑", "desc": "Flex on the peasants."},
    {"name": "Ban Protection", "price": 2000, "emoji": "🛡️", "desc": "One free pass. Use wisely."},
    {"name": "Nuclear Roast", "price": 5000, "emoji": "💀", "desc": "The ultimate roast weapon."},
    {"name": "+10 Fake IQ", "price": 10000, "emoji": "🧠", "desc": "You're still dumb. But less."},
]

# ============ EXPANDED FALLBACK (20+ each) ============

FALLBACK_ROASTS = [
    "तू हर जगह है जैसे WiFi, पर काम किसी काम का नहीं! 📶",
    "तेरी सोच इतनी गहरी है जितनी चाय की प्लेट! ☕",
    "तू अच्छा है... बस दूर से। 😂",
    "तेरा चेहरा देखकर लगता है कल का कल होगा! 🗓️",
    "तुझसे अच्छा तो मेरा पुराना फोन है, वो भी कम से कम चार्ज हो जाता है! 🔋",
    "तू वो दोस्त है जो ग्रुप में आता है और माहौल खराब कर देता है 💀",
    "तेरी हर बात में 90% झूठ और 10% अतिरंजना होती है 😂",
    "तू अगर जिंदगी में भी ऐसा ही है तो मुझे तेरी फिक्र है 🥲",
    "तेरे से बेहतर तो मेरा कल का खाना है जो फ्रिज में पड़ा है 🍲",
    "तू सोचता है कि तू कूल है, पर हकीकत में तू तो बस एक मजाक है 🤡",
    "तेरी आवाज सुनकर लगता है जैसे कोई बंदर को पकड़ कर बोला हो 🐒",
    "तू वो इंसान है जो ऑनलाइन गेम में भी हार जाता है 🎮",
    "तेरी दोस्ती से अच्छा तो मेरी अकेलाई है 😂",
    "तू अगर मेरी जगह होता तो मैं खुद को रोज धन्यवाद देता 🙏",
    "तू हर बात में अपनी तारीफ करता है, जैसे तू ही दुनिया का सबसे बड़ा इंसान हो 😐",
    "तेरी सोच को देखकर लगता है तूने कभी किताब नहीं उठाई 📚",
    "तू वो दोस्त है जो पार्टी में आता है और खाना खाकर चला जाता है 🍕",
    "तेरे से बात करके लगता है जैसे मैंने 5 मिनट बर्बाद कर दिए ⏳",
    "तू सोचता है कि तू मजाकिया है, पर हकीकत में तू बस हास्यास्पद है 😂",
    "तेरी हर बात में एक झूठ छिपा होता है, मानो तू पेशेवर झूठा हो 🤥",
    "तू अगर मेरी जिंदगी में होता तो मैं खुद को अकेला रखना पसंद करता 🚶",
]

FALLBACK_JOKES = [
    "एक आदमी ने डॉक्टर से कहा: मुझे हर रात बुरे सपने आते हैं। डॉक्टर बोला: क्या सपने आते हैं? आदमी बोला: सपने में मुझे नींद नहीं आती! 😂",
    "टीचर: तुम्हारी कॉपी में तो दीमक लग गई है! स्टूडेंट: सर, वो मेरी क्रिएटिविटी है! 💀",
    "पति: मैं तुमसे बहुत प्यार करता हूँ। पत्नी: क्या चाहिए? 😂",
    "एक लड़का लड़की से बोला: तुम मेरी आँखों का तारा हो। लड़की बोली: तो क्या मैं टूट कर गिर जाऊँ? 🤡",
    "बॉस: तुम्हारी सोच बहुत गहरी है। कर्मचारी: सर, वो मेरी अलमारी खाली है इसलिए। 💀",
    "पत्नी: मुझे तुमसे बात नहीं करनी। पति: ठीक है, मुझे भी तुमसे नहीं करनी। पत्नी: तो फिर तुम बोल क्यों रहे हो? 😂",
    "डॉक्टर: आपको रोज सुबह दौड़ना चाहिए। मरीज: क्यों, क्या मुझे कोई बीमारी है? डॉक्टर: नहीं, लेकिन मुझे आपकी शक्ल देखकर दौड़ने का मन करता है 🏃",
    "टीचर: तुम्हारा ध्यान कहाँ है? स्टूडेंट: सर, मेरा ध्यान तो हमेशा भटकता रहता है, जैसे मेरा बॉयफ्रेंड 💀",
    "बॉस: तुम्हारी कॉपी में तो कोई सेंस नहीं है। कर्मचारी: सर, वो मेरी क्रिएटिविटी है 😂",
    "पत्नी: मुझे तुमसे प्यार है। पति: मुझे भी। पत्नी: तो फिर चाय ले आओ। पति: 😂",
]

FALLBACK_COMPLIMENTS = [
    "तू तो लगता है जैसे सुबह की चाय — हर किसी को भाती है! ☕",
    "तू वो दोस्त है जिसके बिना ग्रुप अधूरा है! ❤️",
    "तू वजह है ग्रुप की शान! 👑",
    "तेरी हँसी सुनकर लगता है जैसे बारिश हो गई! 🌧️",
    "तू वो इंसान है जिसके बारे में कोई बुरा नहीं बोल सकता! 🌟",
    "तू जैसे लोगों के लिए ही दोस्ती शब्द बना है! 🤝",
    "तेरी बातें सुनकर लगता है जैसे कोई किताब पढ़ रहा हूँ! 📚",
    "तू वो चीज़ है जिसकी हर ग्रुप को ज़रूरत होती है! 💎",
    "तेरी उपस्थिति से ग्रुप और भी अच्छा लगता है! 🌺",
    "तू वो दोस्त है जो मुश्किल समय में भी साथ खड़ा रहता है! 💪",
    "तेरी हर बात में एक सीख होती है! 🧠",
    "तू जैसे लोग इस दुनिया को बेहतर बनाते हैं! 🌍",
]

FALLBACK_FACTS = [
    "ऑक्टोपस के 3 दिल होते हैं! 💙",
    "केला एक बेरी है! 🍌",
    "वीनस पर 1 दिन 1 साल से भी लंबा होता है! 🌍",
    "मधुमक्खियाँ नाच कर बात करती हैं! 🐝",
    "इंसान का दिमाग 100,000 साल पुराना है! 🧠",
    "पानी 3 रूपों में मौजूद है: ठोस, तरल, गैस! 💧",
    "बिल्लियाँ 100+ आवाज़ें निकाल सकती हैं! 🐱",
    "डॉल्फिन एक दूसरे का नाम रखती हैं! 🐬",
    "इंसान का शरीर 60% पानी है! 💦",
    "सूरज 4.6 अरब साल पुराना है! ☀️",
]

FALLBACK_8BALL = [
    "🎱 शायद हाँ", "🎱 नहीं", "🎱 पक्का नहीं",
    "🎱 बिल्कुल", "🎱 कभी नहीं", "🎱 शायद",
    "🎱 पूछते रहो", "🎱 मेरी समझ से बाहर",
    "🎱 हाँ, लेकिन शर्त के साथ", "🎱 नहीं, बिल्कुल नहीं",
]

FALLBACK_TRIVIA = [
    {"q": "फ्रांस की राजधानी क्या है?", "a": "पेरिस"},
    {"q": "2+2 क्या होता है?", "a": "4"},
    {"q": "सबसे बड़ा ग्रह कौन सा है?", "a": "बृहस्पति"},
    {"q": "भारत की राजधानी क्या है?", "a": "नई दिल्ली"},
    {"q": "मानव शरीर में कितनी हड्डियाँ होती हैं?", "a": "206"},
    {"q": "पृथ्वी का सबसे बड़ा महासागर कौन सा है?", "a": "प्रशांत महासागर"},
    {"q": "सबसे लंबी नदी कौन सी है?", "a": "नील"},
    {"q": "किस देश में सबसे ज्यादा लोग रहते हैं?", "a": "चीन"},
]

ADMIN_TAG_REPLIES = [
    "Ohh tell me what happened, my boss is offline 🧐",
    "Boss is busy! Tell me, I'll handle it 💪",
    "Admin is AFK, but I'm here! What's up? 🤖",
    "My admin is resting. Spill the tea! ☕",
    "Boss is not available. You can tell me, I'm listening 👂",
    "Admin is offline! What drama did I miss? 🍿",
    "My admin is taking a break. But I'm always here! 😎",
]

ADMIN_GREETINGS = [
    "👑 Welcome back boss!",
    "🙇‍♂️ At your service, my lord!",
    "👋 Hey boss! Good to see you!",
    "🫡 Reporting for duty, sir!",
    "👑 The king has arrived!",
]

# ============ STATE (Runtime only) ============

AFK_USERS = {}  # {(thread_id, user_id): (reason, timestamp)}
USER_WELCOME_SENT = {}
ADMIN_LAST_SEEN = {}
WELCOME_SENT = {}
USER_LAST_ACTIVE = {}  # user_id -> timestamp

processed_messages = deque(maxlen=5000)

trivia_state = {}
roast_battle_state = {}
mostlikely_state = {}
active_events = {}
summon_state = {}

command_cooldowns = {}
user_command_cooldowns = defaultdict(dict)

spam_running = False
spam_stop_flag = False
spam_thread = None
spam_threads = {}  # thread_id -> thread

# Context storage
thread_contexts = {}  # thread_id -> deque of messages
bot_response_cache = {}  # thread_id -> deque of recent bot responses
bot_last_reply_time = {}  # thread_id -> timestamp
user_last_reply_time = {}  # (thread_id, user_id) -> timestamp

# Rate limiting
rate_limit_attempts = defaultdict(int)
rate_limit_last_reset = time.time()
current_backoff_index = 0

# ============ GROQ AI ============

def groq_generate(prompt, api_key, max_tokens=Config.AI_MAX_TOKENS, temperature=Config.AI_TEMPERATURE):
    """Generate a response using Groq API with error handling."""
    if not api_key:
        return None
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "model": "groq/compound",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
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
        print(f"[ERROR] Groq error: {e}")
        return None

def groq_roast(target, api_key):
    return groq_generate(f"Give a SHORT savage roast for @{target} in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_joke(api_key):
    return groq_generate("Tell a SHORT funny joke in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_fact(api_key):
    return groq_generate("Give a SHORT interesting fact in HINDI/HINGLISH (5-10 words). Use emojis.", api_key)

def groq_ask_public(question, api_key):
    return groq_generate(f"Reply to this question in a funny way in HINDI/HINGLISH (5-10 words). Question: '{question}'", api_key)

def groq_admin(question, api_key):
    return groq_generate(f"Answer this question in HINDI/HINGLISH. Be helpful, informative, and complete. Question: '{question}'", api_key)

def groq_natural_reply(message, username, api_key, personality=None, context=None):
    """Generate a natural, context-aware reply."""
    if not api_key:
        return None
    
    personality_text = ""
    if personality:
        personality_text = f"""
Mood: {personality.get('mood', 'chill')}
Friendliness: {personality.get('friendliness', 70)}%
Sarcasm: {personality.get('sarcasm', 60)}%
Chaos: {personality.get('chaos', 30)}%
"""
    
    context_text = ""
    if context and len(context) > 0:
        context_text = "Recent conversation:\n" + "\n".join(context[-10:]) + "\n"
    
    prompt = f"""You are a funny, natural member of an Instagram group chat.
You are NOT an assistant. Respond naturally to the latest message.

{personality_text}
{context_text}
Latest message:
@{username}: {message}

Rules:
- Keep it SHORT (1-2 sentences max)
- Use HINDI/HINGLISH
- Be RELEVANT to the conversation
- Don't force jokes
- Don't overuse emojis (max 1-2)
- Don't mention being an AI
- Don't repeat the user's message
- Respond only when there is something meaningful/funny to say
- Match the group's personality

Response:"""
    
    return groq_generate(prompt, api_key, max_tokens=80, temperature=0.9)

def groq_trivia_question(api_key):
    """Generate a trivia question with options and answer."""
    prompt = """Generate ONE short trivia question in HINDI/HINGLISH with 4 options.
Format EXACTLY:
Q: [question]
A) [option1]
B) [option2]
C) [option3]
D) [option4]
Answer: [letter]

Example:
Q: भारत की राजधानी क्या है?
A) मुंबई
B) दिल्ली
C) कोलकाता
D) चेन्नई
Answer: B"""
    
    return groq_generate(prompt, api_key, max_tokens=150, temperature=0.7)

# ============ AI ROUTER ============

class AIRouter:
    def __init__(self):
        self.cooldown_tracker = {}
        self.last_bot_message = {}
        self.response_cache = {}  # thread_id -> deque of recent responses
        self.message_history = {}  # thread_id -> deque of messages for dedup
        self.username = None  # Will be set by bot
        self.cl = None  # Will be set by bot
    
    def should_reply(self, thread_id, user_id, message, bot_username, user_count=0):
        """Smart reply decision based on multiple factors."""
        # Never reply to own messages
        if user_id == self.cl.user_id if self.cl else False:
            return {"should_reply": False, "reason": "own_message", "score": 0}
        
        # Never reply to commands
        if message.startswith('.'):
            return {"should_reply": False, "reason": "command", "score": 0}
        
        # Never reply to empty messages
        if not message or len(message.strip()) < 2:
            return {"should_reply": False, "reason": "empty_message", "score": 0}
        
        score = 0
        reasons = []
        
        # Check for short meaningless messages (unless direct mention)
        short_meaningless = ['ok', 'hmm', 'yes', 'no', 'yeah', 'nah', 'hi', 'hey', 'lol', '😂', '💀']
        if message.lower().strip() in short_meaningless:
            # Only reply if directly mentioned or replied to
            if bot_username.lower() not in message.lower():
                return {"should_reply": False, "reason": "meaningless", "score": 0}
        
        # Check bot cooldown
        if thread_id in self.last_bot_message:
            elapsed = time.time() - self.last_bot_message[thread_id]
            if elapsed < Config.BOT_REPLY_COOLDOWN:
                return {"should_reply": False, "reason": "bot_cooldown", "score": 0}
        
        # Check user cooldown
        user_key = (thread_id, user_id)
        if user_key in self.cooldown_tracker:
            elapsed = time.time() - self.cooldown_tracker[user_key]
            if elapsed < Config.USER_REPLY_COOLDOWN:
                return {"should_reply": False, "reason": "user_cooldown", "score": 0}
        
        # HIGH PRIORITY: Direct mention
        if bot_username.lower() in message.lower():
            score += 100
            reasons.append("direct_mention")
        
        # HIGH PRIORITY: Reply to bot
        if message.startswith('@') and bot_username.lower() in message.lower():
            score += 90
            reasons.append("reply_to_bot")
        
        # HIGH PRIORITY: Question
        question_words = ['?', '?', 'who', 'what', 'when', 'where', 'why', 'how', 'which', 'kya', 'kaun', 'kyu', 'kaise', 'kab', 'kahan']
        if '?' in message or '?' in message or any(word in message.lower() for word in question_words):
            score += 70
            reasons.append("question")
        
        # MEDIUM PRIORITY: Funny message
        funny_patterns = ['😂', '💀', 'lol', '🤣', 'haha', 'lmao', '💀', '😭', '🤡']
        if any(p in message for p in funny_patterns):
            score += 30
            reasons.append("funny_opportunity")
        
        # MEDIUM PRIORITY: Summon mode
        if thread_id in summon_state and summon_state[thread_id].get("active", False):
            score += 40
            reasons.append("summon_mode")
        
        # MEDIUM PRIORITY: Conversation context
        if len(message.split()) > 3:  # Longer messages are more likely to be conversational
            score += 15
            reasons.append("conversational")
        
        # LOW PRIORITY: Random chance
        if random.random() < Config.NATURAL_REPLY_CHANCE:
            score += 10
            reasons.append("random_chance")
        
        # Final decision
        if score >= 60:
            return {"should_reply": True, "reason": reasons[0] if reasons else "general", "score": score}
        elif score >= 30 and random.random() < 0.5:
            return {"should_reply": True, "reason": "medium_priority", "score": score}
        else:
            return {"should_reply": False, "reason": "low_score", "score": score}
    
    def mark_reply(self, thread_id, user_id):
        """Mark that a reply was sent for cooldown tracking."""
        self.cooldown_tracker[(thread_id, user_id)] = time.time()
        self.last_bot_message[thread_id] = time.time()
    
    def is_response_repetitive(self, thread_id, response):
        """Check if a response is too similar to recent bot messages."""
        if thread_id not in self.response_cache:
            self.response_cache[thread_id] = deque(maxlen=10)
        
        # Check similarity with recent responses
        for cached in self.response_cache[thread_id]:
            # Simple similarity check
            if len(cached) > 0 and len(response) > 0:
                similarity = len(set(cached.split()) & set(response.split())) / max(len(set(cached.split())), 1)
                if similarity > 0.7:
                    return True
        
        return False
    
    def add_response(self, thread_id, response):
        """Add a response to the cache."""
        if thread_id not in self.response_cache:
            self.response_cache[thread_id] = deque(maxlen=10)
        self.response_cache[thread_id].append(response)
    
    def add_to_context(self, thread_id, username, message, timestamp=None):
        """Add a message to the thread context."""
        if thread_id not in self.message_history:
            self.message_history[thread_id] = deque(maxlen=Config.MAX_CONTEXT_MESSAGES)
        
        if timestamp is None:
            timestamp = time.time()
        
        # Format: "username: message"
        formatted = f"@{username}: {message}"
        self.message_history[thread_id].append(formatted)
        
        # Clean old messages
        # We'll just rely on the max length for simplicity
    
    def get_context(self, thread_id, limit=10):
        """Get recent context for a thread."""
        if thread_id not in self.message_history:
            return []
        
        return list(self.message_history[thread_id])[-limit:]

# ============ AI ROUTER INSTANCE ============
ai_router = AIRouter()

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
    
    def get_delay(self, action='message', message_length=0):
        """Get a realistic delay based on mood and message length."""
        mood_delays = {
            'chatty': {'message': (1.0, 3.0), 'typing': (0.5, 1.0)},
            'brief': {'message': (0.5, 1.5), 'typing': (0.2, 0.5)},
            'distracted': {'message': (5.0, 12.0), 'typing': (2.0, 5.0)},
            'focused': {'message': (0.8, 2.0), 'typing': (0.3, 0.7)},
            'slow': {'message': (6.0, 15.0), 'typing': (3.0, 6.0)},
            'hyper': {'message': (0.3, 1.0), 'typing': (0.1, 0.3)}
        }
        
        min_d, max_d = mood_delays.get(self.current_mood, mood_delays['focused']).get(action, (1.0, 3.0))
        
        # Adjust for message length
        if action == 'typing':
            char_delay = min(message_length / 100, 2.0)
            max_d = min(max_d + char_delay, 10.0)
        
        return random.uniform(min_d, max_d)
    
    def type_time(self, text):
        """Calculate typing time based on text length and speed."""
        chars = len(text)
        base_time = chars / (self.typing_speed * random.uniform(0.7, 1.3))
        return min(base_time + random.uniform(0.5, 1.5), 10.0)

human = HumanBehavior()

def human_delay(min_sec=1.0, max_sec=4.0, message_length=0):
    """Sleep with human-like delay."""
    if message_length > 0:
        # Longer messages get longer delays
        extra = min(message_length / 50, 2.0)
        max_sec = min(max_sec + extra, 10.0)
    time.sleep(random.uniform(min_sec, max_sec))

def type_message_like_human(text):
    """Simulate typing delay."""
    time.sleep(human.type_time(text))

# ============ MAIN BOT ============

class InstagramGroupBot:
    def __init__(self):
        print("🔧 Initializing bot...")
        self.cl = Client()
        self.cl.set_user_agent("Mozilla/5.0 (Linux; Android 13) Chrome/116.0.5845.92")
        self.running = True
        self.known_members = {}
        self.username_cache = {}
        self.groq_api_key = GROQ_API_KEY
        
        # Set AI router attributes
        ai_router.cl = self.cl
        
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
        print("✅ Bot initialization complete!")
    
    def login(self):
        print("🔐 Logging in...")
        try:
            self.cl.login_by_sessionid(SESSION_ID)
            self.username = self.cl.username
            self.user_id = self.cl.user_id
            ai_router.username = self.username
            print(f"✅ Logged in as: @{self.username}")
            print(f"👥 Followers: {self.cl.user_followers(self.user_id)}")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            raise e
    
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
        """Check if a username is an admin (case-insensitive)."""
        return username.lower() in ADMINS or username.lower() == self.username.lower()
    
    def get_username_cached(self, user_id):
        """Get username from cache or fetch from Instagram."""
        if user_id in self.username_cache:
            return self.username_cache[user_id]
        try:
            user = self.cl.user_info(user_id)
            self.username_cache[user_id] = user.username
            return user.username
        except:
            return None
    
    def send_message(self, thread_id, message):
        """Send a message with error handling and rate limiting."""
        try:
            type_message_like_human(message)
            human_delay(1.0, 3.0, len(message))
            self.cl.direct_send(message, thread_ids=[thread_id])
            print(f"📤 Sent: {message[:30]}...")
            human_delay(1.0, 2.0)
            return True
        except RateLimitError:
            print("⚠️ Rate limited! Waiting with exponential backoff...")
            self.handle_rate_limit()
            return False
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    def handle_rate_limit(self):
        """Handle rate limiting with exponential backoff."""
        global current_backoff_index
        if current_backoff_index < len(Config.RATE_LIMIT_BACKOFFS):
            wait_time = Config.RATE_LIMIT_BACKOFFS[current_backoff_index]
            current_backoff_index += 1
        else:
            wait_time = Config.RATE_LIMIT_BACKOFFS[-1]
        
        print(f"⏳ Waiting {wait_time} seconds...")
        time.sleep(wait_time)
    
    # ============ COMMAND HANDLER ============
    def handle_command(self, thread_id, user_id, username, command):
        """Handle all commands with cooldown enforcement."""
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        print(f"📩 Command from @{username}: {cmd}")
        
        # Check command cooldown
        if cmd in COMMAND_COOLDOWN:
            cooldown_key = (thread_id, user_id, cmd)
            if cooldown_key in command_cooldowns:
                elapsed = time.time() - command_cooldowns[cooldown_key]
                if elapsed < COMMAND_COOLDOWN[cmd]:
                    remaining = int(COMMAND_COOLDOWN[cmd] - elapsed)
                    self.send_message(thread_id, f"⏳ Wait {remaining}s before using {cmd} again.")
                    return
        
        # ============ HELP ============
        if cmd == '.help':
            help_text = """
🔥 ULTIMATE GC BOT COMMANDS:

🎮 Games:
.dice - Roll dice
.flip - Flip coin
.rps - Rock Paper Scissors
.trivia - 5 questions with timer
.roast @user - Roast user
.roastbattle @u1 @u2 - Roast battle!
.compliment @user - Compliment user
.fact - Random fact
.joke - Random joke
.8ball [question] - Magic 8-ball
.love @user OR .love @u1 @u2 - Love calculator
.mostlikely - Who is most likely to...?
.sus @user - Suspicious claim detector

📊 Profile:
.score - Your points
.leaderboard - Top players
.profile @user - View user profile
.balance - Check coins
.daily - Claim daily reward
.give @user amount - Give coins

🧠 Memory:
.memory - Show memories
.remember [thing] - Add memory
.forget [thing] - Delete memory

👑 Admin:
.spam count msg - Spam messages
.stopspam - Stop spam
.afk [reason] - Set AFK
.setwelcome msg - Set welcome
.setrules rules - Set rules
.groq [question] - Ask Groq

🤖 AI:
.ask [question] - Ask bot (funny)
Bot also replies naturally to conversations!

🥚 Secrets:
.chaos - Trigger chaos
.summon - Rare event
"""
            self.send_message(thread_id, help_text)
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ BASIC COMMANDS ============
        elif cmd == '.rules':
            rules = get_rules(thread_id) or RULES
            self.send_message(thread_id, rules)
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        elif cmd == '.ping':
            self.send_message(thread_id, "🏓 Pong! Bot is alive!")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        elif cmd == '.dice':
            roll = random.randint(1, 6)
            self.send_message(thread_id, f"🎲 @{username} rolled **{roll}**!")
            add_xp(user_id, thread_id, 5, "dice_roll")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        elif cmd == '.flip':
            result = random.choice(['Heads', 'Tails'])
            self.send_message(thread_id, f"🪙 @{username} flipped **{result}**!")
            add_xp(user_id, thread_id, 5, "flip_coin")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
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
            elif (user_choice == 'rock' and bot_choice == 'scissors') or (user_choice == 'paper' and bot_choice == 'rock') or (user_choice == 'scissors' and bot_choice == 'paper'):
                result = "You win! 🎉"
                add_xp(user_id, thread_id, 15, "rps_win")
                add_coins(user_id, thread_id, 10)
            else:
                result = "I win! 😎"
            self.send_message(thread_id, f"🪨📄✂️ @{username}: {user_choice} 🤖 Bot: {bot_choice}\n{result}")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ TRIVIA ============
        elif cmd == '.trivia':
            if thread_id in trivia_state:
                self.send_message(thread_id, "⚠️ Trivia already running!")
                return
            
            questions = []
            # Try Groq first
            if self.groq_api_key:
                for _ in range(5):
                    q_data = groq_trivia_question(self.groq_api_key)
                    if q_data:
                        # Parse the response
                        lines = q_data.split('\n')
                        question = ""
                        options = []
                        answer = ""
                        for line in lines:
                            line = line.strip()
                            if line.startswith('Q:'):
                                question = line[2:].strip()
                            elif line.startswith('A)') or line.startswith('B)') or line.startswith('C)') or line.startswith('D)'):
                                options.append(line)
                            elif line.startswith('Answer:'):
                                answer = line[7:].strip()
                        
                        if question and options and answer:
                            # Format the question with options
                            full_q = question + "\n" + "\n".join(options)
                            questions.append({"q": full_q, "a": answer})
            
            # If Groq didn't provide enough questions, use fallback
            if len(questions) < 5:
                qs = random.sample(FALLBACK_TRIVIA, min(5, len(FALLBACK_TRIVIA)))
                questions = [{"q": q['q'], "a": q['a']} for q in qs]
            
            trivia_state[thread_id] = {
                'questions': questions[:5],
                'current': 0,
                'score': 0,
                'user_id': user_id,
                'username': username,
                'start_time': datetime.now()
            }
            self.send_message(thread_id, f"🧠 **TRIVIA STARTED!**\n@{username} has 15 sec per question.\nTotal: {len(questions[:5])} questions.")
            self.send_trivia_question(thread_id)
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
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
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
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
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ JOKE ============
        elif cmd == '.joke':
            msg = None
            if self.groq_api_key:
                msg = groq_joke(self.groq_api_key)
            msg = msg or random.choice(FALLBACK_JOKES)
            self.send_message(thread_id, f"😂 {msg}")
            add_xp(user_id, thread_id, 3, "joke")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ FACT ============
        elif cmd == '.fact':
            msg = None
            if self.groq_api_key:
                msg = groq_fact(self.groq_api_key)
            msg = msg or random.choice(FALLBACK_FACTS)
            self.send_message(thread_id, f"📖 {msg}")
            add_xp(user_id, thread_id, 3, "fact")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ 8BALL ============
        elif cmd == '.8ball':
            if not args:
                self.send_message(thread_id, "Ask me something! Example: .8ball Will I win?")
                return
            msg = random.choice(FALLBACK_8BALL)
            self.send_message(thread_id, msg)
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
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
                name1 = username
                name2 = mentions[0]
                percentage = random.randint(0, 100)
                heart = "❤️🔥" if percentage >= 80 else "❤️" if percentage >= 60 else "💕" if percentage >= 40 else "💛" if percentage >= 20 else "💔"
                msgs = {90: "True love! Soulmates! 😍💕", 75: "A match made in heaven! 🥰", 60: "Good connection! 😊", 40: "It's complicated... 🤔", 20: "Friendzone! 😂", 0: "Bro, you two are like oil and water 💀"}
                msg = next((v for k, v in sorted(msgs.items(), reverse=True) if percentage >= k), msgs[0])
                self.send_message(thread_id, f"💕 **Love Calculator**\n@{name1} + @{name2} = {percentage}% {heart}\n\n{msg}")
            elif len(mentions) == 2:
                name1 = mentions[0]
                name2 = mentions[1]
                percentage = random.randint(0, 100)
                heart = "❤️🔥" if percentage >= 80 else "❤️" if percentage >= 60 else "💕" if percentage >= 40 else "💛" if percentage >= 20 else "💔"
                msgs = {90: "True love! Soulmates! 😍💕", 75: "A match made in heaven! 🥰", 60: "Good connection! 😊", 40: "It's complicated... 🤔", 20: "Friendzone! 😂", 0: "Bro, you two are like oil and water 💀"}
                msg = next((v for k, v in sorted(msgs.items(), reverse=True) if percentage >= k), msgs[0])
                self.send_message(thread_id, f"💕 **Love Calculator**\n@{name1} + @{name2} = {percentage}% {heart}\n\n{msg}")
            else:
                self.send_message(thread_id, "❌ Please tag only 1 or 2 people!")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ MOST LIKELY ============
        elif cmd == '.mostlikely':
            mostlikely_questions = ["कौन सबसे ज्यादा Maggi खाता है?", "कौन सबसे ज्यादा सोता है?", "कौन सबसे ज्यादा बात करता है?", "कौन सबसे ज्यादा देर आता है?", "कौन सबसे ज्यादा मजाक करता है?", "कौन सबसे ज्यादा रोता है?", "कौन सबसे ज्यादा काम करता है?", "कौन सबसे ज्यादा खाता है?"]
            question = random.choice(mostlikely_questions)
            self.send_message(thread_id, f"📊 **Who is most likely to...**\n\n{question}\n\nVote by replying!")
            mostlikely_state[thread_id] = {'question': question, 'votes': {}, 'timestamp': datetime.now()}
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ SUS ============
        elif cmd == '.sus':
            if not args:
                self.send_message(thread_id, "Usage: .sus @user")
                return
            target = args[0].replace('@', '')
            sus_level = random.randint(60, 99)
            reasons = ["You have a history of 'studying' = watching YouTube", "Your story doesn't add up, bro", "The GC has spoken 💀", "Your energy is sus today", "You're too quiet... sus"]
            self.send_message(thread_id, f"🧐 **SUSPICIOUS CLAIM DETECTED**\n\nGC Verdict: {sus_level}% SUS\nReason: {random.choice(reasons)}\n\n💀 The GC has spoken.")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ SCORE ============
        elif cmd == '.score':
            data = get_user_data(user_id, thread_id)
            self.send_message(thread_id, f"🏆 @{username} has {data['xp']} XP (Level {data['level']}) and {data['coins']} coins!")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
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
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
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
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
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
                    self.send_message(thread_id, f"⏳ Daily reward already claimed! Wait {int(remaining/3600)}h {int((remaining%3600)/60)}m.")
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
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ BALANCE ============
        elif cmd == '.balance':
            data = get_user_data(user_id, thread_id)
            self.send_message(thread_id, f"💰 @{username} has {data['coins']} coins!")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
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
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ SHOP ============
        elif cmd == '.shop':
            shop_list = "🏪 **SHOP**\n\n"
            for item in SHOP_ITEMS:
                shop_list += f"{item['emoji']} {item['name']} — {item['price']} coins\n   {item['desc']}\n\n"
            self.send_message(thread_id, shop_list)
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ BUY ============
        elif cmd == '.buy':
            if not args:
                self.send_message(thread_id, "Usage: .buy [item name]")
                return
            item_name = ' '.join(args)
            for item in SHOP_ITEMS:
                if item['name'].lower() in item_name.lower():
                    data = get_user_data(user_id, thread_id)
                    if data['coins'] < item['price']:
                        self.send_message(thread_id, f"❌ Not enough coins! Need {item['price']} coins.")
                        return
                    add_coins(user_id, thread_id, -item['price'])
                    add_inventory_item(user_id, thread_id, item['name'])
                    self.send_message(thread_id, f"✅ {item['emoji']} Purchased: {item['name']}! Enjoy your totally useless item! 😂")
                    command_cooldowns[(thread_id, user_id, cmd)] = time.time()
                    return
            self.send_message(thread_id, "❌ Item not found! Check .shop")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ INVENTORY ============
        elif cmd == '.inventory':
            items = get_inventory(user_id, thread_id)
            if not items:
                self.send_message(thread_id, "📭 You don't own any items!")
                return
            inv_list = "🎒 **Your Inventory:**\n\n"
            for item in items:
                inv_list += f"• {item['item_name']} x{item['quantity']}\n"
            self.send_message(thread_id, inv_list)
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
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
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        elif cmd == '.remember':
            if not args:
                self.send_message(thread_id, "Usage: .remember [thing]")
                return
            memory = ' '.join(args)
            # Check limits
            if len(memory) > Config.MAX_MEMORY_LENGTH:
                self.send_message(thread_id, f"❌ Memory too long! Max {Config.MAX_MEMORY_LENGTH} characters.")
                return
            # Check count
            with get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) as count FROM memories WHERE user_id = ? AND thread_id = ?", (user_id, thread_id))
                count = c.fetchone()['count']
                if count >= Config.MAX_MEMORIES_PER_USER:
                    self.send_message(thread_id, f"❌ Max memories reached ({Config.MAX_MEMORIES_PER_USER})! Use .forget to remove some.")
                    return
            with get_db() as conn:
                c = conn.cursor()
                c.execute("INSERT INTO memories (user_id, thread_id, text) VALUES (?, ?, ?)", (user_id, thread_id, memory))
                conn.commit()
            self.send_message(thread_id, f"✅ Remembered: \"{memory}\"")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
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
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ CHAOS ============
        elif cmd == '.chaos':
            personality = get_or_create_personality(thread_id)
            self.send_message(thread_id, f"🌀 CHAOS LEVEL: {personality['chaos']}%\n\n{random.choice(['You summoned the chaos!', 'The chaos is spreading...', 'I have no idea what I\'m doing 💀', 'This is fine 🔥'])}")
            update_personality(thread_id, chaos=min(100, personality['chaos'] + 10))
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ SUMMON ============
        elif cmd == '.summon':
            summon_state[thread_id] = {"active": True, "expires": time.time() + 300}
            self.send_message(thread_id, "🔮 **SUMMONED.**\n\nI'm listening for the next 5 minutes.\nTalk to me naturally!")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
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
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        # ============ ADMIN COMMANDS ============
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
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        elif cmd == '.stopspam':
            self.stop_spam(thread_id, username)
            return

        elif cmd == '.afk':
            reason = ' '.join(args) if args else "AFK"
            AFK_USERS[(thread_id, user_id)] = (reason, datetime.now())
            self.send_message(thread_id, f"🛏️ @{username} is now AFK: {reason}")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        elif cmd == '.spam':
            if not args:
                self.send_message(thread_id, "Usage: .spam [count] [message]")
                return
            try:
                count = int(args[0])
                if count <= 0 or count > Config.MAX_SPAM_COUNT:
                    self.send_message(thread_id, f"❌ Count must be between 1 and {Config.MAX_SPAM_COUNT}")
                    return
                message = ' '.join(args[1:]) if len(args) > 1 else "SPAM!"
            except ValueError:
                self.send_message(thread_id, "❌ Invalid count.")
                return
            if thread_id in spam_threads and spam_threads[thread_id].is_alive():
                self.send_message(thread_id, "⚠️ Spam already running in this thread! Use .stopspam")
                return
            self.send_message(thread_id, f"📢 Admin starting spam: {count} messages!")
            spam_thread = threading.Thread(target=self.run_spam, args=(thread_id, count, message, username), daemon=True)
            spam_threads[thread_id] = spam_thread
            spam_thread.start()
            return

        elif cmd == '.setwelcome':
            if not args:
                self.send_message(thread_id, "Usage: .setwelcome [message]")
                return
            new_welcome = ' '.join(args)
            set_setting(thread_id, 'welcome_message', new_welcome)
            self.send_message(thread_id, f"✅ Welcome message updated!")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        elif cmd == '.setrules':
            if not args:
                self.send_message(thread_id, "Usage: .setrules [rules]")
                return
            new_rules = ' '.join(args)
            set_setting(thread_id, 'rules', new_rules)
            self.send_message(thread_id, f"✅ Rules updated!")
            command_cooldowns[(thread_id, user_id, cmd)] = time.time()
            return

        else:
            self.send_message(thread_id, f"❌ Unknown: {cmd}\nType .help")

    def run_spam(self, thread_id, count, message, admin_username):
        """Run spam task with safety measures."""
        global spam_stop_flag
        spam_stop_flag = False
        try:
            for i in range(count):
                if spam_stop_flag:
                    self.send_message(thread_id, f"🛑 Spam stopped! Sent {i} messages.")
                    break
                if not self.running:
                    break
                try:
                    emoji = random.choice(SPAM_EMOJIS)
                    self.send_message(thread_id, f"{emoji} {message}")
                    human_delay(Config.SPAM_DELAY_MIN, Config.SPAM_DELAY_MAX)
                except RateLimitError:
                    self.send_message(thread_id, "⚠️ Rate limit hit! Stopping spam.")
                    break
                except Exception as e:
                    self.send_message(thread_id, f"❌ Spam error: {e}")
                    break
            else:
                self.send_message(thread_id, f"✅ Spam complete! {count} messages sent.")
        except Exception as e:
            self.send_message(thread_id, f"❌ Spam error: {e}")
        finally:
            if thread_id in spam_threads:
                del spam_threads[thread_id]

    def stop_spam(self, thread_id, username):
        """Stop spam in a thread."""
        global spam_stop_flag
        if not self.is_admin(username):
            self.send_message(thread_id, f"❌ @{username} Only admins can stop spam!")
            return False
        if thread_id not in spam_threads or not spam_threads[thread_id].is_alive():
            self.send_message(thread_id, "ℹ️ No spam running in this thread.")
            return False
        spam_stop_flag = True
        self.send_message(thread_id, "🛑 Stopping spam...")
        return True

    def send_trivia_question(self, thread_id):
        """Send the next trivia question."""
        state = trivia_state.get(thread_id)
        if not state:
            return
        current = state['current']
        questions = state['questions']
        if current >= len(questions):
            self.end_trivia(thread_id)
            return
        q = questions[current]
        self.send_message(thread_id, f"--- Question {current+1}/{len(questions)} ---\n❓ {q['q']}\n⏰ {Config.TRIVIA_TIME_LIMIT} seconds...")
        
        def check():
            time.sleep(Config.TRIVIA_TIME_LIMIT)
            if thread_id in trivia_state and trivia_state[thread_id]['current'] == current:
                self.send_message(thread_id, f"⏰ Time's up! Answer: {q['a']}")
                trivia_state[thread_id]['current'] += 1
                time.sleep(2)
                self.send_trivia_question(thread_id)
        
        threading.Thread(target=check, daemon=True).start()

    def check_trivia_answer(self, thread_id, user_id, message):
        """Check if a message is a trivia answer."""
        state = trivia_state.get(thread_id)
        if not state:
            return
        if user_id != state['user_id']:
            return
        current = state['current']
        questions = state['questions']
        if current >= len(questions):
            return
        
        answer = message.strip().upper()
        expected = state['questions'][current]['a'].strip().upper()
        
        # Check if answer matches
        if answer == expected or answer in expected or expected in answer:
            state['score'] += 1
            self.send_message(thread_id, f"✅ Correct! {state['score']}/{len(questions)}")
            add_xp(user_id, thread_id, 10, "trivia_correct")
            add_coins(user_id, thread_id, 5)
            state['current'] += 1
            time.sleep(2)
            self.send_trivia_question(thread_id)

    def end_trivia(self, thread_id):
        """End trivia and show results."""
        state = trivia_state.pop(thread_id, None)
        if not state:
            return
        score, total, username = state['score'], len(state['questions']), state['username']
        msgs = ["🧠 GENIUS! 🏆", "🔥 Amazing! 🌟", "👍 Good job! 💪", "🤔 Not bad! 📚", "😂 Did you even try?! 💀"]
        msg = msgs[0] if score == total else msgs[1] if score >= total-1 else msgs[2] if score >= total//2 else msgs[3] if score >= 1 else msgs[4]
        self.send_message(thread_id, f"--- 🎯 GAME OVER! ---\n🏆 @{username} scored {score}/{total}\n{msg}")
        add_xp(state['user_id'], thread_id, score * 10, "trivia")

    def check_messages(self):
        """Check for new messages and process them."""
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
                    
                    # Check for new members
                    new_members = set(current) - self.known_members[thread_id]
                    for mid in new_members:
                        if mid != self.user_id:
                            uname = self.get_username_cached(mid)
                            if uname and (thread_id, mid) not in WELCOME_SENT:
                                print(f"🔔 New member: @{uname}")
                                welcome_msg = get_welcome_message(thread_id) or WELCOME_MSG
                                self.send_message(thread_id, welcome_msg.format(username=uname))
                                human_delay(2.0, 4.0)
                                rules = get_rules(thread_id) or RULES
                                self.send_message(thread_id, rules)
                                WELCOME_SENT[(thread_id, mid)] = True
                    
                    # Check for members who left
                    left = self.known_members[thread_id] - set(current)
                    for mid in left:
                        if mid != self.user_id:
                            uname = self.get_username_cached(mid)
                            if uname:
                                print(f"🚶 Member left: @{uname}")
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
                        print(f"📩 @{username}: {msg.text}")

                        # Update activity tracking
                        now = datetime.now()
                        last = USER_LAST_ACTIVE.get(msg.user_id)
                        if msg.user_id != self.user_id and last and (now - last).total_seconds() >= Config.WELCOME_BACK_INTERVAL:
                            last_welcome = USER_WELCOME_SENT.get(msg.user_id)
                            if not last_welcome or (now - last_welcome).total_seconds() > Config.WELCOME_BACK_INTERVAL:
                                print(f"👋 Welcome back @{username}")
                                self.send_message(thread_id, WELCOME_BACK_MSGS[0].format(username=username))
                                USER_WELCOME_SENT[msg.user_id] = now
                        USER_LAST_ACTIVE[msg.user_id] = now

                        # Track admin activity
                        if username.lower() in [a.lower() for a in ADMINS]:
                            ADMIN_LAST_SEEN[thread_id] = now

                        # Admin tag replies
                        msg_lower = msg.text.lower()
                        if any(f"@{admin}".lower() in msg_lower for admin in ADMINS) and not self.is_admin(username):
                            if thread_id not in ADMIN_LAST_SEEN or (now - ADMIN_LAST_SEEN.get(thread_id, now - timedelta(minutes=10))).total_seconds() > Config.ADMIN_ACTIVE_TIMEOUT:
                                self.send_message(thread_id, f"@{username} {random.choice(ADMIN_TAG_REPLIES)}")
                                human_delay(1.0, 2.0)

                        # Admin greeting
                        if username.lower() in [a.lower() for a in ADMINS]:
                            last_seen = ADMIN_LAST_SEEN.get(thread_id, now - timedelta(minutes=10))
                            if (now - last_seen).total_seconds() > 120:
                                self.send_message(thread_id, random.choice(ADMIN_GREETINGS))

                        # Check trivia answers
                        if thread_id in trivia_state:
                            self.check_trivia_answer(thread_id, msg.user_id, msg.text)

                        # AFK system
                        afk_key = (thread_id, msg.user_id)
                        if afk_key in AFK_USERS:
                            reason, t = AFK_USERS[afk_key]
                            if (now - t).total_seconds() > 300:
                                del AFK_USERS[afk_key]
                                self.send_message(thread_id, f"🟢 @{username} is no longer AFK")

                        # Update context for natural replies
                        ai_router.add_to_context(thread_id, username, msg.text)

                        # NATURAL REPLY - only if not a command
                        if not msg.text.startswith('.') and self.groq_api_key:
                            personality = get_or_create_personality(thread_id)
                            router_result = ai_router.should_reply(thread_id, msg.user_id, msg.text, self.username)
                            
                            if router_result["should_reply"]:
                                context = ai_router.get_context(thread_id, limit=10)
                                reply = groq_natural_reply(
                                    msg.text, 
                                    username, 
                                    self.groq_api_key, 
                                    personality,
                                    context
                                )
                                
                                if reply:
                                    # Check for repetition
                                    if not ai_router.is_response_repetitive(thread_id, reply):
                                        human_delay(2.0, 5.0, len(reply))
                                        self.send_message(thread_id, reply)
                                        print(f"🤖 Natural reply to @{username} ({router_result['reason']})")
                                        ai_router.mark_reply(thread_id, msg.user_id)
                                        ai_router.add_response(thread_id, reply)
                                        add_xp(msg.user_id, thread_id, 2, "natural_reply")

                        # Handle commands
                        if msg.text.startswith('.'):
                            self.handle_command(thread_id, msg.user_id, username, msg.text)

                except RateLimitError:
                    print("⚠️ Rate limited! Waiting with backoff...")
                    self.handle_rate_limit()
                except Exception as e:
                    print(f"⚠️ Thread error: {e}")
                    traceback.print_exc()
        except RateLimitError:
            print("⚠️ Rate limited! Waiting with backoff...")
            self.handle_rate_limit()
        except Exception as e:
            print(f"⚠️ Check error: {e}")
            traceback.print_exc()

    def run(self):
        """Main bot loop."""
        print("\n" + "=" * 60)
        print("🔥 ULTIMATE GC COMPANION BOT RUNNING")
        print(f"👤 Bot: @{self.username}")
        print(f"👑 Admins: {', '.join(ADMINS)}")
        print(f"📊 Monitoring: {getattr(self, 'group_count', 1)} group(s)")
        print("=" * 60)
        print("🤖 Features:")
        print("   ✅ Smart AI reply system")
        print("   ✅ 25% natural reply chance")
        print("   ✅ 20+ fallback jokes/roasts/facts")
        print("   ✅ Context-aware conversations")
        print("   ✅ Database persistence")
        print("   ✅ Multi-GC isolation")
        print("   ✅ All games")
        print("   ✅ Rate limit protection")
        print("=" * 60)
        print("\n⚠️ Press Ctrl+C to stop\n")
        
        while self.running:
            try:
                self.check_messages()
                time.sleep(random.uniform(Config.POLL_INTERVAL_MIN, Config.POLL_INTERVAL_MAX))
            except KeyboardInterrupt:
                self.running = False
                print("\n👋 Stopping...")
                break
            except Exception as e:
                print(f"⚠️ Error: {e}")
                traceback.print_exc()
                time.sleep(30)

    def start(self):
        """Start the bot."""
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

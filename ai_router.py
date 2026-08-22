# ai_router.py
import time
import random
from collections import defaultdict

class AIRouter:
    def __init__(self):
        self.cooldown_tracker = defaultdict(float)
        self.last_bot_message = defaultdict(float)
        self.response_history = defaultdict(list)
        self.conversation_mode = defaultdict(bool)
        self.conversation_timeout = defaultdict(float)
    
    def should_respond(self, thread_id, user_id, message, bot_username, last_message_time):
        # 1. Direct mention → HIGH
        if bot_username.lower() in message.lower():
            return {"should_reply": True, "reason": "direct_mention", "confidence": 0.95}
        
        # 2. Reply to bot → HIGH
        if message.startswith('@') and bot_username.lower() in message.lower():
            return {"should_reply": True, "reason": "reply_to_bot", "confidence": 0.90}
        
        # 3. Question → HIGH
        if '?' in message:
            return {"should_reply": True, "reason": "question", "confidence": 0.80}
        
        # 4. Funny opportunity → MEDIUM
        funny_patterns = ['😂', '💀', 'lol', '🤣', 'haha', '💀', '🔥']
        if any(p in message for p in funny_patterns):
            return {"should_reply": True, "reason": "funny_opportunity", "confidence": 0.65}
        
        # 5. Conversation mode (if user is talking to bot)
        if self.conversation_mode[f"{thread_id}_{user_id}"]:
            if time.time() - self.conversation_timeout[f"{thread_id}_{user_id}"] < 60:
                return {"should_reply": True, "reason": "conversation_mode", "confidence": 0.80}
            else:
                self.conversation_mode[f"{thread_id}_{user_id}"] = False
        
        # 6. Cooldown check
        last_time = self.cooldown_tracker.get(f"{thread_id}_{user_id}", 0)
        if time.time() - last_time < 10:
            return {"should_reply": False, "reason": "cooldown", "confidence": 0}
        
        # 7. Check if bot replied recently
        if time.time() - self.last_bot_message.get(thread_id, 0) < 5:
            return {"should_reply": False, "reason": "bot_cooldown", "confidence": 0}
        
        # 8. Random chance (only if nothing else)
        if random.random() < 0.08:
            return {"should_reply": True, "reason": "random", "confidence": 0.30}
        
        return {"should_reply": False, "reason": "no_trigger", "confidence": 0}
    
    def mark_reply(self, thread_id, user_id):
        self.cooldown_tracker[f"{thread_id}_{user_id}"] = time.time()
        self.last_bot_message[thread_id] = time.time()
        self.conversation_mode[f"{thread_id}_{user_id}"] = True
        self.conversation_timeout[f"{thread_id}_{user_id}"] = time.time()

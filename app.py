from flask import Flask, jsonify
import os
import threading
import sys
import time
import traceback

app = Flask(__name__)

BOT_STATUS = {
    "status": "starting",
    "message": "Initializing...",
    "error": None,
    "bot_username": None,
    "threads_monitored": 0
}

@app.route('/')
def home():
    return "🤖 Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/status')
def status():
    return jsonify(BOT_STATUS)

def start_bot():
    global BOT_STATUS
    try:
        print("=" * 60)
        print("🚀 STARTING BOT THREAD...")
        print("=" * 60)
        
        BOT_STATUS["status"] = "importing"
        BOT_STATUS["message"] = "Importing group_bot..."
        
        import group_bot
        print("✅ group_bot imported!")
        
        BOT_STATUS["status"] = "creating"
        BOT_STATUS["message"] = "Creating bot instance..."
        
        bot = group_bot.InstagramGroupBot()
        print("✅ Bot instance created!")
        
        BOT_STATUS["status"] = "running"
        BOT_STATUS["message"] = "Bot is running"
        BOT_STATUS["bot_username"] = bot.username
        BOT_STATUS["error"] = None
        
        bot.start()
        
    except Exception as e:
        error_msg = str(e)
        BOT_STATUS["status"] = "stopped"
        BOT_STATUS["message"] = f"Error: {error_msg[:100]}"
        BOT_STATUS["error"] = error_msg
        
        print(f"❌ BOT ERROR: {e}")
        traceback.print_exc()

# ✅ START BOT IMMEDIATELY
print("🔄 Starting Flask application...")

bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()
print("✅ Bot thread started!")

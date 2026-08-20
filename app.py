from flask import Flask, jsonify
import os
import threading
import time
import sys
import traceback

# Force flush
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

app = Flask(__name__)

BOT_STATUS = {
    "status": "starting",
    "message": "Initializing...",
    "error": None,
    "bot_username": None
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
        print("🚀 STARTING BOT THREAD...")
        sys.stdout.flush()
        
        print("📂 Importing group_bot...")
        sys.stdout.flush()
        import group_bot
        print("✅ group_bot imported!")
        sys.stdout.flush()
        
        print("🔧 Creating bot instance...")
        sys.stdout.flush()
        bot = group_bot.InstagramGroupBot()
        print("✅ Bot instance created!")
        sys.stdout.flush()
        
        BOT_STATUS["status"] = "running"
        BOT_STATUS["message"] = "Bot is running"
        BOT_STATUS["bot_username"] = bot.username
        
        print("▶️ Starting bot loop...")
        sys.stdout.flush()
        bot.start()
        
    except Exception as e:
        BOT_STATUS["status"] = "stopped"
        BOT_STATUS["message"] = f"Error: {str(e)[:100]}"
        BOT_STATUS["error"] = str(e)
        print(f"❌ BOT ERROR: {e}")
        traceback.print_exc()
        sys.stdout.flush()

# ✅ START THE BOT THREAD
print("🔄 Starting Flask application...")
sys.stdout.flush()

bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()
print("✅ Bot thread started!")
sys.stdout.flush()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

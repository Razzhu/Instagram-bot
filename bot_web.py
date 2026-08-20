from flask import Flask
import os
import threading
import sys

# Force stdout flush
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    try:
        print("=" * 60)
        print("🚀 STARTING BOT THREAD...")
        print("=" * 60)
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
        
        print("▶️ Starting bot...")
        sys.stdout.flush()
        bot.start()
        
    except Exception as e:
        print(f"❌ BOT ERROR: {e}")
        sys.stdout.flush()
        import traceback
        traceback.print_exc()
        sys.stdout.flush()

# ✅ START BOT IMMEDIATELY - NOT INSIDE if __name__ == "__main__"
print("🔄 Starting Flask application...")
sys.stdout.flush()

bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
print("✅ Bot thread started!")
sys.stdout.flush()

# ✅ Keep this for local testing
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Flask running on port {port}")
    sys.stdout.flush()
    app.run(host='0.0.0.0', port=port)

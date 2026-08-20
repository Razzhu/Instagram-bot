from flask import Flask
import os
import threading
import time
import sys

# ✅ Force stdout to flush immediately
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    """Run the Instagram bot in background"""
    try:
        print("=" * 60)
        print("🚀 STARTING BOT THREAD...")
        print("=" * 60)
        sys.stdout.flush()
        
        print("📂 Importing group_bot...")
        sys.stdout.flush()
        import group_bot
        print("✅ group_bot imported successfully!")
        sys.stdout.flush()
        
        print("🔧 Creating bot instance...")
        sys.stdout.flush()
        bot = group_bot.InstagramGroupBot()
        print("✅ Bot instance created!")
        sys.stdout.flush()
        
        print("▶️ Starting bot...")
        sys.stdout.flush()
        bot.start()
        print("✅ Bot started!")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"❌ BOT ERROR: {e}")
        sys.stdout.flush()
        import traceback
        traceback.print_exc()
        sys.stdout.flush()

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 STARTING FLASK APPLICATION...")
    print("=" * 60)
    sys.stdout.flush()
    
    print("🔧 Creating bot thread...")
    sys.stdout.flush()
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print(f"✅ Bot thread started! (Thread ID: {bot_thread.ident})")
    sys.stdout.flush()
    
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Flask running on port {port}")
    print("=" * 60)
    sys.stdout.flush()
    
    app.run(host='0.0.0.0', port=port)

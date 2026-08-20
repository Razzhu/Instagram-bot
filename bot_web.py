from flask import Flask
import threading
import os
import time
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    """Run Instagram bot in background thread"""
    print("=" * 50)
    print("🚀 STARTING BOT THREAD...")
    print("=" * 50)
    
    try:
        # Import the bot module
        print("📂 Importing group_bot...")
        import group_bot
        print("✅ group_bot imported successfully!")
        
        # Create and start bot
        print("🔧 Creating bot instance...")
        bot = group_bot.InstagramGroupBot()
        print("✅ Bot instance created!")
        
        print("▶️ Starting bot...")
        bot.start()
        print("✅ Bot started!")
        
    except Exception as e:
        print(f"❌ BOT ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 STARTING FLASK SERVER...")
    print("=" * 50)
    
    # Start bot in background thread
    print("🔧 Creating bot thread...")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("✅ Bot thread started!")
    
    # Give bot time to initialize
    time.sleep(2)
    print("🚀 Flask server starting...")
    
    # Bind to Render's PORT
    port = int(os.environ.get("PORT", 10000))
    print(f"📡 Binding to port: {port}")
    app.run(host='0.0.0.0', port=port)

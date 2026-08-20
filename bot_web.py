from flask import Flask
import threading
import os
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    """Run the Instagram bot in background"""
    print("🚀 Starting bot thread...")
    try:
        # Import and run the bot
        import group_bot
        print("✅ Bot imported, starting...")
        bot = group_bot.InstagramGroupBot()
        bot.start()
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 Starting Flask server...")
    print("=" * 50)
    
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Give bot time to start
    time.sleep(3)
    print("✅ Bot thread started!")
    print("🚀 Flask server running...")
    
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

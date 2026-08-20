from flask import Flask
import os
import threading
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
    try:
        print("🚀 Starting bot...")
        import group_bot
        bot = group_bot.InstagramGroupBot()
        bot.start()
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔄 Starting Flask...")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("✅ Bot thread started!")
    
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Flask running on port {port}")
    app.run(host='0.0.0.0', port=port)

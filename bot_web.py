from flask import Flask
import os
import time
import threading

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
        print("=" * 50)
        print("🚀 STARTING BOT...")
        print("=" * 50)
        
        import group_bot
        print("✅ group_bot imported successfully!")
        
        bot = group_bot.InstagramGroupBot()
        print("✅ Bot instance created!")
        
        bot.start()
        print("✅ Bot started!")
        
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()

# Start bot in background when app starts
print("🔄 Starting Flask application...")
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
print("✅ Bot thread started!")

if __name__ == "__main__":
    # This is only used when running directly (not with gunicorn)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

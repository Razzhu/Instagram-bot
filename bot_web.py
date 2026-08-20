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
    try:
        print("🚀 Starting bot...")
        import group_bot
        print("✅ Bot imported!")
        bot = group_bot.InstagramGroupBot()
        bot.start()
    except Exception as e:
        print(f"❌ Bot error: {e}")

# Start Flask
print("🔄 Starting Flask application...")
print("📂 Working directory:", os.getcwd())

# Start bot in background thread
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
print("✅ Bot thread started!")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Running on port {port}")
    app.run(host='0.0.0.0', port=port)

from flask import Flask
import threading
import os
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running!"

@app.route('/status')
def status():
    return "✅ Bot is alive!"

def run_bot():
    """Run the Instagram bot in a separate thread"""
    print("🚀 Starting Instagram bot...")
    try:
        # Import the bot
        import group_bot
        print("✅ Bot imported successfully!")
        
        # Create and start bot
        bot = group_bot.InstagramGroupBot()
        bot.start()
        
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔵 Flask server starting...")
    
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Wait a bit for bot to start
    time.sleep(2)
    print("🟢 Bot thread started.")
    
    # Run Flask
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

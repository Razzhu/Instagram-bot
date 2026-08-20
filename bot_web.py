from flask import Flask
import os
import time
import threading
import sys

# Force stdout to flush immediately
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/status')
def status():
    return """
    Bot Status:
    - Flask: Running ✅
    - Bot Thread: Started ✅
    - Check logs for details
    """

def run_bot():
    """Run the Instagram bot in background"""
    try:
        print("=" * 50)
        print("🚀 STARTING BOT THREAD...")
        print("=" * 50)
        print(f"🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 Python version: {sys.version}")
        print("=" * 50)
        
        # Step 1: Import
        print("📂 Step 1: Importing group_bot module...")
        import group_bot
        print("✅ Step 1: group_bot imported successfully!")
        print(f"📂 group_bot location: {group_bot.__file__}")
        
        # Step 2: Create bot instance
        print("🔧 Step 2: Creating bot instance...")
        bot = group_bot.InstagramGroupBot()
        print("✅ Step 2: Bot instance created!")
        
        # Step 3: Start bot
        print("▶️ Step 3: Starting bot...")
        bot.start()
        print("✅ Step 3: Bot started successfully!")
        
    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        print("📦 Check if instagrapi is installed in requirements.txt")
        import traceback
        traceback.print_exc()
        
    except Exception as e:
        print(f"❌ BOT ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 50)
    print("🔄 Bot thread finished (should not happen if bot is running)")
    print("=" * 50)

# Main execution
print("=" * 50)
print("🔄 STARTING FLASK APPLICATION...")
print(f"🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🐍 Python version: {sys.version}")
print(f"📂 Working directory: {os.getcwd()}")
print("=" * 50)

# Start bot in background
print("🔧 Creating bot thread...")
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
print(f"✅ Bot thread started! (Thread ID: {bot_thread.ident})")
print("=" * 50)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Flask running on port: {port}")
    app.run(host='0.0.0.0', port=port)

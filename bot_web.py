from flask import Flask
import os
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 STARTING BOT...")
    print("=" * 50)
    
    # Run bot directly (not in thread)
    try:
        print("📂 Importing group_bot...")
        import group_bot
        print("✅ Imported!")
        
        print("🔧 Creating bot...")
        bot = group_bot.InstagramGroupBot()
        print("✅ Bot created!")
        
        print("▶️ Starting bot...")
        bot.start()
        print("✅ Bot started!")
        
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

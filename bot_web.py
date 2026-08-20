from flask import Flask
import subprocess
import sys
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running!"

@app.route('/status')
def status():
    return "✅ Bot is alive!"

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 STARTING BOT...")
    print("=" * 50)
    
    # Run the bot directly
    try:
        exec(open('group_bot.py').read())
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
    
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

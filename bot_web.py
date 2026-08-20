from flask import Flask
import threading
import os

razz_hu = Flask(__name__)

@razz_hu.route('/')
def home():
    return "🤖 Bot is running!"

def run_bot():
    try:
        exec(open('group_bot.py').read())
    except Exception as e:
        print(f"Bot error: {e}")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    razz_hu.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

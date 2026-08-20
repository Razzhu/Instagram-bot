import os
import sys
import time
import threading
import logging
from flask import Flask, request, jsonify
from instagrapi import Client

# Setup logging - REPLACES all print statements
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Still prints but handles errors better
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Bot configuration
INSTAGRAM_USERNAME = os.environ.get('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.environ.get('INSTAGRAM_PASSWORD')

bot_running = False
bot_thread = None
cl = None

def run_bot():
    global bot_running, cl
    
    try:
        logger.info("Starting Instagram bot...")
        
        if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
            logger.error("Instagram credentials not set in environment variables")
            bot_running = False
            return
        
        cl = Client()
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        logger.info("Successfully logged into Instagram")
        
        user_id = cl.user_id
        logger.info(f"User ID: {user_id}")
        
        # Your main bot logic here
        while bot_running:
            try:
                # Example: Get recent followers
                followers = cl.user_followers(user_id)
                logger.info(f"Current followers count: {len(followers)}")
                
                # Add your bot logic here (comment/uncomment as needed)
                # - Like posts
                # - Follow users
                # - Send messages
                # - etc.
                
                time.sleep(60)  # Wait 1 minute before next loop
                
            except Exception as e:
                # FIXED: Using logger.error instead of print
                logger.error(f"Bot error in loop: {e}")
                time.sleep(30)
                
    except Exception as e:
        # FIXED: Using logger.error instead of print
        logger.error(f"X BOT ERROR: {e}")
        bot_running = False
    finally:
        logger.info("Bot stopped")
        bot_running = False

@app.route('/')
def index():
    return jsonify({
        'status': 'running',
        'bot_status': 'running' if bot_running else 'stopped',
        'message': 'Instagram Bot is active'
    })

@app.route('/start', methods=['POST'])
def start_bot():
    global bot_running, bot_thread
    
    if bot_running:
        return jsonify({'status': 'already_running'})
    
    bot_running = True
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    logger.info("Bot started via API")
    return jsonify({'status': 'started'})

@app.route('/stop', methods=['POST'])
def stop_bot():
    global bot_running
    
    if not bot_running:
        return jsonify({'status': 'already_stopped'})
    
    bot_running = False
    logger.info("Bot stopped via API")
    return jsonify({'status': 'stopped'})

@app.route('/status')
def status():
    return jsonify({
        'bot_running': bot_running,
        'thread_alive': bot_thread.is_alive() if bot_thread else False
    })

@app.errorhandler(Exception)
def handle_exception(e):
    # FIXED: Using logger.error instead of print
    logger.error(f"Unhandled exception: {e}")
    return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    
    # Auto-start bot when server starts (optional)
    # Uncomment below to start automatically
    # if not bot_running:
    #     bot_running = True
    #     bot_thread = threading.Thread(target=run_bot)
    #     bot_thread.start()
    
    app.run(host='0.0.0.0', port=port)

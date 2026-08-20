#!/usr/bin/env python3
"""
TEST BOT - Minimal version to test login
"""

import os
import sys
import time

# Force stdout flush
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

print("=" * 60)
print("🧪 TEST BOT STARTING...")
print("=" * 60)
sys.stdout.flush()

SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "")

if not SESSION_ID:
    print("❌ INSTAGRAM_SESSION_ID not set!")
    sys.exit(1)

print(f"✅ SESSION_ID loaded: {SESSION_ID[:20]}...")
sys.stdout.flush()

try:
    from instagrapi import Client
    print("✅ instagrapi imported!")
    sys.stdout.flush()
    
    cl = Client()
    cl.set_user_agent("Mozilla/5.0 (Linux; Android 13) Chrome/116.0.5845.92")
    
    print("🔐 Logging in...")
    sys.stdout.flush()
    
    cl.login_by_sessionid(SESSION_ID)
    
    print(f"✅ SUCCESS! Logged in as: @{cl.username}")
    print(f"👥 Followers: {cl.user_followers(cl.user_id)}")
    sys.stdout.flush()
    
    print("🎉 Test bot is working!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.stdout.flush()
    import traceback
    traceback.print_exc()
    sys.stdout.flush()

print("=" * 60)
print("🧪 Test complete. Keeping bot alive...")
print("=" * 60)
sys.stdout.flush()

# Keep alive
while True:
    time.sleep(30)
    print("🔄 Test bot alive...")
    sys.stdout.flush()

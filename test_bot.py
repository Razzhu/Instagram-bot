print("=" * 60)
print("🧪 SIMPLE TEST BOT")
print("=" * 60)

try:
    print("1️⃣ Importing instagrapi...")
    from instagrapi import Client
    print("✅ OK")
    
    print("2️⃣ Creating client...")
    cl = Client()
    print("✅ OK")
    
    print("3️⃣ Setting user agent...")
    cl.set_user_agent("Mozilla/5.0 (Linux; Android 13)")
    print("✅ OK")
    
    print("4️⃣ Getting session ID...")
    import os
    SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "")
    if not SESSION_ID:
        SESSION_ID = "11950490138:2e5V9aHxKAosXH:28:AYj0h54d0SaaFBpF3pUpsZOPe29TlKH8wYFA4Ic5Lg"
    print(f"   Session: {SESSION_ID[:20]}...")
    print("✅ OK")
    
    print("5️⃣ Logging in...")
    cl.login_by_sessionid(SESSION_ID)
    print(f"✅ SUCCESS! Logged in as: @{cl.username}")
    print(f"👥 Followers: {cl.user_followers(cl.user_id)}")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

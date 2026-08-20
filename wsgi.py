from bot_web import app

# ✅ The bot thread is already started in bot_web.py
# Gunicorn just needs the app

if __name__ == "__main__":
    app.run()

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "✅ Telegram Bot ishlayapti! 🤖"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Bot 24/7 ishlashi uchun Flask server"""
    t = Thread(target=run)
    t.start()
from threading import Thread
from flask import Flask
from waitress import serve

app = Flask("")


@app.route("/")
def home():
    return "Bot is alive and running!"


def run():
    # استخدام waitress بدلاً من app.run الافتراضي
    serve(app, host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
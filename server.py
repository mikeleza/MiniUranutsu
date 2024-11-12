from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "The bot is running!"

def run():
    app.run(host='0.0.0.0',port=5000)

def server_on():
    t = Thread(target=run)
    t.start()
import os
import time
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer

# ใช้ HTTPServer ที่ไม่มีการทำงานจริง
def run():
    port = int(os.getenv('PORT', 5000))  # ใช้ค่าพอร์ตจาก environment หรือใช้ 5000
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

def server_on():
    t = Thread(target=run)
    t.start()

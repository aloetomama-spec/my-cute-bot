import http.server
import socketserver
import json
import os
import urllib.request
import urllib.parse
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/log':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            action = data.get('action', 'Неизвестно')
            time_now = data.get('time', '')
            user_name = data.get('user', 'Неизвестный пользователь') # Получаем имя
            
            # Выводим в консоль
            print(f"[{time_now}] {user_name} нажал(а): {action}")
            
            # Формируем сообщение для Telegram
            text = f"📊 **Событие в боте!**\n\n👤 Пользователь: {user_name}\n👆 Нажата кнопка: {action}\n🕒 Время: {time_now}"
            
            # Отправляем тебе в личку
            if BOT_TOKEN and ADMIN_ID:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_ID}&text={urllib.parse.quote(text)}&parse_mode=Markdown"
                try:
                    urllib.request.urlopen(url)
                except Exception as e:
                    print("Ошибка отправки в ТГ:", e)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_error(404)

PORT = 8000
socketserver.TCPServer.allow_reuse_address = True

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

if __name__ == '__main__':
    print(f"Сервер запущен на порту {PORT}...")
    with ThreadingHTTPServer(("", PORT), CustomHandler) as httpd:
        httpd.serve_forever()
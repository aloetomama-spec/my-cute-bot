import asyncio
import logging
import os
import urllib.parse
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === НАСТРОЙКИ БАЗЫ ДАННЫХ ===
DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Создаем таблицу, если ее нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            last_active TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def update_user_activity(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute('''
        INSERT INTO users (user_id, last_active) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET last_active = excluded.last_active
    ''', (user_id, now))
    conn.commit()
    conn.close()

# === ФОНОВАЯ ЗАДАЧА ДЛЯ НАПОМИНАНИЙ ===
async def reminder_worker():
    while True:
        # Проверяем раз в час (3600 секунд)
        await asyncio.sleep(3600) 
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # Ищем тех, кто не заходил 3 дня (72 часа)
            three_days_ago = datetime.now() - timedelta(days=3)
            cursor.execute('SELECT user_id FROM users WHERE last_active < ?', (three_days_ago,))
            inactive_users = cursor.fetchall()
            
            for (user_id,) in inactive_users:
                try:
                    # Отправляем напоминание
                    await bot.send_message(
                        chat_id=user_id,
                        text="Привет! Я тут немного заскучал... 🥺\n\nЕсли тебе нужно немного тепла, просто нажми на кнопку ниже. Я всегда рядом ✨",
                        reply_markup=get_main_keyboard()
                    )
                    
                    # Обновляем время, чтобы не спамить каждый час
                    # Теперь следующее напоминание будет только через 3 дня
                    cursor.execute('UPDATE users SET last_active = ? WHERE user_id = ?', (datetime.now(), user_id))
                    conn.commit()
                    
                except Exception as e:
                    # Если человек заблокировал бота, мы просто пропускаем его
                    print(f"Не удалось отправить сообщение {user_id}: {e}")
                    
            conn.close()
        except Exception as e:
            print(f"Ошибка в фоновой задаче: {e}")


# === ФУНКЦИЯ СОЗДАНИЯ КЛАВИАТУРЫ ===
def get_main_keyboard():
    u = None # Заглушка, имя подставим в хендлере
    # Ссылка на твой туннель (не забудь обновить, если он изменится!)
    web_app_url = f"https://copy-affiliates-styles-elizabeth.trycloudflare.com/index.html?v=62" 
    
    webapp_button = KeyboardButton(
        text="✨ Открыть приложение", 
        web_app=WebAppInfo(url=web_app_url)
    )
    
    return ReplyKeyboardMarkup(
        keyboard=[[webapp_button]],
        resize_keyboard=True
    )

# === ХЕНДЛЕРЫ ===
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # 1. Записываем активность пользователя
    update_user_activity(message.from_user.id)
    
    # 2. Формируем персональную ссылку с именем
    u = message.from_user
    user_name = u.first_name
    if u.last_name:
        user_name += f" {u.last_name}"
    if u.username:
        user_name += f" (@{u.username})"
    
    safe_user_name = urllib.parse.quote(user_name)
    
    web_app_url = f"https://copy-affiliates-styles-elizabeth.trycloudflare.com/index.html?v=60&uname={safe_user_name}"
    
    webapp_button = KeyboardButton(
        text="✨ Открыть приложение", 
        web_app=WebAppInfo(url=web_app_url)
    )
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[webapp_button]],
        resize_keyboard=True
    )
    
    await message.answer(
        "Привет! Нажми на кнопку ниже, чтобы открыть красивое мини-приложение с милотой.",
        reply_markup=keyboard
    )

# Этот хендлер ловит любые другие сообщения (например, если человек нажал на кнопку)
@dp.message()
async def any_message_handler(message: Message) -> None:
    # Обновляем время активности, чтобы бот не слал напоминания активным юзерам
    update_user_activity(message.from_user.id)

async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    
    # Инициализируем базу данных при запуске
    init_db()
    
    # Запускаем фоновую задачу для напоминаний
    asyncio.create_task(reminder_worker())
    
    print("Бот запущен. База данных готова. Таймер напоминаний активирован.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
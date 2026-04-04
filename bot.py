import telebot
from telebot import types
import json
import os
import threading
from flask import Flask

TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"
bot = telebot.TeleBot(TOKEN)

DB = "players.json"
chats = {}

# ---------- Flask ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "OK"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------- БАЗА ----------
def load():
    if not os.path.exists(DB):
        return []
    with open(DB, "r") as f:
        return json.load(f)

def save(data):
    with open(DB, "w") as f:
        json.dump(data, f)

# ---------- СТАРТ ----------
@bot.message_handler(commands=['start'])
def start(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить себя", "🔍 Найти тиму")
    kb.add("💬 Чат")
    bot.send_message(m.chat.id, "🔥 Поиск тимы Brawl Stars", reply_markup=kb)

# ---------- ДОБАВИТЬ ----------
@bot.message_handler(func=lambda m: m.text == "➕ Добавить себя")
def add(m):
    msg = bot.send_message(m.chat.id, "🏆 Введи свои кубки:")
    bot.register_next_step_handler(msg, get_trophies)

def get_trophies(m):
    if not m.text.isdigit():
        bot.send_message(m.chat.id, "❌ Введи число")
        return

    trophies = int(m.text)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🟢 ШД", "👥 3v3", "🏆 Ранговый")

    msg = bot.send_message(m.chat.id, "🎮 Выбери режим:", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda msg: get_mode(msg, trophies))

def get_mode(m, trophies):
    mode = m.text

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🐢 Нуб", "⚡ Средний", "🔥 Про")

    msg = bot.send_message(m.chat.id, "⚡ Выбери уровень игры:", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda msg: save_player(msg, trophies, mode))

def save_player(m, trophies, mode):
    skill = m.text

    data = load()
    data = [p for p in data if p["id"] != m.from_user.id]

    data.append({
        "id": m.from_user.id,
        "name": m.from_user.first_name,
        "trophies": trophies,
        "mode": mode,
        "skill": skill
    })

    save(data)
    bot.send_message(m.chat.id, "✅ Ты добавлен в поиск!")

# ---------- ПОИСК ----------
@bot.message_handler(func=lambda m: m.text == "🔍 Найти тиму")
def find(m):
    msg = bot.send_message(m.chat.id, "🏆 Введи свои кубки:")
    bot.register_next_step_handler(msg, search)

def search(m):
    if not m.text.isdigit():
        bot.send_message(m.chat.id, "❌ Введи число")
        return

    trophies = int(m.text)
    data = load()

    found = False

    for p in data:
        if abs(p["trophies"] - trophies) <= 500:
            found = True
            bot.send_message(m.chat.id,
                             f"👤 {p['name']}\n"
                             f"🏆 {p['trophies']}\n"
                             f"🎮 {p['mode']}\n"
                             f"⚡ {p['skill']}\n"
                             f"🆔 ID: {p['id']}")

    if not found:
        bot.send_message(m.chat.id, "❌ Никого не найдено")

# ---------- ЧАТ ----------
@bot.message_handler(func=lambda m: m.text == "💬 Чат")
def chat_start(m):
    msg = bot.send_message(m.chat.id, "🆔 Введи ID игрока:")
    bot.register_next_step_handler(msg, connect_chat)

def connect_chat(m):
    try:
        target_id = int(m.text)

        chats[m.from_user.id] = target_id
        chats[target_id] = m.from_user.id

        bot.send_message(m.chat.id, "✅ Чат подключен!")
        bot.send_message(target_id, "💬 С тобой начали чат!")

    except:
        bot.send_message(m.chat.id, "❌ Ошибка ID")

# ---------- ПЕРЕСЫЛКА ----------
@bot.message_handler(func=lambda m: True)
def chat_handler(m):
    if m.from_user.id in chats:
        target = chats[m.from_user.id]
        try:
            bot.send_message(target, f"💬 {m.from_user.first_name}: {m.text}")
        except:
            bot.send_message(m.chat.id, "❌ Игрок недоступен")

# ---------- ЗАПУСК ----------
def bot_run():
    print("Bot started...")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=bot_run).start()
    run()

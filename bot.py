import telebot
from telebot import types
import json, os, threading
from flask import Flask

TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"
OWNER = "@Vpnbroo"
ADMINS = [7027068118]

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

DB = "players.json"
TOURS = "tournaments.json"

PENDING = {}

# ---------- ВЕБ ----------
@app.route('/')
def home():
    return "Bot is running"

# ---------- БАЗА ----------
def load(file):
    if not os.path.exists(file):
        return []
    with open(file) as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def format_trophies(n):
    return f"{n:,}".replace(",", ".")

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить себя", "👤 Профиль")
    kb.add("🎮 Турниры", "🏆 Рейтинг")
    kb.add("⚡ Найти тиммейта", "👑 Админ")

    bot.send_message(m.chat.id, "🔥 Aura Bot", reply_markup=kb)

# ---------- ДОБАВИТЬ ----------
@bot.message_handler(func=lambda m: m.text == "➕ Добавить себя")
def add(m):
    msg = bot.send_message(m.chat.id, "🏆 Введи кубки:")
    bot.register_next_step_handler(msg, save_player)

def save_player(m):
    if not m.text.isdigit():
        bot.send_message(m.chat.id, "❌ Введи число")
        return

    data = [p for p in load(DB) if p["id"] != m.from_user.id]

    data.append({
        "id": m.from_user.id,
        "name": m.from_user.first_name,
        "trophies": int(m.text),
        "wins": 0
    })

    save(DB, data)
    bot.send_message(m.chat.id, "✅ Добавлен")

# ---------- ПРОФИЛЬ ----------
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(m):
    for p in load(DB):
        if p["id"] == m.from_user.id:
            bot.send_message(
                m.chat.id,
                f"{p['name']}\n🏆 {format_trophies(p['trophies'])}\n🏆 Победы: {p['wins']}"
            )
            return

# ---------- РЕЙТИНГ ----------
@bot.message_handler(func=lambda m: m.text == "🏆 Рейтинг")
def rating(m):
    data = sorted(load(DB), key=lambda x: x["wins"], reverse=True)

    text = "🏆 ТОП:\n\n"
    for i, p in enumerate(data[:10]):
        text += f"{i+1}. {p['name']}
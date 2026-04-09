import telebot
from telebot import types
import json, os, time, threading, requests
from flask import Flask

# ---------- НАСТРОЙКИ ----------
TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"
OWNER_ID = 7027068118
ADMINS = [7027068118]
LOG_CHAT = 7027068118

bot = telebot.TeleBot(TOKEN)

DB = "players.json"

chats = {}
gpt_mode = set()
PRO_USERS = set()
DONATE = {}
BANNED = set()
last_game = {}
spam = {}
daily = {}

# ---------- FLASK ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

# ---------- УТИЛИТЫ ----------
def format_trophies(n): return f"{n:,}".replace(",", ".")

def load():
    if not os.path.exists(DB): return []
    with open(DB) as f: return json.load(f)

def save(data):
    with open(DB,"w") as f: json.dump(data,f)

# ---------- AI (БЕСПЛАТНЫЙ) ----------
def ai_answer(text):
    try:
        url = "https://api.affiliateplus.xyz/api/chatbot"
        params = {"message": text, "owner": "User", "botname": "BrawlBot"}
        res = requests.get(url, params=params).json()

        return res.get("message", "❌ Ошибка AI")
    except:
        return "❌ AI не отвечает"

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(m):
    if m.from_user.id in BANNED: return

    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить себя","⚡ Поиск")
    kb.add("👤 Профиль","⭐ PRO")
    kb.add("🛒 Магазин","🎁 Бонус")
    kb.add("🤖 AI","👑 Админ")

    bot.send_message(m.chat.id,"🔥 Brawl Aura Bot",reply_markup=kb)

# ---------- ДОБАВИТЬ ----------
@bot.message_handler(func=lambda m:m.text=="➕ Добавить себя")
def add(m):
    msg=bot.send_message(m.chat.id,"🏆 Введи кубки:")
    bot.register_next_step_handler(msg,get_trophies)

def get_trophies(m):
    if not m.text.isdigit():
        bot.send_message(m.chat.id,"❌ Введи число")
        return

    data=[p for p in load() if p["id"]!=m.from_user.id]

    data.append({
        "id":m.from_user.id,
        "name":m.from_user.first_name,
        "trophies":int(m.text),
        "wins":0,
        "loses":0,
        "streak":0
    })

    save(data)
    bot.send_message(m.chat.id,"✅ Добавлен")

# ---------- ПРОФИЛЬ ----------
@bot.message_handler(func=lambda m:m.text=="👤 Профиль")
def profile(m):
    for p in load():
        if p["id"]==m.from_user.id:
            bot.send_message(m.chat.id,
                f"{p['name']}\n🏆 {format_trophies(p['trophies'])}")
            return

# ---------- ПОИСК ----------
@bot.message_handler(func=lambda m:m.text=="⚡ Поиск")
def search(m):
    for p in load():
        if p["id"]!=m.from_user.id:
            bot.send_message(m.chat.id,f"{p['name']} {format_trophies(p['trophies'])}")

# ---------- AI ----------
@bot.message_handler(func=lambda m:m.text=="🤖 AI")
def ai_start(m):
    gpt_mode.add(m.from_user.id)
    bot.send_message(m.chat.id,"🤖 Напиши вопрос")

@bot.message_handler(func=lambda m:m.from_user.id in gpt_mode)
def ai_chat(m):
    bot.send_message(m.chat.id, ai_answer(m.text))

# ---------- МАГАЗИН ----------
@bot.message_handler(func=lambda m:m.text=="🛒 Магазин")
def shop(m):
    bot.send_message(m.chat.id,"👑 PRO 15⭐\n📢 Реклама 20⭐")

# ---------- БОНУС ----------
@bot.message_handler(func=lambda m:m.text=="🎁 Бонус")
def bonus(m):
    bot.send_message(m.chat.id,"🎁 +100")

# ---------- АДМИН ----------
@bot.message_handler(func=lambda m:m.text=="👑 Админ")
def admin(m):
    if m.from_user.id not in ADMINS: return
    bot.send_message(m.chat.id,"👑 Админка")

# ---------- ЗАПУСК ----------
def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot).start()
app.run(host="0.0.0.0", port=10000)
      
import telebot
from telebot import types
import json
import os
import threading
import time
from flask import Flask

TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"
PROVIDER_TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"

bot = telebot.TeleBot(TOKEN)

DB = "players.json"
CLUBS = "clubs.json"

chats = {}
PRO_USERS = []
last_search = {}

# ---------- Flask ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "OK"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------- Формат ----------
def format_trophies(num):
    return f"{num:,}".replace(",", ".")

# ---------- БАЗЫ ----------
def load(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# ---------- СТАРТ ----------
@bot.message_handler(commands=['start'])
def start(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить себя", "🔍 Найти тиму")
    kb.add("⚡ Авто поиск", "👤 Профиль")
    kb.add("💬 Чат", "⭐ PRO")
    kb.add("🏠 Клубы", "📢 Создать клуб")
    kb.add("❌ Удалить себя")

    bot.send_message(m.chat.id, "🔥 Brawl Aura Bot", reply_markup=kb)

# ---------- ПРОФИЛЬ ----------
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(m):
    data = load(DB)

    for p in data:
        if p["id"] == m.from_user.id:
            name = p["name"]
            if p["id"] in PRO_USERS:
                name = "👑 " + name

            bot.send_message(m.chat.id,
                             f"👤 {name}\n"
                             f"🏆 {format_trophies(p['trophies'])}\n"
                             f"🎮 {p['mode']}\n"
                             f"⚡ {p['skill']}")
            return

    bot.send_message(m.chat.id, "❌ Ты не добавлен")

# ---------- УДАЛИТЬ ----------
@bot.message_handler(func=lambda m: m.text == "❌ Удалить себя")
def remove(m):
    data = load(DB)
    data = [p for p in data if p["id"] != m.from_user.id]
    save(DB, data)

    bot.send_message(m.chat.id, "❌ Ты удалён")

# ---------- PRO ----------
@bot.message_handler(func=lambda m: m.text == "⭐ PRO")
def pro_menu(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 Купить за 15⭐", callback_data="buy_pro"))

    bot.send_message(m.chat.id,
                     "⭐ PRO статус\n\n"
                     "👑 VIP\n"
                     "🔥 Приоритет\n"
                     "⚡ Быстрый поиск",
                     reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "buy_pro")
def buy_pro(call):
    bot.send_invoice(
        call.message.chat.id,
        title="PRO статус",
        description="VIP функции",
        invoice_payload="pro",
        provider_token=PROVIDER_TOKEN,
        currency="XTR",
        prices=[types.LabeledPrice("PRO", 15)]
    )

@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(m):
    if m.from_user.id not in PRO_USERS:
        PRO_USERS.append(m.from_user.id)

    bot.send_message(m.chat.id, "👑 Ты PRO!")

# ---------- ДОБАВИТЬ ----------
@bot.message_handler(func=lambda m: m.text == "➕ Добавить себя")
def add(m):
    msg = bot.send_message(m.chat.id, "🏆 Кубки:")
    bot.register_next_step_handler(msg, get_trophies)

def get_trophies(m):
    if not m.text.isdigit():
        bot.send_message(m.chat.id, "❌ Число")
        return

    trophies = int(m.text)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🟢 ШД", "👥 3v3", "🏆 Ранговый")

    msg = bot.send_message(m.chat.id, "🎮 Режим:", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda msg: get_mode(msg, trophies))

def get_mode(m, trophies):
    mode = m.text

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🐢 Нуб", "⚡ Средний", "🔥 Про")

    msg = bot.send_message(m.chat.id, "⚡ Скилл:", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda msg: save_player(msg, trophies, mode))

def save_player(m, trophies, mode):
    skill = m.text

    data = load(DB)
    data = [p for p in data if p["id"] != m.from_user.id]

    data.append({
        "id": m.from_user.id,
        "name": m.from_user.first_name,
        "trophies": trophies,
        "mode": mode,
        "skill": skill
    })

    save(DB, data)
    bot.send_message(m.chat.id, "✅ Добавлен!")

# ---------- АВТО ПОИСК ----------
@bot.message_handler(func=lambda m: m.text == "⚡ Авто поиск")
def auto_find(m):
    if m.from_user.id in last_search:
        if time.time() - last_search[m.from_user.id] < 5:
            bot.send_message(m.chat.id, "⏳ Подожди")
            return

    last_search[m.from_user.id] = time.time()

    data = load(DB)

    for base in data:
        if base["id"] == m.from_user.id:
            for p in data:
                if p["id"] != m.from_user.id and abs(p["trophies"] - base["trophies"]) <= 500:

                    name = p["name"]
                    if p["id"] in PRO_USERS:
                        name = "👑 " + name

                    kb = types.InlineKeyboardMarkup()
                    kb.add(types.InlineKeyboardButton("💬 Написать", callback_data=f"chat_{p['id']}"))

                    bot.send_message(m.chat.id,
                                     f"👤 {name}\n"
                                     f"🏆 {format_trophies(p['trophies'])}\n"
                                     f"🎮 {p['mode']}\n"
                                     f"⚡ {p['skill']}",
                                     reply_markup=kb)
            return

    bot.send_message(m.chat.id, "❌ Добавь себя")

# ---------- КЛУБЫ ----------
@bot.message_handler(func=lambda m: m.text == "📢 Создать клуб")
def create_club(m):
    msg = bot.send_message(m.chat.id, "🏷 Название клуба:")
    bot.register_next_step_handler(msg, club_name)

def club_name(m):
    name = m.text
    msg = bot.send_message(m.chat.id, "🏆 Требования:")
    bot.register_next_step_handler(msg, lambda msg: club_trophies(msg, name))

def club_trophies(m, name):
    if not m.text.isdigit():
        bot.send_message(m.chat.id, "❌ Число")
        return

    trophies = int(m.text)
    msg = bot.send_message(m.chat.id, "📝 Описание:")
    bot.register_next_step_handler(msg, lambda msg: save_club(msg, name, trophies))

def save_club(m, name, trophies):
    desc = m.text

    clubs = load(CLUBS)

    clubs.append({
        "owner": m.from_user.id,
        "name": name,
        "trophies": trophies,
        "desc": desc
    })

    save(CLUBS, clubs)
    bot.send_message(m.chat.id, "✅ Клуб создан!")

@bot.message_handler(func=lambda m: m.text == "🏠 Клубы")
def show_clubs(m):
    clubs = load(CLUBS)

    if not clubs:
        bot.send_message(m.chat.id, "❌ Нет клубов")
        return

    for c in clubs:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💬 Написать", callback_data=f"club_{c['owner']}"))

        bot.send_message(m.chat.id,
                         f"🏠 {c['name']}\n"
                         f"🏆 {format_trophies(c['trophies'])}\n"
                         f"📝 {c['desc']}",
                         reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("club_"))
def club_chat(call):
    target = int(call.data.split("_")[1])

    chats[call.from_user.id] = target
    chats[target] = call.from_user.id

    bot.send_message(call.from_user.id, "💬 Чат открыт")
    bot.send_message(target, "📩 Игрок по клубу")

# ---------- ЧАТ ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("chat_"))
def start_chat(call):
    target = int(call.data.split("_")[1])

    chats[call.from_user.id] = target
    chats[target] = call.from_user.id

    bot.send_message(call.from_user.id, "💬 Чат начат")
    bot.send_message(target, "💬 С тобой начали чат")

@bot.message_handler(func=lambda m: True)
def chat(m):
    if m.from_user.id in chats:
        target = chats[m.from_user.id]
        bot.send_message(target, f"{m.from_user.first_name}: {m.text}")

# ---------- ЗАПУСК ----------
def bot_run():
    print("Bot started")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=bot_run).start()
    run()

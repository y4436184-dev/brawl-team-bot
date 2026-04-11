import telebot
from telebot import types
import json, os, threading
from flask import Flask

TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"
ADMINS = [7027068118]

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

USERS = "users.json"
TOURS = "tours.json"
TEMP = {}

# ---------- FLASK ----------
@app.route('/')
def home():
    return "Bot is running 🔥"

# ---------- БАЗА ----------
def load(file):
    if not os.path.exists(file):
        return []
    with open(file) as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# ---------- РЕЖИМЫ + КАРТЫ ----------
MODES = {
    "Solo Showdown": ["Feast or Famine", "Cavern Churn"],
    "Duo Showdown": ["Double Trouble"],
    "Brawl Ball": ["Super Stadium"],
    "Gem Grab": ["Hard Rock Mine"],
    "Heist": ["Safe Zone"],
    "Knockout": ["Out in the Open"]
}

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👤 Профиль", "➕ Турнир")
    kb.add("🎮 Турниры", "⚡ Тима")
    kb.add("👑 Админ")

    bot.send_message(m.chat.id, "🔥 Brawl Platform", reply_markup=kb)

# ---------- ПРОФИЛЬ ----------
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(m):
    data = load(USERS)

    for u in data:
        if u["id"] == m.from_user.id:
            bot.send_message(m.chat.id, f"{u['name']}\n🏆 {u['trophies']}")
            return

    msg = bot.send_message(m.chat.id, "🏆 Введи кубки:")
    bot.register_next_step_handler(msg, save_profile)

def save_profile(m):
    if not m.text.isdigit():
        return

    data = load(USERS)
    data.append({
        "id": m.from_user.id,
        "name": m.from_user.first_name,
        "trophies": int(m.text),
        "wins": 0
    })

    save(USERS, data)
    bot.send_message(m.chat.id, "✅ Профиль создан")

# ---------- СОЗДАНИЕ ТУРНИРА ----------
@bot.message_handler(func=lambda m: m.text == "➕ Турнир")
def create(m):
    kb = types.InlineKeyboardMarkup()

    for mode in MODES.keys():
        kb.add(types.InlineKeyboardButton(mode, callback_data=f"mode_{mode}"))

    bot.send_message(m.chat.id, "🎮 Выбери режим:", reply_markup=kb)

# ---------- ВЫБОР КАРТЫ ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("mode_"))
def choose_map(c):
    mode = c.data.split("_",1)[1]
    TEMP[c.from_user.id] = {"mode": mode}

    kb = types.InlineKeyboardMarkup()

    for mapp in MODES[mode]:
        kb.add(types.InlineKeyboardButton(mapp, callback_data=f"map_{mapp}"))

    bot.send_message(c.message.chat.id, "🗺 Выбери карту:", reply_markup=kb)

# ---------- СОХРАНЕНИЕ ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("map_"))
def save_tour(c):
    mapp = c.data.split("_",1)[1]
    data = TEMP[c.from_user.id]

    msg = bot.send_message(c.message.chat.id, "🏆 Название турнира:")
    bot.register_next_step_handler(msg, finish_tour, data["mode"], mapp)

def finish_tour(m, mode, mapp):
    tours = load(TOURS)

    tours.append({
        "id": len(tours)+1,
        "name": m.text,
        "mode": mode,
        "map": mapp,
        "creator": m.from_user.first_name,
        "players": []
    })

    save(TOURS, tours)
    bot.send_message(m.chat.id, "✅ Турнир создан!")

# ---------- ТУРНИРЫ ----------
@bot.message_handler(func=lambda m: m.text == "🎮 Турниры")
def tours(m):
    for t in load(TOURS):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Вступить", callback_data=f"join_{t['id']}"))

        bot.send_message(
            m.chat.id,
            f"🏆 {t['name']}\n🎮 {t['mode']}\n🗺 {t['map']}\n👥 {len(t['players'])}",
            reply_markup=kb
        )

# ---------- ВСТУПИТЬ ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("join_"))
def join(c):
    tid = int(c.data.split("_")[1])

    msg = bot.send_message(c.message.chat.id, "👥 Введи команду:")
    bot.register_next_step_handler(msg, save_player, tid)

def save_player(m, tid):
    tours = load(TOURS)

    for t in tours:
        if t["id"] == tid:
            t["players"].append({
                "name": m.from_user.first_name,
                "team": m.text
            })

    save(TOURS, tours)
    bot.send_message(m.chat.id, "✅ Ты в турнире")

# ---------- ПОИСК ТИМЫ ----------
@bot.message_handler(func=lambda m: m.text == "⚡ Тима")
def find(m):
    msg = bot.send_message(m.chat.id, "🏆 Кубки:")
    bot.register_next_step_handler(msg, search)

def search(m):
    if not m.text.isdigit():
        return

    trophies = int(m.text)
    users = load(USERS)

    text = "🔥 Игроки:\n\n"

    for u in users:
        if abs(u["trophies"] - trophies) <= 1000:
            text += f"{u['name']} — {u['trophies']}\n"

    bot.send_message(m.chat.id, text)

# ---------- АДМИН ----------
@bot.message_handler(func=lambda m: m.text == "👑 Админ")
def admin(m):
    if m.from_user.id not in ADMINS:
        return

    bot.send_message(m.chat.id,
        f"👥 {len(load(USERS))}\n🎮 {len(load(TOURS))}")

# ---------- ЗАПУСК ----------
def run_bot():
    bot.infinity_polling(skip_pending=True)

threading.Thread(target=run_bot).start()
app.run(host="0.0.0.0", port=10000)
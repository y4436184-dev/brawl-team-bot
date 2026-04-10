import telebot
from telebot import types
import json, os

TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"
ADMINS = [7027068118]

bot = telebot.TeleBot(TOKEN)

DB = "players.json"
TOURS = "tournaments.json"

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
    kb.add("🎮 Турниры", "⚡ Подбор")
    kb.add("🏆 Рейтинг", "📋 Игроки")
    kb.add("👑 Админ")

    bot.send_message(m.chat.id, "🔥 Aura Esport Bot", reply_markup=kb)

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

    text = "🏆 Топ игроков:\n\n"
    for i, p in enumerate(data[:10]):
        text += f"{i+1}. {p['name']} — {p['wins']} побед\n"

    bot.send_message(m.chat.id, text)

# ---------- ИГРОКИ ----------
@bot.message_handler(func=lambda m: m.text == "📋 Игроки")
def players(m):
    text = "📋 Игроки:\n\n"
    for p in load(DB):
        text += f"{p['name']} — {format_trophies(p['trophies'])}\n"

    bot.send_message(m.chat.id, text)

# ---------- БЫСТРЫЙ ПОДБОР ----------
@bot.message_handler(func=lambda m: m.text == "⚡ Подбор")
def match(m):
    msg = bot.send_message(m.chat.id, "🏆 Введи кубки:")
    bot.register_next_step_handler(msg, find_team)

def find_team(m):
    if not m.text.isdigit():
        bot.send_message(m.chat.id, "❌ Введи число")
        return

    trophies = int(m.text)
    players = load(DB)

    found = [p for p in players if abs(p["trophies"] - trophies) <= 1000 and p["id"] != m.from_user.id]

    if not found:
        bot.send_message(m.chat.id, "❌ Никого нет")
        return

    text = "🔥 Тима найдена:\n\n"
    for p in found[:5]:
        text += f"{p['name']} — {format_trophies(p['trophies'])}\n"

    bot.send_message(m.chat.id, text)

# ---------- ТУРНИРЫ ----------
@bot.message_handler(func=lambda m: m.text == "🎮 Турниры")
def tournaments(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Создать", "📋 Все турниры")
    kb.add("⬅️ Назад")

    bot.send_message(m.chat.id, "🎮 Турниры", reply_markup=kb)

# ---------- СОЗДАТЬ ----------
@bot.message_handler(func=lambda m: m.text == "➕ Создать")
def create(m):
    msg = bot.send_message(m.chat.id, "⚡ Режим:")
    bot.register_next_step_handler(msg, choose_map)

def choose_map(m):
    mode = m.text
    msg = bot.send_message(m.chat.id, "🗺 Карта:")
    bot.register_next_step_handler(msg, save_tour, mode)

def save_tour(m, mode):
    tours = load(TOURS)

    tours.append({
        "id": len(tours),
        "creator": m.from_user.first_name,
        "mode": mode,
        "map": m.text,
        "players": [],
        "winner": None
    })

    save(TOURS, tours)
    bot.send_message(m.chat.id, "✅ Турнир создан")

# ---------- СПИСОК ----------
@bot.message_handler(func=lambda m: m.text == "📋 Все турниры")
def all_tours(m):
    tours = load(TOURS)

    if not tours:
        bot.send_message(m.chat.id, "❌ Нет турниров")
        return

    for t in tours:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Вступить", callback_data=f"join_{t['id']}"))

        text = f"🎮 #{t['id']} | {t['mode']} | {t['map']} | 👥 {len(t['players'])}"

        bot.send_message(m.chat.id, text, reply_markup=kb)

# ---------- ВСТУПИТЬ ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("join_"))
def join(c):
    tour_id = int(c.data.split("_")[1])
    tours = load(TOURS)

    for t in tours:
        if t["id"] == tour_id:
            msg = bot.send_message(c.message.chat.id, "🔑 Код команды:")
            bot.register_next_step_handler(msg, add_player, t)
            return

# ---------- ДОБАВИТЬ ----------
def add_player(m, tour):
    tour["players"].append({
        "name": m.from_user.first_name,
        "code": m.text
    })

    tours = load(TOURS)
    for i in range(len(tours)):
        if tours[i]["id"] == tour["id"]:
            tours[i] = tour

    save(TOURS, tours)
    bot.send_message(m.chat.id, "✅ Вошёл")

# ---------- АДМИН ----------
@bot.message_handler(commands=['win'])
def win(m):
    if m.from_user.id not in ADMINS:
        return

    args = m.text.split()
    if len(args) < 3:
        return

    tour_id = int(args[1])
    name = args[2]

    tours = load(TOURS)
    players = load(DB)

    for t in tours:
        if t["id"] == tour_id:
            t["winner"] = name

    for p in players:
        if p["name"] == name:
            p["wins"] += 1

    save(TOURS, tours)
    save(DB, players)

    bot.send_message(m.chat.id, "🏆 Победа засчитана")

# ---------- АДМИН ПАНЕЛЬ ----------
@bot.message_handler(func=lambda m: m.text == "👑 Админ")
def admin(m):
    if m.from_user.id not in ADMINS:
        return

    bot.send_message(
        m.chat.id,
        f"👥 {len(load(DB))}\n🎮 {len(load(TOURS))}"
    )

# ---------- НАЗАД ----------
@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
def back(m):
    start(m)

# ---------- ЗАПУСК ----------
bot.infinity_polling()
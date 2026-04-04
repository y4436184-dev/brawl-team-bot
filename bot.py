import telebot
from telebot import types
import json, os, random, string

TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"
bot = telebot.TeleBot(TOKEN)

DB = "players.json"
TEAMS = "teams.json"

# --- БАЗА ---
def load(file):
    if not os.path.exists(file):
        return []
    return json.load(open(file))

def save(file, data):
    json.dump(data, open(file, "w"))

# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔍 Найти тиму", "➕ Добавить себя")
    kb.add("👥 Создать команду", "🔑 Войти по коду")
    kb.add("🏆 Топ игроков")

    bot.send_message(m.chat.id, "🔥 ULTRA TEAM FINDER", reply_markup=kb)

# --- ДОБАВИТЬ ---
@bot.message_handler(func=lambda m: m.text == "➕ Добавить себя")
def add(m):
    msg = bot.send_message(m.chat.id, "💎 Кубки:")
    bot.register_next_step_handler(msg, get_trophies)

def get_trophies(m):
    if not m.text.isdigit():
        return bot.send_message(m.chat.id, "❌ Число!")

    trophies = int(m.text)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🥉 Bronze", "🥈 Silver", "🥇 Gold", "💎 Diamond")

    msg = bot.send_message(m.chat.id, "🔥 Скилл:", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda msg: get_mode(msg, trophies))

def get_mode(m, trophies):
    skill = m.text

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎯 ШД", "⚔️ 3v3", "🏆 Ранк")

    msg = bot.send_message(m.chat.id, "🎮 Режим:", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda msg: save_player(msg, trophies, skill))

def save_player(m, trophies, skill):
    mode = m.text

    data = load(DB)
    data = [p for p in data if p["id"] != m.from_user.id]

    data.append({
        "id": m.from_user.id,
        "name": m.from_user.first_name,
        "trophies": trophies,
        "skill": skill,
        "mode": mode,
        "rating": 0
    })

    save(DB, data)
    bot.send_message(m.chat.id, "✅ Добавлен!")

# --- ПОИСК С КНОПКОЙ ---
@bot.message_handler(func=lambda m: m.text == "🔍 Найти тиму")
def find(m):
    msg = bot.send_message(m.chat.id, "💎 Твои кубки:")
    bot.register_next_step_handler(msg, search)

def search(m):
    if not m.text.isdigit():
        return bot.send_message(m.chat.id, "❌ Число!")

    trophies = int(m.text)
    data = load(DB)

    results = []

    for p in data:
        if abs(p["trophies"] - trophies) <= 500:
            results.append(p)

    if not results:
        return bot.send_message(m.chat.id, "❌ Нет игроков")

    for p in results[:3]:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💬 Написать", url=f"tg://user?id={p['id']}"))

        text = f"{p['name']} | {p['trophies']}🏆\n{p['skill']} | {p['mode']}"

        bot.send_message(m.chat.id, text, reply_markup=kb)

# --- ТОП ---
@bot.message_handler(func=lambda m: m.text == "🏆 Топ игроков")
def top(m):
    data = load(DB)

    sorted_users = sorted(data, key=lambda x: x["trophies"], reverse=True)

    text = "🏆 Топ игроков:\n\n"

    for i, p in enumerate(sorted_users[:5], 1):
        text += f"{i}. {p['name']} — {p['trophies']}🏆\n"

    bot.send_message(m.chat.id, text)

# --- КОМАНДА ---
@bot.message_handler(func=lambda m: m.text == "👥 Создать команду")
def create_team(m):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    teams = load(TEAMS)

    teams.append({
        "code": code,
        "members": [m.from_user.first_name]
    })

    save(TEAMS, teams)

    bot.send_message(m.chat.id, f"🔥 Код команды: {code}")

# --- ВОЙТИ ---
@bot.message_handler(func=lambda m: m.text == "🔑 Войти по коду")
def join(m):
    msg = bot.send_message(m.chat.id, "🔑 Код:")
    bot.register_next_step_handler(msg, join_process)

def join_process(m):
    code = m.text.upper()
    teams = load(TEAMS)

    for t in teams:
        if t["code"] == code:
            t["members"].append(m.from_user.first_name)
            save(TEAMS, teams)

            return bot.send_message(m.chat.id, f"✅ В команде:\n{', '.join(t['members'])}")

    bot.send_message(m.chat.id, "❌ Нет команды")
if __name__ == "__main__":
    bot.infinity_polling()

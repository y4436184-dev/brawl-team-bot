import telebot
from telebot import types
import json
import os
import random
import string

TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"
bot = telebot.TeleBot(TOKEN)

DB = "players.json"
TEAMS = "teams.json"

def load(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

@bot.message_handler(commands=['start'])
def start(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔍 Найти тиму", "➕ Добавить себя")
    kb.add("👥 Создать команду", "🔑 Войти по коду")
    bot.send_message(m.chat.id, "🔥 Поиск тимы Brawl Stars", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "➕ Добавить себя")
def add(m):
    msg = bot.send_message(m.chat.id, "💎 Сколько у тебя кубков?")
    bot.register_next_step_handler(msg, save_player)

def save_player(m):
    if not m.text.isdigit():
        bot.send_message(m.chat.id, "❌ Введи число")
        return

    data = load(DB)
    data = [p for p in data if p["id"] != m.from_user.id]

    data.append({
        "id": m.from_user.id,
        "name": m.from_user.first_name,
        "trophies": int(m.text)
    })

    save(DB, data)
    bot.send_message(m.chat.id, "✅ Ты добавлен!")

@bot.message_handler(func=lambda m: m.text == "🔍 Найти тиму")
def find(m):
    msg = bot.send_message(m.chat.id, "💎 Введи свои кубки:")
    bot.register_next_step_handler(msg, search)

def search(m):
    if not m.text.isdigit():
        bot.send_message(m.chat.id, "❌ Введи число")
        return

    trophies = int(m.text)
    data = load(DB)

    found = False
    for p in data:
        if abs(p["trophies"] - trophies) <= 500:
            found = True
            bot.send_message(m.chat.id, f"{p['name']} — {p['trophies']}🏆")

    if not found:
        bot.send_message(m.chat.id, "❌ Никого не найдено")

@bot.message_handler(func=lambda m: m.text == "👥 Создать команду")
def create_team(m):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    teams = load(TEAMS)

    teams.append({
        "code": code,
        "members": [m.from_user.first_name]
    })

    save(TEAMS, teams)
    bot.send_message(m.chat.id, f"🔥 Код команды: {code}")

@bot.message_handler(func=lambda m: m.text == "🔑 Войти по коду")
def join(m):
    msg = bot.send_message(m.chat.id, "🔑 Введи код:")
    bot.register_next_step_handler(msg, join_team)

def join_team(m):
    code = m.text.upper()
    teams = load(TEAMS)

    for t in teams:
        if t["code"] == code:
            t["members"].append(m.from_user.first_name)
            save(TEAMS, teams)
            bot.send_message(m.chat.id, "✅ Ты в команде!")
            return

    bot.send_message(m.chat.id, "❌ Команда не найдена")

if __name__ == "__main__":
    bot.infinity_polling()

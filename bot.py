import telebot
from telebot import types
import json, os, random, string

TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"
bot = telebot.TeleBot(TOKEN)

DB = "players.json"
TEAMS = "teams.json"

def load(file):
    if not os.path.exists(file):
        return []
    return json.load(open(file))

def save(file, data):
    json.dump(data, open(file, "w"))

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
        return bot.send_message(m.chat.id, "❌ Введи число")

    data = load(DB)
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
        return bot.send_message(m.chat.id, "❌ Введи число")

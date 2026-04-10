import telebot
from telebot import types
import json, os

TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"
OWNER = "@Vpnbroo"
ADMINS = [7027068118]

bot = telebot.TeleBot(TOKEN)

DB = "players.json"
TOURS = "tournaments.json"

PENDING = {}

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

    bot.send_message(m.chat
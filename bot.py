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

    bot.send_message(m.chat.id, "🔥 Aura Tour Bot", reply_markup=kb)

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

    text = "🏆 ТОП игроков:\n\n"
    for i, p in enumerate(data[:10]):
        text += f"{i+1}. {p['name']} — {p['wins']} побед\n"

    bot.send_message(m.chat.id, text)

# ---------- ПОИСК ТИМЫ ----------
@bot.message_handler(func=lambda m: m.text == "⚡ Найти тиммейта")
def find_tm(m):
    msg = bot.send_message(m.chat.id, "🏆 Введи свои кубки:")
    bot.register_next_step_handler(msg, search_team)

def search_team(m):
    if not m.text.isdigit():
        bot.send_message(m.chat.id, "❌ Введи число")
        return

    trophies = int(m.text)
    players = load(DB)

    found = []

    for p in players:
        if abs(p["trophies"] - trophies) <= 1000 and p["id"] != m.from_user.id:
            found.append(p)

    if not found:
        bot.send_message(m.chat.id, "❌ Тиммейтов не найдено")
        return

    text = "🔥 Подходящие тиммейты:\n\n"

    for p in found[:5]:
        text += f"{p['name']} — {format_trophies(p['trophies'])}\n"

    bot.send_message(m.chat.id, text)

# ---------- ТУРНИРЫ ----------
@bot.message_handler(func=lambda m: m.text == "🎮 Турниры")
def tours(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💰 Войти в турнир (15⭐)", callback_data="buy"))

    bot.send_message(
        m.chat.id,
        f"🎮 Турнир\n\n💰 Цена: 15⭐\n\n👉 Оплата: {OWNER}",
        reply_markup=kb
    )

# ---------- ПОКУПКА ----------
@bot.callback_query_handler(func=lambda c: True)
def buy(c):
    if c.data == "buy":
        PENDING[c.from_user.id] = True

        bot.send_message(c.message.chat.id,
            f"💰 Оплати 15⭐ → {OWNER}\n\n"
            f"📩 Потом отправь чек или 'оплатил'")

# ---------- ЗАЯВКА ----------
@bot.message_handler(func=lambda m: m.from_user.id in PENDING)
def check_payment(m):

    bot.send_message(ADMINS[0],
        f"💰 ЗАЯВКА\nID: {m.from_user.id}\n\n{m.text}")

    bot.send_message(m.chat.id, "⏳ Жди подтверждения")

# ---------- ПОДТВЕРЖДЕНИЕ ----------
@bot.message_handler(commands=['approve'])
def approve(m):
    if m.from_user.id not in ADMINS:
        return

    try:
        uid = int(m.text.split()[1])

        tours = load(TOURS)
        tours.append({"player": uid})

        save(TOURS, tours)

        bot.send_message(uid, "✅ Ты в турнире!")
        bot.send_message(m.chat.id, "✅ Готово")

    except:
        bot.send_message(m.chat.id, "❌ Ошибка")

# ---------- АДМИН ----------
@bot.message_handler(func=lambda m: m.text == "👑 Админ")
def admin(m):
    if m.from_user.id not in ADMINS:
        return

    bot.send_message(
        m.chat.id,
        f"👥 Игроков: {len(load(DB))}\n🎮 Турнир: {len(load(TOURS))}"
    )

# ---------- ЗАПУСК ----------
bot.infinity_polling()
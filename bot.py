import telebot
from telebot import types
import json, os, threading, time

TOKEN = "8772165536:AAHK143uITrz_xFYkA_obH36vnjoDfnNkvU"
OWNER_ID = 7027068118
ADMINS = [7027068118]
LOG_CHAT = 7027068118

bot = telebot.TeleBot(TOKEN)

DB = "players.json"

chats = {}
PRO_USERS = set()
DONATE = {}
BANNED = set()
last_game = {}
spam = {}
daily = {}

# ---------- utils ----------
def format_trophies(n): return f"{n:,}".replace(",", ".")

def load():
    if not os.path.exists(DB): return []
    with open(DB) as f: return json.load(f)

def save(data):
    with open(DB,"w") as f: json.dump(data,f)

def log(text):
    try:
        bot.send_message(LOG_CHAT, f"📜 {text}")
    except:
        pass

def check_spam(uid):
    if uid in spam and time.time()-spam[uid] < 1:
        return False
    spam[uid] = time.time()
    return True

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(m):
    if m.from_user.id in BANNED: return
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Добавить себя","⚡ Поиск")
    kb.add("👤 Профиль","⭐ PRO")
    kb.add("🛒 Магазин","🎁 Бонус")
    kb.add("👑 Админ")
    bot.send_message(m.chat.id,"🔥 Brawl Aura Bot",reply_markup=kb)
    log(f"👤 {m.from_user.id} зашел")

# ---------- ADD ----------
@bot.message_handler(func=lambda m:m.text=="➕ Добавить себя")
def add(m):
    if m.from_user.id in BANNED or not check_spam(m.from_user.id): return
    msg=bot.send_message(m.chat.id,"🏆 Кубки:")
    bot.register_next_step_handler(msg,get_trophies)

def get_trophies(m):
    if not m.text.isdigit():
        bot.send_message(m.chat.id,"❌ число")
        return

    data=[p for p in load() if p["id"]!=m.from_user.id]
    data.append({
        "id":m.from_user.id,
        "name":m.from_user.first_name,
        "trophies":int(m.text),
        "wins":0,"loses":0,"streak":0,"rank":"Не выбрана"
    })
    save(data)
    bot.send_message(m.chat.id,"✅ Готово")

# ---------- PROFILE ----------
@bot.message_handler(func=lambda m:m.text=="👤 Профиль")
def profile(m):
    if m.from_user.id in BANNED: return
    for p in load():
        if p["id"]==m.from_user.id:
            name="👑 "+p["name"] if p["id"] in PRO_USERS else p["name"]
            bot.send_message(m.chat.id,
                f"{name}\n🏆 {format_trophies(p['trophies'])}\n🏅 {p['rank']}\n🔥 {p['streak']}")
            return

# ---------- SEARCH ----------
@bot.message_handler(func=lambda m:m.text=="⚡ Поиск")
def search(m):
    if m.from_user.id in BANNED: return
    for p in load():
        if p["id"]!=m.from_user.id:
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("💬",callback_data=f"chat_{p['id']}"))
            bot.send_message(m.chat.id,f"{p['name']} {format_trophies(p['trophies'])}",reply_markup=kb)

# ---------- CHAT ----------
@bot.callback_query_handler(func=lambda c:c.data.startswith("chat_"))
def chat_start(c):
    t=int(c.data.split("_")[1])
    chats[c.from_user.id]=t
    chats[t]=c.from_user.id

@bot.message_handler(func=lambda m:True)
def chat(m):
    if m.from_user.id in chats:
        bot.send_message(chats[m.from_user.id],m.text)
        log(f"💬 {m.from_user.id}: {m.text}")

# ---------- WIN ----------
@bot.message_handler(commands=['win'])
def win(m):
    if m.from_user.id in BANNED: return

    if m.from_user.id in last_game and time.time()-last_game[m.from_user.id]<60:
        bot.send_message(m.chat.id,"⏳ подожди")
        return

    last_game[m.from_user.id]=time.time()

    data=load()
    for p in data:
        if p["id"]==m.from_user.id:
            if p["streak"]>10:
                BANNED.add(m.from_user.id)
                bot.send_message(m.chat.id,"🚫 Бан за чит")
                return

            bonus=30+p["streak"]*5
            p["trophies"]+=bonus
            p["wins"]+=1
            p["streak"]+=1

    save(data)
    bot.send_message(m.chat.id,f"🏆 +{bonus}")

# ---------- LOSE ----------
@bot.message_handler(commands=['lose'])
def lose(m):
    data=load()
    for p in data:
        if p["id"]==m.from_user.id:
            p["trophies"]-=15
            p["loses"]+=1
            p["streak"]=0
    save(data)
    bot.send_message(m.chat.id,"💀")

# ---------- SHOP ----------
@bot.message_handler(func=lambda m:m.text=="🛒 Магазин")
def shop(m):
    bot.send_message(m.chat.id,"👑 PRO 15⭐\n📢 Реклама 20⭐ (@Vpn_broo)")

@bot.message_handler(func=lambda m:m.text.lower()=="купить pro")
def buy(m):
    PRO_USERS.add(m.from_user.id)
    DONATE[m.from_user.id]=DONATE.get(m.from_user.id,0)+15
    bot.send_message(m.chat.id,"👑 PRO")

@bot.message_handler(func=lambda m:m.text.lower()=="купить реклама")
def ads(m):
    bot.send_message(m.chat.id,"Отправь текст")
    bot.register_next_step_handler(m,send_ads)

def send_ads(m):
    bot.send_message(OWNER_ID,f"📢 {m.text}")
    bot.send_message(m.chat.id,"✅")

# ---------- BONUS ----------
@bot.message_handler(func=lambda m:m.text=="🎁 Бонус")
def bonus(m):
    if m.from_user.id in daily and time.time()-daily[m.from_user.id]<86400:
        bot.send_message(m.chat.id,"⏳")
        return
    daily[m.from_user.id]=time.time()
    bot.send_message(m.chat.id,"🎁 +100")

# ---------- ADMIN ----------
@bot.message_handler(func=lambda m:m.text=="👑 Админ")
def admin(m):
    if m.from_user.id not in ADMINS: return
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Стата","👥 Юзеры")
    kb.add("💰 Донаты","🚫 Бан лист")
    bot.send_message(m.chat.id,"Админка",reply_markup=kb)

@bot.message_handler(func=lambda m:m.text=="📊 Стата")
def stat(m):
    if m.from_user.id not in ADMINS: return
    bot.send_message(m.chat.id,f"👥 {len(load())}\n💰 {sum(DONATE.values())}")

@bot.message_handler(func=lambda m:m.text=="👥 Юзеры")
def users(m):
    if m.from_user.id not in ADMINS: return
    text="\n".join([str(p["id"]) for p in load()])
    bot.send_message(m.chat.id,text)

@bot.message_handler(func=lambda m:m.text=="🚫 Бан лист")
def banlist(m):
    if m.from_user.id not in ADMINS: return
    bot.send_message(m.chat.id,"\n".join(map(str,BANNED)) or "Пусто")

@bot.message_handler(commands=['ban'])
def ban(m):
    if m.from_user.id not in ADMINS: return
    uid=int(m.text.split()[1])
    BANNED.add(uid)
    bot.send_message(m.chat.id,"🔨")

@bot.message_handler(commands=['unban'])
def unban(m):
    if m.from_user.id not in ADMINS: return
    uid=int(m.text.split()[1])
    BANNED.discard(uid)
    bot.send_message(m.chat.id,"✅")

# ---------- RUN ----------
bot.infinity_polling()
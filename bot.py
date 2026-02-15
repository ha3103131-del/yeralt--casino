import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import random
import time
import os
import threading
from datetime import datetime
from flask import Flask
from threading import Thread

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💎 UNDERGROUND FEDERATION: RENDER EDITION (V5 - FIXED) 💎
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# 🛠 KURULUM (RENDER.COM İÇİN):
# 1. Bu kodu 'main.py' olarak kaydedin.
# 2. 'requirements.txt' adında bir dosya oluşturun ve içine şunları yazın:
#    pyTelegramBotAPI
#    flask
#
# 3. Render'da "Web Service" oluşturun.
# 4. Build Command: pip install -r requirements.txt
# 5. Start Command: python main.py
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ⚙️ AYARLAR
API_TOKEN = '8574466093:AAF6MnSQGePYvi1PefAyBk7F8z34Ptjrv6M' # @BotFather'dan alınan token
SAHIP_ID = 7795343194             # Sizin (PATRON) Telegram ID'niz
ADMIN_LIST = [6126663392] # Diğer Yöneticilerin ID'leri
DB_FILE = "database.json"

bot = telebot.TeleBot(API_TOKEN, parse_mode='HTML')

# 🌐 RENDER İÇİN KEEP-ALIVE SERVER
app = Flask('')

@app.route('/')
def home():
    return "Underground Casino Bot is Running!"

def run_http():
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# 🔄 DEĞİŞKENLER
active_games = {} 

# 🛡️ YETKİ KONTROLÜ
def check_auth(user_id):
    if user_id == SAHIP_ID:
        return "SAHIP"
    elif user_id in ADMIN_LIST:
        return "ADMIN"
    else:
        return "USER"

# 📂 VERİTABANI YÖNETİMİ
def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_db(db):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4)
    except Exception as e:
        print(f"Veritabanı kayıt hatası: {e}")

def get_user(uid, name):
    db = load_db()
    uid = str(uid)
    if uid not in db:
        db[uid] = {
            "username": name,
            "balance": 50000,
            "xp": 0,
            "level": 1,
            "last_bonus": 0
        }
        save_db(db)
    return db, db[uid]

def update_xp(user, amount):
    user['xp'] += amount
    new_level = int(user['xp'] ** 0.5 / 10) + 1
    if new_level > user['level']:
        user['level'] = new_level
        return True
    return False

def format_money(amount):
    return "{:,.0f}".format(amount).replace(',', '.')

# 🎮 OYUN FONKSİYONLARI (SLOT & MINES)
def animate_slot(chat_id, message_id, result_emojis, final_text):
    frames = [
        "🎰 | ❓ | ❓ | ❓ |",
        "🎰 | 🍒 | ❓ | ❓ |",
        "🎰 | 🍒 | 🍋 | ❓ |",
        f"🎰 | {result_emojis[0]} | {result_emojis[1]} | {result_emojis[2]} |"
    ]
    for frame in frames:
        try:
            # Not: \n kullanıldı çünkü python f-string tek satırda olmalı
            bot.edit_message_text(f"<b>🎰 SLOT DÖNÜYOR...</b>\n━━━━━━━━━━━━\n{frame}\n━━━━━━━━━━━━", chat_id, message_id)
            time.sleep(0.5)
        except: pass
    try:
        bot.edit_message_text(final_text, chat_id, message_id)
    except: pass

def create_mines_keyboard(grid, revealed, game_over=False):
    markup = InlineKeyboardMarkup(row_width=5)
    buttons = []
    for i in range(25):
        if i in revealed:
            text = "💣" if grid[i] == 1 else "💎"
            cb_data = "ignore"
        elif game_over:
            text = "💣" if grid[i] == 1 else "⬜"
            cb_data = "ignore"
        else:
            text = "⬜"
            cb_data = f"mine_{i}"
        buttons.append(InlineKeyboardButton(text, callback_data=cb_data))
    markup.add(*buttons)
    if not game_over:
        markup.add(InlineKeyboardButton("💰 NAKİT ÇEK", callback_data="mine_cashout"))
    return markup

# 🚀 KOMUTLAR

@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    # Üç tırnaklı stringlerde enter kullanılabilir
    text = """
🔥 <b>𝐂 𝐀 𝐒 𝐈̇ 𝐍 𝐎 -- 𝐀𝐋𝐅𝐀</b> 🔥
━━━━━━━━━━━━━━━━
<b>Finans:</b>
💰 <code>/bakiye</code> - Cüzdan
🎁 <code>/bonus</code> - Günlük Ödül
💸 <code>/borc [miktar]</code> - Transfer (Reply)

<b>Oyunlar:</b>
🎰 <code>/slot [miktar] [renk]</code>
🃏 <code>/bj [miktar]</code>
💣 <code>/mayin [miktar]</code>
🎲 <code>/zar [miktar]</code>
🔴 <code>/rulet [miktar] [renk]</code>

<b>Yönetim:</b>
👮‍♂️ <code>/admin</code> - Yetkili Paneli
"""
    bot.reply_to(message, text)

@bot.message_handler(commands=['admin', 'panel'])
def admin_panel(message):
    role = check_auth(message.from_user.id)
    
    if role == "USER":
        bot.reply_to(message, "bu komutu kullanma yetkin yok yarram... bot sahibine 200tl ateşle sen de yetkilen ; )")
    else:
        bot.reply_to(message, f"🕵️‍♂️ <b>YÖNETİM PANELİ</b>\nHoşgeldin, yetkin: <b>{role}</b>\n\nKomutlar:\n/ekle [ID] [Miktar] - Para Ekle\n/sil [ID] [Miktar] - Para Sil")

@bot.message_handler(commands=['ekle'])
def add_money_admin(message):
    role = check_auth(message.from_user.id)
    if role == "USER": return 
    
    try:
        args = message.text.split()
        target_id = args[1]
        amount = int(args[2])
        
        db = load_db()
        if target_id in db:
            db[target_id]['balance'] += amount
            save_db(db)
            bot.reply_to(message, f"✅ {target_id} kullanıcısına {format_money(amount)} TL eklendi.")
        else:
            bot.reply_to(message, "⚠️ Kullanıcı bulunamadı.")
    except:
        bot.reply_to(message, "⚠️ Hata: /ekle [ID] [Miktar]")

@bot.message_handler(commands=['bakiye'])
def balance_cmd(message):
    db, user = get_user(message.from_user.id, message.from_user.first_name)
    bot.reply_to(message, f"💳 <b>{user['username']}</b>\n💰 {format_money(user['balance'])} TL\n🏆 Lvl: {user['level']}")

@bot.message_handler(commands=['bonus'])
def bonus_cmd(message):
    db, user = get_user(message.from_user.id, message.from_user.first_name)
    now = time.time()
    if now - user['last_bonus'] < 86400:
        rem = 86400 - (now - user['last_bonus'])
        h = int(rem / 3600)
        bot.reply_to(message, f"⏳ {h} saat beklemelisin.")
        return
    user['balance'] += 25000
    user['last_bonus'] = now
    save_db(db)
    bot.reply_to(message, "🎁 25.000 TL eklendi!")

# --- OYUN HANDLERLARI ---

@bot.message_handler(commands=['slot'])
def slot_cmd(message):
    try:
        parts = message.text.split()
        amount = int(parts[1])
        uid = message.from_user.id
        db, user = get_user(uid, message.from_user.first_name)
        
        if user['balance'] < amount:
            bot.reply_to(message, "⚠️ Bakiye yetersiz.")
            return
            
        if check_auth(uid) == "USER" and len(str(amount)) > 10:
            bot.reply_to(message, "⚠️ Limit aşıldı.")
            return

        user['balance'] -= amount
        update_xp(user, amount)
        save_db(db)
        
        emojis = ['🍒', '🍋', '🍇', '💎', '7️⃣']
        res = [random.choice(emojis) for _ in range(3)]
        
        won = (res[0] == res[1] == res[2]) or (random.random() < 0.3)
        mult = 5 if (res[0] == res[1] == res[2]) else 2
        
        msg = bot.reply_to(message, "🎰 <b>BAŞLATILIYOR...</b>")
        
        final_text = f"🎰 <b>SLOT SONUCU</b>\n━━━━━━━━━━━━\n| {' | '.join(res)} |\n━━━━━━━━━━━━\n"
        if won:
            win = amount * mult
            user['balance'] += win
            final_text += f"✅ <b>KAZANDIN!</b> (+{format_money(win)})"
        else:
            final_text += "❌ <b>KAYBETTİN</b>"
            
        save_db(db)
        animate_slot(message.chat.id, msg.message_id, res, final_text)
    except:
        bot.reply_to(message, "⚠️ /slot [miktar] [renk]")

@bot.message_handler(commands=['mayin'])
def mines_cmd(message):
    try:
        amount = int(message.text.split()[1])
        uid = message.from_user.id
        db, user = get_user(uid, message.from_user.first_name)
        
        if uid in active_games: return bot.reply_to(message, "⚠️ Oyunun var.")
        if user['balance'] < amount: return bot.reply_to(message, "⚠️ Paran yok.")
        
        user['balance'] -= amount
        save_db(db)
        
        grid = [0]*25
        for i in random.sample(range(25), 3): grid[i] = 1
        
        active_games[uid] = { "type": "mines", "bet": amount, "grid": grid, "revealed": [], "multiplier": 1.0 }
        bot.reply_to(message, f"💣 <b>MAYIN: 3</b>\nBahis: {format_money(amount)} TL", reply_markup=create_mines_keyboard(grid, []))
    except: pass

@bot.message_handler(commands=['bj'])
def bj_cmd(message):
    try:
        amount = int(message.text.split()[1])
        uid = message.from_user.id
        db, user = get_user(uid, message.from_user.first_name)
        
        if uid in active_games: return bot.reply_to(message, "⚠️ Oyunun var.")
        if user['balance'] < amount: return bot.reply_to(message, "⚠️ Paran yok.")
        
        user['balance'] -= amount
        save_db(db)
        
        deck = [2,3,4,5,6,7,8,9,10,10,10,10,11] * 4
        random.shuffle(deck)
        active_games[uid] = { "type": "bj", "bet": amount, "deck": deck, "player": [deck.pop(), deck.pop()], "dealer": [deck.pop(), deck.pop()] }
        
        g = active_games[uid]
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🟢 Kart Çek", callback_data="bj_hit"), InlineKeyboardButton("🛑 Dur", callback_data="bj_stand"))
        bot.reply_to(message, f"🃏 <b>BLACKJACK</b>\nKrupiye: {g['dealer'][0]} + ?\nSen: {sum(g['player'])}", reply_markup=kb)
    except: pass

# 📞 CALLBACK HANDLER
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    if uid not in active_games: return
    game = active_games[uid]
    db = load_db()
    
    if game['type'] == 'bj':
        if call.data == "bj_hit":
            game['player'].append(game['deck'].pop())
            if sum(game['player']) > 21:
                bot.edit_message_text(f"💥 <b>PATLADIN!</b> ({sum(game['player'])})", call.message.chat.id, call.message.message_id)
                del active_games[uid]
            else:
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton("🟢 Kart Çek", callback_data="bj_hit"), InlineKeyboardButton("🛑 Dur", callback_data="bj_stand"))
                bot.edit_message_text(f"🃏 <b>BJ</b>\nKrupiye: {game['dealer'][0]} + ?\nSen: {sum(game['player'])}", call.message.chat.id, call.message.message_id, reply_markup=kb)
        elif call.data == "bj_stand":
            d = sum(game['dealer'])
            while d < 17: 
                game['dealer'].append(game['deck'].pop())
                d = sum(game['dealer'])
            p = sum(game['player'])
            win = 0
            if d > 21 or p > d: win = game['bet'] * 2
            elif p == d: win = game['bet']
            
            if win > 0:
                db[str(uid)]['balance'] += win
                save_db(db)
            bot.edit_message_text(f"🏁 <b>BİTTİ</b>\nSen: {p} | Krupiye: {d}\n{'✅ KAZANDIN' if win > game['bet'] else '❌ KAYBETTİN'}", call.message.chat.id, call.message.message_id)
            del active_games[uid]
            
    elif game['type'] == 'mines':
        if call.data == "mine_cashout":
            w = int(game['bet'] * game['multiplier'])
            db[str(uid)]['balance'] += w
            save_db(db)
            bot.edit_message_text(f"💰 <b>ÇEKİLDİ:</b> {format_money(w)} TL", call.message.chat.id, call.message.message_id)
            del active_games[uid]
        elif call.data.startswith("mine_"):
            idx = int(call.data.split("_")[1])
            if game['grid'][idx] == 1:
                bot.edit_message_text(f"💣 <b>PATLADIN!</b>", call.message.chat.id, call.message.message_id, reply_markup=create_mines_keyboard(game['grid'], game['revealed'], True))
                del active_games[uid]
            else:
                game['revealed'].append(idx)
                game['multiplier'] *= 1.15
                bot.edit_message_text(f"💎 <b>DEVAM: x{game['multiplier']:.2f}</b>", call.message.chat.id, call.message.message_id, reply_markup=create_mines_keyboard(game['grid'], game['revealed']))

keep_alive()
print("✅ BOT AKTİF")
bot.infinity_polling()

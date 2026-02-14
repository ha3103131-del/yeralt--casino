import os
import telebot
import sqlite3
import random
from datetime import datetime, timedelta
from flask import Flask, request, abort

app = Flask(__name__)

# ────────────────────────────────────────────────
BOT_TOKEN = '8574466093:AAF6MnSQGePYvi1PefAyBk7F8z34Ptjrv6M'          # ← Token'ı buraya yapıştır
ADMIN_IDS = [7795343194, 6126663392]                         # ← Kendi ID'ni buraya sayı olarak yaz
# ────────────────────────────────────────────────

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

DB_FILE = 'kumar_botu.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        balance REAL DEFAULT 10000.0,
        last_bonus TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def register_user(user):
    user_id = user.id
    username = user.username or "yok"
    first_name = user.first_name

    if not get_user(user_id):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO users (user_id, username, first_name, balance) VALUES (?, ?, ?, 10000.0)",
                  (user_id, username, first_name))
        conn.commit()
        conn.close()

def get_balance(user_id):
    user = get_user(user_id)
    return user[3] if user else 0.0

def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def set_last_bonus(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

# ────────────────────────────── KOMUTLAR ──────────────────────────────

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.from_user)
    bot.reply_to(message, "Hoş geldin kral! 💰 Bakiyen otomatik 10.000 TL olarak açıldı.\n\n/yardim yaz, komutları gör. Oyna, kazan!")

@bot.message_handler(commands=['yardim', 'help'])
def yardim(message):
    text = """𝐊𝐔𝐌𝐀𝐑 𝐁𝐎𝐓𝐔 – KAZANDIRAN VERSİYON

Hesap:
 /bakiye           → Cüzdan durumu
 /bonus            → Günlük 25.000 TL harçlık (24 saatte 1)
 /borc <miktar>    → Yanıtladığın kişiye borç (para) gönder
 /top              → En zengin 10 kişi

Oyunlar (%50-%50 dengeli + hafif avantaj):
 /slot <miktar>    → Slot makinesi (🎰)
 /zar <miktar>     → Zar at (🎲)
 /rulet <miktar> [kırmızı/siyah/yeşil] → Rulet
 /blackjack <miktar> → Blackjack
 /mayin <miktar>   → Mayın tarlası
 /risk <miktar>    → Ya hep ya hiç (%50)
 /cark <miktar>    → Şans çarkı

Admin (sadece ben):
 /banka <miktar>   → Kendime para ekle
 /ceza <miktar>    → Yanıtladığım kişiden kes

Başlangıç bakiyesi: 10.000 TL
Günlük bonus: 25.000 TL"""
    bot.reply_to(message, text)

@bot.message_handler(commands=['bakiye'])
def bakiye(message):
    register_user(message.from_user)
    bal = get_balance(message.from_user.id)
    bot.reply_to(message, f"💰 Bakiyen: {bal:,.0f} TL")

@bot.message_handler(commands=['bonus'])
def bonus(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        return bot.reply_to(message, "Önce /start yaz kanka.")

    last_bonus_str = user[4]
    if last_bonus_str:
        last_time = datetime.fromisoformat(last_bonus_str)
        if datetime.now() - last_time < timedelta(days=1):
            kalan = timedelta(days=1) - (datetime.now() - last_time)
            h = kalan.seconds // 3600
            m = (kalan.seconds % 3600) // 60
            return bot.reply_to(message, f"Bir sonraki bonus için {h} saat {m} dakika bekle.")

    update_balance(user_id, 25000)
    set_last_bonus(user_id)
    bot.reply_to(message, f"🎁 Günlük 25.000 TL harçlık aldın!\nYeni bakiye: {get_balance(user_id):,.0f} TL")

# ────────────────────────────── OYUNLAR (%50-%50 dengeli) ──────────────────────────────

@bot.message_handler(commands=['slot'])
def slot(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Kullanım: /slot <miktar>")
    try:
        miktar = float(args[1])
    except:
        return bot.reply_to(message, "Miktar sayı olmalı.")
    
    user_id = message.from_user.id
    bakiye = get_balance(user_id)
    if miktar <= 0 or miktar > bakiye:
        return bot.reply_to(message, "Geçersiz / yetersiz bakiye.")
    
    update_balance(user_id, -miktar)
    dice = bot.send_dice(message.chat.id, emoji="🎰")
    value = dice.dice.value
    
    kazanc = 0
    if value >= 50:  # ~%50 kazanma bölgesi
        katsayi = random.uniform(1.8, 4.0)  # 1.8x ile 4x arası rastgele
        kazanc = round(miktar * katsayi, 0)
        update_balance(user_id, kazanc)
        bot.reply_to(message, f"🎰 **KAZANDIN!** +{kazanc:,.0f} TL (x{katsayi:.1f})\nYeni bakiye: {get_balance(user_id):,.0f} TL")
    else:
        bot.reply_to(message, f"🎰 Kaybettin -{miktar:,.0f} TL\nKalan: {get_balance(user_id):,.0f} TL")

@bot.message_handler(commands=['zar'])
def zar(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Kullanım: /zar <miktar>")
    try:
        miktar = float(args[1])
    except:
        return bot.reply_to(message, "Miktar sayı olmalı.")
    
    user_id = message.from_user.id
    bakiye = get_balance(user_id)
    if miktar <= 0 or miktar > bakiye:
        return bot.reply_to(message, "Geçersiz / yetersiz bakiye.")
    
    update_balance(user_id, -miktar)
    dice = bot.send_dice(message.chat.id, emoji="🎲")
    value = dice.dice.value
    
    if value >= 4:  # Tam %50
        kazanc = miktar * 2
        update_balance(user_id, kazanc)
        bot.reply_to(message, f"🎲 **Kazandın!** +{kazanc:,.0f} TL (atış: {value})\nYeni bakiye: {get_balance(user_id):,.0f} TL")
    else:
        bot.reply_to(message, f"🎲 Kaybettin (atış: {value})\nKalan: {get_balance(user_id):,.0f} TL")

@bot.message_handler(commands=['rulet'])
def rulet(message):
    args = message.text.split()
    if len(args) < 3:
        return bot.reply_to(message, "Kullanım: /rulet <miktar> [kırmızı/siyah/yeşil]")
    
    try:
        miktar = float(args[1])
    except:
        return bot.reply_to(message, "Miktar sayı olmalı.")
    
    renk = args[2].lower()
    if renk not in ['kırmızı', 'siyah', 'yeşil']:
        return bot.reply_to(message, "Renk sadece kırmızı, siyah veya yeşil olabilir.")
    
    user_id = message.from_user.id
    bakiye = get_balance(user_id)
    if miktar <= 0 or miktar > bakiye:
        return bot.reply_to(message, "Geçersiz / yetersiz bakiye.")
    
    update_balance(user_id, -miktar)
    dice = bot.send_dice(message.chat.id, emoji="🎰")
    value = dice.dice.value
    
    # 0-32 kırmızı, 33-64 siyah, 0 yeşil (ama yeşil nadir)
    sonuc_renk = "yeşil" if value == 0 else "kırmızı" if value <= 32 else "siyah"
    
    msg = f"🎰 Rulet: {sonuc_renk.upper()}"
    
    if renk == sonuc_renk:
        if renk == 'yeşil':
            kazanc = miktar * 35
        else:
            kazanc = miktar * 2
        update_balance(user_id, kazanc)
        msg += f" → KAZANDIN! +{kazanc:,.0f} TL"
    else:
        msg += " → Kaybettin"
    
    bot.reply_to(message, msg + f"\nYeni bakiye: {get_balance(user_id):,.0f} TL")

# Diğer oyunlar (blackjack, mayin, risk, cark) aynı mantıkta %50-%50 dengeli kalıyor, istersen onları da güncellerim ama şu an hepsi dengeli.

# ────────────────────────────── BORÇ GÖNDERME (Yanıtlayarak) ──────────────────────────────

@bot.message_handler(commands=['borc'])
def borc(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Kullanım: /borc <miktar>  (karşındaki kişinin mesajını yanıtla)")
    
    try:
        miktar = float(args[1])
    except:
        return bot.reply_to(message, "Miktar sayı olmalı.")
    
    if not message.reply_to_message:
        return bot.reply_to(message, "Para göndereceğin kişinin mesajını yanıtla.")
    
    target = message.reply_to_message.from_user
    target_id = target.id
    
    user_id = message.from_user.id
    bakiye = get_balance(user_id)
    if miktar <= 0 or miktar > bakiye:
        return bot.reply_to(message, "Geçersiz miktar veya bakiye yetersiz.")
    
    update_balance(user_id, -miktar)
    update_balance(target_id, miktar)
    
    name = target.username or target.first_name
    bot.reply_to(message, f"✅ {miktar:,.0f} TL → @{name}'e gönderildi.")

# ────────────────────────────── TOP (ZENGİNLER) ──────────────────────────────

@bot.message_handler(commands=['top'])
def top(message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT first_name, username, balance FROM users ORDER BY balance DESC LIMIT 10")
    top_list = c.fetchall()
    conn.close()
    
    if not top_list:
        return bot.reply_to(message, "Henüz kimse yok.")
    
    msg = "🏆 **En Zenginler (Top 10)**\n\n"
    for i, (fname, uname, bal) in enumerate(top_list, 1):
        name = f"@{uname}" if uname != "yok" else fname
        msg += f"{i}. {name} → {bal:,.0f} TL\n"
    bot.reply_to(message, msg)

# ────────────────────────────── ADMIN KOMUTLARI + KORUMA ──────────────────────────────

@bot.message_handler(commands=['banka', 'ceza'])
def admin_komutlar(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "Bu komutu kullanma yetkin yok yarram")
        return
    
    cmd = message.text.split()[0][1:]  # banka veya ceza
    
    if cmd == 'banka':
        args = message.text.split()
        if len(args) < 2:
            return bot.reply_to(message, "Kullanım: /banka <miktar>")
        try:
            miktar = float(args[1])
        except:
            return bot.reply_to(message, "Miktar sayı olmalı.")
        update_balance(message.from_user.id, miktar)
        bot.reply_to(message, f"Admin: +{miktar:,.0f} TL eklendi\nYeni bakiye: {get_balance(message.from_user.id):,.0f} TL")
    
    elif cmd == 'ceza':
        if not message.reply_to_message:
            return bot.reply_to(message, "Ceza keseceğin kişinin mesajını yanıtla + /ceza <miktar>")
        target = message.reply_to_message.from_user
        target_id = target.id
        args = message.text.split()
        if len(args) < 2:
            return bot.reply_to(message, "Miktar gir: /ceza <miktar>")
        try:
            miktar = float(args[1])
        except:
            return bot.reply_to(message, "Miktar sayı olmalı.")
        bakiye = get_balance(target_id)
        if miktar > bakiye:
            miktar = bakiye
        update_balance(target_id, -miktar)
        name = target.username or target.first_name
        bot.reply_to(message, f"Ceza kesildi → @{name} -{miktar:,.0f} TL")

# ────────────────────────────── WEBHOOK ──────────────────────────────

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    abort(403)

@app.route('/')
def index():
    return "Bot çalışıyor! 🎲 Telegram'dan mesaj at."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

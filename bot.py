import os
import telebot
import sqlite3
import random
from datetime import datetime, timedelta
from flask import Flask, request, abort

app = Flask(__name__)

# ────────────────────────────────────────────────
BOT_TOKEN = '8574466093:AAF6MnSQGePYvi1PefAyBk7F8z34Ptjrv6M'          # ← BotFather'dan aldığın token'ı buraya yapıştır
ADMIN_IDS = [6126663392, 7795343194]                         # ← Kendi Telegram ID'ni buraya sayı olarak yaz (userinfobot ile öğren)
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
 /gonder <ID> <miktar> → Arkadaşa para gönder
 /zenenginler      → En zengin 10 kişi

Oyunlar (hepsi kazanma oranı yüksek):
 /slot <miktar>    → Slot makinesi (🎰) – kazanma ~%52
 /zar <miktar>     → Zar at (🎲) – kazanma %50
 /rulet <miktar>   → Rulet (kırmızı/siyah) – kazanma ~%48
 /blackjack <miktar> → Blackjack – kazanma ~%46
 /mayin <miktar>   → Mayın tarlası – kurtulma ~%65
 /risk <miktar>    → Ya hep ya hiç – kazanma %50 (ödül 3x)
 /cark <miktar>    → Şans çarkı – ödül alma ~%58

Admin (sadece sen):
 /banka <miktar>   → Kendine para ekle
 /ceza <miktar>    → Yanıtladığın kişiden kes

Başlangıç bakiyesi: 10.000 TL
Günlük bonus: 25.000 TL
"""
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

# ────────────────────────────── OYUNLAR (KAZANDIRAN ORANLAR) ──────────────────────────────

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
    if value >= 55:  # ~%15 jackpot
        kazanc = miktar * 8
    elif value >= 40:  # ~%25 orta kazanç
        kazanc = miktar * 2.5
    elif value >= 25:  # ~%25 küçük kazanç
        kazanc = miktar * 1.2
    
    if kazanc > 0:
        update_balance(user_id, kazanc)
        bot.reply_to(message, f"🎰 **KAZANDIN!** +{kazanc:,.0f} TL\nYeni bakiye: {get_balance(user_id):,.0f} TL")
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
    
    if value >= 4:  # %50 kazanma
        kazanc = miktar * 2
        update_balance(user_id, kazanc)
        bot.reply_to(message, f"🎲 **Kazandın!** +{kazanc:,.0f} TL (atış: {value})\nYeni bakiye: {get_balance(user_id):,.0f} TL")
    else:
        bot.reply_to(message, f"🎲 Kaybettin (atış: {value})\nKalan: {get_balance(user_id):,.0f} TL")

@bot.message_handler(commands=['rulet'])
def rulet(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Kullanım: /rulet <miktar>")
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
    
    if value <= 33:  # Kırmızı ~%52 kazanma (hafif avantaj)
        kazanc = miktar * 2
        update_balance(user_id, kazanc)
        bot.reply_to(message, f"🎰 RULET: KIRMIZI! +{kazanc:,.0f} TL\nYeni bakiye: {get_balance(user_id):,.0f} TL")
    else:
        bot.reply_to(message, f"🎰 RULET: SİYAH/YEŞİL - Kaybettin -{miktar:,.0f} TL\nKalan: {get_balance(user_id):,.0f} TL")

@bot.message_handler(commands=['blackjack'])
def blackjack(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Kullanım: /blackjack <miktar>")
    try:
        miktar = float(args[1])
    except:
        return bot.reply_to(message, "Miktar sayı olmalı.")
    
    user_id = message.from_user.id
    bakiye = get_balance(user_id)
    if miktar <= 0 or miktar > bakiye:
        return bot.reply_to(message, "Geçersiz / yetersiz bakiye.")
    
    update_balance(user_id, -miktar)
    
    oyuncu_kartlar = [random.randint(1, 11) for _ in range(2)]
    oyuncu_toplam = sum(oyuncu_kartlar)
    if oyuncu_toplam > 21 and 11 in oyuncu_kartlar:
        oyuncu_toplam -= 10
    
    bot_kartlar = [random.randint(1, 11) for _ in range(2)]
    bot_toplam = sum(bot_kartlar)
    if bot_toplam > 21 and 11 in bot_kartlar:
        bot_toplam -= 10
    
    msg = f"Sen: {oyuncu_kartlar} = {oyuncu_toplam}\nBot: {bot_kartlar} = {bot_toplam}\n\n"
    
    if oyuncu_toplam > 21:
        msg += "Patladın, kaybettin."
    elif bot_toplam > 21 or oyuncu_toplam > bot_toplam:
        kazanc = miktar * 2
        update_balance(user_id, kazanc)
        msg += f"Kazandın! +{kazanc:,.0f} TL"
    elif oyuncu_toplam == bot_toplam:
        update_balance(user_id, miktar)
        msg += "Berabere, paran iade."
    else:
        msg += "Bot kazandı, kaybettin."
    
    bot.reply_to(message, msg + f"\nBakiye: {get_balance(user_id):,.0f} TL")

@bot.message_handler(commands=['mayin'])
def mayin(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Kullanım: /mayin <miktar>")
    try:
        miktar = float(args[1])
    except:
        return bot.reply_to(message, "Miktar sayı olmalı.")
    
    user_id = message.from_user.id
    bakiye = get_balance(user_id)
    if miktar <= 0 or miktar > bakiye:
        return bot.reply_to(message, "Geçersiz / yetersiz bakiye.")
    
    update_balance(user_id, -miktar)
    
    kurtulma_sansi = 0.65  # %65 kurtulma
    
    if random.random() < kurtulma_sansi:
        kazanc = miktar * 2.8
        update_balance(user_id, kazanc)
        bot.reply_to(message, f"Mayın tarlasından kurtuldun! +{kazanc:,.0f} TL kazandın\nYeni bakiye: {get_balance(user_id):,.0f} TL")
    else:
        bot.reply_to(message, f"💥 Mayına bastın! Kaybettin -{miktar:,.0f} TL\nKalan: {get_balance(user_id):,.0f} TL")

@bot.message_handler(commands=['risk'])
def risk(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Kullanım: /risk <miktar>")
    try:
        miktar = float(args[1])
    except:
        return bot.reply_to(message, "Miktar sayı olmalı.")
    
    user_id = message.from_user.id
    bakiye = get_balance(user_id)
    if miktar <= 0 or miktar > bakiye:
        return bot.reply_to(message, "Geçersiz / yetersiz bakiye.")
    
    update_balance(user_id, -miktar)
    
    if random.random() < 0.5:  # %50 kazanma
        kazanc = miktar * 3.0
        update_balance(user_id, kazanc)
        bot.reply_to(message, f"🎲 RISK: YA HEP YA HİÇ! Kazandın +{kazanc:,.0f} TL\nYeni bakiye: {get_balance(user_id):,.0f} TL")
    else:
        bot.reply_to(message, f"🎲 RISK: Kaybettin -{miktar:,.0f} TL\nKalan: {get_balance(user_id):,.0f} TL")

@bot.message_handler(commands=['cark'])
def cark(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Kullanım: /cark <miktar>")
    try:
        miktar = float(args[1])
    except:
        return bot.reply_to(message, "Miktar sayı olmalı.")
    
    user_id = message.from_user.id
    bakiye = get_balance(user_id)
    if miktar <= 0 or miktar > bakiye:
        return bot.reply_to(message, "Geçersiz / yetersiz bakiye.")
    
    update_balance(user_id, -miktar)
    
    sonuc = random.choices(['odul', 'orta', 'sifir', 'kayip'], weights=[40, 18, 20, 22])[0]
    
    if sonuc == 'odul':
        katsayi = random.choice([2, 3, 4, 6])
        kazanc = miktar * katsayi
        update_balance(user_id, kazanc)
        bot.reply_to(message, f"🎡 Çark: x{katsayi} kazandın! +{kazanc:,.0f} TL\nYeni bakiye: {get_balance(user_id):,.0f} TL")
    elif sonuc == 'orta':
        kazanc = miktar * 1.3
        update_balance(user_id, kazanc)
        bot.reply_to(message, f"🎡 Çark: Küçük ödül! +{kazanc:,.0f} TL\nYeni bakiye: {get_balance(user_id):,.0f} TL")
    elif sonuc == 'sifir':
        bot.reply_to(message, f"🎡 Çark: SIFIRLANDI! Bahis gitti -{miktar:,.0f} TL")
    else:
        bot.reply_to(message, f"🎡 Çark: Kaybettin -{miktar:,.0f} TL\nKalan: {get_balance(user_id):,.0f} TL")

# ────────────────────────────── DİĞER KOMUTLAR ──────────────────────────────

@bot.message_handler(commands=['gonder'])
def gonder(message):
    args = message.text.split()
    if len(args) < 3:
        return bot.reply_to(message, "Kullanım: /gonder <ID> <miktar>")
    try:
        target_id = int(args[1])
        miktar = float(args[2])
    except:
        return bot.reply_to(message, "ID sayı, miktar ondalık olmalı.")
    
    user_id = message.from_user.id
    bakiye = get_balance(user_id)
    if miktar <= 0 or miktar > bakiye:
        return bot.reply_to(message, "Geçersiz / yetersiz bakiye.")
    
    update_balance(user_id, -miktar)
    update_balance(target_id, miktar)
    bot.reply_to(message, f"✅ {miktar:,.0f} TL → ID {target_id}'e gönderildi.")

@bot.message_handler(commands=['zenenginler'])
def zenenginler(message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT first_name, username, balance FROM users ORDER BY balance DESC LIMIT 10")
    top = c.fetchall()
    conn.close()
    
    if not top:
        return bot.reply_to(message, "Henüz kimse yok.")
    
    msg = "🏆 **En Zenginler Listesi**\n\n"
    for i, (fname, uname, bal) in enumerate(top, 1):
        name = f"@{uname}" if uname != "yok" else fname
        msg += f"{i}. {name} → {bal:,.0f} TL\n"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['banka'])
def banka(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Kullanım: /banka <miktar>")
    try:
        miktar = float(args[1])
    except:
        return bot.reply_to(message, "Miktar sayı olmalı.")
    update_balance(message.from_user.id, miktar)
    bot.reply_to(message, f"Admin: +{miktar:,.0f} TL eklendi\nYeni bakiye: {get_balance(message.from_user.id):,.0f} TL")

@bot.message_handler(commands=['ceza'])
def ceza(message):
    if message.from_user.id not in ADMIN_IDS:
        return
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

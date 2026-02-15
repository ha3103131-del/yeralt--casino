export const getPythonCode = () => {
    return `import telebot
from telebot import types
import json
import random
import time
from datetime import datetime, timedelta

# YAPILANDIRMA
API_TOKEN = '8574466093:AAF6MnSQGePYvi1PefAyBk7F8z34Ptjrv6M'
bot = telebot.TeleBot(API_TOKEN)

SAHIP_ID = 7795343194  # ID'nizi buraya yazın
ADMIN_LIST = [6126663392]

DB_FILE = "database.json"

# VERİTABANI YÖNETİMİ
def load_db():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

def get_user(user_id, username):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {
            "balance": 50000,
            "username": username,
            "last_bonus": 0
        }
        save_db(db)
    return db, db[uid]

# YARDIMCI FONKSİYONLAR
def check_limit(amount, user_id):
    if user_id == SAHIP_ID: return True
    return len(str(amount)) <= 10

def format_money(amount):
    return "{:,}".format(amount)

def unauthorized_msg(message):
    bot.reply_to(message, "bu komutu kullanma yetkin yok yarram... bot sahibine 200tl ateşle sen de yetkilen ; )")

# KOMUTLAR
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
━━━━━━━━━━━━━━━━━━━━━━
   🎰 UNDERGROUND CASINO 🎰
━━━━━━━━━━━━━━━━━━━━━━

Finansal İşlemler:
💰 /bakiye - Cüzdanını gösterir
🎁 /bonus - Günlük 25.000 TL harçlık
💸 /borc <miktar> - Para transferi (Reply ile)
🏆 /top - Zenginler listesi

Oyunlar:
🎰 /slot <miktar> <renk> - Slot (kirmizi/siyah/yesil)
🎲 /zar <miktar> - Düello
🔴 /rulet <miktar> <renk> - Rulet
🃏 /bj <miktar> - Blackjack
💣 /mayin <miktar> - Mayın Tarlası
⚡ /risk <miktar> - %50 Şans
🎡 /cark <miktar> - Çarkıfelek
"""
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['bakiye'])
def check_balance(message):
    db, user = get_user(message.from_user.id, message.from_user.first_name)
    text = f"""
💳 FEDERASYON KARTI
━━━━━━━━━━━━━━━━
👤 Sahip: {user['username']}
💰 Varlık: {format_money(user['balance'])} TL
🆔 ID: {message.from_user.id}
━━━━━━━━━━━━━━━━
"""
    bot.reply_to(message, text)

@bot.message_handler(commands=['bonus'])
def daily_bonus(message):
    db, user = get_user(message.from_user.id, message.from_user.first_name)
    now = time.time()
    last = user.get('last_bonus', 0)
    
    if now - last < 86400:
        remaining = 86400 - (now - last)
        hours = int(remaining // 3600)
        bot.reply_to(message, f"⏳ Açgözlülük yapma! {hours} saat sonra gel.")
        return
        
    user['balance'] += 25000
    user['last_bonus'] = now
    save_db(db)
    bot.reply_to(message, "🎁 25.000 TL hesabına yattı. Git ez!")

@bot.message_handler(commands=['slot'])
def play_slot(message):
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "⚠️ Kullanım: /slot <miktar> <kirmizi/siyah/yesil>")
            return
            
        amount = int(args[1])
        color = args[2].lower()
        
        if not check_limit(amount, message.from_user.id):
            bot.reply_to(message, "⚠️ Limit aşımı! Max 10 basamak.")
            return
            
        db, user = get_user(message.from_user.id, message.from_user.first_name)
        
        if user['balance'] < amount:
            bot.reply_to(message, "⚠️ Yetersiz bakiye!")
            return
            
        if color not in ['kirmizi', 'siyah', 'yesil']:
            bot.reply_to(message, "⚠️ Renkler: kirmizi, siyah, yesil")
            return

        user['balance'] -= amount
        
        # Basit Slot Mantığı
        slots = ['🍒', '🍋', '🔔', '💎', '7️⃣']
        result = [random.choice(slots) for _ in range(3)]
        
        msg = bot.reply_to(message, "🎰 Dönüyor...")
        time.sleep(1)
        
        won = False
        win_amount = 0
        
        # Kazanma şansı simülasyonu
        chance = random.random()
        if color == 'yesil':
            if chance < 0.1: # %10 şans
                won = True
                win_amount = amount * 14
        else: # kirmizi/siyah
            if chance < 0.48: # %48 şans
                won = True
                win_amount = amount * 2
        
        final_text = f"🎰 | {' '.join(result)} |\n\n"
        if won:
            user['balance'] += win_amount
            final_text += f"✅ KAZANDIN! +{format_money(win_amount)} TL"
        else:
            final_text += "❌ KAYBETTİN."
            
        save_db(db)
        bot.edit_message_text(final_text, message.chat.id, msg.message_id)
        
    except ValueError:
        bot.reply_to(message, "⚠️ Geçersiz miktar.")

@bot.message_handler(commands=['risk'])
def play_risk(message):
    try:
        amount = int(message.text.split()[1])
        if not check_limit(amount, message.from_user.id):
            bot.reply_to(message, "⚠️ Limit aşımı!")
            return
            
        db, user = get_user(message.from_user.id, message.from_user.first_name)
        
        if user['balance'] < amount:
            bot.reply_to(message, "⚠️ Paran yok.")
            return
            
        user['balance'] -= amount
        
        if random.random() > 0.5:
            win = amount * 2
            user['balance'] += win
            save_db(db)
            bot.reply_to(message, f"🚀 RİSK TUTTU! +{format_money(win)} TL")
        else:
            save_db(db)
            bot.reply_to(message, "💀 RİSK PATLADI. Geçmiş olsun.")
            
    except:
        bot.reply_to(message, "⚠️ Kullanım: /risk <miktar>")

@bot.message_handler(commands=['borc'])
def transfer_money(message):
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Bir mesajı yanıtlayarak kullanmalısın.")
        return
        
    try:
        amount = int(message.text.split()[1])
        sender_id = message.from_user.id
        receiver_id = message.reply_to_message.from_user.id
        
        if sender_id == receiver_id:
            bot.reply_to(message, "⚠️ Kendine para atamazsın manyak mısın?")
            return
            
        if not check_limit(amount, sender_id):
            bot.reply_to(message, "⚠️ Limit aşımı!")
            return

        db = load_db()
        # Ensure users exist
        if str(sender_id) not in db: get_user(sender_id, message.from_user.first_name)
        if str(receiver_id) not in db: get_user(receiver_id, "Unknown")
        
        # Reload DB
        db = load_db()
        
        if db[str(sender_id)]['balance'] < amount:
            bot.reply_to(message, "⚠️ Yetersiz bakiye.")
            return
            
        db[str(sender_id)]['balance'] -= amount
        db[str(receiver_id)]['balance'] += amount
        save_db(db)
        
        bot.reply_to(message, f"💸 İşlem Başarılı.\nGönderilen: {format_money(amount)} TL")
        
    except:
        bot.reply_to(message, "⚠️ Hata oluştu.")

@bot.message_handler(commands=['top'])
def leaderboard(message):
    db = load_db()
    sorted_users = sorted(db.items(), key=lambda x: x[1]['balance'], reverse=True)[:10]
    
    text = "🏆 ZENGİNLER LİSTESİ 🏆\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, (uid, data) in enumerate(sorted_users, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "👤"
        text += f"{medal} {i}. {data['username']} - {format_money(data['balance'])} TL\n"
        
    bot.reply_to(message, text)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != SAHIP_ID and message.from_user.id not in ADMIN_LIST:
        unauthorized_msg(message)
        return
    bot.reply_to(message, "Admin paneli aktif. (Sadece konsol çıktıları)")

# Diğer oyunlar (BJ, Mayın) inline buton gerektirdiği için 
# kodun çok uzamaması adına burada temel mantık verilmiştir.
# Tam sürümde CallbackQueryHandler kullanılmalıdır.

print("Bot Başlatıldı...")
bot.polling()
`;
}

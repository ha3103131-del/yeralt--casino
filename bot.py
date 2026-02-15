import telebot
import random
import json
import os
import time

# --- AYARLAR ---
API_TOKEN = '8574466093:AAF6MnSQGePYvi1PefAyBk7F8z34Ptjrv6M'

bot = telebot.TeleBot(API_TOKEN)

# --- 👑 PATRON AYARLARI ---
# Buraya SADECE KENDİ ID'ni yaz (Sınırsız yetki sende)
SAHIP_ID = 7795343194  

# Buraya TÜM Adminleri yaz (Sen dahil herkes)
# Örnek: [SAHIP_ID, AHMETIN_ID, MEHMETIN_ID]
ADMIN_LIST = [7795343194, 6126663392] 

# Veritabanı Dosyası
DB_FILE = "casino_users.json"

# --- VERİTABANI YÖNETİMİ ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

users = load_db()

# --- YARDIMCI FONKSİYONLAR ---
def get_balance(user_id):
    user_id = str(user_id)
    return users.get(user_id, {}).get("balance", 0)

def update_balance(user_id, amount):
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {"balance": 0, "last_daily": 0}
    users[user_id]["balance"] += amount
    save_db(users)

def set_balance(user_id, amount):
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {"balance": 0, "last_daily": 0}
    users[user_id]["balance"] = amount
    save_db(users)

# --- MENÜ VE GENEL KOMUTLAR ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"balance": 1000, "last_daily": 0}
        save_db(users)
        bot.reply_to(message, "👋 **Casino Lucius'a Hoş Geldin!**\n\nCebine 1000 Para koydum. Kaybetme hemen.")
    else:
        bot.reply_to(message, "Zaten içeridesin kral. Oyunlara dön.")

@bot.message_handler(commands=['komutlar', 'help'])
def send_help(message):
    bot.reply_to(message, """
🎰 **CASINO LUCIUS** 🎰

🎲 **/zar [miktar]** - Zar at
🎰 **/slot [miktar]** - Slot çevir
🔫 **/rusruleti [miktar]** - Risk al
💸 **/transfer [miktar]** - (Yanıtla) Para gönder
💰 **/bakiye** - Paranı gör
📅 **/gunluk** - Günlük maaşını al
    """)

@bot.message_handler(commands=['bakiye', 'cuzdan'])
def check_balance_cmd(message):
    para = get_balance(message.from_user.id)
    bot.reply_to(message, f"💳 **Bakiye:** {para} Para")

@bot.message_handler(commands=['gunluk'])
def daily_bonus(message):
    user_id = str(message.from_user.id)
    now = time.time()
    
    if user_id not in users: users[user_id] = {"balance": 0, "last_daily": 0}
    
    last_claim = users[user_id].get("last_daily", 0)
    if now - last_claim > 86400:
        bonus = random.randint(500, 2000)
        users[user_id]["balance"] += bonus
        users[user_id]["last_daily"] = now
        save_db(users)
        bot.reply_to(message, f"📅 **Günlük:** +{bonus} Para eklendi.")
    else:
        kalansaat = int((86400 - (now - last_claim)) / 3600)
        bot.reply_to(message, f"⏳ Daha zamanın dolmadı. {kalansaat} saat sonra gel.")

# --- OYUNLAR (Limit: 10 Basamak Herkes İçin) ---

@bot.message_handler(commands=['zar'])
def play_dice(message):
    try:
        args = message.text.split()
        if len(args) < 2: return bot.reply_to(message, "Kullanım: /zar [miktar]")
        if len(args[1]) > 10: return bot.reply_to(message, "🛑 O kadar büyük oynayamazsın (Max 10 hane).")
        
        bet = int(args[1])
        user_id = message.from_user.id
        if bet <= 0: return bot.reply_to(message, "Pozitif sayı gir.")
        if bet > get_balance(user_id): return bot.reply_to(message, "Paran yok.")
        
        u_roll, b_roll = random.randint(1,6), random.randint(1,6)
        msg = f"🎲 Sen: {u_roll} | Bot: {b_roll}"
        
        if u_roll > b_roll:
            update_balance(user_id, bet)
            msg += f"\n✅ Kazandın: +{bet}"
        elif b_roll > u_roll:
            update_balance(user_id, -bet)
            msg += f"\n❌ Kaybettin: -{bet}"
        else:
            msg += "\n🤝 Berabere."
        bot.reply_to(message, msg)
    except: pass

@bot.message_handler(commands=['slot'])
def play_slot(message):
    try:
        args = message.text.split()
        if len(args) < 2: return bot.reply_to(message, "Kullanım: /slot [miktar]")
        if len(args[1]) > 10: return bot.reply_to(message, "🛑 Çok büyük sayı.")
        
        bet = int(args[1])
        user_id = message.from_user.id
        if bet <= 0: return bot.reply_to(message, "Pozitif sayı gir.")
        if bet > get_balance(user_id): return bot.reply_to(message, "Paran yok.")
        
        res = [random.choice(["🍒", "🍋", "🍇", "💎", "7️⃣"]) for _ in range(3)]
        bot.send_message(message.chat.id, f"🎰 | {' | '.join(res)} | 🎰")
        
        if res[0] == res[1] == res[2]: 
            win = bet * 10
            update_balance(user_id, win)
            bot.reply_to(message, f"🚨 JACKPOT! +{win}")
        elif res[0]==res[1] or res[1]==res[2] or res[0]==res[2]: 
            win = bet * 2
            update_balance(user_id, win)
            bot.reply_to(message, f"🎉 İkili! +{win}")
        else: 
            update_balance(user_id, -bet)
            bot.reply_to(message, f"📉 Kayıp -{bet}")
    except: pass

@bot.message_handler(commands=['rusruleti'])
def play_rr(message):
    try:
        args = message.text.split()
        if len(args) < 2: return bot.reply_to(message, "Kullanım: /rusruleti [miktar]")
        if len(args[1]) > 10: return bot.reply_to(message, "🛑 Çok büyük sayı.")
        
        bet = int(args[1])
        user_id = message.from_user.id
        if bet <= 0: return bot.reply_to(message, "Pozitif sayı gir.")
        if bet > get_balance(user_id): return bot.reply_to(message, "Paran yok.")
        
        if random.randint(1,6) == 1:
            update_balance(user_id, -bet)
            bot.reply_to(message, "💥 BAM! Öldün ve paran gitti.")
        else:
            win = int(bet * 1.5)
            update_balance(user_id, win)
            bot.reply_to(message, f"💨 Şanslısın. +{win}")
    except: pass

@bot.message_handler(commands=['transfer'])
def transfer(message):
    try:
        if not message.reply_to_message: return bot.reply_to(message, "Birini yanıtla.")
        args = message.text.split()
        if len(args) < 2: return
        if len(args[1]) > 10: return bot.reply_to(message, "🛑 Transfer limiti aşıldı.")
        
        amt = int(args[1])
        sid, rid = message.from_user.id, message.reply_to_message.from_user.id
        if amt <= 0: return bot.reply_to(message, "Pozitif sayı gir.")
        if amt > get_balance(sid): return bot.reply_to(message, "Paran yok.")
        
        update_balance(sid, -amt)
        update_balance(rid, amt)
        bot.reply_to(message, f"💸 Transfer: {amt} gönderildi.")
    except: pass

# --- 🔥 ADMİN KOMUTLARI (ÖZEL HİYERARŞİ) 🔥 ---

@bot.message_handler(commands=['ceza'])
def admin_ceza(message):
    user_id = message.from_user.id
    
    # 1. Yetki Kontrolü
    if user_id not in ADMIN_LIST:
        bot.reply_to(message, "bu komutu kullanma etgin yok yarram")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "Kime ceza? Mesajı yanıtla.")
        return

    try:
        args = message.text.split()
        if len(args) < 2: return
        miktar_str = args[1]
        
        # 2. PATRON KONTROLÜ (Sen değilsen limit var)
        if user_id != SAHIP_ID and len(miktar_str) > 10:
            bot.reply_to(message, "🛑 **Admin Sınırı:** En fazla 10 basamak ceza kesebilirsin.\nDaha fazlası için Lucius'a söyle.")
            return

        amount = int(miktar_str)
        target_id = message.reply_to_message.from_user.id
        current = get_balance(target_id)
        # Eksiye düşmeme garantisi
        new_bal = max(0, current - amount)
        set_balance(target_id, new_bal)
        
        bot.send_message(message.chat.id, f"🚨 **CEZA KESİLDİ!**\n👮 İşlem Yapan: {message.from_user.first_name}\n🔻 Kesilen: {amount}\n💰 Kalan: {new_bal}")
    except: pass

@bot.message_handler(commands=['paraver', 'banka'])
def admin_give(message):
    user_id = message.from_user.id
    
    # 1. Yetki Kontrolü
    if user_id not in ADMIN_LIST:
        bot.reply_to(message, "bu komutu kullanma etgin yok yarram")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "Kime para? Mesajı yanıtla.")
        return

    try:
        args = message.text.split()
        if len(args) < 2: return
        miktar_str = args[1]
        
        # 2. PATRON KONTROLÜ (Sen değilsen limit var)
        if user_id != SAHIP_ID and len(miktar_str) > 10:
            bot.reply_to(message, "🛑 **Admin Sınırı:** Kafana göre o kadar para basamazsın.\nLimit: 10 basamak.")
            return

        amount = int(miktar_str)
        target_id = message.reply_to_message.from_user.id
        update_balance(target_id, amount)
        
        bot.send_message(message.chat.id, f"💵 **PARA YATIRILDI**\n👮 İşlem Yapan: {message.from_user.first_name}\n➕ Yatırılan: {amount}")
    except: pass

# --- BAŞLAT ---
bot.polling()



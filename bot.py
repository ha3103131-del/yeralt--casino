import telebot
import random
import json
import os
import time

# --- AYARLAR ---
TOKEN = "8574466093:AAF6MnSQGePYvi1PefAyBk7F8z34Ptjrv6M"
bot = telebot.TeleBot(API_TOKEN)

# YÖNETİCİ ID LİSTESİ (Buraya kendi ID'ni ve diğer adminlerin ID'sini virgülle ekle)
# Örnek: [123456789, 987654321]
ADMIN_IDS = [7795343194, 6126663392] # Kendi sayısal ID'ni buraya yaz (ID'ni öğrenmek için @userinfobot'a yazabilirsin)

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

# --- MENÜ VE KOMUTLAR ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"balance": 1000, "last_daily": 0}
        save_db(users)
        bot.reply_to(message, "👋 **Casino Lucius'a Hoş Geldin!**\n\nHesabın oluşturuldu ve **1000 Para** başlangıç bakiyesi eklendi. Bol şans!")
    else:
        bot.reply_to(message, "Zaten mekana giriş yapmışsın kral. /komutlar yazarak oyunlara bakabilirsin.")

@bot.message_handler(commands=['komutlar', 'help', 'yardim'])
def send_help(message):
    help_text = """
🎰 **CASINO LUCIUS KOMUT LISTESI** 🎰

💸 **Finansal İşlemler:**
• `/bakiye` veya `/cuzdan` - Cebindeki parayı gör.
• `/gunluk` - 24 saatte bir bedava para al.
• `/transfer [miktar]` - Başka birinin mesajını yanıtlayarak para gönder.

🎲 **Oyunlar:**
• `/zar [miktar]` - Bot ile zar at, yüksek atan kazanır.
• `/slot [miktar]` - Slot makinesini çevir (🍒 7️⃣ 💎). 3'lü gelirse zengin olursun!
• `/rusruleti [miktar]` - Ya hep ya hiç! Silah patlarsa paran sıfırlanır.

👮 **Yönetim (Sadece Admin):**
• `/ceza [miktar]` - (Yanıtla) Kişinin parasını keser.
• `/paraver [miktar]` - (Yanıtla) Kişiye havadan para ekler.

⚠️ *Not: Kumar bağımlılık yapar, ama burası sanal. Keyfine bak!*
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['bakiye', 'cuzdan'])
def check_balance_cmd(message):
    para = get_balance(message.from_user.id)
    bot.reply_to(message, f"💳 **HESAP DURUMU**\n\n💰 Mevcut Bakiye: **{para}** Para")

@bot.message_handler(commands=['gunluk'])
def daily_bonus(message):
    user_id = str(message.from_user.id)
    now = time.time()
    
    if user_id not in users:
        users[user_id] = {"balance": 0, "last_daily": 0}

    last_claim = users[user_id].get("last_daily", 0)
    
    if now - last_claim > 86400: # 24 Saat
        bonus = random.randint(500, 2000)
        users[user_id]["balance"] += bonus
        users[user_id]["last_daily"] = now
        save_db(users)
        bot.reply_to(message, f"📅 **Günlük Bonus!**\n\nBugünkü nasibin: **+{bonus} Para** eklendi.")
    else:
        kalan_saat = int((86400 - (now - last_claim)) / 3600)
        bot.reply_to(message, f"⏳ Daha zaman dolmadı kral. **{kalan_saat} saat** sonra tekrar gel.")

# --- OYUN MEKANİKLERİ ---

@bot.message_handler(commands=['zar'])
def play_dice(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Kullanım: `/zar [miktar]`")
            return

        bet = int(args[1])
        user_id = message.from_user.id
        current_bal = get_balance(user_id)

        if bet <= 0:
            bot.reply_to(message, "Pozitif bir sayı girmelisin.")
            return
        if bet > current_bal:
            bot.reply_to(message, "💸 Paran yetmiyor! Bakiye yetersiz.")
            return

        # Oyun
        user_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        
        msg = f"🎲 **ZAR DÜELLOSU** 🎲\n\n👤 Senin Zarın: **{user_roll}**\n🤖 Lucius'un Zarı: **{bot_roll}**\n"

        if user_roll > bot_roll:
            update_balance(user_id, bet)
            msg += f"\n✅ **KAZANDIN!** +{bet} para hesabına eklendi."
        elif bot_roll > user_roll:
            update_balance(user_id, -bet)
            msg += f"\n❌ **KAYBETTİN!** -{bet} para gitti."
        else:
            msg += f"\n🤝 **BERABERE!** Ortada kaldık, para iade."

        bot.reply_to(message, msg)

    except ValueError:
        bot.reply_to(message, "Lütfen geçerli bir sayı gir.")

@bot.message_handler(commands=['slot'])
def play_slot(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Kullanım: `/slot [miktar]`")
            return

        bet = int(args[1])
        user_id = message.from_user.id
        current_bal = get_balance(user_id)

        if bet <= 0 or bet > current_bal:
            bot.reply_to(message, "Geçersiz miktar veya yetersiz bakiye.")
            return

        symbols = ["🍒", "🍋", "🍇", "💎", "7️⃣", "🔔"]
        result = [random.choice(symbols) for _ in range(3)]
        
        # Animasyon Mesajı
        sent_msg = bot.send_message(message.chat.id, "🎰 **Slotlar Dönüyor...** 🎰")
        time.sleep(1.5) # Heyecan efekti
        
        final_text = f"🎰 | {result[0]} | {result[1]} | {result[2]} | 🎰"
        
        # Kazanma Mantığı
        win_amount = 0
        status = ""
        
        if result[0] == result[1] == result[2]:
            win_amount = bet * 10
            status = f"\n🚨 **JACKPOT!** 🚨 Paranı 10'a katladın! (+{win_amount})"
            update_balance(user_id, win_amount) # Bahis zaten cepte, üzerine ekle
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            win_amount = bet * 2
            status = f"\n🎉 **İkili Tutturdun!** Paranı 2'ye katladın! (+{win_amount})"
            update_balance(user_id, win_amount)
        else:
            status = f"\n📉 **Kaybettin.** -{bet} para."
            update_balance(user_id, -bet)
            
        bot.edit_message_text(chat_id=message.chat.id, message_id=sent_msg.message_id, text=final_text + status)

    except ValueError:
        bot.reply_to(message, "Sayı gir sayı.")

@bot.message_handler(commands=['rusruleti'])
def play_russian_roulette(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Kullanım: `/rusruleti [miktar]`")
            return

        bet = int(args[1])
        user_id = message.from_user.id
        current_bal = get_balance(user_id)

        if bet > current_bal:
            bot.reply_to(message, "Cesaretin var ama paran yok.")
            return

        bot.send_message(message.chat.id, "🔫 Silahı doldurdum... Topu çevirdim... Tetiği çekiyorum...")
        time.sleep(2)

        bullet = random.randint(1, 6)
        
        if bullet == 1:
            # BAM - Ölüm
            # Kullanıcı bahsi kaybeder, üstüne bakiyesinin yarısı silinir (Ceza)
            loss = bet
            update_balance(user_id, -loss)
            bot.reply_to(message, "💥 **BAM!** Kafana sıktın.\nMasadaki parayı kaybettin.")
        else:
            # Yaşam - Ödül
            win = int(bet * 1.5)
            update_balance(user_id, win)
            bot.reply_to(message, f"💨 **Tık...** Şanslısın, silah patlamadı.\nCesaret ödülü: **+{win} para** kazandın.")

    except ValueError:
        bot.reply_to(message, "Hata yaptın.")

@bot.message_handler(commands=['transfer'])
def transfer_money(message):
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "Kime para göndereceksin? Mesajını yanıtla.")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Kullanım: `/transfer [miktar]`")
            return
            
        amount = int(args[1])
        sender_id = message.from_user.id
        receiver_id = message.reply_to_message.from_user.id
        
        if sender_id == receiver_id:
            bot.reply_to(message, "Kendine para gönderemezsin manyak.")
            return
            
        sender_bal = get_balance(sender_id)
        
        if amount <= 0:
            bot.reply_to(message, "Pozitif bir sayı gir.")
            return
        if amount > sender_bal:
            bot.reply_to(message, "Olmayan parayı gönderemezsin.")
            return
            
        # İşlem
        update_balance(sender_id, -amount)
        update_balance(receiver_id, amount)
        
        bot.reply_to(message, f"💸 **Transfer Başarılı!**\n\nGönderen: Sen\nAlıcı: {message.reply_to_message.from_user.first_name}\nMiktar: {amount}")

    except ValueError:
        bot.reply_to(message, "Miktarı düzgün yaz.")

# --- ADMIN KOMUTLARI (MANUEL LISTE KONTROLLU) ---

@bot.message_handler(commands=['ceza'])
def admin_ceza(message):
    # ID Listesi Kontrolü
    if message.from_user.id not in ADMIN_LIST:
        bot.reply_to(message, "bu komutu kullanma etgin yok yarram")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "Kime ceza keseceksin? Mesajını yanıtla.")
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Miktar gir: `/ceza [miktar]`")
            return
            
        amount = int(args[1])
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
        
        current_bal = get_balance(target_id)
        # Eksiye düşmeme garantisi (max(0, ...))
        new_bal = max(0, current_bal - amount)
        
        set_balance(target_id, new_bal)
        
        bot.send_message(message.chat.id, f"🚨 **CEZA KESİLDİ!**\n\n👤 **Kişi:** {target_name}\n🔻 **Kesilen:** {amount}\n💰 **Kalan Bakiye:** {new_bal}")
        
    except ValueError:
        bot.reply_to(message, "Sayı gir.")

@bot.message_handler(commands=['paraver'])
def admin_give(message):
    # ID Listesi Kontrolü
    if message.from_user.id not in ADMIN_LIST:
        bot.reply_to(message, "bu komutu kullanma etgin yok yarram")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "Kime para vereceksin? Mesajını yanıtla.")
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Miktar gir: `/paraver [miktar]`")
            return
            
        amount = int(args[1])
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
        
        update_balance(target_id, amount)
        
        bot.send_message(message.chat.id, f"💵 **PARA YATIRILDI**\n\n👤 **Kişi:** {target_name}\n➕ **Yatırılan:** {amount}\n💰 **Yeni Bakiye:** {get_balance(target_id)}")
        
    except ValueError:
        bot.reply_to(message, "Sayı gir.")

# --- BAŞLAT ---
bot.polling()



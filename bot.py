
# --- 2. AYARLAR ---
# Token ve ID'ni buraya tırnak içinde yazmayı unutma!

import os
import random
import time
import threading
import asyncio
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- 1. RENDER KAPANMAMA SİSTEMİ (KEEP-ALIVE) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Lucius Casino System is Active")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- 2. AYARLAR ---
TOKEN = "8574466093:AAF6MnSQGePYvi1PefAyBk7F8z34Ptjrv6M"
ADMIN_IDS = [7795343194] # Kendi sayısal ID'ni buraya yaz (ID'ni öğrenmek için @userinfobot'a yazabilirsin)
DB_FILE = "users.json" # Verilerin tutulacağı dosya

# --- 3. VERİTABANI YÖNETİMİ (AUTO-SAVE) ---
user_data = {}

def load_db():
    global user_data
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            # JSON'dan gelen string keyleri int'e çeviriyoruz
            data = json.load(f)
            user_data = {int(k): v for k, v in data.items()}
            print("✅ Veritabanı yüklendi.")
    except FileNotFoundError:
        print("⚠️ Veritabanı yok, yeni oluşturuluyor.")
        user_data = {}

def save_db():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Kayıt hatası: {e}")

def get_user(user_id, name="Oyuncu"):
    if user_id not in user_data:
        user_data[user_id] = {"bakiye": 10000, "last_bonus": 0, "name": name}
        save_db()
    return user_data[user_id]

def check_funds(user_id, miktar):
    user = get_user(user_id)
    if miktar <= 0 or miktar > user["bakiye"]: return False
    return True

# --- 4. ANA MENÜ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Kullanıcıyı sisteme kaydet
    get_user(update.effective_user.id, update.effective_user.first_name)
    
    menu = (
        "**Ｃ Ａ Ｓ Ｉ Ｎ Ｏ  #Lucius**\n\n"
        "👑 **HESAP İŞLEMLERİ**\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "💳 /bakiye  →  Cüzdan durumu\n\n"
        "🎁 /bonus   →  Günlük 25.000 TL harçlık\n\n"
        "💸 /borc <miktar> → Yanıtladığın kişiye para at\n\n"
        "🏆 /top     →  En zengin 10 kişi\n\n\n"
        "🎲 **OYUNLAR**\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "🎰 /slot <miktar> <renk> → (kirmizi/siyah/yesil)\n\n"
        "🎲 /zar <miktar>  →  Zar at (Animasyonlu)\n\n"
        "🎡 /rulet <miktar> <renk> → Klasik Rulet\n\n"
        "🃏 /bj <miktar>   →  Blackjack (Butonlu)\n\n"
        "💣 /mayin <miktar> → Mayın Tarlası (Butonlu)\n\n"
        "🔥 /risk <miktar>  →  Ya hep ya hiç (%50)\n\n"
        "🎡 /cark <miktar>  →  Şans Çarkı\n\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "💰 *Başlangıç: 10.000 TL* | 📅 *Bonus: 24 Saatte 1*"
    )
    await update.message.reply_text(menu, parse_mode="Markdown")

# --- 5. HESAP KOMUTLARI ---
async def bakiye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"💰 **Mevcut Bakiyeniz:** {user['bakiye']:,} TL", parse_mode="Markdown")

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if time.time() - user["last_bonus"] < 86400:
        kalan = int((86400 - (time.time() - user["last_bonus"])) / 3600)
        return await update.message.reply_text(f"❌ Henüz zamanı gelmedi! {kalan} saat sonra gel.")
    user["bakiye"] += 25000
    user["last_bonus"] = time.time()
    save_db()
    await update.message.reply_text("✅ **25.000 TL** günlük harçlık hesabına eklendi!", parse_mode="Markdown")

async def borc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ Para göndermek için bir mesajı yanıtlamalısın!")
    try:
        miktar = int(context.args[0])
        gonderen = get_user(update.effective_user.id)
        alici_id = update.message.reply_to_message.from_user.id
        alici_isim = update.message.reply_to_message.from_user.first_name
        
        if not check_funds(update.effective_user.id, miktar):
            return await update.message.reply_text("❌ Yetersiz bakiye!")
        
        gonderen["bakiye"] -= miktar
        get_user(alici_id, alici_isim)["bakiye"] += miktar
        save_db()
        await update.message.reply_text(f"✅ **{alici_isim}** kişisine {miktar:,} TL gönderildi.", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Hata! Kullanım: /borc <miktar>")

async def top_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['bakiye'], reverse=True)[:10]
    txt = "🏆 **LUCIUS ZENGİNLER LİSTESİ**\n➖➖➖➖➖➖➖➖➖➖\n"
    for i, (uid, d) in enumerate(sorted_users, 1):
        txt += f"**{i}.** {d['name']} ➔ {d['bakiye']:,} TL\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

# --- 6. OYUNLAR (LOGIC & ANIMATION) ---

async def slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        secim = context.args[1].lower()
        if not check_funds(update.effective_user.id, miktar):
            return await update.message.reply_text("❌ Bakiye yetersiz!")

        msg = await update.message.reply_dice(emoji="🎰")
        await asyncio.sleep(3.5)

        renk = random.choices(["kirmizi", "siyah", "yesil"], weights=[48, 48, 4])[0]
        
        if secim == renk:
            carpan = 10 if renk == "yesil" else 2
            kazanc = (miktar * carpan) - miktar
            user["bakiye"] += kazanc
            await update.message.reply_text(f"🎰 Slot **{renk.upper()}** geldi!\n🔥 **KAZANDIN!** +{kazanc + miktar:,} TL", parse_mode="Markdown")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"🎰 Slot **{renk.upper()}** geldi.\n💀 **KAYBETTİN!** -{miktar:,} TL", parse_mode="Markdown")
        save_db()
    except:
        await update.message.reply_text("⚠️ Kullanım: /slot <miktar> <kirmizi/siyah/yesil>")

async def zar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if not check_funds(update.effective_user.id, miktar):
            return await update.message.reply_text("❌ Bakiye yetersiz!")

        msg = await update.message.reply_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        
        val = msg.dice.value
        if val >= 4:
            user["bakiye"] += miktar
            await update.message.reply_text(f"🎲 Zar **{val}** geldi.\n✅ **KAZANDIN!** +{miktar:,} TL", parse_mode="Markdown")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"🎲 Zar **{val}** geldi.\n❌ **KAYBETTİN!** -{miktar:,} TL", parse_mode="Markdown")
        save_db()
    except: pass

async def rulet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        secim = context.args[1].lower()
        if not check_funds(update.effective_user.id, miktar): return await update.message.reply_text("❌ Paran yok!")

        renk = random.choices(["kirmizi", "siyah", "yesil"], weights=[48, 48, 4])[0]
        if secim == renk:
            carpan = 14 if renk == "yesil" else 2
            odul = miktar * carpan
            user["bakiye"] += (odul - miktar)
            await update.message.reply_text(f"🎡 Top **{renk.upper()}** renginde durdu!\n🤑 **TEBRİKLER!** {odul:,} TL kazandın.", parse_mode="Markdown")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"🎡 Top **{renk.upper()}** renginde durdu.\n💀 Kaybettin.", parse_mode="Markdown")
        save_db()
    except: await update.message.reply_text("⚠️ Kullanım: /rulet <miktar> <kirmizi/siyah/yesil>")

async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if not check_funds(update.effective_user.id, miktar): return await update.message.reply_text("❌ Para yok!")

        if random.random() < 0.5:
            user["bakiye"] += miktar
            await update.message.reply_text(f"🔥 **RİSK BAŞARILI!** Paranı ikiye katladın. (+{miktar:,} TL)", parse_mode="Markdown")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text("💀 **RİSK BAŞARISIZ.** Paranı kaybettin.", parse_mode="Markdown")
        save_db()
    except: pass

async def cark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if not check_funds(update.effective_user.id, miktar): return await update.message.reply_text("❌ Para yok!")

        oran = random.choice([0, 0.5, 1.5, 2, 3])
        kazanc = int(miktar * oran)
        user["bakiye"] = (user["bakiye"] - miktar) + kazanc
        
        if oran < 1:
            await update.message.reply_text(f"🎡 Çark **x{oran}** geldi. Kaybettin. Yeni Bakiye: {user['bakiye']:,} TL")
        else:
            await update.message.reply_text(f"🎡 Çark **x{oran}** geldi! Kazandın! Yeni Bakiye: {user['bakiye']:,} TL")
        save_db()
    except: pass

# --- 7. BUTONLU OYUNLAR (BLACKJACK & MAYIN) ---

async def bj_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        miktar = int(context.args[0])
        if not check_funds(update.effective_user.id, miktar): return await update.message.reply_text("❌ Paran yetersiz!")
        
        puan = random.randint(10, 19)
        keyboard = [[InlineKeyboardButton("🃏 Kart Çek", callback_data=f"bj_h_{miktar}_{puan}"),
                     InlineKeyboardButton("✋ Dur", callback_data=f"bj_s_{miktar}_{puan}")]]
        
        await update.message.reply_text(f"🃏 **BLACKJACK**\nBahis: {miktar:,} TL\nSenin Puanın: **{puan}**\n\nNe yapacaksın?", 
                                       reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except: await update.message.reply_text("⚠️ Kullanım: /bj <miktar>")

async def mayin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        miktar = int(context.args[0])
        if not check_funds(update.effective_user.id, miktar): return await update.message.reply_text("❌ Paran yetersiz!")
        
        keyboard = []
        for r in range(3):
            row = []
            for c in range(3):
                row.append(InlineKeyboardButton("📦", callback_data=f"m_{miktar}_{r}{c}"))
            keyboard.append(row)
            
        await update.message.reply_text(f"💣 **MAYIN TARLASI**\nBahis: {miktar:,} TL\nBir kutu seç ve şansını dene!", 
                                       reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except: await update.message.reply_text("⚠️ Kullanım: /mayin <miktar>")

# --- 8. BUTON İŞLEYİCİ ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = get_user(query.from_user.id)
    data = query.data.split("_")
    
    await query.answer()
    
    # BLACKJACK
    if data[0] == "bj":
        action, miktar, puan = data[1], int(data[2]), int(data[3])
        
        if action == "s": # Dur
            kasa = random.randint(17, 23)
            if kasa > 21:
                user["bakiye"] += miktar
                sonuc = f"✅ **KAZANDIN!**\nSen: {puan} | Kasa: {kasa} (Patladı)"
            elif puan > kasa:
                user["bakiye"] += miktar
                sonuc = f"✅ **KAZANDIN!**\nSen: {puan} | Kasa: {kasa}"
            elif puan == kasa:
                sonuc = f"🤝 **BERABERE!** Para iade.\nSen: {puan} | Kasa: {kasa}"
            else:
                user["bakiye"] -= miktar
                sonuc = f"💀 **KAYBETTİN!**\nSen: {puan} | Kasa: {kasa}"
            await query.edit_message_text(sonuc, parse_mode="Markdown")

        elif action == "h": # Çek
            puan += random.randint(1, 10)
            if puan > 21:
                user["bakiye"] -= miktar
                await query.edit_message_text(f"💥 **PATLADIN!**\nPuanın: {puan}. Kaybettin.", parse_mode="Markdown")
            else:
                kb = [[InlineKeyboardButton("🃏 Kart Çek", callback_data=f"bj_h_{miktar}_{puan}"),
                       InlineKeyboardButton("✋ Dur", callback_data=f"bj_s_{miktar}_{puan}")]]
                await query.edit_message_text(f"🃏 Puanın: **{puan}**. Devam mı?", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    # MAYIN
    if data[0] == "m":
        miktar = int(data[1])
        if random.random() < 0.30:
            user["bakiye"] -= miktar
            await query.edit_message_text(f"💣 **BOOOM!** Mayına bastın.\nKaybedilen: -{miktar:,} TL", parse_mode="Markdown")
        else:
            kazanc = int(miktar * 0.5)
            user["bakiye"] += kazanc
            await query.edit_message_text(f"💎 **ELMAS!** Kutuda elmas vardı.\nKazanç: +{kazanc:,} TL", parse_mode="Markdown")
            
    save_db() # Her buton işleminden sonra kaydet

# --- 9. ADMIN KOMUTLARI (DÜZELTİLDİ + ÖZEL MESAJ EKLENDİ) ---
async def banka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Yetki Kontrolü
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("bu komutu kullanma etgin yok yarram")
    
    try:
        miktar = int(context.args[0])
        get_user(update.effective_user.id)["bakiye"] += miktar
        save_db()
        await update.message.reply_text(f"🏦 Kasa Güncellendi: +{miktar:,} TL")
    except: pass

async def ceza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Yetki Kontrolü
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("bu komutu kullanma etgin yok yarram")
    
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ Kime ceza keseceğini yanıtlayarak seç!")

    try:
        miktar = int(context.args[0])
        target_id = update.message.reply_to_message.from_user.id
        target_name = update.message.reply_to_message.from_user.first_name
        
        # Hedef kullanıcıyı veritabanından çek (yoksa oluşturur)
        target_user = get_user(target_id, target_name)
        target_user["bakiye"] -= miktar
        save_db()
        
        await update.message.reply_text(f"⚖️ **{target_name}** kişisine {miktar:,} TL ceza kesildi.\nKalan Bakiye: {target_user['bakiye']:,} TL", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("⚠️ Hata oluştu. Kullanım: /ceza <miktar>")

# --- 10. ANA ÇALIŞTIRMA ---
def main():
    load_db() # Başlangıçta verileri yükle
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    
    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bakiye", bakiye))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("borc", borc))
    app.add_handler(CommandHandler("top", top_list))
    
    app.add_handler(CommandHandler("slot", slot))
    app.add_handler(CommandHandler("zar", zar))
    app.add_handler(CommandHandler("rulet", rulet))
    app.add_handler(CommandHandler("risk", risk))
    app.add_handler(CommandHandler("cark", cark))
    app.add_handler(CommandHandler("bj", bj_start))
    app.add_handler(CommandHandler("mayin", mayin_start))
    
    # Admin
    app.add_handler(CommandHandler("banka", banka))
    app.add_handler(CommandHandler("ceza", ceza))
    
    app.add_handler(CallbackQueryHandler(handle_buttons))
    
    print("Lucius Casino Aktif...")
    app.run_polling()

if __name__ == "__main__":
    main()

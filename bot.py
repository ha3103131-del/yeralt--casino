import logging
import random
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- AYARLAR ---
TOKEN = 
ADMIN_IDS =  # Kendi sayısal ID'ni buraya yaz (ID'ni öğrenmek için @userinfobot'a yazabilirsin)


import os
import random
import time
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- RENDER KEEP-ALIVE ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Casino Lucius is Active!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- AYARLAR ---
TOKEN = "8574466093:AAF6MnSQGePYvi1PefAyBk7F8z34Ptjrv6M"
ADMIN_IDS = [7795343194, 6126663392] # Kendi ID'ni gir

user_data = {}

def get_user(user_id, name="Bilinmiyor"):
    if user_id not in user_data:
        user_data[user_id] = {"bakiye": 10000, "last_bonus": 0, "name": name}
    return user_data[user_id]

# --- ANA MENÜ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = (
        "**Ｃ Ａ Ｓ Ｉ Ｎ Ｏ  #Lucius**\n\n"
        "**Hesap:**\n"
        "/bakiye  →  Cüzdan durumu\n\n"
        "/bonus  →  Günlük 25.000 TL harçlık (24 saatte 1)\n\n"
        "/borc <miktar>  →  Yanıtladığın kişiye borç gönder\n\n"
        "/top  →  En zengin 10 kişi\n\n\n"
        "**Oyunlar (%50-%50 dengeli + hafif avantaj):**\n"
        "/slot <miktar> <renk>  →  Slot (🎰) (kirmizi/siyah/yesil)\n\n"
        "/zar <miktar>  →  Zar at (🎲)\n\n"
        "/rulet <miktar> <renk>  →  Rulet (kirmizi/siyah/yesil)\n\n"
        "/blackjack <miktar>  →  Blackjack\n\n"
        "/mayin <miktar>  →  Mayın tarlası\n\n"
        "/risk <miktar>  →  Ya hep ya hiç (%50)\n\n"
        "/cark <miktar>  →  Şans çarkı\n\n"
        "Başlangıç bakiyesi: 10.000 TL\n"
        "Günlük bonus: 25.000 TL"
    )
    await update.message.reply_text(menu, parse_mode="Markdown")

# --- ANIMASYONLU OYUNLAR ---

async def slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    try:
        miktar = int(context.args[0])
        secilen_renk = context.args[1].lower()
        if miktar > user["bakiye"] or miktar <= 0: return await update.message.reply_text("❌ Yetersiz bakiye!")
        
        # Animasyonlu Slot
        msg = await update.message.reply_dice(emoji="🎰")
        await asyncio.sleep(4) # Animasyonun bitmesini bekle
        
        # Basit bir renk/kazanç algoritması
        renkler = ["kirmizi", "siyah", "yesil"]
        kazanan_renk = random.choices(renkler, weights=[45, 45, 10])[0]
        
        if secilen_renk == kazanan_renk:
            carpan = 10 if kazanan_renk == "yesil" else 2
            user["bakiye"] += (miktar * carpan) - miktar
            await update.message.reply_text(f"🎰 Slot Durdu! Renk: {kazanan_renk}\n🔥 KAZANDIN! Yeni bakiye: {user['bakiye']:,} TL")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"🎰 Slot Durdu! Renk: {kazanan_renk}\n💀 KAYBETTİN!")
    except: await update.message.reply_text("Kullanım: /slot <miktar> <kirmizi/siyah/yesil>")

async def zar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    try:
        miktar = int(context.args[0])
        if miktar > user["bakiye"]: return
        
        msg = await update.message.reply_dice(emoji="🎲")
        deger = msg.dice.value
        await asyncio.sleep(4)
        
        if deger >= 4:
            user["bakiye"] += miktar
            await update.message.reply_text(f"🎲 Zar: {deger} Geldi! KAZANDIN!")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"🎲 Zar: {deger} Geldi! KAYBETTİN!")
    except: pass

# --- DİĞER TÜM OYUNLAR ---

async def blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if random.random() < 0.48: # Hafif kasa avantajı
            user["bakiye"] += miktar
            await update.message.reply_text(f"🃏 21 yaptın! +{miktar:,} TL")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text("🃏 Kasa kazandı. -TL")
    except: pass

async def mayin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if random.random() < 0.60:
            user["bakiye"] += int(miktar * 0.5)
            await update.message.reply_text("💣 Güvenli bölge! Kazandın.")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text("💣 PATLADIN!")
    except: pass

async def cark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        carpan = random.choice([0, 0.5, 2, 5])
        user["bakiye"] = (user["bakiye"] - miktar) + (miktar * carpan)
        await update.message.reply_text(f"🎡 Çark döndü: x{carpan}! Bakiyen: {user['bakiye']:,}")
    except: pass

# --- ADMIN & HESAP ---
async def bakiye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"💰 Bakiyeniz: {user['bakiye']:,} TL")

async def banka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    get_user(update.effective_user.id)["bakiye"] += int(context.args[0])
    await update.message.reply_text("🏦 Para eklendi patron.")

# --- MAIN ---
def main():
    threading.Thread(target=run_health_check_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bakiye", bakiye))
    app.add_handler(CommandHandler("slot", slot))
    app.add_handler(CommandHandler("zar", zar))
    app.add_handler(CommandHandler("blackjack", blackjack))
    app.add_handler(CommandHandler("mayin", mayin))
    app.add_handler(CommandHandler("cark", cark))
    app.add_handler(CommandHandler("banka", banka))
    
    app.run_polling()

if __name__ == "__main__":
    main()

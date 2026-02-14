import logging
import random
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- AYARLAR ---
TOKEN = "8574466093:AAF6MnSQGePYvi1PefAyBk7F8z34Ptjrv6M"
ADMIN_IDS = [7795343194, 6126663392] # Kendi sayısal ID'ni buraya yaz (ID'ni öğrenmek için @userinfobot'a yazabilirsin)

user_data = {}

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"bakiye": 10000, "last_bonus": 0}
    return user_data[user_id]

# --- MENÜ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = (
        "**Ｃ Ａ Ｓ Ｉ Ｎ Ｏ  #Lucius**\n\n"
        "**Hesap:**\n"
        "/bakiye  →  Cüzdan durumu\n\n"
        "/bonus  →  Günlük 25.000 TL harçlık (24 saatte 1)\n\n"
        "/borc <miktar>  →  Yanıtladığın kişiye borç (para) gönder\n\n"
        "/top  →  En zengin 10 kişi\n\n\n"
        "**Oyunlar (%50-%50 dengeli + hafif avantaj):**\n"
        "/slot <miktar>  →  Slot makinesi (🎰)\n\n"
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

# --- OYUN FONKSİYONLARI ---

async def slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if miktar > user["bakiye"] or miktar <= 0: return await update.message.reply_text("❌ Yetersiz bakiye!")
        
        items = ["🍒", "🍋", "🔔", "💎", "🎰"]
        res = [random.choice(items) for _ in range(3)]
        msg = f"| {' | '.join(res)} |\n\n"
        
        if res[0] == res[1] == res[2]:
            kazanc = miktar * 10
            user["bakiye"] += kazanc
            await update.message.reply_text(f"{msg}🔥 EFSANE! 3'te 3 yaptın! +{kazanc:,} TL")
        elif res[0] == res[1] or res[1] == res[2] or res[0] == res[2]:
            kazanc = int(miktar * 1.5)
            user["bakiye"] += kazanc
            await update.message.reply_text(f"{msg}✨ Güzel! 2'li yakaladın. +{kazanc:,} TL")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"{msg}💀 Kaybettin! -{miktar:,} TL")
    except: await update.message.reply_text("Kullanım: /slot <miktar>")

async def zar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if miktar > user["bakiye"]: return
        bot_zar = random.randint(1, 6)
        senin_zar = random.randint(1, 6)
        
        msg = f"🎲 Senin Zarın: {senin_zar}\n🎲 Botun Zarı: {bot_zar}\n\n"
        if senin_zar > bot_zar:
            user["bakiye"] += miktar
            await update.message.reply_text(f"{msg}✅ Kazandın!")
        elif senin_zar < bot_zar:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"{msg}❌ Kaybettin!")
        else:
            await update.message.reply_text(f"{msg}🤝 Berabere, para iade.")
    except: pass

async def rulet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        secim = context.args[1].lower()
        renkler = ["kirmizi"] * 18 + ["siyah"] * 18 + ["yesil"] * 1
        sonuc = random.choice(renkler)
        
        if sonuc == secim:
            carpan = 14 if sonuc == "yesil" else 2
            user["bakiye"] += miktar * (carpan - 1)
            await update.message.reply_text(f"🎡 Top {sonuc} üzerinde durdu! Kazandın! +{miktar*carpan:,} TL")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"🎡 Top {sonuc} geldi. Kaybettin!")
    except: await update.message.reply_text("Kullanım: /rulet <miktar> <kirmizi/siyah/yesil>")

async def blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Basit şans simülasyonu
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if miktar > user["bakiye"]: return
        if random.random() < 0.45: # %45 kazanma şansı
            user["bakiye"] += miktar
            await update.message.reply_text(f"🃏 Blackjack! Kazandın! +{miktar:,} TL")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"🃏 Bot 21 yaptı! Kaybettin.")
    except: pass

async def mayin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if random.random() < 0.5:
            user["bakiye"] += miktar
            await update.message.reply_text(f"💣 Mayına basmadın! Güvendesin. +{miktar:,} TL")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text("💣 GÜÜÜM! Mayına bastın.")
    except: pass

async def cark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        carpan = random.choice([0, 0.5, 1.2, 1.5, 2, 5])
        kazanc = int(miktar * carpan)
        user["bakiye"] = (user["bakiye"] - miktar) + kazanc
        await update.message.reply_text(f"🎡 Çark döndü: x{carpan} çıktı! Yeni bakiye: {user['bakiye']:,} TL")
    except: pass

# --- DİĞER KOMUTLAR ---
async def bakiye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    await update.message.reply_text(f"💰 Mevcut Bakiyeniz: {user['bakiye']:,} TL")

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    now = time.time()
    if now - user["last_bonus"] < 86400:
        await update.message.reply_text("❌ Bugünlük bonusunu almışsın.")
        return
    user["bakiye"] += 25000
    user["last_bonus"] = now
    await update.message.reply_text("✅ 25.000 TL eklendi!")

# --- ADMIN (MENÜDE GİZLİ) ---
async def banka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    try:
        miktar = int(context.args[0])
        get_user(update.effective_user.id)["bakiye"] += miktar
        await update.message.reply_text(f"✅ Hesabına {miktar:,} TL eklendi Patron.")
    except: pass

async def ceza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not update.message.reply_to_message: return
    try:
        miktar = int(context.args[0])
        target = update.message.reply_to_message.from_user.id
        get_user(target)["bakiye"] -= miktar
        await update.message.reply_text(f"❌ {miktar:,} TL ceza kesildi.")
    except: pass

# --- RUN ---
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bakiye", bakiye))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("slot", slot))
    app.add_handler(CommandHandler("zar", zar))
    app.add_handler(CommandHandler("rulet", rulet))
    app.add_handler(CommandHandler("blackjack", blackjack))
    app.add_handler(CommandHandler("mayin", mayin))
    app.add_handler(CommandHandler("cark", cark))
    app.add_handler(CommandHandler("banka", banka))
    app.add_handler(CommandHandler("ceza", ceza))
    app.run_polling()

if __name__ == "__main__":
    main()

import os
import random
import time
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- RENDER KEEP-ALIVE (Kesintisiz Çalışma) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Lucius Casino V3 Final is LIVE")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- AYARLAR ---
TOKEN = "8574466093:AAF6MnSQGePYvi1PefAyBk7F8z34Ptjrv6M"
ADMIN_IDS = [7795343194] # Kendi sayısal ID'ni buraya yaz (ID'ni öğrenmek için @userinfobot'a yazabilirsin)

user_data = {}

def get_user(user_id, name="Oyuncu"):
    if user_id not in user_data:
        user_data[user_id] = {"bakiye": 10000, "last_bonus": 0, "name": name}
    return user_data[user_id]

def check_funds(user_id, miktar):
    user = get_user(user_id)
    if miktar <= 0 or miktar > user["bakiye"]: return False
    return True

# --- GÖRSEL MENÜ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = (
        "**Ｃ Ａ Ｓ Ｉ Ｎ Ｏ  #Lucius**\n\n"
        "✨ **HESAP İŞLEMLERİ**\n"
        "━━━━━━━━━━━━━━\n"
        "💳 /bakiye  →  Cüzdan durumu\n\n"
        "🎁 /bonus   →  Günlük 25.000 TL harçlık\n\n"
        "💸 /borc <miktar> → Yanıtladığın kişiye gönder\n\n"
        "🏆 /top     →  En zengin 10 kişi\n\n\n"
        "🎲 **ŞANS OYUNLARI**\n"
        "━━━━━━━━━━━━━━\n"
        "🎰 /slot <miktar> <renk> → (kirmizi/siyah/yesil)\n\n"
        "🎲 /zar <miktar>  →  Zar at ve kazan\n\n"
        "🎡 /rulet <miktar> <renk> → Klasik Rulet\n\n"
        "🃏 /bj <miktar>   →  Blackjack (Interaktif)\n\n"
        "💣 /mayin <miktar> → Mayın Tarlası (Kareli)\n\n"
        "🔥 /risk <miktar>  →  Ya hep ya hiç (%50)\n\n"
        "🎡 /cark <miktar>  →  Şans çarkını çevir\n\n\n"
        "💰 *Başlangıç: 10.000 TL* | 📅 *Bonus: 24 Saatte 1*"
    )
    await update.message.reply_text(menu, parse_mode="Markdown")

# --- HESAP KOMUTLARI ---
async def bakiye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"💰 **Cüzdanın:** {user['bakiye']:,} TL")

async def top_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['bakiye'], reverse=True)[:10]
    txt = "🏆 **LUCIUS ZENGİNLER LİSTESİ**\n━━━━━━━━━━━━━━\n"
    for i, (uid, d) in enumerate(sorted_users, 1):
        txt += f"{i}. {d['name']} ➔ {d['bakiye']:,} TL\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

# --- OYUNLAR (GÜVENLİ & ANIMASYONLU) ---
async def slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar, secim = int(context.args[0]), context.args[1].lower()
        if not check_funds(update.effective_user.id, miktar):
            return await update.message.reply_text("❌ Paran yetersiz!")
        msg = await update.message.reply_dice(emoji="🎰")
        await asyncio.sleep(4)
        renk = random.choice(["kirmizi", "siyah", "yesil"])
        if secim == renk:
            carpan = 10 if renk == "yesil" else 2
            user["bakiye"] += (miktar * carpan) - miktar
            await update.message.reply_text(f"🎰 **{renk.upper()}** geldi! Kazandın: +{miktar*carpan:,} TL")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"🎰 **{renk.upper()}** geldi. Kaybettin!")
    except: pass

async def bj_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if not check_funds(update.effective_user.id, miktar): return
        puan = random.randint(12, 19)
        kb = [[InlineKeyboardButton("🃏 Kart Çek", callback_data=f"bj_h_{miktar}_{puan}"),
               InlineKeyboardButton("✋ Dur", callback_data=f"bj_s_{miktar}_{puan}")]]
        await update.message.reply_text(f"🃏 **Blackjack**\nPuanın: {puan}\n\nHamlen?", reply_markup=InlineKeyboardMarkup(kb))
    except: pass

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    u = get_user(q.from_user.id)
    d = q.data.split("_")
    await q.answer()
    if d[0] == "bj":
        act, miktar, puan = d[1], int(d[2]), int(d[3])
        if act == "s":
            kasa = random.randint(16, 23)
            if kasa > 21 or puan > kasa:
                u["bakiye"] += miktar
                await q.edit_message_text(f"✅ Kazandın! Sen: {puan} | Kasa: {kasa}")
            else:
                u["bakiye"] -= miktar
                await q.edit_message_text(f"💀 Kaybettin. Sen: {puan} | Kasa: {kasa}")
        else:
            puan += random.randint(2, 10)
            if puan > 21:
                u["bakiye"] -= miktar
                await q.edit_message_text(f"💥 PATLADIN! Puanın: {puan}. Kaybettin.")
            else:
                kb = [[InlineKeyboardButton("🃏 Kart Çek", callback_data=f"bj_h_{miktar}_{puan}"),
                       InlineKeyboardButton("✋ Dur", callback_data=f"bj_s_{miktar}_{puan}")]]
                await q.edit_message_text(f"🃏 Puanın: {puan}. Devam mı?", reply_markup=InlineKeyboardMarkup(kb))

# --- ADMIN ---
async def banka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        get_user(update.effective_user.id)["bakiye"] += int(context.args[0])
        await update.message.reply_text("🏦 Kasa güncellendi, Patron.")

# --- RUN ---
def main():
    threading.Thread(target=run_health_check_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bakiye", bakiye))
    app.add_handler(CommandHandler("top", top_list))
    app.add_handler(CommandHandler("slot", slot))
    app.add_handler(CommandHandler("bj", bj_start))
    app.add_handler(CommandHandler("banka", banka))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()

if __name__ == "__main__":
    main()

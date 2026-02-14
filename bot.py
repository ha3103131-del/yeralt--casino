import os
import random
import time
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- RENDER KEEP-ALIVE (Kapanmayı Önler) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Lucius Casino V2 Final is LIVE")

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

# --- ANA MENÜ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = (
        "**𝐂 𝐀 𝐒 𝐈̇ 𝐍 𝐎 𝖑𝖚𝖈𝖎𝖚𝖘**\n\n"
        "**Hesap:**\n"
        "/bakiye  →  Cüzdan durumu\n\n"
        "/bonus  →  Günlük 25.000 TL harçlık (24 saatte 1)\n\n"
        "/borc <miktar>  →  Yanıtladığın kişiye borç gönder\n\n"
        "/top  →  En zengin 10 kişi\n\n\n"
        "**Oyunlar (%50-%50 dengeli + hafif avantaj):**\n"
        "/slot <miktar> <renk>  →  Slot (🎰) (kirmizi/siyah/yesil)\n\n"
        "/zar <miktar>  →  Zar at (🎲)\n\n"
        "/rulet <miktar> <renk>  →  Rulet (kirmizi/siyah/yesil)\n\n"
        "/bj <miktar>  →  Blackjack (🃏)\n\n"
        "/mayin <miktar>  →  Mayın tarlası (💣)\n\n"
        "/risk <miktar>  →  Ya hep ya hiç (%50)\n\n"
        "/cark <miktar>  →  Şans çarkı\n\n"
        "Başlangıç bakiyesi: 10.000 TL\n"
        "Günlük bonus: 25.000 TL"
    )
    await update.message.reply_text(menu, parse_mode="Markdown")

# --- HESAP KOMUTLARI ---
async def bakiye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"💰 Mevcut Bakiyeniz: {user['bakiye']:,} TL")

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if time.time() - user["last_bonus"] < 86400:
        kalan = int((86400 - (time.time() - user["last_bonus"])) / 3600)
        return await update.message.reply_text(f"❌ Henüz zamanı gelmedi! {kalan} saat sonra gel.")
    user["bakiye"] += 25000
    user["last_bonus"] = time.time()
    await update.message.reply_text("✅ 25.000 TL bonus hesabına eklendi!")

async def borc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ Para göndermek için bir mesajı yanıtla!")
    try:
        miktar = int(context.args[0])
        user = get_user(update.effective_user.id)
        target = get_user(update.message.reply_to_message.from_user.id, update.message.reply_to_message.from_user.first_name)
        if miktar > user["bakiye"] or miktar <= 0: return await update.message.reply_text("❌ Yetersiz bakiye!")
        user["bakiye"] -= miktar
        target["bakiye"] += miktar
        await update.message.reply_text(f"✅ {target['name']} kişisine {miktar:,} TL gönderildi.")
    except: pass

async def top_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['bakiye'], reverse=True)[:10]
    txt = "🏆 **Zenginler Listesi**\n\n"
    for i, (uid, d) in enumerate(sorted_users, 1):
        txt += f"{i}. {d['name']} - {d['bakiye']:,} TL\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

# --- OYUNLAR ---
async def slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar, secim = int(context.args[0]), context.args[1].lower()
        if miktar > user["bakiye"]: return await update.message.reply_text("❌ Para yetersiz!")
        msg = await update.message.reply_dice(emoji="🎰")
        await asyncio.sleep(4)
        renk = random.choices(["kirmizi", "siyah", "yesil"], weights=[45, 45, 10])[0]
        if secim == renk:
            carpan = 10 if renk == "yesil" else 2
            user["bakiye"] += (miktar * carpan) - miktar
            await update.message.reply_text(f"🎰 Slot {renk} geldi! KAZANDIN! 🔥")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"🎰 Slot {renk} geldi. KAYBETTİN! 💀")
    except: await update.message.reply_text("Kullanım: /slot <miktar> <kirmizi/siyah/yesil>")

async def zar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if miktar > user["bakiye"]: return
        msg = await update.message.reply_dice(emoji="🎲")
        await asyncio.sleep(4)
        if msg.dice.value >= 4:
            user["bakiye"] += miktar
            await update.message.reply_text(f"🎲 {msg.dice.value} geldi, KAZANDIN! ✅")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"🎲 {msg.dice.value} geldi, KAYBETTİN! ❌")
    except: pass

async def rulet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar, secim = int(context.args[0]), context.args[1].lower()
        if miktar > user["bakiye"]: return
        renk = random.choice(["kirmizi", "siyah", "yesil"])
        if secim == renk:
            user["bakiye"] += miktar if renk != "yesil" else miktar*13
            await update.message.reply_text(f"🎡 Rulet döndü: {renk}! Kazandın! ✅")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text(f"🎡 Rulet döndü: {renk}. Kaybettin! 💀")
    except: pass

async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if random.random() < 0.5:
            user["bakiye"] += miktar
            await update.message.reply_text("🔥 Risk başarılı! Kasan katlandı.")
        else:
            user["bakiye"] -= miktar
            await update.message.reply_text("💀 Risk başarısız. Sıfırı tükettin.")
    except: pass

async def cark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        c = random.choice([0, 0.5, 1.2, 2, 5])
        user["bakiye"] = int((user["bakiye"] - miktar) + (miktar * c))
        await update.message.reply_text(f"🎡 Çark x{c} getirdi! Yeni bakiye: {user['bakiye']:,}")
    except: pass

# --- BUTONLU OYUNLAR (BJ & MAYIN) ---
async def bj_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if miktar > user["bakiye"]: return
        puan = random.randint(12, 19)
        kb = [[InlineKeyboardButton("🃏 Kart Çek", callback_data=f"bj_h_{miktar}_{puan}"),
               InlineKeyboardButton("✋ Dur", callback_data=f"bj_s_{miktar}_{puan}")]]
        await update.message.reply_text(f"🃏 **Blackjack**\nPuanın: {puan}\n\nNe yapacaksın?", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    except: pass

async def mayin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    try:
        miktar = int(context.args[0])
        if miktar > user["bakiye"]: return
        kb = []
        for i in range(3):
            row = [InlineKeyboardButton("⬛", callback_data=f"m_{miktar}_{r}") for r in range(3)]
            kb.append(row)
        await update.message.reply_text(f"💣 **Mayın Tarlası**\nBahis: {miktar}\nBir kare seç!", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    except: pass

# --- BUTON İŞLEYİCİ ---
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
            puan += random.randint(1, 10)
            if puan > 21:
                u["bakiye"] -= miktar
                await q.edit_message_text(f"💥 Patladın! Puanın: {puan}. Kaybettin.")
            else:
                kb = [[InlineKeyboardButton("🃏 Kart Çek", callback_data=f"bj_h_{miktar}_{puan}"), InlineKeyboardButton("✋ Dur", callback_data=f"bj_s_{miktar}_{puan}")]]
                await q.edit_message_text(f"🃏 Puanın: {puan}. Devam mı?", reply_markup=InlineKeyboardMarkup(kb))
    if d[0] == "m":
        m = int(d[1])
        if random.random() < 0.25:
            u["bakiye"] -= m
            await q.edit_message_text("💣 GÜÜÜM! Mayın patladı.")
        else:
            u["bakiye"] += int(m * 0.4)
            await q.edit_message_text(f"💎 Elması buldun! Kazancın eklendi.")

# --- ADMIN ---
async def banka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        get_user(update.effective_user.id)["bakiye"] += int(context.args[0])
        await update.message.reply_text("🏦 Para basıldı Patron.")

async def ceza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
        get_user(target)["bakiye"] -= int(context.args[0])
        await update.message.reply_text("⚖️ Ceza kesildi.")

# --- RUN ---
def main():
    threading.Thread(target=run_health_check_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
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
    app.add_handler(CommandHandler("banka", banka))
    app.add_handler(CommandHandler("ceza", ceza))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()

if __name__ == "__main__":
    main()

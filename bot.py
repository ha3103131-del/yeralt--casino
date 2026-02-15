import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import json
import random
import time
import os
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎰 UNDERGROUND FEDERATION CASINO BOT 🎰
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ⚙️ YAPILANDIRMA
API_TOKEN = '8574466093:AAF6MnSQGePYvi1PefAyBk7F8z34Ptjrv6M'
bot = telebot.TeleBot(API_TOKEN)

SAHIP_ID = 7795343194  # PATRON ID
ADMIN_LIST = [6126663392] # YARDIMCILAR
DB_FILE = "casino_db.json"

# Oyun durumlarını geçici hafızada tutuyoruz (Bot kapanınca oyunlar sıfırlanır, bakiye kalır)
active_games = {}

# 📂 VERİTABANI İŞLEMLERİ
def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, indent=4)

def get_user(user_id, first_name):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {
            "balance": 50000,
            "username": first_name,
            "last_bonus": 0,
            "wins": 0,
            "losses": 0
        }
        save_db(db)
    return db, db[uid]

def update_balance(user_id, amount):
    db = load_db()
    uid = str(user_id)
    if uid in db:
        db[uid]['balance'] += amount
        save_db(db)
        return db[uid]['balance']
    return 0

# 🛡️ YARDIMCI FONKSİYONLAR
def check_auth(user_id):
    if user_id == SAHIP_ID: return "SAHIP"
    if user_id in ADMIN_LIST: return "ADMIN"
    return "USER"

def format_money(amount):
    return "{:,}".format(amount).replace(',', '.')

def create_progress_bar(percent):
    filled = int(percent // 10)
    return "█" * filled + "▒" * (10 - filled)

# 🎮 OYUN MANTIKLARI

# --- BLACKJACK ---
def get_deck():
    cards = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
    random.shuffle(cards)
    return cards

def calculate_hand(hand):
    score = sum(hand)
    aces = hand.count(11)
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score

def bj_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("🃏 Kart Çek", callback_data="bj_hit"),
        InlineKeyboardButton("🛑 Dur", callback_data="bj_stand")
    )
    return markup

# --- MAYIN TARLASI ---
def create_mines_keyboard(grid, revealed, game_over=False):
    markup = InlineKeyboardMarkup(row_width=5)
    buttons = []
    for i in range(25):
        btn_text = "⬜"
        callback = f"mine_{i}"
        
        if i in revealed:
            if grid[i] == 1: btn_text = "💣" # Mayın
            else: btn_text = "💎" # Elmas
            callback = "ignore"
        elif game_over:
            if grid[i] == 1: btn_text = "💣"
            else: btn_text = "⬜"
            callback = "ignore"
            
        buttons.append(InlineKeyboardButton(btn_text, callback_data=callback))
    
    markup.add(*buttons)
    if not game_over:
        markup.add(InlineKeyboardButton("💰 NAKİT ÇEK", callback_data="mine_cashout"))
    return markup

# 🚀 KOMUT YÖNETİCİSİ

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = """
━━━━━━━━━━━━━━━━━━━━━━━━━━
🎩 <b>𝐂 𝐀 𝐒 𝐈̇ 𝐍 𝐎  𝐀𝐋𝐅𝐀</b> 🎩
━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>Finansal İşlemler:</b>
💰 <code>/bakiye</code> - Cüzdan Durumu
🎁 <code>/bonus</code> - Günlük 25.000 TL
💸 <code>/borc [miktar]</code> - Transfer (Yanıtla)
🏆 <code>/top</code> - Liderlik Tablosu

<b>Kumar Masaları:</b>
🎰 <code>/slot [miktar] [renk]</code> - Slot Makinesi
🎲 <code>/zar [miktar]</code> - Düello
🔴 <code>/rulet [miktar] [renk]</code> - Rulet
🃏 <code>/bj [miktar]</code> - Blackjack (21)
💣 <code>/mayin [miktar]</code> - Mayın Tarlası
⚡ <code>/risk [miktar]</code> - %50 Ölüm Kalım
🎡 <code>/cark [miktar]</code> - Şans Çarkı

<i>"Kazanmak cesaret ister."</i>
"""
    bot.reply_to(message, text, parse_mode='HTML')

@bot.message_handler(commands=['bakiye'])
def check_balance(message):
    db, user = get_user(message.from_user.id, message.from_user.first_name)
    text = f"""
💳 <b>FEDERASYON KARTI</b>
━━━━━━━━━━━━━━━━
👤 <b>Üye:</b> {user['username']}
💰 <b>Varlık:</b> {format_money(user['balance'])} TL
🆔 <b>ID:</b> <code>{message.from_user.id}</code>
━━━━━━━━━━━━━━━━
"""
    bot.reply_to(message, text, parse_mode='HTML')

@bot.message_handler(commands=['bonus'])
def daily_bonus(message):
    db, user = get_user(message.from_user.id, message.from_user.first_name)
    now = time.time()
    last = user.get('last_bonus', 0)
    
    if now - last < 86400:
        rem = 86400 - (now - last)
        h, m = int(rem // 3600), int((rem % 3600) // 60)
        bot.reply_to(message, f"⏳ <b>Sakin ol şampiyon.</b>
Bonus için: {h} saat {m} dakika beklemelisin.", parse_mode='HTML')
        return

    user['balance'] += 25000
    user['last_bonus'] = now
    save_db(db)
    bot.reply_to(message, "🎁 <b>25.000 TL</b> hesabına eklendi. Git ve katla!", parse_mode='HTML')

# --- OYUN KOMUTLARI ---

@bot.message_handler(commands=['bj'])
def play_blackjack(message):
    try:
        amount = int(message.text.split()[1])
        uid = message.from_user.id
        db, user = get_user(uid, message.from_user.first_name)
        
        if uid in active_games:
            bot.reply_to(message, "⚠️ Zaten açık bir oyunun var!")
            return
        if user['balance'] < amount:
            bot.reply_to(message, "⚠️ Yetersiz bakiye fakir!")
            return
        if len(str(amount)) > 10 and check_auth(uid) == "USER":
            bot.reply_to(message, "⚠️ Limit aşımı!")
            return

        update_balance(uid, -amount)
        deck = get_deck()
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        
        active_games[uid] = {
            "type": "bj",
            "deck": deck,
            "player": player_hand,
            "dealer": dealer_hand,
            "bet": amount
        }
        
        pscore = calculate_hand(player_hand)
        dscore = dealer_hand[0] # Sadece ilk kartı göster
        
        text = f"""
🃏 <b>BLACKJACK MASASI</b>
━━━━━━━━━━━━━━━━
🤵 <b>Krupiye:</b> {dscore} + ❓
🎴 <b>Kartları:</b> [{dealer_hand[0]}, ❓]

👤 <b>Sen:</b> {pscore}
🎴 <b>Kartların:</b> {player_hand}
━━━━━━━━━━━━━━━━
💰 <b>Bahis:</b> {format_money(amount)} TL
"""
        bot.reply_to(message, text, reply_markup=bj_keyboard(), parse_mode='HTML')
        
    except (IndexError, ValueError):
        bot.reply_to(message, "⚠️ Kullanım: /bj <miktar>")

@bot.message_handler(commands=['mayin'])
def play_mines(message):
    try:
        amount = int(message.text.split()[1])
        uid = message.from_user.id
        db, user = get_user(uid, message.from_user.first_name)
        
        if uid in active_games:
            bot.reply_to(message, "⚠️ Önce diğer oyunu bitir.")
            return
        if user['balance'] < amount:
            bot.reply_to(message, "⚠️ Paran yok.")
            return

        update_balance(uid, -amount)
        
        # 3 Mayın yerleştir (25 karede)
        grid = [0]*25
        mines_indices = random.sample(range(25), 3)
        for i in mines_indices: grid[i] = 1
        
        active_games[uid] = {
            "type": "mines",
            "grid": grid,
            "revealed": [],
            "bet": amount,
            "multiplier": 1.0
        }
        
        bot.reply_to(message, 
                     f"💣 <b>MAYIN TARLASI</b>
Bahis: {format_money(amount)} TL
Mayınlar: 3 Adet", 
                     reply_markup=create_mines_keyboard(grid, []), parse_mode='HTML')

    except:
        bot.reply_to(message, "⚠️ Kullanım: /mayin <miktar>")

@bot.message_handler(commands=['zar'])
def play_dice(message):
    try:
        amount = int(message.text.split()[1])
        uid = message.from_user.id
        db, user = get_user(uid, message.from_user.first_name)
        
        if user['balance'] < amount:
            bot.reply_to(message, "⚠️ Yetersiz bakiye.")
            return
            
        update_balance(uid, -amount)
        msg = bot.send_dice(message.chat.id, emoji="🎲")
        result = msg.dice.value
        time.sleep(3)
        
        # 1-3 Kayıp, 4-6 Kazanç
        if result >= 4:
            win = amount * 2
            update_balance(uid, win)
            bot.reply_to(message, f"🎲 Zar: {result}
✅ <b>KAZANDIN!</b> +{format_money(win)} TL", parse_mode='HTML')
        else:
            bot.reply_to(message, f"🎲 Zar: {result}
❌ <b>KAYBETTİN.</b>", parse_mode='HTML')
            
    except:
        bot.reply_to(message, "⚠️ Kullanım: /zar <miktar>")

@bot.message_handler(commands=['slot'])
def play_slot(message):
    try:
        args = message.text.split()
        amount = int(args[1])
        color = args[2].lower()
        uid = message.from_user.id
        db, user = get_user(uid, message.from_user.first_name)
        
        if user['balance'] < amount:
            bot.reply_to(message, "⚠️ Yetersiz bakiye.")
            return
        if color not in ['kirmizi', 'siyah', 'yesil']:
            bot.reply_to(message, "⚠️ Renkler: kirmizi, siyah, yesil")
            return
            
        update_balance(uid, -amount)
        
        slots = ['🍒', '🍋', '🔔', '💎', '7️⃣']
        res = [random.choice(slots) for _ in range(3)]
        
        # Kazanma Mantığı (Basitleştirilmiş)
        won = False
        mult = 0
        chance = random.random()
        
        if color == 'yesil' and chance < 0.1: won, mult = True, 14
        elif color != 'yesil' and chance < 0.45: won, mult = True, 2
        
        win_msg = f"✅ <b>KAZANDIN!</b> +{format_money(amount*mult)}" if won else "❌ <b>KAYBETTİN</b>"
        if won: update_balance(uid, amount*mult)
        
        bot.reply_to(message, f"🎰 <b>SLOT MAKİNESİ</b>
━━━━━━━━━━━━
| {res[0]} | {res[1]} | {res[2]} |
━━━━━━━━━━━━
{win_msg}", parse_mode='HTML')
        
    except:
        bot.reply_to(message, "⚠️ Kullanım: /slot <miktar> <renk>")

@bot.message_handler(commands=['risk'])
def play_risk(message):
    try:
        amount = int(message.text.split()[1])
        uid = message.from_user.id
        db, user = get_user(uid, message.from_user.first_name)
        
        if user['balance'] < amount:
            bot.reply_to(message, "⚠️ Yetersiz bakiye.")
            return
            
        update_balance(uid, -amount)
        
        if random.random() > 0.5:
            win = amount * 2
            update_balance(uid, win)
            bot.reply_to(message, f"🚀 <b>RİSK BAŞARILI!</b>
Paranı ikiye katladın: {format_money(win)} TL", parse_mode='HTML')
        else:
            bot.reply_to(message, "💀 <b>RİSK BAŞARISIZ.</b>
Tüm paran buhar oldu.", parse_mode='HTML')
            
    except:
        bot.reply_to(message, "⚠️ Kullanım: /risk <miktar>")

@bot.message_handler(commands=['borc'])
def transfer(message):
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Bir mesaja yanıt ver.")
        return
    try:
        amount = int(message.text.split()[1])
        sender = message.from_user.id
        receiver = message.reply_to_message.from_user.id
        
        if sender == receiver: return
        db, user = get_user(sender, message.from_user.first_name)
        
        if user['balance'] < amount:
            bot.reply_to(message, "⚠️ Paran yok.")
            return
            
        if len(str(amount)) > 10 and check_auth(sender) == "USER":
            bot.reply_to(message, "⚠️ Limit aşımı.")
            return
            
        update_balance(sender, -amount)
        update_balance(receiver, amount)
        
        bot.reply_to(message, f"💸 <b>TRANSFER BAŞARILI</b>
Gönderilen: {format_money(amount)} TL", parse_mode='HTML')
    except:
        bot.reply_to(message, "⚠️ Hata.")

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    auth = check_auth(message.from_user.id)
    if auth == "USER":
        bot.reply_to(message, "bu komutu kullanma yetkin yok yarram... bot sahibine 200tl ateşle sen de yetkilen ; )")
    else:
        bot.reply_to(message, f"🕵️‍♂️ <b>Admin Paneli</b>
Yetki Seviyeniz: {auth}", parse_mode='HTML')

# 📞 CALLBACK SORGULARI (BUTONLAR)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    if uid not in active_games:
        bot.answer_callback_query(call.id, "⚠️ Aktif oyununuz yok.")
        return

    game = active_games[uid]

    # --- BJ HANDLER ---
    if game['type'] == 'bj':
        if call.data == "bj_hit":
            card = game['deck'].pop()
            game['player'].append(card)
            score = calculate_hand(game['player'])
            
            if score > 21:
                text = f"🃏 <b>PATLADIN!</b> (Skor: {score})
❌ {format_money(game['bet'])} TL Kaybettin."
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
                del active_games[uid]
            else:
                d_show = game['dealer'][0]
                text = f"🃏 <b>BLACKJACK</b>
🤵 Krupiye: {d_show} + ❓
👤 Sen: {score}
🎴 {game['player']}"
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=bj_keyboard(), parse_mode='HTML')
                
        elif call.data == "bj_stand":
            d_score = calculate_hand(game['dealer'])
            while d_score < 17:
                game['dealer'].append(game['deck'].pop())
                d_score = calculate_hand(game['dealer'])
            
            p_score = calculate_hand(game['player'])
            
            win_amount = 0
            res_text = ""
            
            if d_score > 21 or p_score > d_score:
                win_amount = game['bet'] * 2
                res_text = "✅ <b>KAZANDIN!</b>"
            elif p_score == d_score:
                win_amount = game['bet']
                res_text = "⚖️ <b>BERABERE</b>"
            else:
                res_text = "❌ <b>KAYBETTİN</b>"
            
            update_balance(uid, win_amount)
            full_text = f"🃏 <b>OYUN BİTTİ</b>
{res_text}
━━━━━━━━
🤵 Krupiye: {d_score} {game['dealer']}
👤 Sen: {p_score} {game['player']}"
            bot.edit_message_text(full_text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            del active_games[uid]

    # --- MINES HANDLER ---
    elif game['type'] == 'mines':
        if call.data == "mine_cashout":
            win = int(game['bet'] * game['multiplier'])
            update_balance(uid, win)
            bot.edit_message_text(f"💰 <b>CASHOUT!</b>
Kazanç: {format_money(win)} TL", call.message.chat.id, call.message.message_id, parse_mode='HTML')
            del active_games[uid]
            return

        if call.data.startswith("mine_"):
            idx = int(call.data.split("_")[1])
            if idx in game['revealed']: return
            
            game['revealed'].append(idx)
            
            if game['grid'][idx] == 1: # MAYIN
                bot.edit_message_text(f"💣 <b>BOOOOM!</b>
Mayına bastın. {format_money(game['bet'])} TL gitti.", 
                                      call.message.chat.id, call.message.message_id, 
                                      reply_markup=create_mines_keyboard(game['grid'], game['revealed'], True), parse_mode='HTML')
                del active_games[uid]
            else: # ELMAS
                game['multiplier'] *= 1.15
                new_kb = create_mines_keyboard(game['grid'], game['revealed'])
                bot.edit_message_text(f"💎 <b>DEVAM MI?</b>
Çarpan: x{game['multiplier']:.2f}", 
                                      call.message.chat.id, call.message.message_id, 
                                      reply_markup=new_kb, parse_mode='HTML')


print("🎰 Yeraltı Kumarhanesi Açıldı...")
bot.polling()


import requests
import asyncio
import random
import string
from pymongo import MongoClient
from telegram import Update, Poll, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# 🔥 API & Bot Configurations
TELEGRAM_TOKEN = "8151465566:AAFWFcBXPE4u7Fb1XeKrBKA8zlh2uGqHlZs"
CRIC_API_KEY = "9e143604-da14-46fa-8450-1c794febd46b"
MONGO_DB_URL = "mongodb+srv://tsgcoder:tsgcoder@cluster0.1sodg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TELEGRAPH_IMAGE_URL = "https://graph.org/file/d28c8d11173e3742404f6-af0a006bcdf0362c71.jpg"
OWNER_ID = 7548678061  # Replace with your Telegram User ID
CHANNEL_ID = -1002256101563  # Replace with your Telegram Channel ID
SUPPORT_GROUP = "https://t.me/+G_DtJakqOMkxMWU1"
# 🔥 Database Setup
mongo_client = MongoClient(MONGO_DB_URL)
db = mongo_client["cricket_bet"]
users_collection = db["users"]
bets_collection = db["bets"]
redeem_collection = db["redeem_codes"]

# 🔥 Function to Fetch Live Matches
def get_live_matches():
    url = f"https://cricapi.com/api/matches?apikey={CRIC_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        live_matches = [(match["team-1"], match["team-2"], match["unique_id"])
                        for match in data["matches"] if match.get("matchStarted")]
        return live_matches
    return []

# 🔥 Function to Get Live Score
def get_live_score():
    url = f"https://cricapi.com/api/cricketScore?apikey={CRIC_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return f"🏏 **Live Score:** {data.get('score', 'No Score Available')}"
    return "❌ No Live Match Found"

# 🔥 Function to Fetch Match Winner
def get_match_winner():
    url = f"https://cricapi.com/api/matches?apikey={CRIC_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for match in data["matches"]:
            if match.get("matchStarted") and match.get("winner_team"):
                return f"🏆 **Match Winner:** {match['winner_team']}"
    return "❌ No Completed Matches Found"

# # 🔥 Start Command with Structured Buttons
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Live Score", callback_data="live_score")],
        [InlineKeyboardButton("🏆 Match Winner", callback_data="match_winner"),
         InlineKeyboardButton("💰 Bet on Match", callback_data="bet_match")],
        [InlineKeyboardButton("👑 Owner", url="https://t.me/ll_SANKI_II")],
        [InlineKeyboardButton("🎟 Redeem Code", callback_data="redeem_code"),
         InlineKeyboardButton("📢 Join Updates", url="https://t.me/cricketlivescorets")],
        [InlineKeyboardButton("🤝 Support Group", url=SUPPORT_GROUP)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption_text = (
        "🏏 **Welcome to Cricket Betting Bot!** 🎉\n\n"
        "🔹 *Get Live Scores & Match Results*\n"
        "🔹 *Bet & Earn Points*\n"
        "🔹 *Redeem Coins & Join Exciting Matches*\n\n"
        "👇 **Use the buttons below to explore!**"
    )

    await update.message.reply_photo(photo=TELEGRAPH_IMAGE_URL, caption=caption_text, reply_markup=reply_markup)

# 🔥 Generate Redeem Code (Owner Only)
async def genrdm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Only the bot owner can generate redeem codes.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("⚠ Usage: `/genrdm <amount>`")
        return

    amount = int(context.args[0])
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    redeem_collection.insert_one({"code": code, "amount": amount, "used": False})
    await update.message.reply_text(f"✅ Redeem Code Created: `{code}` for {amount} coins.")

# 🔥 Redeem Coins Using Code
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("⚠ Usage: `/redeem <code>`")
        return

    code = context.args[0]
    user = update.message.from_user

    redeem_entry = redeem_collection.find_one({"code": code, "used": False})
    if not redeem_entry:
        await update.message.reply_text("❌ Invalid or already used redeem code.")
        return

    users_collection.update_one({"user_id": user.id}, {"$inc": {"coins": redeem_entry["amount"]}}, upsert=True)
    redeem_collection.update_one({"code": code}, {"$set": {"used": True}})

    await update.message.reply_text(f"🎉 Successfully redeemed {redeem_entry['amount']} coins!")

# 🔥 Start Betting in Group
async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠ Only for groups.")
        return
    message = update.message.text.split()
    if len(message) < 2:
        await update.message.reply_text("⚠ Usage: `/bet <amount>`")
        return
    amount = int(message[1])
    live_matches = get_live_matches()
    if not live_matches:
        await update.message.reply_text("❌ No Live Matches Available.")
        return
    bet_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    bets_collection.insert_one({
        "bet_code": bet_code, "group_id": update.message.chat_id, "bet_amount": amount,
        "users": [], "status": "open", "match_id": live_matches[0][2],
        "team1": live_matches[0][0], "team2": live_matches[0][1]
    })
    await update.message.reply_text(f"✅ Bet Opened!\n💰 Amount: {amount}\n🔗 Code: `{bet_code}`\nUse `/join {bet_code}` to enter!")

# 🔥 Check Match Winner & Distribute Coins
async def check_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_bets = bets_collection.find({"status": "open"})
    for bet in active_bets:
        winner = get_match_winner()
        winning_users = [user for user in bet["users"] if winner in bet["team1"] or winner in bet["team2"]]
        for user_id in winning_users:
            users_collection.update_one({"user_id": user_id}, {"$inc": {"coins": bet["bet_amount"] * 2}})
        await context.bot.send_message(chat_id=bet["group_id"], text=f"🏆 **{winner} Won!** 🎉 Winners received rewards!")
        bets_collection.update_one({"bet_code": bet["bet_code"]}, {"$set": {"status": "completed"}})

# 🔥 Start Bot
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genrdm", genrdm))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("bet", bet))
    app.add_handler(CommandHandler("checkwinner", check_winner))
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())

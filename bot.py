import random
import string
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext, JobQueue
from pymongo import MongoClient

# MongoDB Setup
MONGO_URL = "mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URL)
db = client["member_adding_bot"]
subscriptions_col = db["subscriptions"]
redeem_codes_col = db["redeem_codes"]

# Bot Variables
OWNER_ID = 7877197608
DAILY_ADD_LIMIT = 50

# Helper: Generate Redeem Code
def generate_code():
    return "-".join(["".join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(3)])

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "🤖 Welcome to the Member Adding Bot!\n\n"
        "Use this bot to transfer members from one group to another.\n\n"
        "Commands:\n"
        "- `/adding` to add members (Subscription required).\n"
        "- `/redeem` to activate a plan.\n\n"
        "Contact the owner for redeem codes!"
    )
    await update.message.reply_text(welcome_msg)

# Generate Redeem Code (Owner Only)
async def generate_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can generate redeem codes.")
        return

    if len(context.args) != 1 or context.args[0].lower() not in ["bronz", "silver", "golden", "admin"]:
        await update.message.reply_text("❌ Usage: /genrdm <bronz|silver|golden|admin>")
        return

    plan = context.args[0].lower()
    code = generate_code()
    validity = {
        "bronz": timedelta(weeks=1),
        "silver": timedelta(days=30),
        "golden": timedelta(days=60),
        "admin": None  # Admin codes are permanent
    }.get(plan)

    redeem_codes_col.insert_one({
        "code": code,
        "plan": plan,
        "validity": validity,
        "used": False
    })

    await update.message.reply_text(f"✅ {plan.capitalize()} Redeem Code Generated: `{code}`", parse_mode="Markdown")

# Redeem Command
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /redeem <CODE>")
        return

    code = context.args[0]
    user_id = update.effective_user.id
    code_data = redeem_codes_col.find_one({"code": code})

    if not code_data:
        await update.message.reply_text("❌ Invalid Redeem Code!")
        return

    if code_data["used"]:
        await update.message.reply_text("❌ This Redeem Code has already been used!")
        return

    # Activate subscription
    redeem_codes_col.update_one({"code": code}, {"$set": {"used": True}})

    if code_data["plan"] == "admin":
        subscriptions_col.update_one({"user_id": user_id}, {"$set": {"plan": "admin", "expires": None}}, upsert=True)
        await update.message.reply_text("🎉 You are now an admin! Enjoy permanent access.")
    else:
        expiry_date = datetime.now() + code_data["validity"]
        subscriptions_col.update_one({"user_id": user_id}, {"$set": {"plan": code_data["plan"], "expires": expiry_date}}, upsert=True)
        await update.message.reply_text(f"🎉 Your {code_data['plan'].capitalize()} subscription is now active till {expiry_date.strftime('%Y-%m-%d')}.")

# Adding Command
async def adding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = subscriptions_col.find_one({"user_id": user_id})

    # Check if the user has admin rights or a valid subscription
    if user_id != OWNER_ID and (not user_data or (user_data["plan"] != "admin" and user_data["expires"] < datetime.now())):
        await update.message.reply_text(
            "❌ You need a valid subscription or admin access to use this command.\n"
            "Contact the owner for a redeem code."
        )
        return

    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /adding <SOURCE_GROUP_LINK> <TARGET_GROUP_LINK>")
        return

    source_group, target_group = context.args

    # Here you would have code that actually handles adding members. 
    # Since telegram does not provide direct member extraction from groups,
    # this would require admin access and usage of APIs that the bot can 
    # use for fetching members.
    
    await update.message.reply_text(
        f"🔄 Transferring members from {source_group} to {target_group}...\n"
        "(Ensure members are not hidden and you haven't reached the daily limit!)"
    )

# Notify users of Expiry
async def check_expiries(context: CallbackContext):
    users = subscriptions_col.find({"expires": {"$ne": None}})
    for user in users:
        if user["expires"] < datetime.now():
            # Notify user if their plan has expired
            try:
                await context.bot.send_message(user["user_id"], "❌ Your subscription has expired. Please contact the owner to renew.")
                subscriptions_col.update_one({"user_id": user["user_id"]}, {"$set": {"plan": "expired", "expires": None}})
            except Exception as e:
                print(f"Error notifying user {user['user_id']}: {e}")

# User List (Owner Only)
async def user_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can view the user list.")
        return

    users = subscriptions_col.find()
    response = "👥 **User List:**\n\n"
    for user in users:
        plan = user.get("plan", "N/A").capitalize()
        expires = user.get("expires", "Permanent")
        if isinstance(expires, datetime):
            expires = expires.strftime('%Y-%m-%d')
        response += f"- `{user['user_id']}`: {plan} (Expires: {expires})\n"

    await update.message.reply_text(response, parse_mode="Markdown")

# User Reset (Owner Only)
async def user_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID or len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /userreset <USER_ID>")
        return

    user_id = int(context.args[0])
    subscriptions_col.delete_one({"user_id": user_id})
    try:
        await update.message.reply_text(f"✅ User {user_id}'s plan has been deactivated.")
        await context.bot.send_message(user_id, "❌ Your plan has been deactivated by the owner.")
    except Exception as e:
        print(f"Error notifying user {user_id}: {e}")

# Data Reset (Owner Only)
async def data_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can reset data.")
        return

    subscriptions_col.delete_many({})
    await update.message.reply_text("✅ All user data has been reset.")

# Main Function
if __name__ == "__main__":
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

    job_queue = app.job_queue
    job_queue.run_repeating(check_expiries, interval=86400, first=10)  # Check for expiries daily

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genrdm", generate_redeem))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("adding", adding))
    app.add_handler(CommandHandler("list", user_list))
    app.add_handler(CommandHandler("userreset", user_reset))
    app.add_handler(CommandHandler("datarst", data_reset))

    print("Bot is running...")
    app.run_polling()

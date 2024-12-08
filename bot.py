import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Bot Variables
OWNER_ID = 7877197608  # Replace with the owner's Telegram ID
active_redeem_codes = {}
user_subscriptions = {}

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "🤖 Welcome to the Member Adding Bot!\n\n"
        "Use this bot to transfer members from one group to another.\n\n"
        "To get started:\n"
        "- Add me to a group.\n"
        "- Use `/adding` command after getting a subscription.\n\n"
        "Contact the owner for redeem codes!"
    )
    await update.message.reply_text(welcome_msg)

# Generate Redeem Code (Owner Only)
async def generate_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can generate redeem codes.")
        return

    code = "-".join(
        ["".join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(3)]
    )
    active_redeem_codes[code] = False  # False means the code is unused
    await update.message.reply_text(f"✅ Redeem Code Generated: `{code}`", parse_mode="Markdown")

# Redeem Command
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /redeem <CODE>")
        return

    code = context.args[0]
    user_id = update.effective_user.id

    if code not in active_redeem_codes:
        await update.message.reply_text("❌ Invalid Redeem Code!")
        return

    if active_redeem_codes[code]:
        await update.message.reply_text("❌ This Redeem Code has already been used!")
        return

    # Activate subscription
    active_redeem_codes[code] = True
    user_subscriptions[user_id] = datetime.now() + timedelta(days=30)
    await update.message.reply_text("🎉 Your subscription is now active for 1 month!\nUse /adding command in a group.")

# Adding Command
async def adding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ You can only use this command in groups.\nAdd me to a group first!")
        return

    if user_id not in user_subscriptions or user_subscriptions[user_id] < datetime.now():
        await update.message.reply_text(
            "❌ You need a valid subscription to use this command.\n"
            "Contact the owner for a redeem code."
        )
        return

    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /adding <SOURCE_GROUP_LINK> <TARGET_GROUP_LINK>")
        return

    source_group, target_group = context.args
    await update.message.reply_text(f"🔄 Transferring members from {source_group} to {target_group}...\n(Ensure members are not hidden!)")

# Main Function
if __name__ == "__main__":
    app = ApplicationBuilder().token("7908847221:AAFo2YqgQ4jYG_Glbp96sINg79zF8T6EWoo").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genrdm", generate_redeem))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("adding", adding))

    print("Bot is running...")
    app.run_polling()

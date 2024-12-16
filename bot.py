from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest
from datetime import datetime
import logging
import asyncio
import pymongo

# Bot token and logger group ID
BOT_TOKEN = "7718687925:AAHaKS11Trfc7nQztuM_uEmWWgzSBopZgBU"  # Replace with your bot token
LOGGER_GROUP_ID = "-1002100433415"  # Replace with your logger group ID
OWNER_ID = 7877197608  # Replace with your Telegram user ID (bot owner)

# MongoDB connection URL
MONGO_URL = "mongodb://localhost:27017"  # Replace with your MongoDB URL
client = pymongo.MongoClient(MONGO_URL)
db = client['bot_data']
stats_collection = db['stats']

# List of banned words
BANNED_WORDS = ["madrchod", "randi", "randwi", "chutiya", "gaand", "gand", "lund", "lwda", "loda", "louda", "behnchod"]

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Welcome message
WELCOME_PHOTO_URL = "https://graph.org/file/ae1108390e6dc4f7231cf-ce089431124e12e862.jpg"  # Replace with your photo URL
WELCOME_CAPTION = """
Welcome to the bot! 🌟
1. This bot secures your group effectively.
2. Automatically handles abusive behavior.
3. Use /utag <msg> to tag everyone (Admins only).
4. Keeps your group clean and spam-free.
5. Built to enhance your group experience!
"""

# Track warnings
USER_WARNINGS = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("Owner", url="https://t.me/TSGCODER")],
        [InlineKeyboardButton("Support Channel", url="https://t.me/Teamsankinetworkk")],
        [InlineKeyboardButton("Commands", callback_data="show_commands")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_photo(
        photo=WELCOME_PHOTO_URL, caption=WELCOME_CAPTION, reply_markup=keyboard
    )
    # Log start to the logger group
    await context.bot.send_message(
        chat_id=LOGGER_GROUP_ID,
        text=f"User @{update.effective_user.username} ({update.effective_user.id}) started the bot.",
    )

# Show commands inline
async def show_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    commands_info = """
Commands available:
- /utag <msg>: Tag all group members (Admins only).
- Secure group with banned word detection.
- Warn and mute abusive users.
- /ban <reply/username>: Ban a group member (Admins only).
"""
    await query.answer()
    await query.edit_message_text(commands_info)

# Handle group addition
async def added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    added_by = update.effective_user.username
    await context.bot.send_message(
        chat_id=LOGGER_GROUP_ID,
        text=f"Bot added to group '{update.effective_chat.title}' by @{added_by}.",
    )
    # Log to MongoDB
    db.stats.insert_one({
        "event": "group_added",
        "group_name": update.effective_chat.title,
        "added_by": added_by,
        "timestamp": datetime.now()
    })
    # Check for admin rights
    try:
        chat_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        if chat_member.status != "administrator":
            await update.effective_chat.send_message(
                "Hey, I need admin rights to work properly. Please make me an admin!"
            )
    except Exception as e:
        logger.error(e)

# Ban words and abusive language handler
async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    if any(banned_word in message.text.lower() for banned_word in BANNED_WORDS):
        await message.delete()
        await update.message.reply_text(
            f"Message deleted! @{user.username}, using banned words is not allowed!"
        )
        return

    # Warn user for abusive messages
    if "abuse" in message.text.lower():
        user_id = user.id
        USER_WARNINGS[user_id] = USER_WARNINGS.get(user_id, 0) + 1
        if USER_WARNINGS[user_id] >= 6:
            try:
                await context.bot.restrict_chat_member(
                    update.effective_chat.id,
                    user_id,
                    ChatPermissions(can_send_messages=False),
                    until_date=60,  # Mute for 2 minutes
                )
                await update.message.reply_text(
                    f"@{user.username} has been muted for 2 minutes for repeated abusive behavior."
                )
            except BadRequest:
                await update.message.reply_text("I need admin rights to mute members!")
        else:
            await update.message.reply_text(
                f"Warning {USER_WARNINGS[user_id]}/6: @{user.username}, please stop abusive behavior!"
            )
        await message.delete()

# Utag command for tagging members (Admins only)
async def utag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.get_member(update.effective_user.id).status in ("administrator", "creator"):
        message = " ".join(context.args)
        members = await context.bot.get_chat_administrators(update.effective_chat.id)
        mentions = " ".join([f"@{member.user.username}" for member in members if member.user.username])
        await update.message.reply_text(f"{message}\n{mentions}")
    else:
        await update.message.reply_text("Only admins can use this command!")

# Stats command
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("Overall", callback_data="stats_overall")],
        [InlineKeyboardButton("Back", callback_data="stats_back")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        text="Statistics of the bot:\nSelect an option below:",
        reply_markup=keyboard
    )

# Show overall stats with photo and stylish text
async def show_overall_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uptime = str(datetime.now() - start_time).split('.')[0]  # Get uptime in HH:MM:SS format
    # You can add a photo URL here if it's hosted online, or a file path if it's local.
    photo_url = "https://graph.org/file/ae1108390e6dc4f7231cf-ce089431124e12e862.jpg"  # Replace with actual image URL or file path

    overall_stats = f"""
*👥 Users:* {stats_data['users']}
*📚 Groups:* {stats_data['groups']}
*⏳ Uptime:* {uptime}
*🚫 Blocked:* {stats_data['blocked']}

Made by @TSGCODER
"""
    await query.answer()
    await query.edit_message_text(
        overall_stats,
        parse_mode="Markdown",  # Markdown styling
    )
    await query.message.reply_photo(photo_url)  # Sends the image with the stats

# Back button functionality
async def back_to_main_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await stats(update, context)

Define the broadcast function
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user is the owner
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # The message to be broadcasted
    message = update.message

    # Check the type of message (text, photo, video, etc.) and broadcast accordingly
    if message.text:
        # Broadcast text message
        for user_id in get_all_user_ids():  # Replace with function to get all user IDs
            try:
                await context.bot.send_message(user_id, message.text, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                print(f"Error sending message to {user_id}: {e}")
    elif message.photo:
        # Broadcast photo
        for user_id in get_all_user_ids():  # Replace with function to get all user IDs
            try:
                await context.bot.send_photo(user_id, message.photo[-1].file_id)
            except Exception as e:
                print(f"Error sending photo to {user_id}: {e}")
    elif message.video:
        # Broadcast video
        for user_id in get_all_user_ids():  # Replace with function to get all user IDs
            try:
                await context.bot.send_video(user_id, message.video.file_id)
            except Exception as e:
                print(f"Error sending video to {user_id}: {e}")
    else:
        await update.message.reply_text("Unsupported media type.")
    await update.message.reply_text("Broadcast completed.")

# Main function to start the bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("utag", utag))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_messages))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, added_to_group))
    application.add_handler(CallbackQueryHandler(show_commands, pattern="^show_commands$"))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(show_overall_stats, pattern="^stats_overall$"))
    application.add_handler(CallbackQueryHandler(back_to_main_stats, pattern="^stats_back$"))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest
from datetime import datetime
import logging
import pymongo

# Bot token and logger group ID
BOT_TOKEN = "7718687925:AAHaKS11Trfc7nQztuM_uEmWWgzSBopZgBU"  # Replace with your bot token
LOGGER_GROUP_ID = "-1002100433415"  # Replace with your logger group ID
OWNER_ID = 7877197608  # Replace with your Telegram user ID (bot owner)

# MongoDB connection URL
MONGO_URL = "mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace with your MongoDB URL
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
        [InlineKeyboardButton("Commands", callback_data="show_commands")],  # Button to show commands
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    try:
        await update.message.reply_photo(
            photo=WELCOME_PHOTO_URL, caption=WELCOME_CAPTION, reply_markup=keyboard
        )
        # Log start to the logger group
        await context.bot.send_message(
            chat_id=LOGGER_GROUP_ID,
            text=f"User @{update.effective_user.username} ({update.effective_user.id}) started the bot.",
        )
    except BadRequest as e:
        logger.error(f"Error sending message to logger group: {e}")


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
    try:
        await query.answer()
        # Edit the message text to show commands when button is clicked
        await query.edit_message_text(commands_info, reply_markup=None)  # Set reply_markup=None to avoid additional buttons
    except BadRequest as e:
        logger.error(f"Error editing message: {e}")
        await query.answer("Sorry, I couldn't edit the message. Please try again later.")

# Handle group addition
async def added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    added_by = update.effective_user.username
    try:
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
    except BadRequest as e:
        logger.error(f"Error sending message to logger group: {e}")
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

# Ban command
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.get_member(update.effective_user.id).status not in ("administrator", "creator"):
        await update.message.reply_text("Only admins can use the ban command!")
        return

    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
    else:
        try:
            target_user_id = context.args[0]
        except IndexError:
            await update.message.reply_text("Please reply to a message or specify a username to ban.")
            return

    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target_user_id)
        await update.message.reply_text("User has been banned successfully!")
    except Exception as e:
        await update.message.reply_text(f"Failed to ban user: {e}")

# Utag command for tagging members (Admins only)
async def utag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user is an admin or owner
    if update.effective_chat.get_member(update.effective_user.id).status in ("administrator", "creator"):
        # Get the message sent with the command
        message = " ".join(context.args)
        
        # Get all the members of the group
        members = await context.bot.get_chat_members(update.effective_chat.id)
        
        # Prepare the mentions
        mentions = " ".join([f"@{member.user.username}" for member in members if member.user.username])
        
        # Send the message with mentions
        await update.message.reply_text(f"{message}\n{mentions}")
    else:
        # If user is not admin, send this message
        await update.message.reply_text("Only admins can use this command!")

# Bot start time to calculate uptime
start_time = datetime.now()

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

    # Fetch stats from MongoDB
    stats_data = stats_collection.find_one({"_id": "bot_stats"})  # Assuming the stats are stored with this ID
    if not stats_data:
        stats_data = {"users": 0, "groups": 0, "blocked": 0}  # Default stats if no data found

    uptime = str(datetime.now() - start_time).split('.')[0]  # Get uptime in HH:MM:SS format
    photo_url = "https://graph.org/file/ae1108390e6dc4f7231cf-ce089431124e12e862.jpg"  # Replace with actual image URL or file path

    overall_stats = f"""
*👥 Users:* {stats_data['users']}
*📚 Groups:* {stats_data['groups']}
*⏳ Uptime:* {uptime}
*🚫 Blocked:* {stats_data['blocked']}

Made by @TSGCODER
"""
    try:
        await query.answer()
        await query.edit_message_text(
            overall_stats,
            parse_mode="Markdown",  # Markdown styling
        )
        await query.edit_message_media(media=photo_url)
    except BadRequest as e:
        logger.error(f"Error editing stats message: {e}")

# Define your handler functions (start, ban_user, etc.)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Register your handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("utag", utag))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(show_commands, pattern="show_commands"))
    app.add_handler(CallbackQueryHandler(show_overall_stats, pattern="stats_overall"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_messages))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, added_to_group))

    # Run the bot synchronously
    app.run_polling()

if __name__ == "__main__":
    main()

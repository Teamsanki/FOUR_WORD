from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler
from telegram.ext import filters  # Import filters directly
import yt_dlp

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token and other configuration
TOKEN = "7589149031:AAHCojdq5OmeGjHhDE8qWKiRwSxtRgN5gGk"
OWNER_ID = "7877197608"
LOGGER_GROUP_ID = "-1002100433415"

# Function to send welcome message
def start(update, context):
    user = update.message.from_user
    welcome_msg = (
        "Welcome to the Advanced Music Bot!\n"
        "You can use this bot to play music in groups.\n"
        "Commands:\n"
        "/play [song name or URL] - Play music\n"
        "/pause - Pause music\n"
        "/resume - Resume music\n"
        "/end - End music session"
    )
    
    # Send welcome message with inline buttons
    keyboard = [
        [InlineKeyboardButton("Add Group", callback_data="add_group")],
        [InlineKeyboardButton("Add Commands", callback_data="add_commands")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_photo(photo='YOUR_WELCOME_IMAGE_URL', caption=welcome_msg, reply_markup=reply_markup)

    # Log user details
    user_data = f"Name: {user.full_name}\nUsername: @{user.username}\nUser ID: {user.id}"
    context.bot.send_message(LOGGER_GROUP_ID, user_data)

# Command to handle adding bot to a group
def add_group(update, context):
    update.callback_query.answer("To add the bot to a group, use the 'Add Group' button in the bot's menu.")

# Command to show available commands
def add_commands(update, context):
    commands = (
        "Here are the available commands:\n"
        "/play [song name or URL] - Play music\n"
        "/pause - Pause music\n"
        "/resume - Resume music\n"
        "/end - End music session"
    )
    update.callback_query.answer(commands)

# Play music command
def play(update, context):
    if update.message.chat.type != 'private':  # Ensure it's a group
        user = update.message.from_user
        song = ' '.join(context.args)
        assistant_id = "BQB6_J0AAb6mb69WZ0-m6E847-Pao_ikLMYGzM3su_7XG6IOjuqjLJd-HmYp3_HD6NPDoTeve7oNeNpQQxUj0dcuITKz4LOgOgstLZg8-gJCVGLKoGhAzeNXCVqSxmqNw9mmmpxzdg3YndP8xSaEQ65ZntU9UJ3YXv9dRkHTLI-So1cnY1Sfa4Bz-GWPkTwAdUVxOSz8AAaM3vYGAN0hIsm_M-IAn3vmSAhykifVto8yKjxp9bnEVD7AqRc3qqQzzdv422JZSWZV5jlO2dGWOSYabSh8A0CWol3bAOKl9y2hwvT7YbDawZVNFOGk3ImvS9SFDH9-Mhi3KsIAWaPAHQQsqEWCegAAAAFq-q5XAA"
        
        # Music playing logic using yt-dlp or another library
        play_msg = f"Playing song: {song}\nRequested by: {user.full_name}"
        context.bot.send_message(LOGGER_GROUP_ID, f"Name: {user.full_name}\nUsername: @{user.username}\nUser ID: {user.id}\nSong: {song}")

        update.message.reply_text(play_msg)
        
        # Add code to join VC and play music

    else:
        update.message.reply_text("You can only use this command in a group!")

# Pause music command
def pause(update, context):
    # Implement pause logic (e.g., pause music in the voice chat)
    update.message.reply_text("Music paused.")

# Resume music command
def resume(update, context):
    # Implement resume logic (e.g., resume music in the voice chat)
    update.message.reply_text("Music resumed.")

# End music command
def end(update, context):
    # Implement end music logic (e.g., stop music in the voice chat)
    update.message.reply_text("Music ended.")

    # Log the end of the music session
    user = update.message.from_user
    context.bot.send_message(LOGGER_GROUP_ID, f"Music session ended by {user.full_name}")

def main():
    # Set up the Updater and Dispatcher
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("play", play))
    dp.add_handler(CommandHandler("pause", pause))
    dp.add_handler(CommandHandler("resume", resume))
    dp.add_handler(CommandHandler("end", end))

    # Add callback handlers for inline buttons
    dp.add_handler(CallbackQueryHandler(add_group, pattern="add_group"))
    dp.add_handler(CallbackQueryHandler(add_commands, pattern="add_commands"))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

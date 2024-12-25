import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
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
async def start(update, context):
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
    
    await update.message.reply_photo(photo='https://graph.org/file/cfdf03d8155f959c18668-3c90376a72789999f1.jpg', caption=welcome_msg, reply_markup=reply_markup)

    # Log user details
    user_data = f"Name: {user.full_name}\nUsername: @{user.username}\nUser ID: {user.id}"
    await context.bot.send_message(LOGGER_GROUP_ID, user_data)

# Command to handle adding bot to a group
async def add_group(update, context):
    await update.callback_query.answer("To add the bot to a group, use the 'Add Group' button in the bot's menu.")

# Command to show available commands
async def add_commands(update, context):
    commands = (
        "Here are the available commands:\n"
        "/play [song name or URL] - Play music\n"
        "/pause - Pause music\n"
        "/resume - Resume music\n"
        "/end - End music session"
    )
    await update.callback_query.answer(commands)

# Play music command
async def play(update, context):
    if update.message.chat.type != 'private':  # Ensure it's a group
        user = update.message.from_user
        song = ' '.join(context.args)
        assistant_id = "BQB6_J0AAb6mb69WZ0-m6E847-Pao_ikLMYGzM3su_7XG6IOjuqjLJd-HmYp3_HD6NPDoTeve7oNeNpQQxUj0dcuITKz4LOgOgstLZg8-gJCVGLKoGhAzeNXCVqSxmqNw9mmmpxzdg3YndP8xSaEQ65ZntU9UJ3YXv9dRkHTLI-So1cnY1Sfa4Bz-GWPkTwAdUVxOSz8AAaM3vYGAN0hIsm_M-IAn3vmSAhykifVto8yKjxp9bnEVD7AqRc3qqQzzdv422JZSWZV5jlO2dGWOSYabSh8A0CWol3bAOKl9y2hwvT7YbDawZVNFOGk3ImvS9SFDH9-Mhi3KsIAWaPAHQQsqEWCegAAAAFq-q5XAA"
        
        # Music playing logic using yt-dlp or another library
        play_msg = f"Playing song: {song}\nRequested by: {user.full_name}"
        await context.bot.send_message(LOGGER_GROUP_ID, f"Name: {user.full_name}\nUsername: @{user.username}\nUser ID: {user.id}\nSong: {song}")

        await update.message.reply_text(play_msg)
        
        # Add code to join VC and play music

    else:
        await update.message.reply_text("You can only use this command in a group!")

# Pause music command
async def pause(update, context):
    # Implement pause logic (e.g., pause music in the voice chat)
    await update.message.reply_text("Music paused.")

# Resume music command
async def resume(update, context):
    # Implement resume logic (e.g., resume music in the voice chat)
    await update.message.reply_text("Music resumed.")

# End music command
async def end(update, context):
    # Implement end music logic (e.g., stop music in the voice chat)
    await update.message.reply_text("Music ended.")

    # Log the end of the music session
    user = update.message.from_user
    await context.bot.send_message(LOGGER_GROUP_ID, f"Music session ended by {user.full_name}")

def main():
    # Create the application and pass the bot's token
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play))
    application.add_handler(CommandHandler("pause", pause))
    application.add_handler(CommandHandler("resume", resume))
    application.add_handler(CommandHandler("end", end))

    # Add callback handlers for inline buttons
    application.add_handler(CallbackQueryHandler(add_group, pattern="add_group"))
    application.add_handler(CallbackQueryHandler(add_commands, pattern="add_commands"))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()

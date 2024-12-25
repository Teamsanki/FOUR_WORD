from telegram import Update
from telegram.ext import CommandHandler, Application, ContextTypes
import logging
import random
import string

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

API_TOKEN = '7589149031:AAHCojdq5OmeGjHhDE8qWKiRwSxtRgN5gGk'  # Replace with your bot token

# Function to generate a random join code
def generate_join_code() -> str:
    sections = [
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=3)),
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)),
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)),
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)),
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=2)),
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
    ]
    return '-'.join(sections)

# Command to ban a user
async def newgen_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.reply_to_message:
        await update.message.reply_text('Please reply to a user\'s message to ban them.')
        return

    user_to_ban = update.message.reply_to_message.from_user
    try:
        await context.bot.kick_chat_member(update.message.chat.id, user_to_ban.id)
        await update.message.reply_text(f'User {user_to_ban.full_name} has been banned.')
    except Exception as e:
        await update.message.reply_text(f'Error banning user: {e}')

# Command to generate a join code
async def joinban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    join_code = generate_join_code()
    await update.message.reply_text(f'Use this code to join the group: {join_code}')

# Command to ban a user with a reason
async def sankiban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1 or not update.message.reply_to_message:
        await update.message.reply_text('Usage: /sankiban <reason> (reply to a user)')
        return

    user_to_ban = update.message.reply_to_message.from_user
    reason = ' '.join(context.args)
    try:
        await context.bot.kick_chat_member(update.message.chat.id, user_to_ban.id)
        await update.message.reply_text(f'User {user_to_ban.full_name} has been banned for: {reason}')
    except Exception as e:
        await update.message.reply_text(f'Error banning user: {e}')

# Main function to run the bot
def main() -> None:
    application = Application.builder().token(API_TOKEN).build()

    application.add_handler(CommandHandler('newgen', newgen_ban))
    application.add_handler(CommandHandler('joinban', joinban))
    application.add_handler(CommandHandler('sankiban', sankiban))

    application.run_polling()

if __name__ == '__main__':
    main()

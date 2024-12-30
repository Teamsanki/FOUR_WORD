from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Bot Token
BOT_TOKEN = "7710137855:AAHUJe_Ce9GdT_DPhvNd3dcgaBuWJY2odzQ"

# /id command handler
async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # User input se ID lete hain
        user_id = ' '.join(context.args)
        if not user_id:
            await update.message.reply_text("Please provide a user ID after /id.")
            return

        # Inline button banate hain
        button = InlineKeyboardButton(
            text="DM this user",
            url=f"https://t.me/{user_id}" if user_id.isdigit() else f"https://t.me/{user_id}"
        )
        keyboard = InlineKeyboardMarkup([[button]])

        # Message ke saath button send karte hain
        await update.message.reply_text(
            text=f"Click the button below to DM @{user_id} directly:",
            reply_markup=keyboard
        )
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

# Main function to run the bot
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers add karte hain
    app.add_handler(CommandHandler("id", id_command))

    # Bot ko run karte hain
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

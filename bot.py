from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Function to report a user
def report_user(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Please provide the User ID to report. Example: /report <user_id>")
        return
    
    # Collecting the user ID to be reported
    user_id = context.args[0]
    if user_id.isdigit():
        # Notify the reporter
        update.message.reply_text(f"User ID {user_id} is being reported to Telegram moderation.")
        
        # Forward the report to @SpamBot (manually handled by admin)
        context.bot.send_message(chat_id="@SpamBot", text=f"/report {user_id}")
    else:
        update.message.reply_text("Invalid User ID. Please provide a numeric ID.")

# Start bot function
def main():
    TOKEN = "7869282132:AAFPwZ8ZrFNQxUOPgAbgDm1oInXzDx5Wk74"  # Replace with your bot's token
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Command to report a user
    dispatcher.add_handler(CommandHandler("report", report_user))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

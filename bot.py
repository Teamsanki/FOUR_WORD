from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Function to report a user
async def report_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide the User ID to report. Example: /report <user_id>")
        return
    
    # Collecting the user ID to be reported
    user_id = context.args[0]
    if user_id.isdigit():
        # Notify the reporter
        await update.message.reply_text(f"User ID {user_id} is being reported to Telegram moderation.")
        
        # Forward the report to @SpamBot (you can modify this logic as needed)
        await context.bot.send_message(chat_id="@SpamBot", text=f"/report {user_id}")
    else:
        await update.message.reply_text("Invalid User ID. Please provide a numeric ID.")

# Start bot function
async def main():
    TOKEN = "7869282132:AAFPwZ8ZrFNQxUOPgAbgDm1oInXzDx5Wk74"  # Replace with your bot's token

    # Create the Application (replacing Updater)
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("report", report_user))

    # Start the bot
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

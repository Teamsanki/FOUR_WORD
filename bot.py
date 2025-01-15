from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import random

# List of Indian names for fake reporters
INDIAN_NAMES = [
    "Rahul Sharma", "Priya Verma", "Vikram Patel", "Sneha Mehta",
    "Sunil Desai", "Ritu Singh", "Aman Kumar", "Kavita Joshi",
    "Ankit Malhotra", "Pooja Gupta", "Arjun Thakur", "Nisha Aggarwal",
    "Rohan Chauhan", "Simran Kaur", "Vivek Tripathi", "Aarti Pandey",
    "Rajeev Nair", "Megha Jain", "Karan Kapoor", "Sonal Bansal"
]

# Step 1: Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Custom menu button
    menu_keyboard = [
        ["🆔Report"]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)

    await context.bot.send_message(
        chat_id,
        "Welcome to Telegram Id Report!\n\nClick on Report Menu Button to Enter Target User Id.",
        reply_markup=reply_markup,
    )

# Step 2: /rp Command (When the user presses "🆔Report")
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id,
        "Please enter the Target User ID (e.g., 123456789)."
    )

# Step 3: Process User Input and Fetch Target Name (After user enters ID)
async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    # Check if the user input is a valid numeric ID
    if not user_input.isdigit():
        await update.message.reply_text("Invalid ID. Please enter a valid numeric ID.")
        return

    target_id = user_input
    target_name = f"User_{target_id}"  # Here you can customize based on the ID format.

    # Inline buttons for confirm/cancel
    buttons = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{target_id}:{target_name}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await context.bot.send_message(
        update.effective_chat.id,
        f"Do you want to report '{target_name}'? (Target ID: {target_id})",
        reply_markup=reply_markup
    )

# Step 4: Handle Confirmation or Cancellation
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("confirm:"):
        target_data = data.split(":")
        target_id = target_data[1]
        target_name = target_data[2]
        await query.edit_message_text(f"Reporting initiated for:\n**Target ID:** {target_id}\n**Target Name:** {target_name}")

        # Step 4.1: Generate 20 fake reports with processing
        report_messages = []
        for i in range(1, 21):
            reporter_name = random.choice(INDIAN_NAMES)
            message = await query.message.reply_text(
                f"[Report {i}]**\n"
                f"🆔Target ID:{target_id}\n"
                f"👀Reporter Name: {reporter_name}\n"
                f"✨Status: Processing..."
            )
            report_messages.append(message)
            await asyncio.sleep(5)  # 5-second delay between reports

        # Step 4.2: Start final fake processing
        await fake_processing(query)

        # Step 4.3: Update reports to "Success"
        for message in report_messages:
            await message.edit_text(
                message.text.replace("Processing...", "✅ Success")
            )

    elif data == "cancel":
        await query.edit_message_text("Report process cancelled.")

# Step 5: Fake Processing Animation
async def fake_processing(query):
    # Initial processing message
    progress_message = await query.message.reply_text("Processing...\n▬")

    # Progress steps up to 100%
    progress_steps = [
        "▬", "▬▬", "▬▬▬", "▬▬▬▬", "▬▬▬▬▬",
        "▬▬▬▬▬▬", "▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬",
        "▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", 
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    ]

    for i, step in enumerate(progress_steps, 1):
        percentage = i * 4  # Calculate percentage (since there are 25 steps, each step = 4%)
        await asyncio.sleep(2)  # Wait 2 seconds for each step
        await progress_message.edit_text(
            f"Processing...\n{step}\nProgress: {percentage}%"
        )

    # Final message after processing completes
    await progress_message.edit_text("Processing complete! ✅\nAll fake reports have been submitted successfully.")

# Main Function
def main():
    bot_token = '7869282132:AAFPwZ8ZrFNQxUOPgAbgDm1oInXzDx5Wk74'

    application = ApplicationBuilder().token(bot_token).build()

    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('rp', report))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_input))
    application.add_handler(CallbackQueryHandler(handle_confirmation))

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()

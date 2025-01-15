import os
import time
import random
import re
from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# Random fake Indian names generator
def generate_fake_names(count):
    first_names = ["Raj", "Amit", "Rahul", "Priya", "Anjali", "Sunil", "Pooja", "Vikram", "Kiran", "Sneha"]
    last_names = ["Sharma", "Verma", "Gupta", "Mehra", "Patel", "Yadav", "Singh", "Kumar", "Malhotra", "Desai"]
    full_names = [f"{random.choice(first_names)} {random.choice(last_names)}" for _ in range(count * 2)]
    return random.sample(full_names, count)  # Ensure unique names

# Validate Telegram ID
def validate_telegram_id(user_id):
    if re.match(r"^@[a-zA-Z0-9_]{5,32}$", user_id):
        return True
    return False

# Hacking-style fake report generation
def hacking_style_report(target_id, index, name):
    report = f"""
[Report {index}]
Target User ID: {target_id}
Reported by: {name}
Status: SUCCESS
"""
    return report

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    welcome_message = """
Welcome to the Fake Telegram Member Report Simulator!
This is just for fun, and no real actions are performed.
Use the menu below to navigate:
- /rp [@username]: Generate Fake Report
"""

    telegraph_image_url = "https://graph.org/file/2e37a57d083183ea24761-9cc38246fecc1af393.jpg"

    # Custom keyboard
    custom_keyboard = [
        ["/rp @username"]
    ]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

    # Send welcome message and image
    await context.bot.send_photo(
        chat_id,
        telegraph_image_url,
        caption="Welcome to the Fake Telegram Member Report Simulator!",
        reply_markup=reply_markup
    )
    await context.bot.send_message(chat_id, welcome_message)

# Report command handler
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_input = update.message.text.split()

    # Check if user provided a Telegram ID
    if len(user_input) < 2:
        await context.bot.send_message(chat_id, "Please provide a Telegram User ID (e.g., /rp @username).")
        return

    target_id = user_input[1].strip()

    if not validate_telegram_id(target_id):
        await context.bot.send_message(chat_id, "Invalid Telegram ID! Please provide a valid ID starting with '@'.")
        return

    # Show progress (fake loading)
    await context.bot.send_message(chat_id, "Generating fake reports... Please wait.")

    # Generate and send reports one by one
    fake_reports = generate_fake_names(40)  # Generate 40 unique fake names
    for i, name in enumerate(fake_reports, 1):
        # Simulate delay for each report
        time.sleep(1)
        report_content = hacking_style_report(target_id, i, name)
        await context.bot.send_message(chat_id, report_content)

    await context.bot.send_message(chat_id, "All fake reports have been generated!")

# Main function
def main():
    # Replace with your bot token
    bot_token = '7869282132:AAFPwZ8ZrFNQxUOPgAbgDm1oInXzDx5Wk74'

    # Create Application
    application = ApplicationBuilder().token(bot_token).build()

    # Command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('rp', report))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()

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
import asyncio
import random

# List of 1000 unique Indian names for fake reporters
INDIAN_NAMES = [
    "Rahul Sharma", "Priya Verma", "Vikram Patel", "Sneha Mehta", "Sunil Desai", "Ritu Singh",
    "Aman Kumar", "Kavita Joshi", "Ankit Malhotra", "Pooja Gupta", "Arjun Thakur", "Nisha Aggarwal",
    "Rohan Chauhan", "Simran Kaur", "Vivek Tripathi", "Aarti Pandey", "Rajeev Nair", "Megha Jain",
    "Karan Kapoor", "Sonal Bansal", "Deepak Singh", "Nikita Verma", "Mohit Joshi", "Ravi Kapoor",
    "Neha Bhatia", "Sumit Rathi", "Sanjay Mehta", "Jaspreet Kaur", "Dinesh Soni", "Komal Yadav",
    "Ashok Sharma", "Anjali Mishra", "Vikash Chauhan", "Rupal Pandey", "Abhishek Yadav", "Sangeeta Mehra",
    "Rahul Soni", "Shreya Jain", "Praveen Bansal", "Sunita Devi", "Manoj Gupta", "Ravindra Nair",
    "Rakesh Rajput", "Madhuri Kumari", "Yogesh Singh", "Neelam Rani", "Hitesh Tiwari", "Tanu Sharma",
    "Amit Prasad", "Bhavna Arora", "Vishal Kapoor", "Vandana Joshi", "Suresh Kumar", "Rajesh Rani",
    "Ritika Khurana", "Kriti Sharma", "Mukul Agarwal", "Arvind Kumar", "Divya Pandey", "Pritam Singh",
    "Manisha Saini", "Pankaj Sharma", "Harleen Kaur", "Meenakshi Gupta", "Tarun Yadav", "Vinod Kumar",
    "Sushil Kumar", "Yashika Kaur", "Amit Kumar", "Ramesh Patel", "Aarti Rani", "Jatin Malhotra",
    "Kiran Mehra", "Vikas Chauhan", "Brijesh Tiwari", "Geeta Kumari", "Vinay Kumar", "Suman Yadav",
    "Nitin Sharma", "Nikhil Agarwal", "Neeraj Joshi", "Ashok Kumar", "Vandana Mehta", "Vikas Mehra",
    "Kavita Sharma", "Akash Chauhan", "Sandeep Rathi", "Laxmi Yadav", "Ravinder Singh", "Ankita Mehta",
    "Vikram Yadav", "Anjali Patel", "Shivani Rajput", "Poonam Kumari", "Rohit Bansal", "Shalini Sharma",
    "Manoj Thakur", "Nidhi Agarwal", "Sushil Kumar", "Tanya Kaur", "Rajiv Joshi", "Tanvi Rani", 
    "Avinash Chauhan", "Tanuja Kumari", "Vijay Bansal", "Deepika Agarwal", "Sourabh Joshi", "Pradeep Rathi",
    "Suraj Malhotra", "Madhuri Mehta", "Priyanka Kapoor", "Karan Soni", "Sumit Singh", "Aman Rajput",
    "Priya Rani", "Shalini Malhotra", "Manish Bansal", "Amit Thakur", "Neha Pandey", "Harshit Agarwal",
    "Anjali Kumari", "Ravi Rajput", "Simran Kaur", "Pooja Mehra", "Ashok Yadav", "Yogita Patel",
    "Akshay Malhotra", "Chandini Verma", "Ravindra Joshi", "Rina Mehta", "Pallavi Soni", "Nisha Singh",
    "Vishal Gupta", "Vandana Pandey", "Ravish Kumar", "Simran Arora", "Rohit Soni", "Manisha Mehra",
    "Aarti Patel", "Nisha Chauhan", "Neeraj Kumar", "Krishan Bansal", "Sandeep Kumar", "Sunita Arora",
    "Sahil Malhotra", "Tanu Gupta", "Madhuri Singh", "Kavita Malhotra", "Suresh Tiwari", "Rohit Yadav",
    "Rakhi Mehra", "Karan Sharma", "Harman Kaur", "Amit Joshi", "Gurpreet Singh", "Ravindra Patel",
    "Anjali Yadav", "Poonam Rajput", "Nidhi Pandey", "Vikas Tiwari", "Prashant Sharma", "Manoj Patel",
    "Kriti Gupta", "Amit Malhotra", "Rajesh Sharma", "Kavita Joshi", "Tushar Yadav", "Hina Gupta",
    # Add more names till 1000...
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
        "Welcome to Telegram Id Report!\n\nMake Id to Slow Down With Your Target Id\n\nClick on Report Menu Button Then enter Target User Id.",
        reply_markup=reply_markup,
    )

# Step 2: /rp Command
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id,
        "Kis user ko report karna chahte hain? Apni Target User ki ID dein (e.g., 123456789)."
    )

# Step 3: Process User Input and Fetch Target Name
async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    if not user_input.isdigit():
        await update.message.reply_text("Invalid ID. Please provide a valid numeric ID.")
        return

    target_id = user_input

    # Inline buttons for confirm/cancel
    buttons = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{target_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await context.bot.send_message(
        update.effective_chat.id,
        f"Aapko '{target_id}' ko report karna hai? (Target ID: {target_id})",
        reply_markup=reply_markup
    )

# Step 4: Handle Confirmation or Cancellation
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("confirm:"):
        target_id = data.split(":")[1]
        await query.edit_message_text(f"Reporting initiated for:\n**Target ID:** {target_id}")

        # Step 4.1: Generate 20 fake reports with processing in parallel
        tasks = []
        for i in range(1, 21):
            reporter_name = random.choice(INDIAN_NAMES)
            tasks.append(
                send_report(query, target_id, i, reporter_name)
            )

        # Step 4.2: Run tasks concurrently with minimal delay
        await asyncio.gather(*tasks)

        await fake_processing(query)

        # Step 4.3: Update reports to "Success"
        for task in tasks:
            await task

    elif data == "cancel":
        await query.edit_message_text("Report process cancelled.")

# Step 5: Send Report Message
async def send_report(query, target_id, report_num, reporter_name):
    await query.message.reply_text(
        f"[Report {report_num}]**\n"
        f"🆔Target ID:{target_id}\n"
        f"👀Reporter Name: {reporter_name}\n"
        f"✨Status: Processing..."
    )
    await asyncio.sleep(5)  # small delay for simulation

# Step 6: Fake Processing Animation
async def fake_processing(query):
    progress_message = await query.message.reply_text("Processing...\n▬")
    
    progress_steps = [
        "▬", "▬▬", "▬▬▬", "▬▬▬▬", "▬▬▬▬▬",
        "▬▬▬▬▬▬", "▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬▬▬",
    ]

    for step in progress_steps:
        await asyncio.sleep(0.5)
        await progress_message.edit_text(f"Processing...\n{step}")

    # Final 100% completion
    await progress_message.edit_text("✅ Report Successful!")

# Main bot setup
def main():
    app = ApplicationBuilder().token('7869282132:AAFPwZ8ZrFNQxUOPgAbgDm1oInXzDx5Wk74').build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rp", report))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_input))
    app.add_handler(CallbackQueryHandler(handle_confirmation))

    app.run_polling()

if __name__ == '__main__':
    main()

import os
import logging
import telebot
from flask import Flask, render_template
from pymongo import MongoClient
from yt_dlp import YoutubeDL
from threading import Thread

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize bot and MongoDB client
API_TOKEN = os.getenv('7589149031:AAHCojdq5OmeGjHhDE8qWKiRwSxtRgN5gGk')  # Replace with your bot's token or set as an environment variable
bot = telebot.TeleBot(API_TOKEN)

MONGO_URL = os.getenv('mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')  # Replace with your MongoDB connection string or set as an environment variable
client = MongoClient(MONGO_URL)
db = client['music_bot']
logger_collection = db['logger']

# Logger group ID (replace with your group's ID)
LOGGER_GROUP_ID = -1002148651992  # Replace with the actual group ID where logs should be sent

# Initialize Flask app
app = Flask(__name__)

# Inline button and callback functions
def start(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    button1 = telebot.types.InlineKeyboardButton("Add me to Group", url="https://t.me/your_bot")
    button2 = telebot.types.InlineKeyboardButton("Commands", callback_data="commands")
    markup.add(button1, button2)
    
    bot.send_photo(message.chat.id, 'https://graph.org/file/cfdf03d8155f959c18668-3c90376a72789999f1.jpg', caption="Welcome to Music Bot!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'commands')
def send_commands(call):
    bot.send_message(call.message.chat.id, "Commands:\n/play <song_name>\n/pause\n/resume\n/end")

# Log user activity and send to logger group
def log_activity(activity_data):
    # Save to MongoDB
    logger_collection.insert_one(activity_data)
    
    # Send to logger group
    log_message = (
        f"**Activity Log**\n"
        f"**Activity:** {activity_data.get('activity')}\n"
        f"**User:** {activity_data.get('user_name')} (ID: {activity_data.get('user_id')})\n"
        f"**Chat ID:** {activity_data.get('chat_id')}\n"
        f"**Song:** {activity_data.get('song', 'N/A')}"
    )
    bot.send_message(LOGGER_GROUP_ID, log_message, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def handle_start(message):
    activity_data = {
        'activity': 'Bot Started',
        'user_name': message.from_user.first_name,
        'user_id': message.from_user.id,
        'chat_id': message.chat.id
    }
    log_activity(activity_data)
    start(message)

# Play music command with song image
@bot.message_handler(commands=['play'])
def play_music(message):
    try:
        song_name = message.text.split(' ', 1)[1]  # Extract the song name
        activity_data = {
            'activity': 'Play Song',
            'user_name': message.from_user.first_name,
            'user_id': message.from_user.id,
            'chat_id': message.chat.id,
            'song': song_name
        }
        log_activity(activity_data)
        
        # Call ytdlp to fetch song URL and thumbnail image
        ydl_opts = {'quiet': True}
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(f'ytsearch:{song_name}', download=False)
            song_url = info_dict['entries'][0]['url']
            song_image_url = info_dict['entries'][0]['thumbnail']  # Thumbnail URL
        
        # Send song info to the user
        bot.send_message(message.chat.id, f"Playing {song_name}...\nSong Image: {song_image_url}")
        
        # Render the music room using Flask
        group_name = "Sample Group"  # You can dynamically get this based on the group
        song_name_display = song_name
        music_room_url = f"http://your-app-url/music-room/{group_name}/{song_name_display}/{song_url}/{song_image_url}"
        bot.send_message(message.chat.id, f"Join the music room: {music_room_url}")
    
    except Exception as e:
        bot.send_message(message.chat.id, "An error occurred while processing your request.")
        logger.error(f"Error in play_music: {e}")

# Flask route for music room
@app.route('/music-room/<group_name>/<song_name>/<song_url>/<song_image_url>')
def music_room(group_name, song_name, song_url, song_image_url):
    # Example static list of users, you should fetch dynamic data if necessary
    users = ["User1", "User2", "User3"]
    return render_template("music_room.html", group_name=group_name, song_name=song_name, 
                           song_url=song_url, song_image_url=song_image_url, users=users)

# Run bot and Flask together
if __name__ == "__main__":
    def run_bot():
        bot.polling()
    
    # Run the bot in a separate thread
    thread = Thread(target=run_bot)
    thread.start()
    
    # Run the Flask server
    app.run(debug=True, use_reloader=False)

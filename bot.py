import yt_dlp
from pyrogram import Client, filters
import ffmpeg
from pymongo import MongoClient
import asyncio
from datetime import datetime
from pyrogram import Client
from pyrogram.sessions import StringSession

# MongoDB Setup
client = MongoClient("mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['bot_db']
logger_collection = db['bot_logger']

# Telegram Client Setup (with bot token and assistant string session)
api_id = '8060061'
api_hash = '0a19238a019c119cea065eae38cebcd2'
bot_token = '7589149031:AAHCojdq5OmeGjHhDE8qWKiRwSxtRgN5gGk'  # Add your bot token here
ASSISTANT_STRING_SESSION = 'BQB6_J0AAb6mb69WZ0-m6E847-Pao_ikLMYGzM3su_7XG6IOjuqjLJd-HmYp3_HD6NPDoTeve7oNeNpQQxUj0dcuITKz4LOgOgstLZg8-gJCVGLKoGhAzeNXCVqSxmqNw9mmmpxzdg3YndP8xSaEQ65ZntU9UJ3YXv9dRkHTLI-So1cnY1Sfa4Bz-GWPkTwAdUVxOSz8AAaM3vYGAN0hIsm_M-IAn3vmSAhykifVto8yKjxp9bnEVD7AqRc3qqQzzdv422JZSWZV5jlO2dGWOSYabSh8A0CWol3bAOKl9y2hwvT7YbDawZVNFOGk3ImvS9SFDH9-Mhi3KsIAWaPAHQQsqEWCegAAAAFq-q5XAA'  # Replace this with your assistant's string session

# Initialize the Telegram Clients using StringSession
bot_client = Client("bot", api_id, api_hash, bot_token=bot_token)
assistant_client = Client("assistant", api_id, api_hash, session_string=StringSession(ASSISTANT_STRING_SESSION))

# Cookies setup
cookies_file = "tsk.txt"  # Path to your YouTube cookies

# Function to search and get the song URL using yt-dlp
def get_song_url(song_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'cookiefile': cookies_file  # Use cookies to bypass restrictions
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
        video_url = info['entries'][0]['url']  # Get the URL of the first result
        return video_url, info['entries'][0]['title']

# Function to play music in VC (voice chat)
async def play_music_in_vc(group_id, song_name):
    # Get song URL
    video_url, song_title = get_song_url(song_name)

    # Join the voice chat using the assistant
    group = await assistant_client.get_chat(group_id)
    call = await assistant_client.start_voice_chat(group.id)

    # Stream the audio into the voice chat
    ffmpeg.input(video_url).output('pipe:1', format='wav').run()

    # Log the play event
    log_play_event(group_id, song_title, video_url)

# Log the play event in MongoDB
def log_play_event(group_id, song_title, video_url):
    play_data = {
        "song_name": song_title,
        "group_id": group_id,
        "play_time": datetime.now(),
        "song_url": video_url
    }
    logger_collection.insert_one(play_data)

# Telegram Bot to handle play command
@bot_client.on_message(filters.command("play"))
async def handle_play_command(client, message):
    if message.chat.type == 'private':
        await message.reply("This command only works in a group!")
        return

    # Extract the song name from the command
    song_name = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) > 1 else None
    if song_name:
        group_id = message.chat.id
        await play_music_in_vc(group_id, song_name)
        await message.reply(f"Now playing: {song_name} 🎶")

# Function to start the bot
async def start_bot():
    print("Bot is running...")
    await bot_client.start()
    await assistant_client.start()

# Run the bot
loop = asyncio.get_event_loop()
loop.run_until_complete(start_bot())

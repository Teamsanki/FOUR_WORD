import yt_dlp
from telethon import TelegramClient, events
import ffmpeg
from pymongo import MongoClient
import asyncio
from telethon.sessions import StringSession

# MongoDB Setup
client = MongoClient("mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['bot_db']
logger_collection = db['bot_logger']

# Telegram Client Setup (with bot token and assistant string session)
api_id = '8060061'
api_hash = '0a19238a019c119cea065eae38cebcd2'
bot_token = '7589149031:AAHCojdq5OmeGjHhDE8qWKiRwSxtRgN5gGk'  # Add your bot token here
ASSISTANT_STRING_SESSION = 'BQB6_J0AAb6mb69WZ0-m6E847-Pao_ikLMYGzM3su_7XG6IOjuqjLJd-HmYp3_HD6NPDoTeve7oNeNpQQxUj0dcuITKz4LOgOgstLZg8-gJCVGLKoGhAzeNXCVqSxmqNw9mmmpxzdg3YndP8xSaEQ65ZntU9UJ3YXv9dRkHTLI-So1cnY1Sfa4Bz-GWPkTwAdUVxOSz8AAaM3vYGAN0hIsm_M-IAn3vmSAhykifVto8yKjxp9bnEVD7AqRc3qqQzzdv422JZSWZV5jlO2dGWOSYabSh8A0CWol3bAOKl9y2hwvT7YbDawZVNFOGk3ImvS9SFDH9-Mhi3KsIAWaPAHQQsqEWCegAAAAFq-q5XAA'  # Replace this with your assistant's string session

# Initialize the Telegram Clients
bot_client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
assistant_client = TelegramClient(StringSession(ASSISTANT_STRING_SESSION), api_id, api_hash)

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

# Function to play music in VC
async def play_music_in_vc(group_id, song_name):
    # Get song URL
    video_url, song_title = get_song_url(song_name)

    # Join the voice chat using the assistant
    group = await assistant_client.get_entity(group_id)
    call = await assistant_client.start_voice_chat(group)

    # Stream the audio into the voice chat
    ffmpeg.input(video_url).output('pipe:1', format='wav').run()

    # Log the play event
    log_play_event(group_id, song_title, video_url)

# Log the play event in MongoDB
def log_play_event(group_id, song_title, video_url):
    from datetime import datetime
    play_data = {
        "song_name": song_title,
        "group_id": group_id,
        "play_time": datetime.now(),
        "song_url": video_url
    }
    logger_collection.insert_one(play_data)

# Telegram Bot to handle play command
@bot_client.on(events.NewMessage(pattern='/play'))
async def handle_play_command(event):
    if event.chat.type == 'private':
        await event.reply("This command only works in a group!")
        return

    # Extract the song name from the command
    song_name = event.text.split(' ', 1)[1] if len(event.text.split(' ', 1)) > 1 else None
    if song_name:
        group_id = event.chat.id
        await play_music_in_vc(group_id, song_name)
        await event.reply(f"Now playing: {song_name} 🎶")

# Function to start the bot
async def start_bot():
    print("Bot is running...")
    await bot_client.run_until_disconnected()

# Run the bot
loop = asyncio.get_event_loop()
loop.run_until_complete(start_bot())

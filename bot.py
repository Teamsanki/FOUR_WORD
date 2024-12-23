import yt_dlp
from telethon import TelegramClient
import ffmpeg
from pymongo import MongoClient
import asyncio

# MongoDB Setup
client = MongoClient("your_mongodb_connection_string")
db = client['bot_db']
logger_collection = db['bot_logger']

# Telegram Client Setup (with string session)
api_id = 'your_api_id'
api_hash = 'your_api_hash'
string_session = 'your_string_session'
telethon_client = TelegramClient('bot', api_id, api_hash).start(session=string_session)

# Cookies setup
cookies_file = "path_to_your_cookies.txt"  # Path to your YouTube cookies

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

    # Join the voice chat
    group = await telethon_client.get_entity(group_id)
    call = await telethon_client.start_voice_chat(group)

    # Stream the audio into the voice chat
    # Use ffmpeg to stream the music from the YouTube video URL
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
async def handle_play_command(message):
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
    @telethon_client.on(events.NewMessage(pattern='/play'))
    async def play_command_handler(event):
        await handle_play_command(event.message)

    print("Bot is running...")
    await telethon_client.run_until_disconnected()

# Run the bot
loop = asyncio.get_event_loop()
loop.run_until_complete(start_bot())

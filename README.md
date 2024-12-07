# IPL Live Score Telegram Bot 🏏

This is a Telegram bot that provides live IPL scores to users. The bot fetches the latest scores from a cricket API and sends updates to users every 5 minutes.

## Features
- Start the bot using the `/start` command.
- Receive live IPL score updates every 5 minutes automatically.
- Logs each user who starts the bot in a logger group with their username and user ID.

## Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ipl_live_score_bot.git
   cd ipl_live_score_bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   - Create a `.env` file in the project directory with the following content:
     ```env
     TELEGRAM_BOT_TOKEN=your_telegram_bot_token
     CRICKET_API_KEY=your_cricket_api_key
     LOGGER_GROUP_ID=your_logger_group_id
     ```

4. Run the bot:
   ```bash
   python bot.py
   ```

## Deploy on Heroku

1. Install the Heroku CLI and log in:
   ```bash
   heroku login
   ```

2. Create a new Heroku app:
   ```bash
   heroku create
   ```

3. Set environment variables on Heroku:
   ```bash
   heroku config:set TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   heroku config:set CRICKET_API_KEY=your_cricket_api_key
   heroku config:set LOGGER_GROUP_ID=your_logger_group_id
   ```

4. Deploy the bot:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push heroku main
   ```

5. Scale the bot worker:
   ```bash
   heroku ps:scale worker=1
   ```

## License
This project is licensed under the MIT License.

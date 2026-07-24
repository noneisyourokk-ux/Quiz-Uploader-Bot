# Telegram Quiz Uploader Bot

A modular Telegram bot that parses `.txt` or `.json` files and uploads formatted quizzes directly to a Telegram channel.

## 🚀 Environment Variables
- `BOT_TOKEN`: Telegram bot token from @BotFather.
- `CHANNEL_ID`: Channel username (e.g., `@mychannel`) or ID where bot is Admin.
- `ADMIN_IDS`: Comma-separated user IDs authorized to upload files (e.g., `1234567,9876543`).

## 📁 How to Run
```bash
pip install -r requirements.txt
python bot.py

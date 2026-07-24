from telegram import Update
from telegram.ext import ContextTypes

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to Quiz Uploader Bot!**\n\n"
        "Send me a `.txt` or `.json` file containing quiz questions, "
        "and I will publish them directly to your Telegram channel.\n\n"
        "Use /help to see required file formats."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📝 **TXT Format Example:**\n"
        "```\n"
        "What is 2 + 2?\n"
        "- 3\n"
        "* - 4\n"
        "- 5\n"
        "-- Explanation: 2 plus 2 equals 4.\n"
        "```\n"
        "💡 Put an asterisk (`*`) in front of the correct answer."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

from pyrogram import filters
from pyrogram.types import Message

from config import OWNER_ID

def is_owner(user_id: int) -> bool:
    return OWNER_ID == 0 or user_id == OWNER_ID

async def start_cmd(client, message: Message):
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    text = (
        "Quiz Uploader Bot is ready.\n\n"
        "Commands:\n"
        "/uploadquiz - reply to a TXT/JSON file or send quiz text after command\n"
        "/setdelay 2 - set delay in seconds\n"
        "/setchannel @channelusername or -100xxxxxxxxxx\n"
        "/stop - stop current upload\n"
        "/help - show format\n"
    )
    await message.reply_text(text)

async def help_cmd(client, message: Message):
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    text = (
        "TXT format:\n"
        "Question?\n"
        "Option 1*\n"
        "Option 2\n"
        "Option 3\n"
        "Option 4\n"
        "Explanation: optional text\n\n"
        "Blank line = next question.\n\n"
        "JSON format:\n"
        "[{\"question\":\"...\",\"options\":[\"A\",\"B\"],\"correct\":0,\"explanation\":\"...\"}]"
    )
    await message.reply_text(text)

import os
from typing import Tuple
from pyrogram.types import Message


async def read_text_from_message(msg: Message) -> Tuple[str, str]:
    """
    Returns:
      text, filename

    Supports:
      - replied document
      - direct document
      - command text after /uploadquiz
    """
    if msg.document:
        filename = msg.document.file_name or "quiz.txt"
        path = await msg.download()
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        try:
            os.remove(path)
        except Exception:
            pass
        return text, filename

    if msg.reply_to_message and msg.reply_to_message.document:
        filename = msg.reply_to_message.document.file_name or "quiz.txt"
        path = await msg.reply_to_message.download()
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        try:
            os.remove(path)
        except Exception:
            pass
        return text, filename

    if msg.text:
        parts = msg.text.split(None, 1)
        if len(parts) > 1:
            return parts[1], "quiz.txt"

    raise ValueError("Please reply to a TXT/JSON file or send quiz text after the command.")

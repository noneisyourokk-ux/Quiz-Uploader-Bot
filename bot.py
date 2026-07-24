import asyncio
import logging

from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import Message

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    OWNER_ID,
    CHANNEL_ID,
    DEFAULT_DELAY,
    PORT,
)
from utils.file_reader import read_text_from_message
from utils.parser import parse_quiz_file
from utils.uploader import upload_quizzes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("quiz-uploader-bot")

app = Client(
    "quiz_uploader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

state = {
    "delay": DEFAULT_DELAY,
    "channel_id": CHANNEL_ID,
    "stop": False,
    "uploading": False,
}


def is_owner(user_id: int) -> bool:
    return OWNER_ID == 0 or user_id == OWNER_ID


def get_target_channel() -> str:
    target = str(state.get("channel_id", "")).strip()
    if not target:
        raise ValueError("CHANNEL_ID is not set. Use /setchannel or set it in .env.")
    return target


async def health(_: web.Request):
    return web.Response(text="OK")


async def start_web_server():
    web_app = web.Application()
    web_app.router.add_get("/", health)
    web_app.router.add_get("/health", health)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    log.info("Web server running on port %s", PORT)


@app.on_message(filters.command("start") & filters.private)
async def start_cmd(_, message: Message):
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    text = (
        "Quiz Uploader Bot is ready.\n\n"
        "Commands:\n"
        "/uploadquiz - reply to a TXT/JSON file or send quiz text after the command\n"
        "/setdelay 2 - set delay in seconds\n"
        "/setchannel @channelusername or -100xxxxxxxxxx\n"
        "/stop - stop current upload\n"
        "/help - show format\n"
    )
    await message.reply_text(text)


@app.on_message(filters.command("help") & filters.private)
async def help_cmd(_, message: Message):
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


@app.on_message(filters.command("setdelay") & filters.private)
async def setdelay_cmd(_, message: Message):
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply_text(f"Current delay: {state['delay']} sec\nUse: /setdelay 2")

    try:
        delay = int(parts[1].strip())
        if delay < 0 or delay > 3600:
            raise ValueError
        state["delay"] = delay
        await message.reply_text(f"Delay updated to {delay} seconds.")
    except Exception:
        await message.reply_text("Send a valid number. Example: /setdelay 2")


@app.on_message(filters.command("setchannel") & filters.private)
async def setchannel_cmd(_, message: Message):
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply_text("Use: /setchannel @channelusername or -100xxxxxxxxxx")

    state["channel_id"] = parts[1].strip()
    await message.reply_text(f"Channel set to: `{state['channel_id']}`", quote=True)


@app.on_message(filters.command("stop") & filters.private)
async def stop_cmd(_, message: Message):
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    state["stop"] = True
    await message.reply_text("Stop signal sent.")


@app.on_message(filters.command("uploadquiz") & filters.private)
async def uploadquiz_cmd(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    if state["uploading"]:
        return await message.reply_text("An upload is already running. Use /stop first.")

    try:
        target = get_target_channel()
    except Exception as e:
        return await message.reply_text(str(e))

    try:
        text, filename = await read_text_from_message(message)
        quizzes = parse_quiz_file(text, filename)

        if not quizzes:
            return await message.reply_text("No valid quiz questions found in the file.")

        state["uploading"] = True
        await message.reply_text(f"Found {len(quizzes)} quiz questions. Uploading to {target}...")
        await upload_quizzes(
            client=client,
            quizzes=quizzes,
            chat_id=target,
            state=state,
            reply_msg=message,
            default_delay=state["delay"],
        )

    except Exception as e:
        log.exception("Upload failed")
        await message.reply_text(f"Error: {e}")
    finally:
        state["uploading"] = False


@app.on_message(filters.document & filters.private)
async def document_handler(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return

    caption = (message.caption or "").lower()
    if "uploadquiz" not in caption:
        return

    if state["uploading"]:
        return await message.reply_text("An upload is already running. Use /stop first.")

    try:
        target = get_target_channel()
    except Exception as e:
        return await message.reply_text(str(e))

    try:
        text, filename = await read_text_from_message(message)
        quizzes = parse_quiz_file(text, filename)

        if not quizzes:
            return await message.reply_text("No valid quiz questions found in the file.")

        state["uploading"] = True
        await message.reply_text(f"Found {len(quizzes)} quiz questions. Uploading to {target}...")
        await upload_quizzes(
            client=client,
            quizzes=quizzes,
            chat_id=target,
            state=state,
            reply_msg=message,
            default_delay=state["delay"],
        )

    except Exception as e:
        log.exception("Document upload failed")
        await message.reply_text(f"Error: {e}")
    finally:
        state["uploading"] = False


async def main():
    if not API_ID or not API_HASH or not BOT_TOKEN:
        raise RuntimeError("Set API_ID, API_HASH, and BOT_TOKEN in environment variables.")

    if OWNER_ID == 0:
        log.warning("OWNER_ID is not set. Bot will accept all users.")

    await app.start()
    log.info("Bot started")
    asyncio.create_task(start_web_server())
    await idle()
    await app.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

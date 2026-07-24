import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple

from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import Message

# =========================
# CONFIG
# =========================
API_ID = int(os.getenv("API_ID", "22470912"))
API_HASH = os.getenv("API_HASH", "511be78079ed5d4bd4c967bc7b5ee023")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8254141632:AAFvRU6E4amexKzidBe2Ij9pBvkoCYozHNg")
OWNER_ID = int(os.getenv("OWNER_ID", "7678862761"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "")  # can be @channelusername or -100xxxxxxxxxx
DEFAULT_DELAY = int(os.getenv("DEFAULT_DELAY", "2"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.DEBUG)
log = logging.getLogger("quiz-uploader")

app = Client(
    "quiz_uploader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)
@app.on_message(filters.all)
async def debug_all(client, message):
    log.info(
        f"Update received: chat={message.chat.id}, user={message.from_user.id if message.from_user else None}, text={message.text}"
    )

# =========================
# RUNTIME STATE
# =========================
current_delay = DEFAULT_DELAY
uploading_task: Optional[asyncio.Task] = None
stop_flag = False

# =========================
# WEB SERVER (Render health check)
# =========================
async def health(request):
    return web.Response(text="OK")

async def start_web_server():
    port = int(os.getenv("PORT", "10000"))
    web_app = web.Application()
    web_app.router.add_get("/", health)
    web_app.router.add_get("/health", health)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"Web server running on port {port}")

# =========================
# HELPERS
# =========================
def is_owner(user_id: int) -> bool:
    return OWNER_ID == 0 or user_id == OWNER_ID

def clean_line(s: str) -> str:
    return s.strip().replace("\u200b", "")

def parse_txt_quiz(text: str) -> List[Dict[str, Any]]:
    """
    Format:
    Question?
    Option A*
    Option B
    Option C
    Option D
    Explanation: optional text

    Blank line separates questions.
    """
    blocks = [b.strip() for b in text.strip().split("\n\n") if b.strip()]
    quizzes: List[Dict[str, Any]] = []

    for block in blocks:
        lines = [clean_line(x) for x in block.splitlines() if clean_line(x)]
        if len(lines) < 3:
            continue

        question = lines[0]
        explanation = ""
        options: List[str] = []
        correct_index = None

        for line in lines[1:]:
            if line.lower().startswith("explanation:"):
                explanation = line.split(":", 1)[1].strip()
                continue

            starred = line.endswith("*")
            option = line[:-1].strip() if starred else line.strip()
            if option:
                if starred:
                    correct_index = len(options)
                options.append(option)

        if len(options) < 2:
            continue

        # If no starred option, take first option as default
        if correct_index is None:
            correct_index = 0

        quizzes.append(
            {
                "question": question,
                "options": options,
                "correct": correct_index,
                "explanation": explanation,
            }
        )

    return quizzes

def parse_json_quiz(text: str) -> List[Dict[str, Any]]:
    """
    Supports:
    [
      {
        "question": "...",
        "options": ["A","B","C","D"],
        "correct": 1,            # 0-based index OR
        "correct_text": "B",     # alternative
        "explanation": "..."
      }
    ]
    """
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("JSON must be a list of quiz objects")

    quizzes: List[Dict[str, Any]] = []
    for item in data:
        question = str(item.get("question", "")).strip()
        options = item.get("options", [])
        explanation = str(item.get("explanation", "")).strip()

        if not question or not isinstance(options, list) or len(options) < 2:
            continue

        options = [str(x).strip() for x in options if str(x).strip()]
        if len(options) < 2:
            continue

        correct_index = None

        if "correct" in item:
            c = item["correct"]
            if isinstance(c, int):
                correct_index = c
            elif isinstance(c, str):
                if c.isdigit():
                    correct_index = int(c)
                elif c in options:
                    correct_index = options.index(c)

        if correct_index is None and "correct_text" in item:
            ct = str(item["correct_text"]).strip()
            if ct in options:
                correct_index = options.index(ct)

        if correct_index is None:
            correct_index = 0

        if correct_index < 0 or correct_index >= len(options):
            correct_index = 0

        quizzes.append(
            {
                "question": question,
                "options": options,
                "correct": correct_index,
                "explanation": explanation,
            }
        )

    return quizzes

def parse_quiz_file(text: str, filename: str = "") -> List[Dict[str, Any]]:
    ext = os.path.splitext(filename.lower())[1]
    if ext == ".json":
        return parse_json_quiz(text)
    if ext == ".txt" or ext == "":
        # try JSON first if text looks like JSON
        stripped = text.lstrip()
        if stripped.startswith("[") or stripped.startswith("{"):
            try:
                return parse_json_quiz(text)
            except Exception:
                pass
        return parse_txt_quiz(text)

    # fallback: try JSON, then TXT
    try:
        return parse_json_quiz(text)
    except Exception:
        return parse_txt_quiz(text)

async def get_text_from_message(msg: Message) -> Tuple[str, str]:
    """
    Returns: (text, filename)
    Supports reply to document or using text directly.
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
        # support /uploadquiz followed by raw pasted content
        parts = msg.text.split(None, 1)
        if len(parts) > 1:
            return parts[1], "quiz.txt"

    raise ValueError("Please reply to a TXT/JSON file or send quiz text after the command.")

def resolve_channel(arg: str = "") -> str:
    target = (arg or "").strip() or str(CHANNEL_ID).strip()
    if not target:
        raise ValueError("CHANNEL_ID is not set. Use /setchannel or set env CHANNEL_ID.")
    return target

async def upload_quizzes(
    client: Client,
    quizzes: List[Dict[str, Any]],
    chat_id: str,
    reply_msg: Optional[Message] = None
):
    global stop_flag
    total = len(quizzes)
    stop_flag = False

    status = None
    if reply_msg:
        status = await reply_msg.reply_text(f"Starting upload of {total} quiz questions...")

    for idx, q in enumerate(quizzes, start=1):
        if stop_flag:
            if status:
                await status.edit_text(f"Stopped at {idx-1}/{total}.")
            return

        question = q["question"]
        options = q["options"]
        correct = int(q["correct"])
        explanation = q.get("explanation", "") or ""

        if len(options) < 2:
            continue

        if correct < 0 or correct >= len(options):
            correct = 0

        try:
            await client.send_poll(
                chat_id=chat_id,
                question=question[:300],
                options=options[:10],
                is_anonymous=True,
                type="quiz",
                correct_option_id=correct,
                explanation=explanation[:200] if explanation else None,
            )
        except Exception as e:
            log.exception("Failed to send poll %s", idx)
            if status:
                await status.edit_text(f"Error at {idx}/{total}: {e}")
            return

        if status and (idx == 1 or idx % 5 == 0 or idx == total):
            await status.edit_text(f"Uploaded {idx}/{total} quizzes...")

        await asyncio.sleep(max(0, current_delay))

    if status:
        await status.edit_text(f"Done. Uploaded {total}/{total} quiz questions.")

# =========================
# COMMANDS
# =========================
@app.on_message(filters.private)
async def test(client, message):
    log.info("TEST HANDLER")
    await message.reply_text("Hello")

@app.on_message(filters.command("help") & filters.private)
async def help_cmd(client: Client, message: Message):
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
async def setdelay_cmd(client: Client, message: Message):
    global current_delay
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply_text(f"Current delay: {current_delay} sec\nUse: /setdelay 2")

    try:
        d = int(parts[1].strip())
        if d < 0 or d > 3600:
            raise ValueError
        current_delay = d
        await message.reply_text(f"Delay updated to {current_delay} seconds.")
    except Exception:
        await message.reply_text("Send a valid number. Example: /setdelay 2")

@app.on_message(filters.command("setchannel") & filters.private)
async def setchannel_cmd(client: Client, message: Message):
    global CHANNEL_ID
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply_text("Use: /setchannel @channelusername or -100xxxxxxxxxx")

    CHANNEL_ID = parts[1].strip()
    await message.reply_text(f"Channel set to: `{CHANNEL_ID}`", quote=True)

@app.on_message(filters.command("stop") & filters.private)
async def stop_cmd(client: Client, message: Message):
    global stop_flag
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")
    stop_flag = True
    await message.reply_text("Stop signal sent.")

@app.on_message(filters.command("uploadquiz") & filters.private)
async def uploadquiz_cmd(client: Client, message: Message):
    global uploading_task

    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    if uploading_task and not uploading_task.done():
        return await message.reply_text("An upload is already running. Use /stop first.")

    try:
        target = resolve_channel()
    except Exception as e:
        return await message.reply_text(str(e))

    try:
        text, filename = await get_text_from_message(message)
        quizzes = parse_quiz_file(text, filename)
        if not quizzes:
            return await message.reply_text("No valid quiz questions found in file.")

        await message.reply_text(f"Found {len(quizzes)} quiz questions. Uploading to {target}...")

        async def runner():
            await upload_quizzes(client, quizzes, target, reply_msg=message)

        uploading_task = asyncio.create_task(runner())
        await uploading_task

    except Exception as e:
        log.exception("Upload failed")
        await message.reply_text(f"Error: {e}")

# Allow sending a document directly while replying to /uploadquiz
@app.on_message(filters.document & filters.private)
async def document_handler(client: Client, message: Message):
    if not is_owner(message.from_user.id):
        return

    # Only process if user replies to /uploadquiz or the document caption says uploadquiz
    caption = (message.caption or "").lower()
    if "uploadquiz" not in caption:
        return

    if uploading_task and not uploading_task.done():
        return await message.reply_text("An upload is already running. Use /stop first.")

    try:
        target = resolve_channel()
        text, filename = await get_text_from_message(message)
        quizzes = parse_quiz_file(text, filename)
        if not quizzes:
            return await message.reply_text("No valid quiz questions found in file.")

        async def runner():
            await upload_quizzes(client, quizzes, target, reply_msg=message)
            global uploading_task
            uploading_task = asyncio.create_task(runner())
            await uploading_task

    except Exception as e:
        log.exception("Document upload failed")
        await message.reply_text(f"Error: {e}")

# =========================
# MAIN
# =========================
async def main():
    if not API_ID or not API_HASH or not BOT_TOKEN:
        raise RuntimeError("Set API_ID, API_HASH, BOT_TOKEN in environment variables.")
    if OWNER_ID == 0:
        log.warning("OWNER_ID is not set. Bot will accept all users (not recommended).")

    await app.start()
    me = await app.get_me()
    log.info(f"Logged in as @{me.username} ({me.id})")
    log.info("Bot started")
    asyncio.create_task(start_web_server())
    await idle()
    await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

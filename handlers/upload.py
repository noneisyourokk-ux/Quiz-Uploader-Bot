import os
import json
import asyncio
from typing import List, Dict, Any, Tuple, Optional

from pyrogram.types import Message

from config import OWNER_ID, CHANNEL_ID, DEFAULT_DELAY

def is_owner(user_id: int) -> bool:
    return OWNER_ID == 0 or user_id == OWNER_ID

def clean_line(s: str) -> str:
    return s.strip().replace("\u200b", "")

def parse_txt_quiz(text: str) -> List[Dict[str, Any]]:
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
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("JSON must be a list")

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

        correct_index = 0
        if "correct" in item:
            c = item["correct"]
            if isinstance(c, int):
                correct_index = c
            elif isinstance(c, str):
                if c.isdigit():
                    correct_index = int(c)
                elif c in options:
                    correct_index = options.index(c)

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
        stripped = text.lstrip()
        if stripped.startswith("[") or stripped.startswith("{"):
            try:
                return parse_json_quiz(text)
            except Exception:
                pass
        return parse_txt_quiz(text)

    try:
        return parse_json_quiz(text)
    except Exception:
        return parse_txt_quiz(text)

async def get_text_from_message(msg: Message) -> Tuple[str, str]:
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

def resolve_channel(state: dict) -> str:
    target = (state.get("channel_id") or "").strip() or str(CHANNEL_ID).strip()
    if not target:
        raise ValueError("CHANNEL_ID is not set. Use /setchannel or set env CHANNEL_ID.")
    return target

async def upload_quizzes(client, quizzes: List[Dict[str, Any]], chat_id: str, reply_msg: Optional[Message], state: dict):
    total = len(quizzes)
    state["stop"] = False

    status = None
    if reply_msg:
        status = await reply_msg.reply_text(f"Starting upload of {total} quiz questions...")

    for idx, q in enumerate(quizzes, start=1):
        if state.get("stop"):
            if status:
                await status.edit_text(f"Stopped at {idx-1}/{total}.")
            return

        question = q["question"]
        options = q["options"]
        correct = int(q["correct"])
        explanation = q.get("explanation", "") or ""

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
            if status:
                await status.edit_text(f"Error at {idx}/{total}: {e}")
            return

        if status and (idx == 1 or idx % 5 == 0 or idx == total):
            await status.edit_text(f"Uploaded {idx}/{total} quizzes...")

        await asyncio.sleep(max(0, int(state.get("delay", DEFAULT_DELAY))))

    if status:
        await status.edit_text(f"Done. Uploaded {total}/{total} quiz questions.")

async def uploadquiz_cmd(client, message: Message, state: dict):
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    if state.get("uploading"):
        return await message.reply_text("An upload is already running. Use /stop first.")

    try:
        target = resolve_channel(state)
    except Exception as e:
        return await message.reply_text(str(e))

    try:
        text, filename = await get_text_from_message(message)
        quizzes = parse_quiz_file(text, filename)
        if not quizzes:
            return await message.reply_text("No valid quiz questions found in file.")

        await message.reply_text(f"Found {len(quizzes)} quiz questions. Uploading to {target}...")

        state["uploading"] = True
        await upload_quizzes(client, quizzes, target, reply_msg=message, state=state)

    except Exception as e:
        await message.reply_text(f"Error: {e}")
    finally:
        state["uploading"] = False

async def document_handler(client, message: Message, state: dict):
    if not is_owner(message.from_user.id):
        return

    caption = (message.caption or "").lower()
    if "uploadquiz" not in caption:
        return

    if state.get("uploading"):
        return await message.reply_text("An upload is already running. Use /stop first.")

    try:
        target = resolve_channel(state)
        text, filename = await get_text_from_message(message)
        quizzes = parse_quiz_file(text, filename)
        if not quizzes:
            return await message.reply_text("No valid quiz questions found in file.")

        state["uploading"] = True
        await upload_quizzes(client, quizzes, target, reply_msg=message, state=state)

    except Exception as e:
        await message.reply_text(f"Error: {e}")
    finally:
        state["uploading"] = False

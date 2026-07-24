import asyncio
import logging
from typing import List, Dict, Any, Optional

from pyrogram.types import Message

log = logging.getLogger(__name__)


async def upload_quizzes(
    client,
    quizzes: List[Dict[str, Any]],
    chat_id: str,
    state: dict,
    reply_msg: Optional[Message] = None,
    default_delay: int = 2,
):
    """
    Upload quiz polls to a Telegram channel/chat.
    State keys used:
      - stop: bool
      - delay: int
    """
    total = len(quizzes)
    state["stop"] = False

    status = None
    if reply_msg:
        status = await reply_msg.reply_text(f"Starting upload of {total} quiz questions...")

    for idx, q in enumerate(quizzes, start=1):
        if state.get("stop"):
            if status:
                await status.edit_text(f"Stopped at {idx - 1}/{total}.")
            return

        question = str(q.get("question", "")).strip()
        options = q.get("options", [])
        correct = int(q.get("correct", 0))
        explanation = str(q.get("explanation", "")).strip()

        if not question or not isinstance(options, list) or len(options) < 2:
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

        delay = int(state.get("delay", default_delay))
        if delay > 0:
            await asyncio.sleep(delay)

    if status:
        await status.edit_text(f"Done. Uploaded {total}/{total} quiz questions.")

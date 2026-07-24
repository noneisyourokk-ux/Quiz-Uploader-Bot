import asyncio
from telegram import Bot
from telegram.constants import PollType
import config

async def upload_quizzes_to_channel(bot: Bot, quizzes: list, delay: float = 2.0) -> int:
    """Uploads a list of quiz dicts to the target Telegram Channel."""
    count = 0
    for quiz in quizzes:
        await bot.send_poll(
            chat_id=config.CHANNEL_ID,
            question=quiz["question"],
            options=quiz["options"],
            type=PollType.QUIZ,
            correct_option_id=quiz["correct_option_id"],
            explanation=quiz.get("explanation", ""),
            is_anonymous=True
        )
        count += 1
        await asyncio.sleep(delay)  # Prevent rate limits
    return count

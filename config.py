import os
from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int = 0) -> int:
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError:
        return default


API_ID = _get_int("API_ID")
API_HASH = os.getenv("API_HASH", "").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID = _get_int("OWNER_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()
DEFAULT_DELAY = _get_int("DEFAULT_DELAY", 2)
PORT = _get_int("PORT", 10000)

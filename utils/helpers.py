from typing import Optional


def is_owner(user_id: int, owner_id: int) -> bool:
    return owner_id == 0 or user_id == owner_id


def normalize_channel_id(channel_id: Optional[str]) -> str:
    return str(channel_id or "").strip()


def clip_text(text: str, limit: int) -> str:
    text = text or ""
    return text[:limit]

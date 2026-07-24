from pyrogram.types import Message

from config import OWNER_ID

def is_owner(user_id: int) -> bool:
    return OWNER_ID == 0 or user_id == OWNER_ID

async def setdelay_cmd(client, message: Message, state: dict):
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply_text(f"Current delay: {state['delay']} sec\nUse: /setdelay 2")

    try:
        d = int(parts[1].strip())
        if d < 0 or d > 3600:
            raise ValueError
        state["delay"] = d
        await message.reply_text(f"Delay updated to {state['delay']} seconds.")
    except Exception:
        await message.reply_text("Send a valid number. Example: /setdelay 2")

async def setchannel_cmd(client, message: Message, state: dict):
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply_text("Use: /setchannel @channelusername or -100xxxxxxxxxx")

    state["channel_id"] = parts[1].strip()
    await message.reply_text(f"Channel set to: `{state['channel_id']}`", quote=True)

async def stop_cmd(client, message: Message, state: dict):
    if not is_owner(message.from_user.id):
        return await message.reply_text("This bot is owner-only.")
    state["stop"] = True
    await message.reply_text("Stop signal sent.")

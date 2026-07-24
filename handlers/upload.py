from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import is_admin
from utils.parser import parse_file_content
from utils.uploader import upload_quizzes_to_channel

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    doc = update.message.document
    if not (doc.file_name.endswith(".txt") or doc.file_name.endswith(".json")):
        await update.message.reply_text("⚠️ Please send a valid `.txt` or `.json` file.")
        return

    status_msg = await update.message.reply_text("📥 Processing file...")

    try:
        telegram_file = await context.bot.get_file(doc.file_id)
        byte_content = await telegram_file.download_as_bytearray()
        content_str = byte_content.decode("utf-8")

        quizzes = parse_file_content(content_str, doc.file_name)
        
        if not quizzes:
            await status_msg.edit_text("❌ Failed to parse any valid quizzes from the file.")
            return

        await status_msg.edit_text(f"🚀 Uploading {len(quizzes)} quizzes to channel...")
        uploaded_count = await upload_quizzes_to_channel(context.bot, quizzes)

        await status_msg.edit_text(f"🎉 Successfully posted {uploaded_count} quizzes to channel!")

    except Exception as e:
        await status_msg.edit_text(f"❌ An error occurred: {str(e)}")

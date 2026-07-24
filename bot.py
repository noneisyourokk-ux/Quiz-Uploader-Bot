import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import config
from handlers.start import start_handler, help_handler
from handlers.upload import handle_document
from handlers.admin import status_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def main():
    if not config.BOT_TOKEN or config.BOT_TOKEN == "8683892422:AAFBEVW0vxbRxqpObQsyGWcQtb1-N6wB6DU":
        raise ValueError("BOT_TOKEN is missing in environment variables!")

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("status", status_handler))
    
    # Document Upload Handler
    app.add_handler(MessageHandler(filters.ATTACHMENT & (~filters.COMMAND), handle_document))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

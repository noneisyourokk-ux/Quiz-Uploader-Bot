import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8683892422:AAFBEVW0vxbRxqpObQsyGWcQtb1-N6wB6DU")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "7678862761").split(",") if x.strip()]
CHANNEL_ID = os.getenv("CHANNEL_ID", "@pdf_book_channel")

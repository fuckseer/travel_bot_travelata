from utils.config import load_config
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot_service import handlers

config = load_config()

def main():
    token = config["telegram"]["token"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))

    print("🤖 Travel Bot поднят и ждёт сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()
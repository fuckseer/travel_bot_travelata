from telegram import Update
from telegram.ext import ContextTypes
from bot_service.core import process_user_query

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет 👋 Напиши куда и когда хочешь поехать.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print(f"✉️ Received from user: {user_text}")
    response = process_user_query(user_text)
    await update.message.reply_text(response)
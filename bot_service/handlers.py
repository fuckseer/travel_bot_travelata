# bot_service/handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from bot_service.core import process_user_query

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет 👋 Я TravelBot! Напиши, куда и когда хочешь поехать."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    response = process_user_query(query)
    await update.message.reply_text(response)
import asyncio
from aiogram import Bot
from aiogram.types import FSInputFile
from main import API_TOKEN

async def send_file(USER_ID, file_path):
    bot = Bot(token=API_TOKEN)
    user_id = USER_ID  # например, 123456789
    
    document = FSInputFile(file_path)
    await bot.send_document(chat_id=user_id, document=document)
    await bot.session.close()  # обязательно закрыть сессию

async def send_text_message(USER_ID, text):
    """Отправка текстового сообщения в Telegram"""
    bot = Bot(token=API_TOKEN)
    user_id = USER_ID
    
    await bot.send_message(chat_id=user_id, text=text)
    await bot.session.close()


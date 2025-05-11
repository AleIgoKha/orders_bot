from aiogram import Router
from aiogram.types import Message

messages_remover = Router()

# Удаляет сообщения вне хэндлеров
@messages_remover.message()
async def odd_messages_remover(message: Message, removed: bool = False):
    if not removed:
        await message.delete()
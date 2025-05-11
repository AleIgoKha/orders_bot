from aiogram import BaseMiddleware
from aiogram.types import Message

# Удаляем сообщения заходящие в обработчики
class MessagesRemover(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.text != '/start':
            await event.delete()
            data['removed'] = True
        return await handler(event, data)
    
# class DoubleStartPreventer(BaseMiddleware):
#     async def __call__(self, handler, event, data):
#         if event.text != '/start':
            
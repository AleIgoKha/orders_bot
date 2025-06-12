from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Any, Awaitable
from aiogram.types import CallbackQuery

# Удаляем сообщения заходящие в обработчики
class MessagesRemover(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.text != '/start':
            await event.delete()
            data['removed'] = True
        return await handler(event, data)


class OutOfPagesAnswer(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any]
    ) -> Any:
        result = await handler(event, data) 

        if event.data.endswith('page_edge'):
            await event.answer(
                text='Крайняя страница',
            )
        return result
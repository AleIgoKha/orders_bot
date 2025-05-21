import os
import asyncio
# import logging
import redis.asyncio as aioredis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from dotenv import load_dotenv

from app.message_remover import messages_remover
from app.main_menu.main_menu import main_menu

from app.main_menu.products.products_menu import products_menu

from app.main_menu.sessions.session.order_downloading.order_downloading import order_downloading
from app.main_menu.sessions.sessions_menu import sessions_menu
from app.main_menu.sessions.session.session_menu import session_menu
from app.main_menu.sessions.session.order_changing.order_changing import order_changing
from app.main_menu.sessions.session.order_creation.order_creation import order_creation
from app.main_menu.sessions.session.order_processing.order_processing import order_processing
from app.main_menu.sessions.session.completed_orders.completed_orders import completed_orders
from app.main_menu.sessions.session.session_stats.session_stats import session_stats

from app.database.models import async_main
from app.middlewares import MessagesRemover

async def main():
    load_dotenv()
    redis = await aioredis.from_url(os.getenv(f'REDIS_URL'))
    bot = Bot(token=os.getenv('TG_TOKEN'))
    dp = Dispatcher(storage=RedisStorage(redis))
    dp.message.middleware(MessagesRemover())
    dp.include_routers(main_menu,
                       sessions_menu,
                       products_menu,
                       session_menu,
                       order_creation,
                       order_processing,
                       order_changing,
                       completed_orders,
                       session_stats,
                       order_downloading,
                       messages_remover)
    dp.startup.register(on_startup)
    await dp.start_polling(bot)
    
async def on_startup(*args):
    await async_main()

if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
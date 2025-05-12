import os
import asyncio
# import logging
import redis.asyncio as aioredis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from dotenv import load_dotenv

from app.message_remover import messages_remover
from app.main_menu import main_menu

from app.products_menu.products_menu import products_menu

from app.orders_menu.orders_menu import orders_menu
from app.orders_menu.change_order import change_order
from app.orders_menu.order_creation.order_creation import order_creation
from app.orders_menu.order_processing.order_processing import order_processing
from app.orders_menu.completed_orders.completed_orders import completed_orders

from app.stats_menu.stats_menu import stats_menu

from app.database.models import async_main
from app.middlewares import MessagesRemover

async def main():
    load_dotenv()
    redis = await aioredis.from_url(os.getenv(f'REDIS_URL'))
    bot = Bot(token=os.getenv('TG_TOKEN'))
    dp = Dispatcher(storage=RedisStorage(redis))
    dp.message.middleware(MessagesRemover())
    dp.include_routers(main_menu,
                       products_menu,
                       orders_menu,
                       stats_menu,
                       order_creation,
                       order_processing,
                       change_order,
                       completed_orders,
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
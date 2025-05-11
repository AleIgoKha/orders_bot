from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Filter, Command
from aiogram.fsm.context import FSMContext

import app.stats_menu.keyboard as kb
from app.states import Product

stats_menu = Router()


# Раздел статистики
@stats_menu.callback_query(F.data == 'stats')
async def stats_menu_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='Статистика', reply_markup=kb.stats_menu)
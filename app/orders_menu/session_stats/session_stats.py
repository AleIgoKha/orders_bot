from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime

import app.orders_menu.session_stats.keyboard as kb
from app.states import Session
from app.database.requests import get_orders_items, get_session_items_stats
from app.com_func import group_orders_items

session_stats = Router()


# открываем меню со статистикой сессии и предлагаем выбрать категорию
@session_stats.callback_query(F.data == 'stats_orders_menu')
async def stats_orders_menu_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ КАТЕГОРИЮ СТАТИСТИКИ</b> ❓',
                                     reply_markup=kb.stats_orders_menu,
                                     parse_mode='HTML')
    

# статистика по количеству товаров
@session_stats.callback_query(F.data == 'products_stats')
async def products_stats_handler(callback: CallbackQuery, state: FSMContext):
    # Запрашиваем данные для всех заказов сессии
    data = await state.get_data()
    session_id = data['session_id']
    items_stats = await get_session_items_stats(session_id)
    
    text = f'📈 <b>СТАТИСТИКА ЗАКАЗАННЫХ ТОВАРОВ</b> 🧀\n\n' \
    
    est_revenue = 0
    exp_revenue = 0
    for item_stats in items_stats:
        text += f'🧀 <b>{item_stats[0]}</b>\n' \
                f'Всего заказано - <b>{item_stats[2]} {item_stats[1]}</b>\n'
                
        if item_stats[1] == 'кг':
            text += f'Всего взвешено - <b>{item_stats[3]} {item_stats[1]}</b>\n'
            
        text += f'Заказано в вакууме - <b>{item_stats[6]} шт.</b>\n\n'
                
        est_revenue += item_stats[4] # по заказанным количествам
        exp_revenue += item_stats[5] # по фактическим количествам
        if item_stats[1] == 'шт.':
            exp_revenue = est_revenue
        
    text += f'<b>💸 Ожидаемая выручка (без учета вак. уп.)</b>\n' \
            f'По зазанному количеству - <b>{est_revenue} р</b>\n' \
            f'По взвешенному количеству - <b>{est_revenue} р</b>'
        
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.back_stats_orders_menu,
                                    parse_mode='HTML')
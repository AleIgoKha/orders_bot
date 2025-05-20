from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext


import app.main_menu.sessions.statistics.keyboard as kb
from app.database.requests import get_session_items_stats, get_orders, get_session

session_stats = Router()

# статистика по количеству товаров
@session_stats.callback_query(F.data == 'back_to_stats_orders_menu')
@session_stats.callback_query(F.data == 'stats_orders_menu')
async def products_stats_handler(callback: CallbackQuery, state: FSMContext):
    # Запрашиваем данные для всех заказов сессии
    data = await state.get_data()
    session_id = data['session_id']
    orders_data = await get_orders(session_id)
    items_stats = await get_session_items_stats(session_id)
    
    text = f'📈 <b>СТАТИСТИКА ТЕКУЩЕЙ СЕССИИ</b> 🧀\n\n' \
            f'Общее количество заказов - <b>{len(orders_data)}</b>\n\n'
    
    
    est_revenue = 0
    exp_revenue = 0
    for item_stats in items_stats:
        text += f'🧀 <b>{item_stats[0]}</b>\n'
                
        if item_stats[1] == 'кг':
            text += f'Всего заказано - <b>{round(item_stats[2], 3)} {item_stats[1]}</b>\n' \
                    f'Всего взвешено - <b>{round(item_stats[3], 3)} {item_stats[1]}</b>\n'
                    
        else:
            text += f'Всего заказано - <b>{round(item_stats[2])} {item_stats[1]}</b>\n' \
                    f'Всего взвешено - <b>{round(item_stats[3])} {item_stats[1]}</b>\n'
            
        text += f'Заказано в вакууме - <b>{round(item_stats[6])} шт.</b>\n\n'
                
        est_revenue += item_stats[4] # по заказанным количествам
        exp_revenue += item_stats[5] # по фактическим количествам
    
    text += f'<b>💸 Ожидаемая выручка (без учета вак. уп.)</b>\n' \
            f'По зазанному количеству - <b>{round(est_revenue)} р</b>\n' \
            f'По взвешенному количеству - <b>{round(exp_revenue)} р</b>'
    
    
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.stats_orders_menu,
                                    parse_mode='HTML')
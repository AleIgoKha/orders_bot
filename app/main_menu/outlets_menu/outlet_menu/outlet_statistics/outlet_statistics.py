from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime

import app.main_menu.outlets_menu.outlet_menu.outlet_statistics.keyboard as kb
from app.main_menu.main_menu import main_menu_handler 
from app.states import Outlet
from app.database.all_requests.outlet_statistics import selling_statistics
from app.com_func import represent_utc_3

outlet_statistics = Router()


# меню статистики
@outlet_statistics.callback_query(F.data == 'outlet:statistics')
@outlet_statistics.callback_query(F.data.startswith('outlet:statistics:month:prev:'))
@outlet_statistics.callback_query(F.data.startswith('outlet:statistics:month:next:'))
async def outlet_statistics_handler(callback: CallbackQuery):
    now = represent_utc_3(datetime.now())
    year = now.year
    month = now.month
    # Переключаем месяца вперед и назад
    if callback.data.startswith('outlet:statistics:month:'):
        calendar_data = callback.data.split(':')
        if calendar_data[3] == 'prev':
            year = int(calendar_data[4])
            month = int(calendar_data[5]) - 1
            if month < 1:
                month = 12
                year -= 1
        elif calendar_data[3] == 'next':
            year = int(calendar_data[4])
            month = int(calendar_data[5]) + 1
            if month > 12:
                month = 1
                year += 1
        await callback.message.edit_reply_markup(reply_markup=kb.calendar_keyboard(year, month))
    else:
        await callback.message.edit_text(text=f'❓ <b>УКАЖИТЕ ДАТУ СТАТИСТИКИ</b>\n\n',
                                        reply_markup=kb.calendar_keyboard(year, month),
                                        parse_mode='HTML')
        

# заходим в статистику дня
@outlet_statistics.callback_query(F.data.startswith('outlet:statistics:date:'))
async def outlet_statistics_date_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    
    date_comp = [int(_) for _ in callback.data.split(':')[-3:]]
    finished_datetime = datetime(year=date_comp[0],
                            month=date_comp[1],
                            day=date_comp[2])
    
    aware_dt = represent_utc_3(finished_datetime)
    
    selling_statistics_data = await selling_statistics(outlet_id, aware_dt)
    
    text = 'Статистика за день\n\n'
    
    for product_statistics in selling_statistics_data:
        product_name = product_statistics['product_name']
        product_sum_qty = product_statistics['product_sum_qty']
        product_unit = product_statistics['product_unit']
        product_revenue = product_statistics['product_revenue']
        product_balance = product_statistics['product_balance']
        
        text += f'{product_name}:\nПродано{product_sum_qty} {product_unit}\nОжидаемая выручка{product_revenue} руб\nОстаток {product_balance} {product_unit}\n\n'
        
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.back_button,
                                     parse_mode='HTML')
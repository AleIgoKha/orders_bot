from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
import pytz

import app.main_menu.outlets_menu.outlet_menu.outlet_statistics.keyboard as kb
from app.database.all_requests.outlet_statistics import selling_statistics
from app.com_func import localize_user_input

outlet_statistics = Router()

# меню статистики
@outlet_statistics.callback_query(F.data == 'outlet:statistics')
async def stats_menu_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ВИД СТАТИСТИКИ</b>',
                                     reply_markup=kb.stats_menu,
                                     parse_mode='HTML')

# меню выбора дня для экспресс статистики
@outlet_statistics.callback_query(F.data == 'outlet:statistics:express')
@outlet_statistics.callback_query(F.data.startswith('outlet:statistics:month:prev:'))
@outlet_statistics.callback_query(F.data.startswith('outlet:statistics:month:next:'))
async def outlet_statistics_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_id = data['outlet_id']
    
    now = localize_user_input(datetime.now(pytz.timezone("Europe/Chisinau")))
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
        await callback.message.edit_reply_markup(reply_markup=await kb.calendar_keyboard(outlet_id, year, month))
    else:
        await callback.message.edit_text(text=f'❓ <b>УКАЖИТЕ ДАТУ СТАТИСТИКИ</b>\n\n',
                                        reply_markup=await kb.calendar_keyboard(outlet_id, year, month),
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
    
    selling_statistics_data = await selling_statistics(outlet_id, finished_datetime)
    
    # если заказов не было то выводим предупреждение
    if len(selling_statistics_data) == 0:
        await callback.answer(text='Нет статистики за выбранный день')
        return None
    
    text = f'📊 <b>СТАТИСТИКА ЗА {finished_datetime.strftime('%d-%m-%Y')}</b>\n\n'
    
    total_revenue = 0
    
    for product_statistics in selling_statistics_data:
        product_name = product_statistics['product_name']
        product_sum_qty = round(product_statistics['product_sum_qty'], 3)
        product_unit = product_statistics['product_unit']
        product_revenue = round(product_statistics['product_revenue'], 2)
        
        if product_unit != 'кг':
            product_sum_qty = round(product_sum_qty)
        
        text += f'🧀 <b>{product_name}:</b>\n' \
                f'Продано - <b>{product_sum_qty} {product_unit}</b>\n' \
                f'Ожидаемая выручка - <b>{product_revenue} руб</b>\n\n'
                
        total_revenue += product_revenue
        
    text += f'<b>Общая ожидаемая выручка - {round(total_revenue, 2)} руб</b>'
        
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.back_button,
                                     parse_mode='HTML')
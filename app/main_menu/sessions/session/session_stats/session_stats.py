from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from app.com_func import represent_utc_3
import app.main_menu.sessions.session.session_stats.keyboard as kb
from app.database.requests import get_session_stats, get_orders_by_date, get_items


session_stats = Router()


# меню статистики
@session_stats.callback_query(F.data == 'session:stats_menu')
async def stats_menu(callback: CallbackQuery):
    await callback.message.edit_text(text=f'❓ <b>ВЫБЕРИТЕ ВИД СТАТИСТИКИ</b>\n\n',
                                reply_markup=kb.stats_menu,
                                parse_mode='HTML')


# Выбираем дату за которую нужно посмотреть статистику
@session_stats.callback_query(F.data == 'stats_menu:not_issued')
@session_stats.callback_query(F.data == 'stats_menu:issued')
@session_stats.callback_query(F.data.startswith('stats_menu:month:prev:'))
@session_stats.callback_query(F.data.startswith('stats_menu:month:next:'))
async def new_session_handler(callback: CallbackQuery, state: FSMContext):
    # запоминаем, чтобы далее различать выданные или не выданные заказы
    if not callback.data.startswith('stats_menu:month:'):
        callback_name = callback.data.split(':')[-1]
        await state.update_data(callback_name=callback_name)
    
    data = await state.get_data()
    callback_name = data['callback_name']
    
    await state.set_state(None)
    now = represent_utc_3(datetime.now())
    year = now.year
    month = now.month
    # Переключаем месяца вперед и назад
    if callback.data.startswith('stats_menu:month:'):
        calendar_data = callback.data.split(':')
        if calendar_data[2] == 'prev':
            year = int(calendar_data[3])
            month = int(calendar_data[4]) - 1
            if month < 1:
                month = 12
                year -= 1
        elif calendar_data[2] == 'next':
            year = int(calendar_data[3])
            month = int(calendar_data[4]) + 1
            if month > 12:
                month = 1
                year += 1
        await callback.message.edit_reply_markup(reply_markup=kb.create_calendar_keyboard(callback_name, year, month))
    else:
        await callback.message.edit_text(text=f'❓ <b>УКАЖИТЕ ДАТУ СТАТИСТИКИ</b>\n\n',
                                        reply_markup=kb.create_calendar_keyboard(callback_name, year, month),
                                        parse_mode='HTML')
    # await state.set_state(Stats.date)


# статистика по выданным заказам за конкретный день
@session_stats.callback_query(F.data.startswith('stats_menu:issued:date:'))
async def issue_datetime_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    session_id = data['session_id']

    # формируем время выдачи
    date_comp = [int(_) for _ in callback.data.split(':')[-3:]]
    finished_datetime = datetime(year=date_comp[0],
                              month=date_comp[1],
                              day=date_comp[2])
    
    # получаем номера заказов
    orders = await get_orders_by_date(session_id=session_id,
                                     datetime=finished_datetime,
                                     issued=True)
    
    if len(orders) == 0:
        await callback.answer(text='Нет выданных заказов за этот день')
        return None
    
    text = f'📈 <b>СТАТИСТИКА СЕССИИ ПО ВЫДАННЫМ ЗАКАЗАМ ЗА {finished_datetime.strftime('%d-%m-%Y')}</b> \n\n'

    total_income = 0
    
    for order in orders:
        # получаем все товары одного заказа
        items = await get_items(order.order_id)
        for item in items:
            # считаем стоимость вакуума, если он есть
            if item.item_vacc:
                if item.item_qty_fact == 0:
                    vacc_price = 0
                elif 0 < item.item_qty_fact < 200:
                    vacc_price = 5
                elif 200 <= item.item_qty_fact < 300:
                    vacc_price = 6
                elif 300 <= item.item_qty_fact:
                    vacc_price = (item.item_qty_fact * 2) / 100
            else:
                vacc_price = 0
            
            total_income += item.item_qty_fact * item.item_price + vacc_price
    
    items_stats = await get_session_stats(session_id,
                                          datetime=finished_datetime,
                                          issued=True)
    
    for item_stats in items_stats:
        text += f'🧀 <b>{item_stats[0]}</b>\n'
                
        if item_stats[1] == 'кг':
            text += f'Всего продано - <b>{round(item_stats[2], 3)} {item_stats[1]}</b>\n'
                    
        else:
            text += f'Всего продано - <b>{round(item_stats[3])} {item_stats[1]}</b>\n'
            
        text += f'Продано в вакууме - <b>{round(item_stats[4])} шт.</b>\n\n'
    
    text += f'🛍 Выдано заказов - <b>{len(orders)}</b>\n'
    text += f'💸 Рассчетная выручка - <b>{round(total_income)} руб.</b>'
    
    # Выводим сообщение
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.session_stats,
                                    parse_mode='HTML')


# статистика по выданным заказам за все время
@session_stats.callback_query(F.data == 'stats_menu:issued:total_stats')
async def issue_datetime_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    session_id = data['session_id']
    
    # получаем номера заказов
    orders = await get_orders_by_date(session_id=session_id,
                                     issued=True)
    
    text = f'📈 <b>СТАТИСТИКА СЕССИИ ПО ВЫДАННЫМ ЗАКАЗАМ ЗА ВСЕ ВРЕМЯ</b> \n\n'

    total_income = 0
    
    for order in orders:
        # получаем все товары одного заказа
        items = await get_items(order.order_id)
        for item in items:
            # считаем стоимость вакуума, если он есть
            if item.item_vacc:
                if item.item_qty_fact == 0:
                    vacc_price = 0
                elif 0 < item.item_qty_fact < 200:
                    vacc_price = 5
                elif 200 <= item.item_qty_fact < 300:
                    vacc_price = 6
                elif 300 <= item.item_qty_fact:
                    vacc_price = (item.item_qty_fact * 2) / 100
            else:
                vacc_price = 0
            
            total_income += item.item_qty_fact * item.item_price + vacc_price
    
    items_stats = await get_session_stats(session_id,
                                          issued=True)
    
    for item_stats in items_stats:
        text += f'🧀 <b>{item_stats[0]}</b>\n'
                
        if item_stats[1] == 'кг':
            text += f'Всего продано - <b>{round(item_stats[2], 3)} {item_stats[1]}</b>\n'
                    
        else:
            text += f'Всего продано - <b>{round(item_stats[3])} {item_stats[1]}</b>\n'
            
        text += f'Продано в вакууме - <b>{round(item_stats[4])} шт.</b>\n\n'
    
    text += f'🛍 Выдано заказов - <b>{len(orders)}</b>\n'
    text += f'💸 Рассчетная выручка - <b>{round(total_income)} руб.</b>'
    
    # Выводим сообщение
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.session_stats,
                                    parse_mode='HTML')


# статистика по не выданным заказам за отдельный день
@session_stats.callback_query(F.data.startswith('stats_menu:not_issued:date:'))
async def products_stats_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    session_id = data['session_id']
    print(data)
    # формируем время выдачи
    date_comp = [int(_) for _ in callback.data.split(':')[-3:]]
    creation_datetime = datetime(year=date_comp[0],
                              month=date_comp[1],
                              day=date_comp[2])
    
    # получаем номера заказов
    orders = await get_orders_by_date(session_id=session_id,
                                      datetime=creation_datetime,
                                      issued=False)
    
    if len(orders) == 0:
        await callback.answer(text='Нет выданных заказов за этот день')
        return None
    
    text = f'📈 <b>СТАТИСТИКА СЕССИИ ПО НЕ ВЫДАННЫМ ЗАКАЗАМ ЗА {creation_datetime.strftime('%d-%m-%Y')}</b> \n\n'

    est_revenue = 0
    
    for order in orders:
        # получаем все товары одного заказа
        items = await get_items(order.order_id)
        for item in items:
            # считаем стоимость вакуума, если он есть
            if item.item_vacc:
                if item.item_qty == 0:
                    vacc_price = 0
                elif 0 < item.item_qty < 200:
                    vacc_price = 5
                elif 200 <= item.item_qty < 300:
                    vacc_price = 6
                elif 300 <= item.item_qty:
                    vacc_price = (item.item_qty * 2) / 100
            else:
                vacc_price = 0
            
            est_revenue += item.item_qty * item.item_price + vacc_price
    
    items_stats = await get_session_stats(session_id,
                                          datetime=creation_datetime,
                                          issued=False)

    for item_stats in items_stats:
        text += f'🧀 <b>{item_stats[0]}</b>\n'
                
        if item_stats[1] == 'кг':
            text += f'Всего заказано - <b>{round(item_stats[2], 3)} {item_stats[1]}</b>\n' \
                    f'Всего взвешено - <b>{round(item_stats[3], 3)} {item_stats[1]}</b>\n'
                    
        else:
            text += f'Всего заказано - <b>{round(item_stats[2])} {item_stats[1]}</b>\n' \
                    f'Всего взвешено - <b>{round(item_stats[3])} {item_stats[1]}</b>\n'
            
        text += f'Заказано в вакууме - <b>{round(item_stats[4])} шт.</b>\n\n'
                
    text += f'🛍 Всего заказов - <b>{len(orders)}</b>\n'
    text += f'💸 Ожидаемая выручка <b>{round(est_revenue)} р</b>\n'
    
    
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.session_stats,
                                    parse_mode='HTML')
    
    
# статистика по не выданным заказам за все время
@session_stats.callback_query(F.data.startswith('stats_menu:not_issued:total_stats'))
async def products_stats_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    session_id = data['session_id']
    
    # получаем номера заказов
    orders = await get_orders_by_date(session_id=session_id,
                                      issued=False)
    
    text = f'📈 <b>СТАТИСТИКА СЕССИИ ПО НЕ ВЫДАННЫМ ЗАКАЗАМ ЗА ВСЕ ВРЕМЯ</b> \n\n'

    est_revenue = 0
    
    for order in orders:
        # получаем все товары одного заказа
        items = await get_items(order.order_id)
        for item in items:
            # считаем стоимость вакуума, если он есть
            if item.item_vacc:
                if item.item_qty == 0:
                    vacc_price = 0
                elif 0 < item.item_qty < 200:
                    vacc_price = 5
                elif 200 <= item.item_qty < 300:
                    vacc_price = 6
                elif 300 <= item.item_qty:
                    vacc_price = (item.item_qty * 2) / 100
            else:
                vacc_price = 0
            
            est_revenue += item.item_qty * item.item_price + vacc_price
    
    items_stats = await get_session_stats(session_id,
                                          issued=False)

    for item_stats in items_stats:
        text += f'🧀 <b>{item_stats[0]}</b>\n'
                
        if item_stats[1] == 'кг':
            text += f'Всего заказано - <b>{round(item_stats[2], 3)} {item_stats[1]}</b>\n' \
                    f'Всего взвешено - <b>{round(item_stats[3], 3)} {item_stats[1]}</b>\n'
                    
        else:
            text += f'Всего заказано - <b>{round(item_stats[2])} {item_stats[1]}</b>\n' \
                    f'Всего взвешено - <b>{round(item_stats[3])} {item_stats[1]}</b>\n'
            
        text += f'Заказано в вакууме - <b>{round(item_stats[4])} шт.</b>\n\n'
                
    text += f'🛍 Всего заказов - <b>{len(orders)}</b>\n'
    text += f'💸 Ожидаемая выручка <b>{round(est_revenue)} р</b>\n'
    
    
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.session_stats,
                                    parse_mode='HTML')
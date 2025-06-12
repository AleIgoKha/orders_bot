from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import app.main_menu.sessions.session.issued_orders.keyboard as kb
from app.main_menu.sessions.session.session_menu import back_to_session_menu_handler
from app.database.requests import get_order_items, change_order_data, get_orders_sorted
from app.com_func import group_orders_items, order_text


issued_orders = Router()


# выводим все заказы в виде интерактивной клавиатуры
@issued_orders.callback_query(F.data.startswith('issued_orders:sorting:'))
@issued_orders.callback_query(F.data.startswith('issued_orders:page_'))
@issued_orders.callback_query(F.data == 'session:issued_orders')
@issued_orders.callback_query(F.data == 'issued_orders:back')
async def issued_orders_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('issued_orders:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1
    
    # Запоминаем, для дальнейших различий при изменении заказа
    if callback.data == 'session:issued_orders':
        await state.update_data(callback_name=callback.data,
                                desc=True)
    
    # запоминаем сортировку
    if callback.data.startswith('issued_orders:sorting:'):
        if callback.data.split(':')[-1] == 'asc':
            desc = False
        else:
            desc = True
        await state.update_data(desc=desc)
    
    data = await state.get_data()
    session_id = data['session_id']
    desc = data['desc']
    orders = await get_orders_sorted(session_id=session_id)
    
    # если выданных заказов нет, то выводим алерт
    orders = [order for order in orders if order.order_issued == True]   
    # Проверяем наличие заказов и если их нет, то показываем предупреждение
    if not orders:
        await callback.answer(text='Нет выданных заказов', show_alert=True)
        # Если зашли не через callback completed_orders, а при вызове функции, то переходим в меню сессии
        if callback.data != 'session:issued_orders':
            return await back_to_session_menu_handler(callback, state)
        return None # это сделано чтобы не было ошибки редактирования меню сессии
        
    await callback.message.edit_text(text='👌🏽 <b>ВЫДАННЫЕ ЗАКАЗЫ</b>',
                                     reply_markup=kb.choose_order(orders=orders, desc=desc, page=page),
                                     parse_mode='HTML')
    

# выводим данные отдельного выполненного заказа
@issued_orders.callback_query(F.data.startswith('issued_orders:order_id_'))
async def issued_order_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('issued_orders:order_id_'):
        order_id = int(callback.data.split('_')[-1])
        await state.update_data(order_id=order_id)
    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]
    
    # Выводим один заказ
    text = order_text(order_items_data)
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.issued_order,
                                     parse_mode='HTML')


# инициируем изменение статуса
@issued_orders.callback_query(F.data == 'issued_orders:change_status')
async def change_status_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data['order_id']
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ СТАТУС</b>',
                                     reply_markup=kb.change_status(order_id),
                                     parse_mode='HTML')
    
    
# изменяем статус на выбранный
@issued_orders.callback_query(F.data == 'issued_orders:mark_completed')
@issued_orders.callback_query(F.data == 'issued_orders:mark_processing')
async def change_status_receiver_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data['order_id']
    if callback.data.endswith("completed"):
        order_data = {
            'order_issued': False,
            'order_completed': True,
            'finished_datetime': None
        }
        text = "Заказ перемещен в Готовые"
    elif callback.data.endswith("processing"):
        order_data = {
            'order_issued': False,
            'order_completed': False,
            'finished_datetime': None
        }
        text = "Заказ перемещен в Обработку"
    await change_order_data(order_id=order_id, order_data=order_data)
    await issued_orders_handler(callback, state)
    await callback.answer(text=text)
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime
from pytz import timezone

import app.main_menu.sessions.session.completed_orders.keyboard as kb
from app.database.requests import change_order_data, get_orders_sorted, get_order_items, get_orders
from app.main_menu.sessions.session.session_menu import back_to_session_menu_handler
from app.com_func import group_orders_items
from app.states import Order

completed_orders = Router()

def order_message(order_items_data):
    text = 'Здравствуйте!✋\nЭто Мастерская Сыра Игоря Харченко. ' \
            f'Номер вашего заказа <b>№{order_items_data['order_number']}</b> сообщите его при получении.\n\n' \
            f'🧀Ваш заказ:\n'
    
    items_list = [item for item in order_items_data.keys() if item.startswith('item_')]
    total_price = 0
    
    if items_list: # Проверяем пуст ли заказ
        for item in items_list:
            item_name = order_items_data[item]['item_name']
            item_price = float(order_items_data[item]['item_price'])
            item_qty = float(order_items_data[item]['item_qty'])
            item_unit = order_items_data[item]['item_unit']
            item_qty_fact = float(order_items_data[item]['item_qty_fact'])
            item_vacc = order_items_data[item]['item_vacc']
                    
            
            if item_vacc:
                item_vacc = ' (вак. уп.)'
                if item_qty_fact < 200:
                    vacc_price = 5
                elif 200 <= item_qty_fact < 300:
                    vacc_price = 6
                elif 300 <= item_qty_fact:
                    vacc_price = (item_qty_fact * 2) / 100
            else:
                item_vacc = ''
                vacc_price = 0
                
            text += f'{item_name}{item_vacc}'
            item_price = round(item_qty_fact * item_price + vacc_price)
            if item_unit == 'кг': # Переводим килограмы в граммы
                text += f' - {int(item_qty_fact * 1000)} {item_unit[-1]}\n'
            else:
                text += f' - {int(item_qty_fact)} {item_unit}\n'
            # Рассчитываем стоимость всключая вакуум
            
            total_price += round(item_price)
    
    delivery_price = order_items_data['delivery_price']
    
    if order_items_data['issue_method'] != 'Самовывоз':
        if delivery_price == 0:
            text += '\n<b>Бесплатная доставка</b>\n'
        else:
            text += f'\nСтоимость доставки - <b>{round(delivery_price)} руб.</b>\n'
    else:
        delivery_price = 0
    

    
    order_disc = order_items_data['order_disc']
    if order_disc > 0:
        text += f'\nРазмер скидки <b>{order_disc}%</b>\n'
    
    text += f'\nК оплате - <b>{round(total_price * ((100 - order_disc) / 100) + int(delivery_price))} руб.</b>\n\n' \
            'До встречи!'
    
    return text


# Выводим список заказов
@completed_orders.callback_query(F.data.startswith('completed_orders:sorting:'))
@completed_orders.callback_query(F.data.startswith('completed_orders:page_'))
@completed_orders.callback_query(F.data == 'session:completed_orders')
@completed_orders.callback_query(F.data == 'completed_orders:back')
async def completed_orders_list_handler(callback: CallbackQuery, state: FSMContext):
    # Запоминаем, для дальнейших различий при изменении заказа
    if callback.data == 'session:completed_orders':
        await state.update_data(from_menu='completed_orders',
                                callback_name=callback.data,  # запоминаем имя колбека для различия действий в изменении продуктов
                                desc=False)
        
    # запоминаем сортировку
    if callback.data.startswith('completed_orders:sorting:'):
        if callback.data.split(':')[-1] == 'asc':
            desc = False
        else:
            desc = True
        await state.update_data(desc=desc)
        
    
    data = await state.get_data()
    session_id = data['session_id']
    desc = data['desc']
    orders = await get_orders_sorted(session_id=session_id)
    
    # если готовых заказов нет, то выводим алерт
    orders = [order for order in orders if order.order_completed == True]
    # Проверяем наличие заказов и если их нет, то показываем предупреждение
    if not orders:
        await callback.answer(text='Нет готовых заказов', show_alert=True)
        # Если зашли не через callback completed_orders, а при вызове функции, то переходим в меню сессии
        if callback.data != 'session:completed_orders':
            return await back_to_session_menu_handler(callback, state)
        return None # это сделано чтобы не было ошибки редактирования
    
    if callback.data.startswith('completed_orders:page_'):
        page = int(callback.data.split('_')[-1])
    else:
        page = 1
        
    await callback.message.edit_text(text='☑️ <b>ГОТОВЫЕ ЗАКАЗЫ</b>',
                                     reply_markup=kb.choose_order(orders=orders, desc=desc, page=page),
                                     parse_mode='HTML')


# выводим данные отдельного готового заказа
@completed_orders.callback_query(F.data.startswith('completed_orders:order_id_'))
async def issued_order_handler(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split('_')[-1])
    await state.update_data(order_id=order_id)
    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]
    
    # Выводим один заказ
    text = order_message(order_items_data)
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.completed_order,
                                     parse_mode='HTML')


# инициируем перевод заказа в статус выданного и просим подтверждения
@completed_orders.callback_query(F.data == "completed_orders:change_status")
async def change_status_handler(callback: CallbackQuery, state: FSMContext):
    finished_datetime = datetime.now(timezone("Europe/Chisinau"))
    await state.update_data(finished_datetime={
                                'year': finished_datetime.year,
                                'month': finished_datetime.month,
                                'day': finished_datetime.day
                            })
    data = await state.get_data()
    order_id = data['order_id']
    await callback.message.edit_text(text='❓ <b>ПОДТВЕРДИТЕ ВЫДАЧУ ЗАКАЗА</b>\n\n' \
                                            'Нажав <b>Подтвердить</b>, датой выдачи будет установлен сегодняшний день. '\
                                            'Вы также можете ввести свою дату в формате <i>ДД-ММ-ГГГ</i>',
                                     reply_markup=kb.change_status(order_id),
                                     parse_mode='HTML')
    await state.set_state(Order.finished_datetime)

# Принимаем дату выдачи заказа
@completed_orders.message(Order.finished_datetime)
async def finished_datetime_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    order_id = data['order_id']
    
    try:
        date_comp = [int(_) for _ in message.text.split('-')]
        if len(date_comp) != 3 or len(str(date_comp[2])) != 4:
            raise ValueError('Неправильный формат')
        finished_datetime = {
            'year': date_comp[2],
            'month': date_comp[1],
            'day': date_comp[0]
        }
        datetime(**finished_datetime)
        await state.update_data(finished_datetime=finished_datetime)
    except:
        try:
            await state.set_state(Order.finished_datetime)
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗ <b>НЕВЕРНО УКАЗАНА ДАТА</b>\n\n' \
                                                    '❓ <b>ПОДТВЕРДИТЕ ВЫДАЧУ ЗАКАЗА</b>\n\n' \
                                                    'Нажав <b>Подтвердить</b>, датой выдачи будет установлен сегодняшний день. '\
                                                    'Вы также можете ввести свою дату в формате <i>ДД-ММ-ГГГ</i>',
                                                reply_markup=kb.change_status(order_id),
                                                parse_mode='HTML')
            return None
        except TelegramBadRequest:
            return None
        
    text_date = datetime(**finished_datetime).strftime('%d-%m-%Y')
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=f'Вы указали дату выдачи заказа <b>{text_date}</b>.',
                                        reply_markup=kb.confirm_change_status(order_id),
                                        parse_mode='HTML')


# переводим заказ в статус выданного
@completed_orders.callback_query(F.data == "completed_orders:mark_issued")
async def mark_issued_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data['order_id']
    finished_datetime = data['finished_datetime']
    print(datetime(**finished_datetime))
    order_data = {
        'finished_datetime': datetime(**finished_datetime),
        'order_issued': True,
        'order_completed': False
    }
    await change_order_data(order_id=order_id, order_data=order_data)
    await callback.answer(text='Заказ отмечен как Выдан')
    await completed_orders_list_handler(callback, state)


# инициируем перевод всех заказов в статус выданного и просим подтверждения
@completed_orders.callback_query(F.data == "completed_orders:issue_all")
async def change_status_handler(callback: CallbackQuery, state: FSMContext):
    finished_datetime = datetime.now(timezone("Europe/Chisinau")).strftime('%d-%m-%Y')
    await callback.message.edit_text(text='❓ <b>ПОДТВЕРДИТЕ ВЫДАЧУ ВСЕХ ЗАКАЗОВ</b>\n\n' \
                                            'Чтобы подтвердить выдачу ВСЕХ готовых заказов введите дату выдачи в формате <i>ДД-ММ-ГГГ</i>\n\n' \
                                            f'Сегодня - <b>{finished_datetime}</b>',
                                     reply_markup=kb.issue_all,
                                     parse_mode='HTML')
    await state.set_state(Order.finished_datetime_all)


# Принимаем дату выдачи заказа
@completed_orders.message(Order.finished_datetime_all)
async def finished_datetime_all_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    finished_datetime = datetime.now(timezone("Europe/Chisinau")).strftime('%d-%m-%Y')
    
    try:
        date_comp = [int(_) for _ in message.text.split('-')]
        if len(date_comp) != 3 or len(str(date_comp[2])) != 4:
            raise ValueError('Неправильный формат')
        finished_datetime = {
            'year': date_comp[2],
            'month': date_comp[1],
            'day': date_comp[0]
        }
        datetime(**finished_datetime)
        await state.update_data(finished_datetime=finished_datetime)
    except:
        try:
            await state.set_state(Order.finished_datetime_all)
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗ <b>НЕВЕРНО УКАЗАНА ДАТА</b>\n\n' \
                                                    '❓ <b>ПОДТВЕРДИТЕ ВЫДАЧУ ВСЕХ ЗАКАЗОВ</b>\n\n' \
                                                    'Чтобы подтвердить выдачу ВСЕХ готовых заказов введите дату выдачи в формате <i>ДД-ММ-ГГГ</i>\n\n' \
                                                    f'Сегодня - <b>{finished_datetime}</b>',
                                                reply_markup=kb.issue_all,
                                                parse_mode='HTML')
            return None
        except TelegramBadRequest:
            return None
        
    text_date = datetime(**finished_datetime).strftime('%d-%m-%Y')
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=f'Вы указали дату выдачи для ВСЕХ готовых заказов <b>{text_date}</b>.',
                                        reply_markup=kb.issue_all_confirmation,
                                        parse_mode='HTML')


# переводим все заказы в статус выданного
@completed_orders.callback_query(F.data == "completed_orders:mark_issued_all")
async def mark_issued_all_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_id = data['session_id']
    orders = await get_orders(session_id)
    orders = [order for order in orders if order.order_completed == True and order.order_issued == False]
    
    for order in orders:
        order_id = order.order_id
        finished_datetime = data['finished_datetime']
        print(datetime(**finished_datetime))
        order_data = {
            'finished_datetime': datetime(**finished_datetime),
            'order_issued': True,
            'order_completed': False
        }
        await change_order_data(order_id=order_id, order_data=order_data)
    await callback.answer(text='Все заказы выданы', show_alert=True)
    await back_to_session_menu_handler(callback, state)
    
    


# # Выводим все заказы в виде отдельных сообщений с кнопкой "Обработать"
# @completed_orders.callback_query(F.data == 'completed_orders')
# async def completed_orders_list_handler(callback: CallbackQuery, state: FSMContext):
#     # Если хандлер был запущет при помощи callback, сохраняем для различия
#     if callback.data:
#         await state.update_data(callback_name=callback.data)
    
#     # Запрашиваем данные для всех заказов сессии
#     data = await state.get_data()
#     session_id = data['session_id']
#     orders_items = await get_orders_items(session_id)
#     orders_items_data = group_orders_items(orders_items)
    
#     # фильтр - если у заказа статус готового, то в обработку он не попадет
#     orders_items_data = [order_items_data for order_items_data in orders_items_data if order_items_data['order_completed']
#                          and not order_items_data['order_issued']]
    
    # # Проверяем наличие заказов и если их нет, то показываем предупреждение
    # if not orders_items_data:
    #     await callback.answer(text='Нет готовых заказов', show_alert=True)
    #     # Если зашли не через callback completed_orders, а при вызове функции, то переходим в меню сессии
    #     if data['callback_name'] != 'completed_orders':
    #         return await back_to_session_menu_handler(callback, state)
    #     return None # это сделано чтобы не было ошибки редактирования
    

#     messages_sent = 0
#     # Формируем и отправляем сообщения с информацией о заказах
#     for order_items_data in orders_items_data:
        
#         text = order_message(order_items_data)
        
#         messages_sent += 1
#         if messages_sent != len(orders_items_data):
#             message = await callback.bot.send_message(chat_id=data['chat_id'],
#                                             text=text,
#                                             reply_markup=kb.change_button(order_items_data['order_id']),
#                                             parse_mode='HTML')
#         else:
#             message = await callback.bot.send_message(chat_id=data['chat_id'],
#                                             text=text,
#                                             reply_markup=kb.last_change_button(order_items_data['order_id']),
#                                             parse_mode='HTML')
            
#     # Удаляем сообщение с меню сессии
#     await callback.bot.delete_message(chat_id=data['chat_id'], message_id=data['message_id'])
            
#     # сохраняем данные id последнего сообщения
#     await state.update_data(message_id=message.message_id, messages_sent=messages_sent, from_menu='completed_orders')



from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import app.orders_menu.completed_orders.keyboard as kb
from app.database.requests import get_orders_items
from app.orders_menu.orders_menu import back_to_orders_menu_handler
from app.com_func import group_orders_items

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
            item_price = order_items_data[item]['item_price']
            item_qty = order_items_data[item]['item_qty']
            item_unit = order_items_data[item]['item_unit']
            item_qty_fact = order_items_data[item]['item_qty_fact']
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
            item_price = round(item_qty_fact * float(item_price) + vacc_price)
            if item_unit == 'кг': # Переводим килограмы в граммы
                text += f' - {int(item_qty_fact * 1000)} {item_unit[-1]}\n'
            else:
                text += f' - {int(item_qty_fact)} {item_unit}\n'
            # Рассчитываем стоимость всключая вакуум
            
            total_price += item_price
            
    
    order_disc = order_items_data['order_disc']
    if order_disc > 0:
        text += f'\nРазмер скидки <b>{order_disc}%</b>\n'
    
    text += f'\nК оплате - <b>{round(total_price * ((100 - order_disc) / 100))} р</b>\n\n' \
            'До встречи!'
    
    return text

# Выводим все заказы в виде отдельных сообщений с кнопкой "Обработать"
@completed_orders.callback_query(F.data == 'completed_orders')
async def completed_orders_list_handler(callback: CallbackQuery, state: FSMContext):
    # Если хандлер был запущет при помощи callback, сохраняем для различия
    if callback.data:
        await state.update_data(callback_name=callback.data)
    
    # Запрашиваем данные для всех заказов сессии
    data = await state.get_data()
    session_id = data['session_id']
    orders_items = await get_orders_items(session_id)
    orders_items_data = group_orders_items(orders_items)
    
    # фильтр - если у заказа статус готового, то в обработку он не попадет
    orders_items_data = [order_items_data for order_items_data in orders_items_data if order_items_data['order_completed']]
    
    # Проверяем наличие заказов и если их нет, то показываем предупреждение
    if not orders_items_data:
        await callback.answer(text='Нет готовых заказов', show_alert=True)
        # Если зашли не через callback completed_orders, а при вызове функции, то переходим в меню сессии
        if data['callback_name'] != 'completed_orders':
            return await back_to_orders_menu_handler(callback, state)
        return None # это сделано чтобы не было ошибки редактирования
    

    messages_sent = 0
    # Формируем и отправляем сообщения с информацией о заказах
    for order_items_data in orders_items_data:
        
        text = order_message(order_items_data)
        
        messages_sent += 1
        if messages_sent != len(orders_items_data):
            message = await callback.bot.send_message(chat_id=data['chat_id'],
                                            text=text,
                                            reply_markup=kb.change_button(order_items_data['order_id']),
                                            parse_mode='HTML')
        else:
            message = await callback.bot.send_message(chat_id=data['chat_id'],
                                            text=text,
                                            reply_markup=kb.last_change_button(order_items_data['order_id']),
                                            parse_mode='HTML')
            
    # Удаляем сообщение с меню сессии
    await callback.bot.delete_message(chat_id=data['chat_id'], message_id=data['message_id'])
            
    # сохраняем данные id последнего сообщения
    await state.update_data(message_id=message.message_id, messages_sent=messages_sent, from_menu='completed_orders')


from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import app.orders_menu.completed_orders.keyboard as kb
from app.database.requests import get_orders_items
from app.orders_menu.orders_menu import back_to_orders_menu_handler

completed_orders = Router()

# Функция группирует данные полученные из запроса
def group_orders_items(orders_items):
    order_id = 0
    orders_items_data = []
    for order, item in orders_items:
        if order_id != order.order_id:
            order_id = order.order_id
            if item != None:
                orders_items_data.append({'order_number': order.order_number,
                                        'client_name': order.client_name,
                                        'order_id': order.order_id,
                                        'order_completed': order.order_completed,
                                        f'item_{item.item_id}': {
                                            'item_id': item.item_id,
                                            'item_name': item.item_name,
                                            'item_unit': item.item_unit,
                                            'item_price': item.item_price,
                                            'item_qty': item.item_qty,
                                            'item_qty_fact': item.item_qty_fact
                                        }})
            else:
                orders_items_data.append({'order_number': order.order_number,
                                        'client_name': order.client_name,
                                        'order_id': order.order_id,
                                        'order_completed': order.order_completed})
        else:
            orders_items_data[-1][f'item_{item.item_id}'] = {
                                    'item_id': item.item_id,
                                    'item_name': item.item_name,
                                    'item_unit': item.item_unit,
                                    'item_price': item.item_price,
                                    'item_qty': item.item_qty,
                                    'item_qty_fact': item.item_qty_fact
                                }
    return orders_items_data


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
    
    # Удаляем последнее сообщение
    await callback.bot.delete_message(chat_id=data['chat_id'], message_id=data['message_id'])

    messages_sent = 0
    # Формируем и отправляем сообщения с информацией о заказах
    for order_items_data in orders_items_data:        
        text = f'Заказ №{order_items_data['order_number']} клиента {order_items_data['client_name']}:\n\n'
        items_list = [item for item in order_items_data.keys() if item.startswith('item_')]
        
        for item in items_list:
            text += f'{order_items_data[item]['item_name']} - {order_items_data[item]['item_qty']} {order_items_data[item]['item_unit']}\n'

        messages_sent += 1
        if messages_sent != len(orders_items_data):
            message = await callback.bot.send_message(chat_id=data['chat_id'],
                                            text=text,
                                            reply_markup=kb.change_button(order_items_data['order_id']))
        else:
            message = await callback.bot.send_message(chat_id=data['chat_id'],
                                            text=text,
                                            reply_markup=kb.last_change_button(order_items_data['order_id']))
            
    # сохраняем данные id последнего сообщения
    await state.update_data(message_id=message.message_id, messages_sent=messages_sent, from_menu='completed_orders')



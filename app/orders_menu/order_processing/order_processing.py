from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from decimal import Decimal

import app.orders_menu.order_processing.keyboard as kb
from app.states import Item
from app.database.requests import get_orders_items, get_order_items, get_item, change_item_data, change_order_data
from app.orders_menu.orders_menu import back_to_orders_menu_handler
from app.com_func import group_orders_items, order_text

order_processing = Router()

# Выводим все заказы в виде отдельных сообщений с кнопкой "Обработать"
@order_processing.callback_query(F.data == 'order_processing')
async def orders_processing_list_handler(callback: CallbackQuery, state: FSMContext):
    # Если хандлер был запущет при помощи callback, сохраняем для различия
    if callback.data:
        await state.update_data(callback_name=callback.data)
    
    # Запрашиваем данные для всех заказов сессии
    data = await state.get_data()
    session_id = data['session_id']
    orders_items = await get_orders_items(session_id)
    orders_items_data = group_orders_items(orders_items)
    
    # фильтр - если у заказа статус готового, то в обработку он не попадет
    orders_items_data = [order_items_data for order_items_data in orders_items_data if not order_items_data['order_completed']]
    
    # Проверяем наличие заказов и если их нет, то показываем предупреждение
    if not orders_items_data:
        await callback.answer(text='Нет заказов для обработки', show_alert=True)
        # Если зашли не через callback order_processing, а при вызове функции, то переходим в меню сессии
        if data['callback_name'] != 'order_processing':
            return await back_to_orders_menu_handler(callback, state)
        return None # это сделано чтобы не было ошибки редактирования


    messages_sent = 0
    # Формируем и отправляем сообщения с информацией о заказах
    for order_items_data in orders_items_data:        
        text = order_text(order_items_data)

        messages_sent += 1
        if messages_sent != len(orders_items_data):
            message = await callback.bot.send_message(chat_id=data['chat_id'],
                                                        text=text,
                                                        reply_markup=kb.process_button(order_items_data['order_id']),
                                                        parse_mode='HTML')
        else:
            message = await callback.bot.send_message(chat_id=data['chat_id'],
                                                        text=text,
                                                        reply_markup=kb.last_process_button(order_items_data['order_id']),
                                                        parse_mode='HTML')
    
    # Удаляем сообщение с мею сессии
    await callback.bot.delete_message(chat_id=data['chat_id'], message_id=data['message_id'])
    
    # сохраняем данные id последнего сообщения
    await state.update_data(message_id=message.message_id, messages_sent=messages_sent, from_menu='order_processing')


# Заходим в меню заказа
@order_processing.callback_query(F.data.startswith('process_order_'))
@order_processing.callback_query(F.data == 'back_process_order_menu')
async def orders_processing_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Удаляем все лишние сообщения если не через кнопку возврата
    if callback.data.startswith('process_order_'):
        for i in range(data['messages_sent']):
            try:
                message_id = data['message_id'] - i
                if callback.message.message_id != message_id:
                    await callback.bot.delete_message(chat_id=data['chat_id'], message_id=message_id)
            except TelegramBadRequest:
                continue
    
        # Достаем id одного заказа
        order_id = int(callback.data.split('_')[-1])
        await state.update_data(message_id=callback.message.message_id,
                        order_id=order_id)
    else:
        order_id = data['order_id']
        
    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]

    text = order_text(order_items_data)
    
    await callback.bot.edit_message_text(chat_id=data['chat_id'],
                                         message_id=callback.message.message_id,
                                         text=text,
                                         reply_markup=kb.order_processing_menu_keyboard,
                                         parse_mode='HTML')


# Выбираем товар для обработки
@order_processing.callback_query(F.data.startswith('item_page_'))
@order_processing.callback_query(F.data == 'process_order')
async def process_order_data_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    # Делаем запрос на товары из заказа
    data = await state.get_data()
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    items_data_list = [order_items_data[item]
                       for item in order_items_data.keys() if item.startswith('item_')
                       and order_items_data[item]['item_qty_fact'] == 0
                       and order_items_data[item]['item_unit'] != 'шт.']
    
    if len(items_data_list) == 0:
        await callback.answer(text='Нет товаров для обработки', show_alert=True)
        return None
    
    if callback.data.startswith('item_page_'):
        page = int(callback.data.split('_')[-1])
        
    else:
        page = 1
    
    await callback.bot.edit_message_text(chat_id=data['chat_id'],
                                         message_id=data['message_id'],
                                         text='❓<b>ВЫБЕРИТЕ ПРОДУКТ ДЛЯ ОБРАБОТКИ</b>❓',
                                         reply_markup=kb.choose_item_processing(items_data_list, page=page),
                                         parse_mode='HTML')


# Обрабатываем товар указывая его фактическое количество
@order_processing.callback_query(F.data.startswith('item_id_'))
async def item_processing(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split('_')[-1])
    await state.update_data(item_id=item_id)
    item = await get_item(item_id)
    
    await callback.message.edit_text(text='❓<b>ВВЕДИТЕ ВЗВЕШЕННОЕ КОЛИЧЕСТВО ТОВАРА</b>❓\n\n' \
                                            f'Выбранный товар <b>{item.item_name}</b> заказан в размере ' \
                                            f'<b>{int(item.item_qty * 1000)} {item.item_unit[-1]}</b>',
                                            reply_markup=kb.back_to_order_proccessing_menu,
                                            parse_mode='HTML')
    await state.set_state(Item.item_qty_fact)


# Сохраняем фактическое количество товара
@order_processing.message(Item.item_qty_fact)
async def item_qty_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    # Проверяем формат ввода цифр
    try:
        item_qty_fact = Decimal(message.text.replace(',', '.'))
    except:
        try:
            item = await get_item(data['item_id'])
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text='❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>❗\n\n' \
                                                'Формат ввода предполагает использование цифр и одного десятичного разделителя: <i>123.45</i>\n\n' \
                                                '❓<b>ВВЕДИТЕ ВЗВЕШЕННОЕ КОЛИЧЕСТВО ТОВАРА</b>❓\n\n' \
                                                f'Выбранный товар <b>{item.item_name}</b> заказан в размере ' \
                                                f'<b>{int(item.item_qty * 1000)} {item.item_unit[-1]}</b>',
                                            reply_markup=kb.back_to_order_proccessing_menu,
                                            parse_mode='HTML')
            return None
        except TelegramBadRequest:
            return None
    
    item_id = data['item_id']
    item_data = {'item_qty_fact': item_qty_fact / 1000}
    await change_item_data(item_id, item_data)
    await state.set_state(None)

    # Делаем запрос на товары из заказа
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    

    items_data_list = [order_items_data[item]
                       for item in order_items_data.keys() if item.startswith('item_')
                       and order_items_data[item]['item_qty_fact'] == 0
                       and order_items_data[item]['item_unit'] != 'шт.']
    if len(items_data_list) != 0:
        # переходим на первую страницу списка товаров для обработки
        await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text='❓<b>ВЫБЕРИТЕ ПРОДУКТ ДЛЯ ОБРАБОТКИ</b>❓',
                                            reply_markup=kb.choose_item_processing(items_data_list),
                                            parse_mode='HTML')
    else:
        # Переходим в меню заказа 
        # Достаем данные о продуктах одного заказа
        order_id = data['order_id']
        order_items = await get_order_items(order_id)
        order_items_data = group_orders_items(order_items)[0]
        
        text = order_text(order_items_data)
        
        await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text=text,
                                            reply_markup=kb.order_processing_menu_keyboard,
                                            parse_mode='HTML')


# Переводим заказ в готовый, если не осталось необработанных товаров
@order_processing.callback_query(F.data == 'complete_order')
async def complete_order_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(callback_name=callback.data) # флаг для меню на случай отсутствия заказов
    
    # Достаем данные о продуктах одного заказа
    data = await state.get_data()
    order_id = data['order_id']
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]
    
    # Если не не осталось необработанных товаров, то разрешаем перевести в успешно обработанный
    items_left = len([item for item in order_items_data.keys() if item.startswith('item_')
                    and order_items_data[item]['item_qty_fact'] == 0
                    and order_items_data[item]['item_unit'] != 'шт.'])
    if items_left == 0:
        order_data = {'order_completed': True}
        await change_order_data(order_id=order_id, order_data=order_data)
        await callback.answer(text='Заказ успешно обработан', show_alert=True)
        await orders_processing_list_handler(callback, state)
    else:
        await callback.answer(text='Не все товары были обработаны.', show_alert=True)
    





##################
# 3. Сделать функции для удаления сессии (и, возможно, для изменения ее данных)
# 4. Сделать функцию для изменения товаров
# 5. Удалить базу данных и протестировать все что получилось и исправить ошибки
# 7. Показать отцу и научить пользоваться



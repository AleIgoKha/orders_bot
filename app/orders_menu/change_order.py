from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from decimal import Decimal

import app.orders_menu.keyboard as kb
from app.states import Item, Order
from app.database.requests import get_order_items, get_item, change_item_data, change_order_data, get_product, add_order_items, delete_items, delete_order, get_order, change_items_data
from app.orders_menu.completed_orders.completed_orders import completed_orders_list_handler
from app.orders_menu.order_processing.order_processing import orders_processing_list_handler


change_order = Router()


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
                                        'order_note': order.order_note,
                                        f'item_{item.item_id}': {
                                            'item_id': item.item_id,
                                            'item_name': item.item_name,
                                            'item_unit': item.item_unit,
                                            'item_price': item.item_price,
                                            'item_qty': item.item_qty,
                                            'item_qty_fact': item.item_qty_fact,
                                            'item_disc': item.item_disc,
                                            'item_vacc': item.item_vacc
                                        }})
            else:
                orders_items_data.append({'order_number': order.order_number,
                                        'client_name': order.client_name,
                                        'order_id': order.order_id,
                                        'order_completed': order.order_completed,
                                        'order_note': order.order_note})
        else:
            orders_items_data[-1][f'item_{item.item_id}'] = {
                                    'item_id': item.item_id,
                                    'item_name': item.item_name,
                                    'item_unit': item.item_unit,
                                    'item_price': item.item_price,
                                    'item_qty': item.item_qty,
                                    'item_qty_fact': item.item_qty_fact,
                                    'item_disc': item.item_disc,
                                    'item_vacc': item.item_vacc
                                }
    return orders_items_data


# формирует сообщение для меню заказа и изменения заказа
def order_text(order_items_data):
    text = f'📋 <b>ЗАКАЗ №{order_items_data['order_number']}</b>\n\n' \
            f'👤 Клиент - <b>{order_items_data['client_name']}</b>\n\n'
    
    items_list = [item for item in order_items_data.keys() if item.startswith('item_')]
    
    if items_list: # Проверяем пуст ли заказ
        for item in items_list:
            item_name = order_items_data[item]['item_name']
            item_price = order_items_data[item]['item_price']
            item_qty = order_items_data[item]['item_qty']
            item_unit = order_items_data[item]['item_unit']
            item_qty_fact = order_items_data[item]['item_qty_fact']
            
            item_unit_amend = item_unit
            if item_unit_amend == 'кг': # Переводим килограмы в граммы
                item_unit_amend = 'г'
                item_qty = int(item_qty * 1000)
                item_qty_fact = int(item_qty_fact * 1000)
                item_price_fact = round(order_items_data[item]['item_qty_fact'] * float(item_price), 2)
                text += f'🧀 <b>{item_name}</b>\nЗаказано - <b>{item_qty} {item_unit_amend}</b>\nВзвешено - <b>{item_qty_fact} {item_unit_amend}</b>\nСтоимость - <b>{item_price_fact} р</b>\n\n'
            elif item_unit_amend == 'шт.':
                item_price_fact = round(item_qty * float(item_price), 2)
                item_qty = int(order_items_data[item]['item_qty'])
                text += f'🧀 <b>{item_name}</b>\nЗаказано - <b>{item_qty} {item_unit_amend}</b>\nСтоимость - <b>{item_price_fact} р</b>\n\n'
    else:
        text += '<b>Заказ пуст 🤷‍♂️</b>\n\n'
    
    order_note = order_items_data['order_note']
    if order_note:
        text += f'<b>📝 Комментарий к заказу</b>\n{order_note}'  
    return text


# Переходим в меню изменения данных заказа либо напрямую из меню с обрабатываемыми/готовыми заказами либо после изменения параметра
@change_order.callback_query(F.data == 'change_order_data')
@change_order.callback_query(F.data.endswith('_change_order'))
async def change_order_data_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    
    # Если пришли из change_order_{id}, то нужно зафиксировать order_id
    if callback.data.split('_')[0].isdigit():
        # Удаляем все лишние сообщения
        for i in range(data['messages_sent']):
            try:
                message_id = data['message_id'] - i
                if callback.message.message_id != message_id:
                    await callback.bot.delete_message(chat_id=data['chat_id'], message_id=message_id)
            except TelegramBadRequest:
                continue
    
        # Достаем id одного заказа
        order_id = int(callback.data.split('_')[0])
        await state.update_data(message_id=callback.message.message_id,
                        order_id=order_id)
        data = await state.get_data()

    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    # Выводим один заказ
    text = order_text(order_items_data)
    
    # В зависимости от того из какого меню пришли, выходит соответствующая клавиатура
    if data['from_menu'] == 'order_processing':
        await callback.message.edit_text(text=text,
                                         reply_markup=kb.change_order_data_keyboard,
                                         parse_mode='HTML')
    elif data['from_menu'] == 'completed_orders':
        await callback.message.edit_text(text=text,
                                         reply_markup=kb.change_completed_order_data_keyboard,
                                         parse_mode='HTML')     


# Заходим в меню управления данными товаров
@change_order.callback_query(F.data == 'change_item_data')
async def change_item_data_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    text = order_text(order_items_data)
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.change_item_data,
                                     parse_mode='HTML')


# инициируем изменение имени клиента и просим ввести новое
@change_order.callback_query(F.data == 'change_client_name')
async def change_client_name_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='❓<b>ВВЕДИТЕ НОВОЕ ИМЯ КЛИЕНТА</b>❓',
                                            reply_markup=kb.back_to_change_order_data,
                                            parse_mode='HTML')
    await state.set_state(Order.change_client_name)


# Инициируем изменение количества товара или его удаление
@change_order.callback_query(F.data.startswith('change_item_qty_page_'))
@change_order.callback_query(F.data == 'delete_item')
@change_order.callback_query(F.data == 'change_item_qty')
@change_order.callback_query(F.data == 'change_item_qty_fact')
async def change_item_qty_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('change_item_qty_page_'):
        page = int(callback.data.split('_')[-1])
        
    else:
        page = 1
        await state.update_data(callback_name=callback.data)
    
    # Делаем запрос на товары из заказа
    data = await state.get_data()
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    
    # формируем сообщение
    if data['callback_name'] == 'change_item_qty':
        qty_option = 'ИЗМЕНЕНИЯ ЕГО ЗАКАЗАННОГО КОЛИЧЕСТВА'
        items_data_list = [order_items_data[item]
                        for item in order_items_data.keys() if item.startswith('item_')]
    elif data['callback_name'] == 'change_item_qty_fact':
        qty_option = 'ИЗМЕНЕНИЯ ЕГО ФАКТИЧЕСКОГО КОЛИЧЕСТВА'
        items_data_list = [order_items_data[item]
                        for item in order_items_data.keys() if item.startswith('item_')
                        and order_items_data[item]['item_unit'] != 'шт.']
    elif data['callback_name'] == 'delete_item':
        qty_option = 'ЕГО УДАЛЕНИЯ'
        items_data_list = [order_items_data[item]
                        for item in order_items_data.keys() if item.startswith('item_')]
        
    # Формируем список словарей содержащих информацию о товарах из заказа
        
    await callback.bot.edit_message_text(chat_id=data['chat_id'],
                                         message_id=data['message_id'],
                                         text=f'❓<b>ВЫБЕРИТЕ ПРОДУКТ ДЛЯ {qty_option}</b>❓',
                                         reply_markup=kb.choose_change_item_qty(items_data_list, page=page),
                                         parse_mode='HTML')


# Инициируем добавление нового товара в заказ
@change_order.callback_query(F.data.startswith('add_item_page_'))
@change_order.callback_query(F.data == 'add_new_item')
async def choose_new_item_handler(callback: CallbackQuery):
    if callback.data.startswith('add_item_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        page = 1
    await callback.message.edit_text(text='❓<b>ВЫБЕРИТЕ ТОВАР ДЛЯ ДОБАВЛЕНИЯ</b>❓',
                                     reply_markup=await kb.choose_add_item(page=page),
                                     parse_mode='HTML')


# Запрашиваем количество новодобавленного товара
@change_order.callback_query(F.data.startswith('add_item_id_'))
async def add_new_item_handler(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split('_')[-1])
    item_data =  await get_product(product_id=item_id) # сохраняем номер продукта, чтобы не сохранять все данные о нем, чтобы избежать неприятностей на случай отмены
    await state.update_data(item_id=item_id)
    product_unit = item_data.product_unit
    product_unit_amend = 'штуках'
    if product_unit == 'кг':
        product_unit = product_unit[-1]
        product_unit_amend = 'граммах'
    await callback.message.edit_text(text='❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА </b>❓\n\n' \
                                            f'Выбранный товар - <b>{item_data.product_name} - {item_data.product_price} р/{product_unit}</b>. ' \
                                            f'Количество укажите в <b>{product_unit_amend}</b>',
                                    reply_markup=kb.back_to_change_item_data,
                                    parse_mode='HTML')
    await state.set_state(Item.item_qty)


# Запрашиваем новое количество товара
@change_order.callback_query(F.data.startswith('change_item_qty_'))
async def change_item_qty_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    item_id = int(callback.data.split('_')[-1])
    await state.update_data(item_id=item_id)
    item_data = await get_item(item_id)
    
    # формируем сообщение
    item_unit = item_data.item_unit
    item_unit_amend = 'штуках'
    if item_unit == 'кг':
        item_unit = item_unit[-1]
        item_unit_amend = 'граммах'
        
    if data['callback_name'] == 'delete_item':
        await callback.message.edit_text(text=f'❓ <b>ПОДТВЕРДИТЕ УДАЛЕНИЕ ТОВАРА ИЗ ЗАКАЗА</b> ❓\n\n'
                                         f'Выбранный товар - <b>{item_data.item_name}</b>',
                                        reply_markup=kb.confirm_delete_item,
                                        parse_mode='HTML')
    else:
        qty_option = 'ФАКТИЧЕСКОЕ'
        if data['callback_name'] == 'change_item_qty':
            qty_option = 'ЗАКАЗАННОЕ'
        await callback.message.edit_text(text=f'❓ <b>УКАЖИТЕ {qty_option} КОЛИЧЕСТВО ПРОДУКТА</b> ❓\n\n' \
                                            f'Выбранный товар - <b>{item_data.item_name} - {item_data.item_price} р/{item_unit}</b>. ' \
                                            f'Количество укажите в <b>{item_unit_amend}</b>',
                                        reply_markup=kb.back_to_change_item_data,
                                        parse_mode='HTML')
        await state.set_state(Item.change_item_qty)


# Принимаем состояния для изменения данных и возвращаем меню для изменения данных
@change_order.message(Order.change_disc)
@change_order.message(Item.item_qty)
@change_order.message(Order.change_client_name)
@change_order.message(Item.change_item_qty)
@change_order.message(Order.change_note)
async def confirm_change_item_qty_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    state_name = await state.get_state()
    
    # Если сохраняем новый вес продукта как фактический так и заказанный
    if 'change_item_qty' in state_name:
        qty_option = 'item_qty_fact'
        text_option = 'ФАКТИЧЕСКОЕ'
        if data['callback_name'] == 'change_item_qty':
            qty_option = 'item_qty'
            text_option = 'ЗАКАЗАННОЕ'
    # Проверяем формат ввода цифр
        try:
            item_qty = Decimal(message.text.replace(',', '.')) / 1000
        except:
            try:
                item_data = await get_item(data['item_id'])
                item_unit = item_data.item_unit
                item_unit_amend = 'штуках'
                if item_unit == 'кг':
                    item_unit_amend = 'граммах'
                await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗ <b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b> ❗\n\n' \
                                                    f'❓ <b>УКАЖИТЕ {text_option} КОЛИЧЕСТВО ПРОДУКТА</b> ❓\n\n' \
                                                    f'Выбранный товар - <b>{item_data.item_name} - {item_data.item_price} р/{item_unit}</b>. ' \
                                                    f'Количество укажите в <b>{item_unit_amend}</b>',
                                                reply_markup=kb.back_to_change_item_data,
                                                parse_mode='HTML')
                return None
            except TelegramBadRequest:
                return None
        # Если все ок, то сохраняем  новый вес
        item_data = {qty_option: item_qty}
        await change_item_data(item_id=data['item_id'], item_data=item_data)
    
    # Если сохраняем новое имя клиента
    elif 'change_client_name' in state_name:
        order_data = {'client_name': message.text}
        await change_order_data(order_id=data['order_id'], order_data=order_data)
        
    # Если нужно сохранить вес нового добавленного товара
    elif 'item_qty' in state_name:
        # Достаем данные одного продукта из прайса
        item_data = await get_product(product_id=data['item_id'])
        try:
            item_qty = Decimal(message.text.replace(',', '.'))
        except:
            try:
                item_unit = item_data.product_unit
                item_unit_amend = 'штуках'
                if item_unit == 'кг':
                    item_unit_amend = 'граммах'
                await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗ <b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b> ❗\n\n' \
                                                    f'❓ <b>УКАЖИТЕ ЗАКАЗАННОЕ КОЛИЧЕСТВО ПРОДУКТА</b> ❓\n\n' \
                                                    f'Выбранный товар - <b>{item_data.product_name} - {item_data.product_price} р/{item_unit}</b>\n' \
                                                    f'Количество укажите в <b>{item_unit_amend}</b>',
                                                reply_markup=kb.back_to_change_item_data,
                                                parse_mode='HTML')
                return None
            except TelegramBadRequest:
                return None
        # Если все окей то сохраняем данные новодобавленного товара
        
        # Достаем данные о продуктах одного заказа
        order_data = await get_order(data['order_id'])
        order_item_data = [{
            'order_id': data['order_id'],
            'product_name': item_data.product_name,
            'product_unit': item_data.product_unit,
            'product_price': item_data.product_price,
            'product_qty': item_qty,
            'item_disc': order_data.order_disc,
            'item_vacc': False
        }]
        await add_order_items(order_item_data)
        
    # Добавляем или изменяем комментарий к заказу
    elif 'change_note' in state_name:
        order_data = {'order_note': message.text}
        await change_order_data(order_id=data['order_id'], order_data=order_data)
    
    # Сохраняем новую скидку заказа
    elif 'change_disc' in state_name:
        data = await state.get_data()
        
        try:
            disc = int(message.text)
            if not 0 <= disc <= 100:
                raise
        except:
            try:
                await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                    message_id=data['message_id'],
                                                    text='❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>❗\n\n' \
                                                        'Формат ввода предполагает использование цифр значением от 0 до 100: <i>123.45</i>\n\n' \
                                                        f'<b>Введите размер скидки в процентах</b>',
                                                    parse_mode='HTML',
                                                    reply_markup=kb.back_to_change_order_data)
                return None
            except TelegramBadRequest:
                return None
        
        order_id = data['order_id']
        order_data = {'order_disc': disc}
        await change_order_data(order_id=order_id, order_data=order_data)
            
    
    await state.set_state(None)
    
    # Возвращаемся в меню изменения товаров
    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    # Выводим данные одного заказа в сообщение
    text = order_text(order_items_data)
    
    # Здесть двойное условие, так как некоторые состояния касаются заказа, а некоторые товара
    # И в зависимости от того данные чего мы обработали необходимо перейти в соответствующее меню 
    if data['from_menu'] == 'order_processing':
        reply_markup = kb.change_order_data_keyboard
        if state_name.split(':')[-1] in ('item_qty', 'change_item_qty'):
            reply_markup = kb.change_item_data
        await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text=text,
                                            reply_markup=reply_markup,
                                            parse_mode='HTML')
    elif data['from_menu'] == 'completed_orders':
        reply_markup = kb.change_completed_order_data_keyboard
        if state_name.split(':')[-1] in ('item_qty', 'change_item_qty', ):
            reply_markup = kb.change_item_data
        await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text=text,
                                            reply_markup=reply_markup,
                                            parse_mode='HTML')


# Удаляем товар после подтверждения
@change_order.callback_query(F.data == 'confirm_delete_item')
async def confirm_delete_item_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item_id = [data['item_id']]
    await delete_items(item_ids=item_id)
    await callback.answer(text='Продукт был успешно удален', show_alert=True) 
    await change_item_data_handler(callback, state)


# Запрашиваем подтверждение на удаление заказа
@change_order.callback_query(F.data == 'delete_order')
async def delete_order_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='<b>Для удаления заказа введите</b> <i>УДАЛИТЬ</i>',
                                     parse_mode='HTML',
                                     reply_markup=kb.back_to_change_order_data)
    await state.set_state(Order.delete_order)
    

# Просим подтвердить удаление после ввода слова
@change_order.message(Order.delete_order)
async def confirm_delete_order_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text.upper() == 'УДАЛИТЬ':
        await state.set_state(None)
        await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text='❗ <b>ВНИМАНИЕ</b> ❗\n\nПосле удаления заказа все его данные будут удалены.\n' \
                                                'Вы уверены, что желаете удалить заказ?',
                                            parse_mode='HTML',
                                            reply_markup=kb.confirm_delete_order
                                            )
    else:
        await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text='❗ <b>НЕПРАВИЛЬНО ВВЕДЕНЫ ДАННЫЕ!</b> ❗\n\nДля удаления заказа введите:\n <i>УДАЛИТЬ</i>',
                                            parse_mode='HTML',
                                            reply_markup=kb.back_to_change_order_data)


# Удаляем заказ и переходим к списку заказов или в меню сессии
@change_order.callback_query(F.data == 'confirm_delete_order')
async def finish_delete_order_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='Заказ был успешно удален', show_alert=True)
    
    # Делаем запрос на товары из заказа
    data = await state.get_data()
    print(data)
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    # Удаляем все товары
    item_ids = [item_id.split('_')[-1] for item_id in order_items_data.keys() if item_id.startswith('item_')]
    await delete_items(item_ids)
    
    # Удаляем заказ
    order_id = data['order_id']
    await delete_order(order_id)
    
    # Возвращаемся к списку всех заказов
    await state.update_data(callback_name=callback.data) # флаг для меню на случай отсутствия заказов
    
    if data['from_menu'] == 'completed_orders':
        await completed_orders_list_handler(callback, state)
    elif data['from_menu'] == 'order_processing':
        await orders_processing_list_handler(callback, state)

    
# Инициируем изменение статуса товара
@change_order.callback_query(F.data == 'change_status')
async def change_status_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='Текущий статус, заказа "Обработан". Желаете переветси статус на "Не обработан"?',
                                     reply_markup=kb.confirm_change_status)

  
# сохраняем новый статус заказа и возвращаемся в меню с готовыми заказами
@change_order.callback_query(F.data == 'confirm_change_status')
async def confirm_change_status_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data['order_id']
    order_data = {'order_completed': False}
    await change_order_data(order_id=order_id, order_data=order_data)
    await callback.answer(text='Статус заказа успешно изменен.', show_alert=True)
    await completed_orders_list_handler(callback, state)


# инициируем изменение комментария
@change_order.callback_query(F.data == 'change_note')
async def change_note_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Достаем данные об одном заказе
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    text = '❗ <b>Введить комментарий к заказу</b> ❗\n'
    if order_items_data['order_note']:
        text += f'\n<b>Текущий комментарий к заказу:</b>\n<blockquote>{order_items_data['order_note']}</blockquote>'
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.confirm_change_note,
                                     parse_mode='HTML')
    await state.set_state(Order.change_note)


# Удаление комментария
@change_order.callback_query(F.data == 'note_removal_from_order')
async def confirm_change_note(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    order_id = data['order_id']
    order_data = {'order_note': None}
    await change_order_data(order_id=order_id, order_data=order_data)
    await change_order_data_handler(callback, state)
    
    
# Инициируем изменение скидки на заказ
@change_order.callback_query(F.data == 'change_order_disc')
async def change_item_disc_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='❗ <b>ВВЕДИТЕ РАЗМЕР СКИДКИ</b> ❗\n\n' \
                                        'Значение скидки должно быть в диапазоне от от 0 до 100 процентов',
                                    reply_markup=kb.back_to_change_order_data,
                                    parse_mode='HTML')
    await state.set_state(Order.change_disc)


# Инициируем выбор товаров для изменения вакуума
@change_order.callback_query(F.data.startswith('change_vacc_page_'))
@change_order.callback_query(F.data == 'change_delete_item_vacc')
@change_order.callback_query(F.data == 'change_add_item_vacc')
async def change_vacc_to_order_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('change_vacc_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        await state.update_data(from_callback=callback.data)
        page = 1
        
    data = await state.get_data()
    
    # Сохраняем, чтобы затем различать удаление и не удаление
    from_callback = data['from_callback']
    
    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    if from_callback == 'change_add_item_vacc':
        # получаем список словарей с информацией о товаре без вакуумной упаковки
        products = {item:order_items_data[item] for item in order_items_data.keys() if item.startswith('item_')
                    and order_items_data[item]['item_vacc'] == False}
        if products:
            await callback.message.edit_text(text='❗ <b>ВЫБЕРИТЕ ПРОДУКТ ДЛЯ ВАКУУМАЦИИ</b> ❗',
                                            reply_markup= await kb.choose_change_product_vacc(products, from_callback, page=page),
                                            parse_mode='HTML')
        else:
            await callback.answer(text='Нет продуктов для вакуумации', show_alert=True)
    elif from_callback == 'change_delete_item_vacc':
        # получаем список словарей с информацией о товаре с вакуумной упаковкой
        products = {item:order_items_data[item] for item in order_items_data.keys() if item.startswith('item_')
                    and order_items_data[item]['item_vacc'] == True}
        if products:
            await callback.message.edit_text(text='❗ <b>ВЫБЕРИТЕ ПРОДУКТ ДЛЯ ОТМЕНЫ ВАКУУМАЦИИ</b> ❗',
                                            reply_markup= await kb.choose_change_product_vacc(products, from_callback, page=page),
                                            parse_mode='HTML')
        else:
            await callback.answer(text='Нет продуктов с вакуумацией', show_alert=True)
            

# Сохраняем обновленные данные по вакуумной упаковке
@change_order.callback_query(F.data.startswith('change_vacc_item_'))
@change_order.callback_query(F.data == 'change_vacc_all')
async def apply_change_vacc_to_order_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    from_callback = data['from_callback']
    
    # Удалить или наоборот
    if from_callback == 'change_add_item_vacc':
        flag = True
    elif from_callback == 'change_delete_item_vacc':
        flag = False
    # если один продукт
    if callback.data.startswith('change_vacc_item_'): 
        item_id = int(callback.data.split('_')[-1])
        item_data = {'item_vacc': flag}
        await change_item_data(item_id, item_data)
    # Если все продукты сразу
    elif callback.data == 'change_vacc_all':

        order_items = await get_order_items(data['order_id'])
        order_items_data = group_orders_items(order_items)[0]

        items_id = [int(item_id.split('_')[-1]) for item_id in order_items_data.keys() if item_id.startswith('item_')]
        items_data = [{'item_vacc': flag} for _ in range(len(items_id))]
        await change_items_data(items_id, items_data)
    
    # В зависимости от того удаляем вакуум или добавляем выбираем соответствующее меню
    await change_item_data_handler(callback, state)
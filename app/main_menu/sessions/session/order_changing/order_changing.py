import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from decimal import Decimal
from datetime import datetime

import app.main_menu.sessions.session.order_changing.keyboard as kb
from app.states import Item, Order
from app.database.requests import get_order_items, get_item, change_item_data, change_order_data, get_product, add_order_items, delete_items, delete_order, get_order, change_items_data, get_session, change_order_session_id, get_items
from app.main_menu.sessions.session.completed_orders.completed_orders import completed_orders_list_handler
from app.main_menu.sessions.session.order_processing.order_processing import orders_processing_handler
from app.com_func import group_orders_items, order_text

order_changing = Router()


# Переходим в меню изменения данных заказа либо напрямую из меню с обрабатываемыми/готовыми заказами либо после изменения параметра
@order_changing.callback_query(F.data == 'change_order_data')
@order_changing.callback_query(F.data.endswith('completed_orders:change_order'))
async def change_order_data_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    order_id = data['order_id']
    
    # # Если пришли из change_order_{id}, то нужно зафиксировать order_id
    # if callback.data.split('_')[0].isdigit():
    #     # Удаляем все лишние сообщения
    #     for i in range(data['messages_sent']):
    #         try:
    #             message_id = data['message_id'] - i
    #             if callback.message.message_id != message_id:
    #                 await callback.bot.delete_message(chat_id=data['chat_id'], message_id=message_id)
    #         except TelegramBadRequest:
    #             continue
    
        # # Достаем id одного заказа
        # order_id = int(callback.data.split('_')[0])
        # await state.update_data(message_id=callback.message.message_id,
        #                 order_id=order_id)
        # data = await state.get_data()

    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]
    
    # Выводим один заказ
    text = order_text(order_items_data)
    
    from_menu = data['from_menu']
    
    await callback.message.edit_text(text=text,
                                        reply_markup=kb.change_order_menu(from_menu, order_id),
                                        parse_mode='HTML')


# Заходим в меню управления данными товаров
@order_changing.callback_query(F.data == 'change_item_data')
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
@order_changing.callback_query(F.data == 'change_order_name')
async def change_order_name_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='❓<b>ВВЕДИТЕ НОВОЕ ИМЯ КЛИЕНТА</b>❓',
                                            reply_markup=kb.back_to_change_order_data,
                                            parse_mode='HTML')
    await state.set_state(Order.change_order_name)


# Инициируем изменение количества товара или его удаление
@order_changing.callback_query(F.data.startswith('change_item_qty_page_'))
@order_changing.callback_query(F.data == 'delete_item')
@order_changing.callback_query(F.data == 'change_item_qty')
@order_changing.callback_query(F.data == 'change_item_qty_fact')
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
                        for item in order_items_data.keys() if item.startswith('item_')]
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
@order_changing.callback_query(F.data.startswith('add_item_page_'))
@order_changing.callback_query(F.data == 'add_new_item')
async def choose_new_item_handler(callback: CallbackQuery):
    if callback.data.startswith('add_item_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        page = 1
    await callback.message.edit_text(text='❓<b>ВЫБЕРИТЕ ТОВАР ДЛЯ ДОБАВЛЕНИЯ</b>❓',
                                     reply_markup=await kb.choose_add_item(page=page),
                                     parse_mode='HTML')


# Запрашиваем количество новодобавленного товара
@order_changing.callback_query(F.data.startswith('add_item_id_'))
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
                                            f'Выбранный товар - <b>{item_data.product_name} - {item_data.product_price} р/{product_unit}</b>.\n' \
                                            f'Количество укажите в <b>{product_unit_amend}</b>',
                                    reply_markup=kb.back_to_change_item_data,
                                    parse_mode='HTML')
    await state.set_state(Item.item_qty)


# Запрашиваем новое количество товара
@order_changing.callback_query(F.data.startswith('change_item_qty_'))
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
        qty = round(item_data.item_qty * 1000)
        qty_fact = f' Товар взвешен в количестве <b>{round(item_data.item_qty_fact * 1000)} {item_unit}</b>'
    else:
        qty = item_data.item_qty
        qty_fact = ' '
        
    if data['callback_name'] == 'delete_item':
        await callback.message.edit_text(text=f'❓ <b>ПОДТВЕРДИТЕ УДАЛЕНИЕ ТОВАРА ИЗ ЗАКАЗА</b> ❓\n\n'
                                            f'Выбранный товар - <b>{item_data.item_name} - {qty} {item_unit}</b>.{qty_fact}',
                                        reply_markup=kb.confirm_delete_item,
                                        parse_mode='HTML')
    else:
        qty_option = 'ФАКТИЧЕСКОЕ'
        if data['callback_name'] == 'change_item_qty':
            qty_option = 'ЗАКАЗАННОЕ'
        await callback.message.edit_text(text=f'❓ <b>УКАЖИТЕ {qty_option} КОЛИЧЕСТВО ПРОДУКТА</b> ❓\n\n' \
                                            f'Выбранный товар - <b>{item_data.item_name} - {qty} {item_unit}</b>.{qty_fact}.\n' \
                                            f'Количество укажите в <b>{item_unit_amend}</b>',
                                        reply_markup=kb.back_to_change_item_data,
                                        parse_mode='HTML')
        await state.set_state(Item.change_item_qty)


# Принимаем состояния для изменения данных и возвращаем меню для изменения данных
@order_changing.message(Order.change_disc)
@order_changing.message(Item.item_qty)
@order_changing.message(Order.change_order_name)
@order_changing.message(Item.change_item_qty)
@order_changing.message(Order.change_note)
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
            item_data = await get_item(data['item_id'])
            item_unit = item_data.item_unit
            item_unit_amend = 'штуках'
            if item_unit == 'кг':
                item_qty = Decimal(message.text.replace(',', '.')) / 1000
                item_unit = item_unit[-1]
                item_unit_amend = 'граммах'
                qty = item_data.item_qty * 1000
                qty_fact = f' Товар взвешен в количестве <b>{round(item_data.item_qty_fact * 1000)} {item_unit}</b>'

            else:
                qty = item_data.item_qty
                qty_fact = '.'
                item_qty = Decimal(message.text.replace(',', '.'))
        except:
            try:

                await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗ <b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b> ❗\n\n' \
                                                    f'❓ <b>УКАЖИТЕ {text_option} КОЛИЧЕСТВО ПРОДУКТА</b> ❓\n\n' \
                                                    f'Выбранный товар - <b>{item_data.item_name} - {round(qty)} {item_unit}</b>.{qty_fact}.\n' \
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
    elif 'change_order_name' in state_name:
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
                                                    f'Выбранный товар - <b>{item_data.product_name} - {item_data.product_price} р/{item_unit}</b>.\n' \
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
    
    from_menu = data['from_menu']
    
    reply_markup = kb.change_order_menu(from_menu, order_id)
    if state_name.split(':')[-1] in ('item_qty', 'change_item_qty'):
        reply_markup = kb.change_item_data
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=reply_markup,
                                        parse_mode='HTML')


# Удаляем товар после подтверждения
@order_changing.callback_query(F.data == 'confirm_delete_item')
async def confirm_delete_item_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item_id = [data['item_id']]
    await delete_items(item_ids=item_id)
    await callback.answer(text='Продукт был успешно удален', show_alert=True) 
    await change_item_data_handler(callback, state)


# Запрашиваем подтверждение на удаление заказа
@order_changing.callback_query(F.data == 'delete_order')
async def delete_order_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='<b>Для удаления заказа введите</b> <i>УДАЛИТЬ</i>',
                                     parse_mode='HTML',
                                     reply_markup=kb.back_to_change_order_data)
    await state.set_state(Order.delete_order)
    

# Просим подтвердить удаление после ввода слова
@order_changing.message(Order.delete_order)
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
                                            text='❗ <b>НЕПРАВИЛЬНО ВВЕДЕНЫ ДАННЫЕ!</b> ❗\n\nДля удаления заказа введите:\n<i>УДАЛИТЬ</i>',
                                            parse_mode='HTML',
                                            reply_markup=kb.back_to_change_order_data)


# Удаляем заказ и переходим к списку заказов или в меню сессии
@order_changing.callback_query(F.data == 'confirm_delete_order')
async def finish_delete_order_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='Заказ был успешно удален', show_alert=True)
    
    # Делаем запрос на товары из заказа
    data = await state.get_data()
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    # Удаляем все товары
    item_ids = [int(item_id.split('_')[-1]) for item_id in order_items_data.keys() if item_id.startswith('item_')]
    await delete_items(item_ids)
    
    # Удаляем заказ
    order_id = data['order_id']
    await delete_order(order_id)
    
    # Возвращаемся к списку всех заказов
    await state.update_data(callback_name=callback.data) # флаг для меню на случай отсутствия заказов
    
    if data['from_menu'] == 'completed_orders':
        await completed_orders_list_handler(callback, state)
    elif data['from_menu'] == 'order_processing':
        await orders_processing_handler(callback, state)

    
# Инициируем изменение статуса товара
@order_changing.callback_query(F.data == 'change_status')
async def change_status_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='Текущий статус, заказа "Обработан". Желаете переветси статус на "Не обработан"?',
                                     reply_markup=kb.confirm_change_status)

  
# сохраняем новый статус заказа и возвращаемся в меню с готовыми заказами
@order_changing.callback_query(F.data == 'confirm_change_status')
async def confirm_change_status_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data['order_id']
    order_data = {'order_completed': False}
    await change_order_data(order_id=order_id, order_data=order_data)
    await callback.answer(text='Статус заказа успешно изменен.', show_alert=True)
    await completed_orders_list_handler(callback, state)


# инициируем изменение комментария
@order_changing.callback_query(F.data == 'change_note')
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
@order_changing.callback_query(F.data == 'note_removal_from_order')
async def confirm_change_note(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    order_id = data['order_id']
    order_data = {'order_note': None}
    await change_order_data(order_id=order_id, order_data=order_data)
    await change_order_data_handler(callback, state)
    
    
# Инициируем изменение скидки на заказ
@order_changing.callback_query(F.data == 'change_order_disc')
async def change_item_disc_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='❗ <b>ВВЕДИТЕ РАЗМЕР СКИДКИ</b> ❗\n\n' \
                                        'Значение скидки должно быть в диапазоне от от 0 до 100 процентов',
                                    reply_markup=kb.back_to_change_order_data,
                                    parse_mode='HTML')
    await state.set_state(Order.change_disc)


# Инициируем выбор товаров для изменения вакуума
@order_changing.callback_query(F.data.startswith('change_vacc_page_'))
@order_changing.callback_query(F.data == 'change_delete_item_vacc')
@order_changing.callback_query(F.data == 'change_add_item_vacc')
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
@order_changing.callback_query(F.data.startswith('change_vacc_item_'))
@order_changing.callback_query(F.data == 'change_vacc_all')
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
    

# инициируем изменение номера телефона
@order_changing.callback_query(F.data == 'change_order_phone')
async def change_client_phone_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data['order_id']
    order_data = await get_order(order_id)
    client_phone = order_data.client_phone
    await callback.message.edit_text(text='❓ <b>ВЕДИТЕ НОВЫЙ НОМЕР ТЕЛЕФОНА КЛИЕНТА</b>\n\n' \
                                        f'Текущий номер - <b>{client_phone}</b>',
                                        reply_markup=kb.change_phone,
                                        parse_mode='HTML')
    await state.set_state(Order.change_order_phone)
    
    
# Удаляем номер телефона
@order_changing.callback_query(F.data == 'change_order:delete_phone')
async def delete_phone_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    order_id = data['order_id']
    order_data = await get_order(order_id)
    order_data = {'client_phone': None}
    await change_order_data(order_id=order_id, order_data=order_data)
    await change_order_data_handler(callback, state)


# сохраняем новый номер телефона
@order_changing.message(Order.change_order_phone)
async def recieve_phone_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    order_id = data['order_id']
    order_data = await get_order(order_id)
    client_phone = order_data.client_phone
    
    current_number = ''
    if client_phone:
        current_number = f'Текущий номер - <b>{client_phone}</b>'
    
    client_phone = message.text 
    # проверяем на наличие букв в номере, на всякий случай
    if re.search(r'[A-Za-zА-Яа-я]', client_phone) or not re.search(r'\d', client_phone):
        try:
            await state.set_state(Order.change_order_phone)
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗️ <b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ</b> \n\n' \
                                                    '❓ <b>ВВЕДИТЕ НОВЫЙ НОМЕР ТЕЛЕФОНА КЛИЕНТА</b> \n\n' \
                                                    f'{current_number}' \
                                                    'Формат ввода: <i>Номер телефона должен состоять только из цифр. ' \
                                                    'Если номер НЕ молдавский то должен включать код страны начинаясь с +</i>',
                                                reply_markup=kb.back_to_change_order_data,
                                                parse_mode='HTML')

            return None
        except TelegramBadRequest:
            return None
    
    # проверяем начинается ли с кода, и если нет то добавляем молдавский
    client_phone = re.sub(r'[^\d+]', '', client_phone).lstrip('0')
    if client_phone.startswith('373'):
        client_phone = '+' + client_phone
    elif client_phone.startswith('+'):
        pass
    else:
        client_phone = '+373' + client_phone
    
    # Сохраняем номер в базу данных
    order_data = {'client_phone': client_phone}
    await change_order_data(order_id=order_id, order_data=order_data)
    
    # Возвращаемся в меню изменения товаров
    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    # Выводим данные одного заказа в сообщение
    text = order_text(order_items_data)
    
    from_menu = data['from_menu']
    
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.change_order_menu(from_menu, order_id),
                                        parse_mode='HTML')
    
    
# Меняем сессию
@order_changing.callback_query(F.data.startswith('change_order:change_session_page_'))
@order_changing.callback_query(F.data == 'change_order:change_session')
async def change_session_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data['order_id']
    order_data = await get_order(order_id=order_id)
    session_id = order_data.session_id
    session_data = await get_session(session_id=session_id)
    current_session = session_data.session_name

    if callback.data.startswith('change_order:change_session_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        page = 1
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ СЕССИЮ</b>\n\n' \
                                            f'Текущая сессия - <b>{current_session}</b>',
                                     reply_markup=await kb.choose_session(page=page),
                                     parse_mode='HTML')



# Изменяем сессию и переходим в меню изменения заказа
@order_changing.callback_query(F.data.startswith('change_order:change_session_id_'))
async def change_order_data_handler(callback: CallbackQuery, state: FSMContext):
    new_session_id = int(callback.data.split('_')[-1])
    data = await state.get_data()
    old_session_id = data['session_id']
    order_id = data['order_id']
    await change_order_session_id(order_id=order_id, new_session_id=new_session_id, old_session_id=old_session_id)
    print(data)
    

    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    # Выводим один заказ
    text = order_text(order_items_data)
    
    from_menu = data['from_menu']
    
    await callback.message.edit_text(text=text,
                                        reply_markup=kb.change_order_menu(from_menu, order_id),
                                        parse_mode='HTML')
    
    
# переходим в меню управления данными выдачи
@order_changing.callback_query(F.data == 'change_order:issue_menu')
async def issue_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()

    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]

    text = order_text(order_items_data)
    issue_method = order_items_data['issue_method']
    issue_datetime = order_items_data['issue_datetime']
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.issue_menu(issue_method, issue_datetime),
                                     parse_mode='HTML')
    

# инициируем изменения метода выдачи
@order_changing.callback_query(F.data == 'change_order:issue_method')
async def issue_method_handler(callback: CallbackQuery, state: FSMContext):
    # Достаем данные о продуктах одного заказа
    data = await state.get_data()
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    issue_method = order_items_data['issue_method']
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ МЕТОД ВЫДАЧИ</b>\n\n' \
                                            f'Текущий метод - <b>{issue_method}</b>\n\n',
                                     reply_markup=kb.issue_method_kb(issue_method),
                                     parse_mode='HTML')
    

# Применяем выбранный метод выдачи
@order_changing.callback_query(F.data == 'change_order:self_pickup')
@order_changing.callback_query(F.data == 'change_order:delivery')
async def issue_method_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data['order_id']
    
    if callback.data == 'change_order:self_pickup':
        order_data = {'issue_method': 'Самовывоз', 'delivery_price': None, 'issue_place': None}
        await change_order_data(order_id, order_data)
        
    if callback.data == 'change_order:delivery':
        order_data = {'issue_method': 'Доставка'}
        await change_order_data(order_id, order_data)
        
    await issue_menu_handler(callback, state)



# инициируем изменение стоимости доставки
@order_changing.callback_query(F.data == 'change_order:delivery_price')
async def add_delivery_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    delivery_price = order_items_data['delivery_price']
    issue_method = order_items_data['issue_method']
    items_data = await get_items(data['order_id'])
    
    total_price = sum([round(item.item_price * item.item_qty_fact) for item in items_data])
    
    if issue_method != 'Самовывоз':
        if not delivery_price:
            if total_price >= 300:
                delivery_price = 0
            else:
                delivery_price = 20
    else:
        delivery_price = 0

    current_price = ''
    if delivery_price != None:
        current_price = f'Текущая стоимость доставки - <b>{round(delivery_price)} руб.</b>\n\n'
    
    from_menu = data['from_menu']
    
    await callback.message.edit_text(text='❓ <b>ВВЕДИТЕ СТОИМОСТЬ ДОСТАВКИ</b>\n\n' \
                                            f'{current_price}' \
                                            'Формат ввода данных: <i>123.45</i>',
                                     reply_markup=kb.cancel_delivery_price(from_menu),
                                     parse_mode='HTML')
    await state.set_state(Order.delivery_price)


# принимаем стоимость доставки и просим ввести адресс
@order_changing.message(Order.delivery_price)
async def delivery_price_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    order_id = data['order_id']
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]
    delivery_price = order_items_data['delivery_price']
    issue_method = order_items_data['issue_method']
    items_data = await get_items(data['order_id'])
    
    total_price = sum([round(item.item_price * item.item_qty_fact) for item in items_data])
    
    if issue_method != 'Самовывоз':
        if not delivery_price:
            if total_price >= 300:
                delivery_price = 0
            else:
                delivery_price = 20
    else:
        delivery_price = 0

    current_price = ''
    if delivery_price != None:
        current_price = f'Текущая стоимость доставки - <b>{round(delivery_price)} руб.</b>\n\n'
    
    try:
        delivery_price = str(Decimal(message.text.replace(',', '.')))
    except:
        try:
            from_menu = data['from_menu']
            await state.set_state(Order.delivery_price)
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text='❗️ <b>НЕВЕРНЫЙ ФОРМАТ ВВОДА</b>\n\n'\
                                            '❓ <b>ВВЕДИТЕ СТОИМОСТЬ</b>\n\n' \
                                            f'{current_price}' \
                                                'Формат ввода данных: <i>123.45</i>',
                                        reply_markup=kb.cancel_delivery_price(from_menu),
                                        parse_mode='HTML')
            return None
        except TelegramBadRequest:
            return None
        
    order_data = {'delivery_price': Decimal(delivery_price)}
    await change_order_data(order_id, order_data)
    
    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    # Выводим данные одного заказа в сообщени
    text = order_text(order_items_data)
    issue_method = order_items_data['issue_method']
    issue_datetime = order_items_data['issue_datetime']
    
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.issue_menu(issue_method, issue_datetime),
                                        parse_mode='HTML')
    

# удаляем стоимость заказа
@order_changing.callback_query(F.data == 'change_order:delete_delivery_price')
async def delete_delivery_price_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    order_id = data['order_id']
    
    order_data = {'delivery_price': None}
    await change_order_data(order_id, order_data)
    await issue_menu_handler(callback, state)
    

# инициируем изменение адресса
@order_changing.callback_query(F.data == 'change_order:issue_place')
async def issue_place_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data['order_id']
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]
    
    
    issue_place = order_items_data['issue_place']
    current_address = ''
    if issue_place:
        current_address = f'Текущий адресс доставки - <b>{issue_place}</b>\n\n'

    await callback.message.edit_text(text='❓ <b>ВВЕДИТЕ АДРЕСС ДОСТАВКИ</b>\n\n'
                                            f'{current_address}',
                                        reply_markup=kb.cancel_delivery_address,
                                        parse_mode='HTML')
    await state.set_state(Order.change_issue_place)
    
    
# Принимаем новый адресс
@order_changing.message(Order.change_issue_place)
async def issue_place_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    issue_place = message.text
    order_id = data['order_id']
    order_data = {'issue_place': issue_place}
    await change_order_data(order_id, order_data)
    
    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    # Выводим данные одного заказа в сообщени
    text = order_text(order_items_data)
    issue_method = order_items_data['issue_method']
    issue_datetime = order_items_data['issue_datetime']
    
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.issue_menu(issue_method, issue_datetime),
                                        parse_mode='HTML')
    

# удаляем адресс
@order_changing.callback_query(F.data == 'change_order:delete_address')
async def delete_address_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    order_id = data['order_id']
    
    order_data = {'issue_place': None}
    await change_order_data(order_id, order_data)
    await issue_menu_handler(callback, state)
  
    
# инициируем изменение даты выдачи
@order_changing.callback_query(F.data.startswith('change_order:delivery:prev:'))
@order_changing.callback_query(F.data.startswith('change_order:delivery:next:'))
@order_changing.callback_query(F.data == 'change_order:issue_date')
async def issue_date_handler(callback: CallbackQuery, state: FSMContext):   
    data = await state.get_data()
    order_id = data['order_id']
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]
    
    # Строим текст для текущих данных
    issue_datetime = order_items_data['issue_datetime']
    current_date = ''
    if issue_datetime:
        day_cur = issue_datetime.day
        month_cur = issue_datetime.month
        year_cur = issue_datetime.year
        current_date = f'Текущая дата - <b>{day_cur:02d}-{month_cur:02d}-{year_cur}</b>\n\n.'
        
    # Если методом выдачи был самовывоз, то АДРЕСС не нужен
    issue_method = order_items_data['issue_method']
    issue_opt = 'ДОСТАВКИ'
    if issue_method == 'Самовывоз':
        issue_opt = 'ВЫДАЧИ'
        
    await state.set_state(None)
    now = datetime.now()
    year = now.year
    month = now.month
    # Переключаем месяца вперед и назад
    if callback.data.startswith('change_order:delivery:'):
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
        await callback.message.edit_reply_markup(reply_markup=kb.create_calendar_keyboard(year, month))
    else:
        await callback.message.edit_text(text=f'❓ <b>УКАЖИТЕ ДАТУ {issue_opt}</b>\n\n' \
                                                f'{current_date}' \
                                                'Дату можно ввести вручную в формате: <i>ДД-ММ-ГГГГ</i>',
                                        reply_markup=kb.create_calendar_keyboard(year, month),
                                        parse_mode='HTML')
    await state.set_state(Order.change_issue_datetime)
    
    
# Указание даты
@order_changing.message(Order.change_issue_datetime)
async def issue_datetime_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    # Определяем слово для правильного отображения
    data = await state.get_data()
    order_id = data['order_id']
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]
    
    issue_method = order_items_data['issue_method']
    issue_opt = 'ДОСТАВКИ'
    if issue_method == 'Самовывоз':
        issue_opt = 'ВЫДАЧИ'
    
    issue_datetime = order_items_data['issue_datetime']
    current_date = ''
    if issue_datetime:
        day = issue_datetime.day
        month = issue_datetime.month
        year = issue_datetime.year
        current_date = f'Текущая дата - <b>{day:02d}-{month:02d}-{year}</b>\n\n.'
            
    try:
        date_comp = [int(_) for _ in message.text.split('-')]
        if len(date_comp) != 3 or len(str(date_comp[2])) != 4:
            raise ValueError('Неправильный формат')
        issue_datetime = {
            'year': date_comp[2],
            'month': date_comp[1],
            'day': date_comp[0]
        }
        datetime(**issue_datetime)
    except:
        try:
            await state.set_state(Order.change_issue_datetime)
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗ <b>НЕВЕРНО УКАЗАНА ДАТА</b>\n\n' \
                                                    f'❓ <b>УКАЖИТЕ ДАТУ {issue_opt}</b>\n\n' \
                                                    f'{current_date}' \
                                                    'Дату можно ввести вручную в формате:</b>\n<i>ДД-ММ-ГГГГ</i>',
                                                reply_markup=kb.create_calendar_keyboard(year, month),
                                                parse_mode='HTML')
            return None
        except TelegramBadRequest:
            return None
    
    order_data = {'issue_datetime': datetime(**issue_datetime)}
    await change_order_data(order_id, order_data)
    
    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    # Выводим данные одного заказа в сообщени
    text = order_text(order_items_data)
    issue_method = order_items_data['issue_method']
    issue_datetime = order_items_data['issue_datetime']
    
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.issue_menu(issue_method, issue_datetime),
                                        parse_mode='HTML')
    
    
# 
@order_changing.callback_query(F.data == 'change_order:delete_date')
@order_changing.callback_query(F.data.startswith('change_order:delivery:date:'))
async def issue_datetime_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    order_id = data['order_id']  
    if callback.data != 'change_order:delete_date':
        date_comp = [int(_) for _ in callback.data.split(':')[-3:]]
        issue_datetime = {
            'year': date_comp[0],
            'month': date_comp[1],
            'day': date_comp[2]
        }
        order_data = {'issue_datetime': datetime(**issue_datetime)}
    else:
        order_data = {'issue_datetime': None}
    await change_order_data(order_id, order_data)
    
    await issue_menu_handler(callback, state)
    
    
# инициируем изменение времени
@order_changing.callback_query(F.data == 'change_order:issue_time')
async def issue_time_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data['order_id']
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]
    
    # Определяем слово для правильного отображения
    data = await state.get_data()
    issue_method = order_items_data['issue_method']
    issue_opt = 'ДОСТАВКИ'
    if issue_method == 'Самовывоз':
        issue_opt = 'ВЫДАЧИ'
    
    issue_datetime = order_items_data['issue_datetime']
    current_time = ''
    if issue_datetime:
        hour = issue_datetime.hour
        minute = issue_datetime.minute
        if any((issue_datetime.hour, issue_datetime.minute)):
            current_time = f'Текущее время - <b>{hour:02d}:{minute:02d}</b>\n\n.'
            
    await callback.message.edit_text(text=f'❓⌚️ <b>УКАЖИТЕ ВРЕМЯ {issue_opt}</b>\n\n' \
                                        f'{current_time}' \
                                        'Формат ввода времени: <i>Например 13:30 можно указать как 1330 без символа " : ". '\
                                        'Важно, чтобы перед компонентами времени с одним заком стоял 0 в начале - 08:05 или 0805.</i>',
                                    reply_markup=kb.cancel_delivery_time,
                                    parse_mode='HTML')
    await state. set_state(Order.change_issue_time)
    

# Принимаем время доставки заказа
@order_changing.message(Order.change_issue_time)
async def issue_time_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)

    data = await state.get_data()
    order_id = data['order_id']
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]
    
    # Определяем слово для правильного отображения
    issue_method = order_items_data['issue_method']
    issue_opt = 'ДОСТАВКИ'
    if issue_method == 'Самовывоз':
        issue_opt = 'ВЫДАЧИ'
    
    issue_datetime = order_items_data['issue_datetime']
    if issue_datetime:
        hour = issue_datetime.hour
        minute = issue_datetime.minute
        if any((issue_datetime.hour, issue_datetime.minute)):
            current_time = f'Текущее время - <b>{hour:02d}:{minute:02d}</b>\n\n.'
    
    issue_time = message.text.replace(':', '')
    try:
        if len(issue_time) != 4:
            raise(ValueError('Неправильный формат'))
        issue_datetime_parts = {
            'year': issue_datetime.year,
            'month': issue_datetime.month,
            'day': issue_datetime.day,
            'hour': int(issue_time[:2]),
            'minute': int(issue_time[-2:])
            }
        datetime(**issue_datetime_parts)
    except Exception as e:
        try:
            await state.set_state(Order.change_issue_time)
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗ <b>НЕВЕРНО УКАЗАНО ВРЕМЯ</b>\n\n' \
                                                    f'⌚️ <b>УКАЖИТЕ ВРЕМЯ {issue_opt}</b>\n\n' \
                                                    f'{current_time}' \
                                                    'Формат ввода времени: <i>Например 13:30 можно указать как 1330 без символа " : ". '\
                                                    'Важно, чтобы перед компонентами времени с одним заком стоял 0 в начале - 08:05 или 0805.</i>',
                                                reply_markup=kb.cancel_delivery_time,
                                                parse_mode='HTML')
            return None
        except TelegramBadRequest:
            return None
            
    order_data = {'issue_datetime': datetime(**issue_datetime_parts)}
    await change_order_data(order_id, order_data)
    
    # Достаем данные о продуктах одного заказа
    order_items = await get_order_items(data['order_id'])
    order_items_data = group_orders_items(order_items)[0]
    
    # Выводим данные одного заказа в сообщени
    text = order_text(order_items_data)
    issue_method = order_items_data['issue_method']
    issue_datetime = order_items_data['issue_datetime']
    
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.issue_menu(issue_method, issue_datetime),
                                        parse_mode='HTML')


# удаление времени выдачи
@order_changing.callback_query(F.data == 'change_order:delete_time')
async def delete_time_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)

    data = await state.get_data()
    order_id = data['order_id']
    order_items = await get_order_items(order_id)
    order_items_data = group_orders_items(order_items)[0]
    
    issue_datetime = order_items_data['issue_datetime']
    issue_datetime_parts = {
        'year': issue_datetime.year,
        'month': issue_datetime.month,
        'day': issue_datetime.day,
        'hour': 0,
        'minute': 0
        }
    
    order_data = {'issue_datetime': datetime(**issue_datetime_parts)}
    await change_order_data(order_id, order_data)
    
    await issue_menu_handler(callback, state)
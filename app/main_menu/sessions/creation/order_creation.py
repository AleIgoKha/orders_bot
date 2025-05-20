from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from decimal import Decimal

import app.main_menu.sessions.creation.keyboard as kb
from app.main_menu.sessions.orders_menu import session_menu_handler
from app.states import Order, Product
from app.database.requests import get_product, add_order, get_new_last_number, get_order_id, add_order_items


order_creation = Router()


# формирование сообщения
def order_text(data):
    products_list = [product_data for product_data in data.keys() if product_data.startswith('product_data_')]
    
    text = f'📋 <b>МЕНЮ ЗАКАЗА</b> 📋\n\n' \
            f'👤 Клиент - <b>{data['client_name']}</b>\n\n'
    
    if products_list: 
        for product in products_list:
            product_name = data[product]['product_name']
            product_qty = data[product]['product_qty']
            product_unit = data[product]['product_unit']
            item_vacc = data[product]['item_vacc']
            # item_disc = data[product]['item_disc']
            
            product_unit_amend = product_unit
            if product_unit_amend == 'кг':
                product_unit_amend = 'г'
                
            if item_vacc:
                item_vacc = ' (вак. уп.)'
            else:
                item_vacc = ''
            
            text += f'🧀 <b>{product_name}{item_vacc}</b>\nЗаказано - <b>{product_qty} {product_unit_amend}</b>\n'
            
        if data['order_disc'] != 0:
            text += f'\nСкидка на заказ - <b>{data['order_disc']} %</b>\n'
        
    if data['order_note']:
        text += f'\n<b>📝 Комментарий к заказу</b>\n{data['order_note']}'
        
    return text


# Создаем новый заказ внутри сессии и просим ввести имя клиента
@order_creation.callback_query(F.data == 'order_creation')
async def order_creation_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Order.client_name)
    await callback.message.edit_text('<b>Введите имя клиента</b>',
                                     reply_markup=kb.order_cancelation,
                                     parse_mode='HTML')
    await state.update_data(next_product_number=0,
                            order_note=None) # инициируем создание номера продукта для дальшейней инкрементации при добавлении


# Сохраняем имя клиента и попадаем в меню для создания заказа
@order_creation.message(Order.client_name)
async def order_menu_handler(message: Message, state: FSMContext):   
    state_name = await state.get_state()
    
    if state_name:
        if 'client_name' in state_name:
            await state.update_data(client_name=message.text, order_disc=0)
        
    await state.set_state(None)
    data = await state.get_data()
    
    text = order_text(data)
    
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.new_order_keyboard,
                                        parse_mode='HTML')


# Возвращение в меню с созданием заказа
@order_creation.callback_query(F.data == 'back_to_order_creation')
async def back_to_order_creation_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()  
    
    text = order_text(data)
    
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.new_order_keyboard,
                                    parse_mode='HTML')


# Выбираем продукт для добавления из списка
@order_creation.callback_query(F.data.startswith('product_page_'))
@order_creation.callback_query(F.data == 'add_product_to_order')
async def choose_product_handler(callback: CallbackQuery):
    if callback.data.startswith('product_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        page = 1
    await callback.message.edit_text(text='<b>Для выбора товара нажмите на него</b>',
                                     reply_markup=await kb.choose_product(page=page),
                                     parse_mode='HTML')


# Продукт выбрали, теперь просим ввести вес
@order_creation.callback_query(F.data.startswith('product_id_'))
async def add_product_handler(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split('_')[-1])
    product_data =  await get_product(product_id=product_id) # сохраняем номер продукта, чтобы не сохранять все данные о нем, чтобы избежать неприятностей на случай отмены
    
    product_name = product_data.product_name
    product_price = float(product_data.product_price)
    product_unit = product_data.product_unit
    
    product_unit_amend = product_unit
    if product_unit_amend == 'кг':
        product_unit_amend = 'граммах'
    await state.update_data(product_id=product_id,
                            product_name=product_name,
                            product_price=product_price,
                            product_unit=product_unit,
                            product_unit_amend=product_unit_amend)
        
    await callback.message.edit_text(text=f'Выбранный товар: <b>{product_name} - {product_price} р/{product_unit}\n</b>' \
                                        f'Введите заказанное количество товара в {product_unit_amend}',
                                        reply_markup=kb.back_to_order_creation,
                                        parse_mode='HTML')
    await state.set_state(Product.qty)


# Сохраняем данные о продукте в FSMContext включая вес товара и снова выводим меню заказа
@order_creation.message(Product.qty)
async def product_qty_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # Проверяем на формат
    try:
        qty = str(Decimal(message.text.replace(',', '.')))
        if Decimal(qty) == 0:
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗<b>КОЛИЧЕСТВО НЕ МОЖЕТ БЫТЬ РАВНО НУЛЮ!</b>❗\n\n' \
                                                    f'Выбранный товар: <b>{data['product_name']} - {data['product_price']} р/{data['product_unit']}\n</b>' \
                                                    f'Введите заказанное количество товара в {data["product_unit_amend"]}',
                                                parse_mode='HTML',
                                                reply_markup=kb.back_to_order_creation)
            return None
    except:
        try:
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>❗\n\n' \
                                                    'Формат ввода предполагает использование цифр и одного десятичного разделителя: <i>123.45</i>\n\n' \
                                                    f'Выбранный товар: <b>{data['product_name']} - {data['product_price']} р/{data['product_unit']}\n</b>'  \
                                                    f'Введите заказанное количество товара в {data["product_unit_amend"]}',
                                                parse_mode='HTML',
                                                reply_markup=kb.back_to_order_creation)
            return None
        except TelegramBadRequest:
            return None
    
    product_data =  await get_product(product_id=data['product_id'])
    product_data_dict = {
        'product_name': product_data.product_name,
        'product_price': str(product_data.product_price),
        'product_unit': product_data.product_unit,
        'product_qty': qty,
        'item_vacc': False,
        'item_disc': data['order_disc']
    }
    
    product_number = data['next_product_number']
    await state.update_data({f'product_data_{product_number}': product_data_dict, # Добавляем данные о продукте в FSMContext с ключем product_i
                             'next_product_number': product_number + 1,  # i увеличиваем на 1 для следующего продукта
                             'current_product': f'product_data_{product_number}' # фиксируем продукт, с которым работаем на данный момент
                             })
    # еще раз загружаем обновленный FSMContext
    data = await state.get_data()
    
    await order_menu_handler(message, state)


# Инициализируем изменение в заказе
@order_creation.callback_query(F.data == 'change_order')
async def change_order_handler(callback: CallbackQuery):
    await callback.message.edit_text('<b>Выберите изменение</b>',
                                     reply_markup=kb.change_order_keyboard,
                                     parse_mode='HTML')


# Инициализируем изменение имени клиента
@order_creation.callback_query(F.data == 'change_name')
async def change_name_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='<b>Введите новое имя клиента</b>',
                                     reply_markup=kb.back_to_order_changing,
                                     parse_mode='HTML')
    await state.set_state(Order.client_name)


# Предлагаем список продуктов для изменения
@order_creation.callback_query(F.data.startswith('product_data_page_'))
@order_creation.callback_query(F.data == 'change_product')
async def choose_change_product_handler(callback: CallbackQuery, state: FSMContext):
    # получаем список словарей с информацией о товаре
    if callback.data.startswith('product_data_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        page = 1
    data = await state.get_data()
    products = {product:data[product] for product in data.keys() if product.startswith('product_data_')}
    await callback.message.edit_text(text='<b>Выберите продукт для изменения</b>',
                                     reply_markup= await kb.change_product_keyboard(products, page=page),
                                     parse_mode='HTML')


# Инициализируем изменение веса продукта
@order_creation.callback_query(F.data.startswith('product_data_')) # важно помнить, это условине работает только потому что находится ниже предыдущего
async def change_product_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_data = data[callback.data]
    
    product_name = product_data['product_name']
    product_unit = product_data['product_unit']
    product_qty = product_data['product_qty']
    
    product_unit_amend = product_unit
    if product_unit_amend == 'кг':
        product_unit_amend = 'граммах'
    await state.update_data(product_name=product_name,
                            product_unit=product_unit,
                            product_qty=product_qty,
                            product_unit_amend=product_unit_amend)
        
    await callback.message.edit_text(text=f'<b>{product_name} - {product_qty} {product_unit_amend[0]}\n</b>' \
                                        f'Введите новое количество товара в {product_unit_amend}. Для удаления укажите 0',
                                        reply_markup=kb.back_to_order_creation,
                                        parse_mode='HTML')
    
    await state.set_state(Product.new_qty)
    await state.update_data(current_product=callback.data)


# Сохраняем новый вес и возвращаемся в меню заказа
@order_creation.message(Product.new_qty)
async def new_qty_product_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # Проверяем на формат
    try:
        qty = str(Decimal(message.text.replace(',', '.')))
    except:
        try:
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>❗\n\n' \
                                                    'Формат ввода предполагает использование цифр и одного десятичного разделителя: <i>123.45</i>\n\n' \
                                                    f'<b>{data['product_name']} - {data['product_qty']} {data['product_unit_amend'][0]}\n</b>'  \
                                                    f'Введите новое количество товара в {data["product_unit_amend"]}. Для удаления укажите 0',
                                                parse_mode='HTML',
                                                reply_markup=kb.back_to_order_creation)
            return None
        except TelegramBadRequest:
            return None
        
    if qty == '0':
        data = {key:value for key, value in data.items() if key != data['current_product']}
        await state.clear()
        await state.update_data(data)
    else:
        current_product = data['current_product']
        data[current_product]['product_qty'] = qty
        await state.clear()
        await state.update_data(data)
        
    await order_menu_handler(message, state)


# инициируем Добавление комментарий к заказу
@order_creation.callback_query(F.data == 'add_note')
async def add_note_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = '<b>Введить комментарий к заказу</b>\n'
    if data['order_note']:
        text += f'\n<b>Текущий комментарий к заказу:</b>\n{data['order_note']}'
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.note_removal,
                                     parse_mode='HTML')
    await state.set_state(Order.add_note)


# Удаление комментария
@order_creation.callback_query(F.data == 'note_removal')
async def add_note_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await state.update_data(order_note=None)
    await back_to_order_creation_handler(callback, state)


# Добавляем комментарий к заказу
@order_creation.message(Order.add_note)
async def add_note_handler(message: Message, state: FSMContext):
    order_note = message.text
    await state.update_data(order_note=order_note)
    await state.set_state(None)
    await order_menu_handler(message, state)


# просим подтвердить сохранение заказа в базу данных
@order_creation.callback_query(F.data == 'save_order')
async def save_order_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='<b>Подтвердите сохранение заказа</b>',
                                     reply_markup=kb.order_confirmation,
                                     parse_mode='HTML')
    

# сохраняем заказ в базу данных
@order_creation.callback_query(F.data == 'confirm_order_creation')
async def confirm_order_creation_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Создаем новый заказ в базе данных
    order_number = await get_new_last_number(data['session_id']) + 1
    order_data = {
        'session_id': data['session_id'],
        'client_name': data['client_name'],
        'order_number': order_number,
        'order_note': data['order_note'],
        'order_disc': data['order_disc']
    }
    await add_order(order_data)
    
    # Добавляем данные о товарах в базу данных
    order_id = await get_order_id(data['session_id'], order_number)
    items_data = [{'order_id': order_id} | data[product] for product in data.keys() if product.startswith('product_data_')]
    await add_order_items(items_data)
    
    # Показываем сообщение об успешности создания заказа
    await callback.answer('Заказ успешно создан', show_alert=True)
    await session_menu_handler(callback, state)

    
@order_creation.callback_query(F.data == 'confirm_order_cancelation')
async def confirm_order_cancelation_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='❗<b>ВНИМАНИЕ</b>❗\n\nПри отмене заказа его данные буду удалены. Подтвердить отмену заказа?',
                                     reply_markup=kb.confirm_order_cancelation,
                                     parse_mode='HTML')


# Добавляем вакуумную упаковку к продукту в заказе
@order_creation.callback_query(F.data.startswith('add_vacc_page_'))
@order_creation.callback_query(F.data == 'add_vacc_to_order')
@order_creation.callback_query(F.data == 'delete_vacc')
async def add_vacc_to_order_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('add_vacc_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        await state.update_data(from_callback=callback.data)
        page = 1
    data = await state.get_data()
    from_callback = data['from_callback']
    if from_callback == 'add_vacc_to_order':
        # получаем список словарей с информацией о товаре без вакуумной упаковки
        products = {product:data[product] for product in data.keys() if product.startswith('product_data_')
                    and data[product]['item_vacc'] == False}
        if products: 
            await callback.message.edit_text(text='<b>Выберите продукт для вакуумации</b>',
                                            reply_markup= await kb.choose_product_vacc(products, from_callback, page=page),
                                            parse_mode='HTML')
        else:
            await callback.answer(text='Нет продуктов для вакуумации', show_alert=True)
    elif from_callback == 'delete_vacc':
        # получаем список словарей с информацией о товаре с вакуумной упаковкой
        products = {product:data[product] for product in data.keys() if product.startswith('product_data_')
                    and data[product]['item_vacc'] == True}
        if products:
            await callback.message.edit_text(text='<b>Выберите продукт для удаления вакуумации</b>',
                                            reply_markup= await kb.choose_product_vacc(products, from_callback, page=page),
                                            parse_mode='HTML')
        else:
            await callback.answer(text='Нет продуктов с вакуумацией', show_alert=True)


# Сохраняем данные о добавлении вакуумной упаковки
@order_creation.callback_query(F.data.startswith('add_vacc_item_'))
@order_creation.callback_query(F.data.startswith('vacc_all'))
async def add_vacc_item_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    from_callback = data['from_callback']
    
    # Удалить или наоборот
    if from_callback == 'add_vacc_to_order':
        flag = True
    elif from_callback == 'delete_vacc':
        flag = False
    
    if callback.data.startswith('add_vacc_item_'): # если один продукт
        product_data_id = int(callback.data.split('_')[-1])
        product = f'product_data_{product_data_id}'
        data[product]['item_vacc'] = flag
    elif callback.data == 'vacc_all': # Если все продукты сразу
        product_list = [product for product in data.keys() if product.startswith('product_data_')]
        for product in product_list:
            data[product]['item_vacc'] = flag
            
    # Перезаписываем весь FSM 
    await state.clear()
    await state.update_data(data)
    
    # В зависимости от того удаляем вакуум или добавляем выбираем соответствующее меню
    if from_callback == 'add_vacc_to_order':
        await back_to_order_creation_handler(callback, state)
    elif from_callback == 'delete_vacc':
        await change_order_handler(callback)
    

# Временно отключено
# Инициируем добавление дискаунта и предлагаем выбрать продукт которому дать скидку
@order_creation.callback_query(F.data == 'add_disc_to_order')
@order_creation.callback_query(F.data.startswith('add_disc_page_'))
async def add_disc_to_order_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('add_disc_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        page = 1
    data = await state.get_data()
    # получаем список словарей с информацией о товаре
    products = {product:data[product] for product in data.keys() if product.startswith('product_data_')}
    await callback.message.edit_text(text='<b>Выберите продукт указания скидки</b>',
                                     reply_markup= await kb.choose_add_disc(products, page=page),
                                     parse_mode='HTML')
    

# Запрашиваем ввод размера скидки
@order_creation.callback_query(F.data.startswith('add_disc_item_'))
@order_creation.callback_query(F.data == 'disc_all')
async def add_disc_item_handler(callback: CallbackQuery, state: FSMContext):
    from_callback = callback.data
    await state.update_data(from_callback=from_callback)
    
    # Пока что отключено, по необходимости и неудобствам в связи с недоработкой
    if from_callback != 'disc_all':
        product_data_id = int(callback.data.split('_')[-1])
        current_product = f'product_data_{product_data_id}'
        await state.update_data(current_product=current_product)
        
    await callback.message.edit_text(text='<b>Введите размер скидки в процентах от 0 до 100</b>',
                                    reply_markup=kb.back_to_order_creation,
                                    parse_mode='HTML')
    await state.set_state(Product.disc)


# Наданный момент работает только на весь заказ
# (Применение скидки на отдельные товары)
@order_creation.message(Product.disc)
async def save_disc_item_handler(message: Message, state: FSMContext):
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
                                                reply_markup=kb.back_to_order_creation)
            return None
        except TelegramBadRequest:
            return None
        
    await state.set_state(None)

    if data['from_callback'] != 'disc_all': # если один продукт
        current_product = data['current_product']
        data[current_product]['item_disc'] = disc
    else: # Если все продукты сразу
        product_list = [product for product in data.keys() if product.startswith('product_data_')]
        for product in product_list:
            data[product]['item_disc'] = disc
            data['order_disc'] = disc
    

    await state.clear()
    await state.update_data(data)
        
    await order_menu_handler(message, state)
    
    

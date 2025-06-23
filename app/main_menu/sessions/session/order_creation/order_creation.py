import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from decimal import Decimal
from datetime import datetime, time
import pytz

import app.main_menu.sessions.session.order_creation.keyboard as kb
from app.main_menu.sessions.session.session_menu import session_menu_handler
from app.main_menu.main_menu import main_menu_handler
from app.com_func import represent_utc_3
from app.states import Order, Product
from app.database.requests import get_product, add_order, add_order_items, get_session_by_name, get_session


order_creation = Router()


# формирование сообщения
def order_text(data):
    products_list = [product_data for product_data in data.keys() if product_data.startswith('product_data_')]
    
    text = f'📋 <b>МЕНЮ ЗАКАЗА</b>\n\n'
    
    if data['client_name']:
        text += f'👤 Клиент - <b>{data['client_name']}</b>\n'
           
    if data['client_phone']:
        text += f'☎️ Телефон - <b>{data['client_phone']}</b>\n'
        
    text += f'📂 Сессия - <b>{data['session_name']}</b>\n'
    
    if products_list:
        text += '\n🧀 Состав заказа:\n'
        
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
            
            text += f'<b>{product_name}{item_vacc} - {product_qty} {product_unit_amend}</b>\n'
            
        if data['order_disc'] != 0:
            text += f'\n🤑 Скидка на заказ - <b>{data['order_disc']} %</b>\n'
    
    text += f'\n🛍 Метод выдачи - <b>{data['issue_method']}</b>\n'
    
    issue_method = data['issue_method']
    issue_opt = 'доставки'
    if issue_method == 'Самовывоз':
        issue_opt = 'выдачи'
    
    if data['issue_place']:
        text += f'📍 Место доставки - <b>{data['issue_place']}</b>\n'
    if data['issue_datetime']:
        text += f'📅 Дата {issue_opt} - <b>{data['issue_datetime']['day']:02d}-{data['issue_datetime']['month']:02d}-{data['issue_datetime']['year']}</b>\n'
        if 'hour' in data['issue_datetime'].keys():
            text += f'⌚️ Время {issue_opt} - <b>{data['issue_datetime']['hour']:02d}:{data['issue_datetime']['minute']:02d}</b>\n'

    
    if data['order_note']:
        text += f'\n<b>📝 Комментарий к заказу</b>\n{data['order_note']}'
        
    return text


# Создаем новый заказ внутри сессии и просим ввести имя клиента
@order_creation.callback_query(F.data == 'main:new_order')
@order_creation.callback_query(F.data == 'session:new_order')
async def new_order_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_default = await get_session_by_name(session_name='⭐️ Входящие')
    session_id = data['session_id'] if 'session_id' in data.keys() else session_default.session_id
    session = await get_session(session_id)
    initial_data = {
        'next_product_number': 0, # инкремент для идентификации продукта в FSMContext
        'order_note': None,
        'order_disc': 0,
        'back_opt': f'{callback.data.split(':')[0]}:menu',
        'chat_id': callback.message.chat.id,
        'message_id': callback.message.message_id,
        'session_id': session_id,
        'session_name': session.session_name,
        'issue_method': 'Самовывоз',
        'issue_place': None,
        'issue_datetime': None
    }
    
    await state.update_data(initial_data)
    
    # определяем кнопку возврата
    if callback.data == 'main:new_order':
        back_opt = 'main:menu'
    else:
        back_opt = 'back_from_order_creation'
        
    await callback.message.edit_text(text='❓ <b>ВВЕДИТЕ НОМЕР ТЕЛЕФОНА КЛИЕНТА</b> \n\n' \
                                        'Формат ввода: <i>Номер телефона должен состоять только из цифр. ' \
                                        'Если номер НЕ молдавский то должен включать код страны начинаясь с +</i>',
                                     reply_markup=kb.client_phone_cancelation(back_opt),
                                     parse_mode='HTML')
    await state.set_state(Order.client_phone)
    
    
# Создаем новый заказ внутри сессии и просим ввести имя клиента
@order_creation.callback_query(F.data == 'new_order:skip_phone')
async def skip_phone_handler(callback: CallbackQuery, state: FSMContext):
    # определяем кнопку возврата
    data = await state.get_data()
    back_opt = data['back_opt']
    if back_opt != 'main:menu':
        back_opt = 'back_from_order_creation'
    
    await callback.message.edit_text('❓ <b>ВВЕДИТЕ ИМЯ КЛИЕНТА</b>',
                                     reply_markup=kb.client_name_cancelation(back_opt),
                                     parse_mode='HTML')
    # инициируем создание номера продукта для дальшейней инкрементации при добавлении
    await state.update_data(client_phone=None)
    await state.set_state(Order.client_name)


# Сохраняем имя клиента и/или телефон и попадаем в меню для создания заказа
@order_creation.message(Order.client_phone)
@order_creation.message(Order.client_name)
async def order_menu_handler(message: Message, state: FSMContext):
    state_name = str(await state.get_state()).split(':')[-1]
    await state.set_state(None)
    
    if state_name == 'client_name':  
        await state.update_data(client_name=message.text)
        data = await state.get_data()
        # выводим меню нового заказа
        text = order_text(data)
        await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text=text,
                                            reply_markup=kb.new_order_keyboard,
                                            parse_mode='HTML')
    elif state_name == 'client_phone':
        data = await state.get_data()
        # определяем кнопку возврата
        back_opt = data['back_opt']
        if back_opt != 'main:menu':
            back_opt = 'back_from_order_creation'
        
        client_phone = message.text 
        # проверяем на наличие букв в номере, на всякий случай
        if re.search(r'[A-Za-zА-Яа-я]', client_phone) or not re.search(r'\d', client_phone):
            try:
                await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                    message_id=data['message_id'],
                                                    text='❗️ <b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ</b> \n\n' \
                                                        '❓ <b>ВВЕДИТЕ НОМЕР ТЕЛЕФОНА КЛИЕНТА</b> \n\n' \
                                                        'Формат ввода: <i>Номер телефона должен состоять только из цифр. ' \
                                                        'Если номер НЕ молдавский то должен включать код страны начинаясь с +</i>',
                                                    reply_markup=kb.client_phone_cancelation(back_opt),
                                                    parse_mode='HTML')
                await state.set_state(Order.client_phone)
                return None
            except TelegramBadRequest:
                await state.set_state(Order.client_phone)
                return None
        
        # проверяем начинается ли с кода, и если нет то добавляем молдавский
        client_phone = re.sub(r'[^\d+]', '', client_phone).lstrip('0')
        if client_phone.startswith('373'):
            client_phone = '+' + client_phone
        elif client_phone.startswith('+'):
            pass
        else:
            client_phone = '+373' + client_phone
        
        # Сохраняем номер в контекст
        await state.update_data(client_phone=client_phone)
        
        # Просим ввести имя
        await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text='❓ <b>ВВЕДИТЕ ИМЯ КЛИЕНТА</b>',
                                            reply_markup=kb.client_name_cancelation(back_opt),
                                            parse_mode='HTML')
        await state.set_state(Order.client_name)


# Возвращение в меню с созданием заказа
@order_creation.callback_query(F.data == 'new_order:menu')
@order_creation.callback_query(F.data == 'new_order:delete_time')
@order_creation.callback_query(F.data == 'new_order:delete_date')
async def back_to_order_creation_handler(callback: CallbackQuery, state: FSMContext):
    # в случае удаления времени выдачи
    if callback.data == 'new_order:delete_date':
        await state.update_data(issue_datetime=None)
    elif callback.data == 'new_order:delete_time':
        data = await state.get_data()
        issue_datetime = data['issue_datetime']
        issue_datetime = {
            'day': issue_datetime['day'],
            'month': issue_datetime['month'],
            'year': issue_datetime['year']
        }
        await state.update_data(issue_datetime=issue_datetime)
        
    
    await state.set_state(None)
    data = await state.get_data()
    text = order_text(data)
    
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.new_order_keyboard,
                                    parse_mode='HTML')


# Выбираем продукт для добавления из списка
@order_creation.callback_query(F.data.startswith('product_page_'))
@order_creation.callback_query(F.data == 'new_order:add_product')
async def choose_product_handler(callback: CallbackQuery):
    if callback.data.startswith('product_page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1
    await callback.message.edit_text(text='❓ <b> ВЫБЕРИТЕ ТОВАР</b>',
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
    # выводим меню нового заказа
    data = await state.get_data()
    text = order_text(data)
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.new_order_keyboard,
                                        parse_mode='HTML')
    


# Инициализируем изменение в заказе
@order_creation.callback_query(F.data.startswith('new_order:change_session_id_'))
@order_creation.callback_query(F.data == 'new_order:change_order')
async def change_order_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('new_order:change_session_id_'):
        session_id = int(callback.data.split('_')[-1])
        session = await get_session(session_id)
        await state.update_data(session_id=session_id, session_name=session.session_name)
        
    data = await state.get_data()
    text = order_text(data)
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.change_order_keyboard,
                                     parse_mode='HTML')


# инициируем изменение имени клиента
@order_creation.callback_query(F.data == 'new_order:change_name')
async def change_name_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='❓ <b>ВВЕДИТЕ НОВОЕ ИМЯ КЛИЕНТА</b>',
                                     reply_markup=kb.back_to_order_changing,
                                     parse_mode='HTML')
    await state.set_state(Order.change_client_name)
    
    
# инициируем изменение номера телефона клиента
@order_creation.callback_query(F.data == 'new_order:change_phone')
async def change_name_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='❓ <b>ВВЕДИТЕ НОВЫЙ НОМЕР ТЕЛЕФОНА КЛИЕНТА</b>',
                                     reply_markup=kb.back_to_order_changing,
                                     parse_mode='HTML')
    await state.set_state(Order.change_client_phone)


# Сохраняем имя клиента и/или телефон и попадаем в меню для создания заказа
@order_creation.message(Order.change_client_phone)
@order_creation.message(Order.change_client_name)
async def change_order_data_handler(message: Message, state: FSMContext):
    # сохраняем состояние в переменную и обнуляем его
    state_name = str(await state.get_state()).split(':')[-1]
    await state.set_state(None)
    data = await state.get_data()
    
    if state_name == 'change_client_name':
        await state.update_data(client_name=message.text)


    elif state_name == 'change_client_phone':
        client_phone = message.text 
        # проверяем на наличие букв в номере, на всякий случай
        if re.search(r'[A-Za-zА-Яа-я]', client_phone) or not re.search(r'\d', client_phone):
            try:
                await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                    message_id=data['message_id'],
                                                    text='❗️ <b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ</b> \n\n' \
                                                        '❓ <b>ВВЕДИТЕ НОВЫЙ НОМЕР ТЕЛЕФОНА КЛИЕНТА</b> \n\n' \
                                                        'Формат ввода: <i>Номер телефона должен состоять только из цифр. ' \
                                                        'Если номер НЕ молдавский то должен включать код страны начинаясь с +</i>',
                                                    reply_markup=kb.back_to_order_changing,
                                                    parse_mode='HTML')
                await state.set_state(Order.client_phone)
                return None
            except TelegramBadRequest:
                await state.set_state(Order.client_phone)
                return None
        
        # проверяем начинается ли с кода, и если нет то добавляем молдавский
        client_phone = re.sub(r'[^\d+]', '', client_phone).lstrip('0')
        if client_phone.startswith('373'):
            client_phone = '+' + client_phone
        elif client_phone.startswith('+'):
            pass
        else:
            client_phone = '+373' + client_phone
        
        # Сохраняем номер в контекст
        await state.update_data(client_phone=client_phone)
        
    # выводим меню нового заказа
    data = await state.get_data()
    text = order_text(data)
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.change_order_keyboard,
                                        parse_mode='HTML')


# Предлагаем список продуктов для изменения
@order_creation.callback_query(F.data.startswith('product_data_page_'))
@order_creation.callback_query(F.data == 'change_product')
async def choose_change_product_handler(callback: CallbackQuery, state: FSMContext):
    # получаем список словарей с информацией о товаре
    if callback.data.startswith('product_data_page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1
    data = await state.get_data()
    products = {product:data[product] for product in data.keys() if product.startswith('product_data_')}
    if len(products) == 0:
        await callback.answer(text='Нет товаров в заказе', show_alert=True)
    else:
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
        
    # выводим меню нового заказа
    data = await state.get_data()
    text = order_text(data)
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.new_order_keyboard,
                                        parse_mode='HTML')


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
    # выводим меню нового заказа
    
    data = await state.get_data()
    text = order_text(data)
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.new_order_keyboard,
                                        parse_mode='HTML')


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
    session_id = data['session_id']
    
    # tz = pytz.timezone("Europe/Chisinau")
    # localized_midnight = tz.localize(datetime.combine(datetime.now(tz).date(), time(0, 0)))

    
    # Создаем новый заказ в базе данных
    # order_number = await get_new_last_number(data['session_id']) + 1
    order_data = {
        'session_id': data['session_id'],
        'client_name': data['client_name'],
        'client_phone': data['client_phone'],
        # 'order_number': order_number,
        'order_note': data['order_note'],
        'order_disc': data['order_disc'],
        'order_completed': False,
        'issue_method': data['issue_method'],
        'issue_place': data['issue_place'],
        'issue_datetime': represent_utc_3(datetime(**data['issue_datetime'])) if data['issue_datetime'] else None,
        # 'creation_datetime': localized_midnight
    }
    order_id = await add_order(order_data, session_id)
    
    # Добавляем данные о товарах в базу данных
    # order_id = await get_order_id(data['session_id'], order_number)
    items_data = [{'order_id': order_id} | data[product] for product in data.keys() if product.startswith('product_data_')]
    await add_order_items(items_data)
    
    # Показываем сообщение об успешности создания заказа
    await callback.answer('Заказ успешно создан', show_alert=True)
    if data['back_opt'] == 'session:menu':
        await session_menu_handler(callback, state)
    else:
        await main_menu_handler(callback, state)

    
@order_creation.callback_query(F.data == 'confirm_order_cancelation')
async def confirm_order_cancelation_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # определяем кнопку возврата
    back_opt = data['back_opt']
    if back_opt != 'main:menu':
        back_opt = 'back_from_order_creation'
    await callback.message.edit_text(text='❗<b>ВНИМАНИЕ</b>❗\n\nПри отмене заказа его данные буду удалены. Подтвердить отмену заказа?',
                                     reply_markup=kb.confirm_order_cancelation(back_opt),
                                     parse_mode='HTML')


# Добавляем вакуумную упаковку к продукту в заказе
@order_creation.callback_query(F.data.startswith('add_vacc_page_'))
@order_creation.callback_query(F.data == 'add_vacc_to_order')
@order_creation.callback_query(F.data == 'delete_vacc')
async def add_vacc_to_order_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('add_vacc_page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
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
        await change_order_handler(callback, state)
    

# инициируем выбор сессии для ее смены
@order_creation.callback_query(F.data.startswith('new_order:change_session_page_'))
@order_creation.callback_query(F.data == 'new_order:change_session')
async def change_session_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_session = data['session_name']
    if callback.data.startswith('new_order:change_session_page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ СЕССИЮ</b>\n\n' \
                                            f'Текущая сессия - <b>{current_session}</b>',
                                     reply_markup=await kb.choose_session(page=page),
                                     parse_mode='HTML')
    

# инициируем указание метода выдачи заказа
@order_creation.callback_query(F.data == 'new_order:add_delivery')
async def add_delivery_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    issue_method = data['issue_method']
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ МЕТОД ВЫДАЧИ</b>\n\n' \
                                            f'Текущий метод - <b>{issue_method}</b>\n\n',
                                     reply_markup=kb.cancel_delivery_price(issue_method),
                                     parse_mode='HTML')
    

# В случае указания метода доставки попадаем сюда
@order_creation.callback_query(F.data == 'new_order:delivery')
async def add_address_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(issue_method='Доставка')
    data = await state.get_data()
    issue_place = data['issue_place']
    current_address = ''
    if issue_place:
        current_address = f'Текущий адресс доставки - <b>{issue_place}</b>\n\n'
    
    await callback.message.edit_text(text='❓ <b>ВВЕДИТЕ АДРЕСС ДОСТАВКИ</b>\n\n'
                                            f'{current_address}',
                                        reply_markup=kb.cancel_delivery_address,
                                        parse_mode='HTML')
    await state.set_state(Order.issue_place)

    

# Принимаем адресс доставки и просим указать дату доставки
@order_creation.message(Order.issue_place)
async def issue_place_receiver_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    
    issue_datetime = data['issue_datetime']
    current_date = ''
    if issue_datetime:
        day = issue_datetime['day']
        month = issue_datetime['month']
        year = issue_datetime['year']
        current_date = f'Текущая дата - <b>{day:02d}-{month:02d}-{year}</b>\n\n.'
    
    await state.set_state(None)
    data = await state.get_data()
    issue_place = message.text
    await state.update_data(issue_place=issue_place)
    
    now = represent_utc_3(datetime.now())
    year = now.year
    month = now.month
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text='❓ <b>УКАЖИТЕ ДАТУ ДОСТАВКИ</b>\n\n' \
                                                f'{current_date}' \
                                                'Дату можно ввести вручную в формате: <i>ДД-ММ-ГГГГ</i>',
                                        reply_markup=kb.create_calendar_keyboard(year, month, issue_datetime),
                                        parse_mode='HTML')
    await state.set_state(Order.issue_datetime)



# Предлагаем выбрать дату доставки или выдачи
# добавление новой сессии
@order_creation.callback_query(F.data == 'new_order:self_pickup')
@order_creation.callback_query(F.data.startswith('new_order:delivery:prev:'))
@order_creation.callback_query(F.data.startswith('new_order:delivery:next:'))
@order_creation.callback_query(F.data == 'new_order:delete_address')
@order_creation.callback_query(F.data == 'new_order:delivery_date')
async def new_session_handler(callback: CallbackQuery, state: FSMContext):
    # Если методом выдачи был самовывоз, то АДРЕСС не нужен
    issue_opt = 'ДОСТАВКИ'
    if callback.data == 'new_order:self_pickup':
        await state.update_data(issue_method='Самовывоз', issue_place=None)
        issue_opt = 'ВЫДАЧИ'
    elif callback.data == 'new_order:delete_address':
        await state.update_data(issue_place=None)
        
    data = await state.get_data()
    # Строим текст для текущих данных
    issue_datetime = data['issue_datetime']
    current_date = ''
    if issue_datetime:
        day_cur = issue_datetime['day']
        month_cur = issue_datetime['month']
        year_cur = issue_datetime['year']
        current_date = f'Текущая дата - <b>{day_cur:02d}-{month_cur:02d}-{year_cur}</b>\n\n.'
        
    await state.set_state(None)
    now = represent_utc_3(datetime.now())
    year = now.year
    month = now.month
    # Переключаем месяца вперед и назад
    if callback.data.startswith('new_order:delivery:'):
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
        await callback.message.edit_reply_markup(reply_markup=kb.create_calendar_keyboard(year, month, issue_datetime))
    else:
        await callback.message.edit_text(text=f'❓ <b>УКАЖИТЕ ДАТУ {issue_opt}</b>\n\n' \
                                                f'{current_date}' \
                                                'Дату можно ввести вручную в формате: <i>ДД-ММ-ГГГГ</i>',
                                        reply_markup=kb.create_calendar_keyboard(year, month, issue_datetime),
                                        parse_mode='HTML')
    await state.set_state(Order.issue_datetime)

    
    
# Обработка и сохранение даты при нажатии на кнопку
@order_creation.callback_query(F.data == 'new_order:skip_date')
@order_creation.callback_query(F.data.startswith('new_order:delivery:date:'))
async def issue_datetime_handler(callback: CallbackQuery, state: FSMContext):
    # Определяем слово для правильного отображения
    data = await state.get_data()
    issue_method = data['issue_method']
    issue_opt = 'ДОСТАВКИ'
    if issue_method == 'Самовывоз':
        issue_opt = 'ВЫДАЧИ'
    
    issue_datetime = data['issue_datetime']
    current_time = ''
    if issue_datetime:
        if 'hour' in issue_datetime.keys():
            hour = issue_datetime['hour']
            minute = issue_datetime['minute']
            current_time = f'Текущее время - <b>{hour:02d}:{minute:02d}</b>\n\n.'
        
    if callback.data != 'new_order:skip_date':
        date_comp = [int(_) for _ in callback.data.split(':')[-3:]]
        issue_datetime = {
            'year': date_comp[0],
            'month': date_comp[1],
            'day': date_comp[2]
        }
        await state.update_data(issue_datetime=issue_datetime)
    
    await callback.message.edit_text(text=f'❓⌚️ <b>УКАЖИТЕ ВРЕМЯ {issue_opt}</b>\n\n' \
                                            f'{current_time}' \
                                            'Формат ввода времени: <i>Например 13:30 можно указать как 1330 без символа " : ". '\
                                            'Важно, чтобы перед компонентами времени с одним заком стоял 0 в начале - 08:05 или 0805.</i>',
                                    reply_markup=kb.cancel_delivery_time,
                                    parse_mode='HTML')
    await state.set_state(Order.issue_time)
    

# Указание даты
@order_creation.message(Order.issue_datetime)
async def issue_datetime_receiver_handler(message: Message, state: FSMContext):
    # Определяем слово для правильного отображения
    data = await state.get_data()
    issue_method = data['issue_method']
    issue_opt = 'ДОСТАВКИ'
    if issue_method == 'Самовывоз':
        issue_opt = 'ВЫДАЧИ'
    
    issue_datetime = data['issue_datetime']
    current_date = ''
    if issue_datetime:
        day = issue_datetime['day']
        month = issue_datetime['month']
        year = issue_datetime['year']
        current_date = f'Текущая дата - <b>{day:02d}-{month:02d}-{year}</b>\n\n.'
        if 'hour' in issue_datetime.keys():
            hour = issue_datetime['hour']
            minute = issue_datetime['minute']
            current_time = f'Текущее время - <b>{hour:02d}:{minute:02d}</b>\n\n.'
            
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
        await state.update_data(issue_datetime=issue_datetime)
        await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text=f'❓⌚️ <b>УКАЖИТЕ ВРЕМЯ {issue_opt}</b>\n\n' \
                                                f'{current_time}' \
                                                'Формат ввода времени: <i>Например 13:30 можно указать как 1330 без символа " : ". '\
                                                'Важно, чтобы перед компонентами времени с одним заком стоял 0 в начале - 08:05 или 0805.</i>',
                                            reply_markup=kb.cancel_delivery_time,
                                            parse_mode='HTML')
        await state.set_state(Order.issue_time)
    except:
        try:
            await state.set_state(Order.issue_datetime)
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗ <b>НЕВЕРНО УКАЗАНА ДАТА</b>\n\n' \
                                                    f'❓ <b>УКАЖИТЕ ДАТУ {issue_opt}</b>\n\n' \
                                                    f'{current_date}' \
                                                    'Дату можно ввести вручную в формате:</b>\n<i>ДД-ММ-ГГГГ</i>',
                                                reply_markup=kb.cancel_delivery_time,
                                                parse_mode='HTML')
            return None
        except TelegramBadRequest:
            return None



# Принимаем время доставки заказа
@order_creation.message(Order.issue_time)
async def issue_time_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    # Определяем слово для правильного отображения
    data = await state.get_data()
    issue_method = data['issue_method']
    issue_opt = 'ДОСТАВКИ'
    if issue_method == 'Самовывоз':
        issue_opt = 'ВЫДАЧИ'
    
    issue_datetime = data['issue_datetime']
    current_time = ''
    if 'hour' in issue_datetime.keys():
        hour = data['issue_datetime']['hour']
        minute = data['issue_datetime']['minute']
        current_time = f'Текущее время - <b>{hour:02d}:{minute:02d}</b>\n\n.'
    
    issue_time = message.text.replace(':', '')
    try:
        if len(issue_time) != 4:
            raise(ValueError('Неправильный формат'))
        issue_datetime = data['issue_datetime']
        issue_datetime['hour'] = int(issue_time[:2])
        issue_datetime['minute'] = int(issue_time[-2:])
        datetime(**issue_datetime)
        await state.update_data(issue_datetime=issue_datetime)
    except Exception as e:
        try:
            await state.set_state(Order.issue_time)
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
            
    await state.update_data(issue_datetime=issue_datetime)
    data = await state.get_data()
    text = order_text(data)
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.new_order_keyboard,
                                        parse_mode='HTML')







# # Временно отключено
# # Инициируем добавление дискаунта и предлагаем выбрать продукт которому дать скидку
# @order_creation.callback_query(F.data == 'add_disc_to_order')
# @order_creation.callback_query(F.data.startswith('add_disc_page_'))
# async def add_disc_to_order_handler(callback: CallbackQuery, state: FSMContext):
#     if callback.data.startswith('add_disc_page_'):
#         page = int(callback.data.split('_')[-1])
#     else:
#         page = 1
#     data = await state.get_data()
#     # получаем список словарей с информацией о товаре
#     products = {product:data[product] for product in data.keys() if product.startswith('product_data_')}
#     await callback.message.edit_text(text='<b>Выберите продукт указания скидки</b>',
#                                      reply_markup= await kb.choose_add_disc(products, page=page),
#                                      parse_mode='HTML')
    

# Запрашиваем ввод размера скидки
# @order_creation.callback_query(F.data.startswith('add_disc_item_'))
@order_creation.callback_query(F.data == 'disc_all')
async def add_disc_item_handler(callback: CallbackQuery, state: FSMContext):
    from_callback = callback.data
    await state.update_data(from_callback=from_callback)
    
    # # Пока что отключено, по необходимости и неудобствам в связи с недоработкой
    # if from_callback != 'disc_all':
    #     product_data_id = int(callback.data.split('_')[-1])
    #     current_product = f'product_data_{product_data_id}'
    #     await state.update_data(current_product=current_product)
        
    await callback.message.edit_text(text='<b>Введите размер скидки в процентах от 0 до 100</b>',
                                    reply_markup=kb.back_to_order_changing,
                                    parse_mode='HTML')
    await state.set_state(Product.disc)


# На данный момент работает только на весь заказ
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
        
    # выводим меню нового заказа
    data = await state.get_data()
    text = order_text(data)
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text=text,
                                        reply_markup=kb.new_order_keyboard,
                                        parse_mode='HTML')
    
    

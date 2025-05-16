from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

import app.products_menu.keyboard as kb
from app.states import Product
from app.database.requests import add_product, get_products, get_product, change_product_data

products_menu = Router()


# Раздел товаров
@products_menu.callback_query(F.data == 'products_menu')
async def products_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text='<b>МЕНЮ ТОВАРОВ</b>',
                                     reply_markup=kb.products_menu,
                                     parse_mode='HTML')


# Добавление нового товара
@products_menu.callback_query(F.data == 'add_product')
async def product_add(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Product.name)
    await callback.message.edit_text(text='<b>Введите название товара</b>',
                                     reply_markup=kb.product_cancellation,
                                     parse_mode='HTML')
    await state.update_data(message_id=callback.message.message_id, chat_id=callback.message.chat.id)


# Фиксирование наименования товара
@products_menu.message(Product.name)
async def product_name(message: Message, state: FSMContext):
    await state.update_data(product_name=message.text)
    data = await state.get_data()
    
    # Изменяем состояние для операции добавления е.и.
    await state.set_state(Product.unit) 
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text='<b>Выберите единицы измерения товара</b>',
                                        reply_markup=kb.product_units,
                                        parse_mode='HTML')


# Фиксируем единицу измерения товара и предлагаем ввести стоимость одной единицы
@products_menu.callback_query(F.data.in_(["кг", "шт."]))
async def product_unit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(product_unit=callback.data)
    # Изменяем состояние для операции стоимости товара
    await state.set_state(Product.price)
    await callback.message.edit_text(text=f'<b>Введите стоимость 1 {callback.data} товара {data['product_name']} в рублях ПМР</b>',
                                    reply_markup=kb.product_cancellation,
                                    parse_mode='HTML')


# Фиксирование стоимости единицы товара
@products_menu.message(Product.price)
async def product_price(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        float(message.text)
    except:
        try:
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>❗\n\n' \
                                                    'Формат ввода предполагает использование цифр и одного десятичного разделителя: <i>123.45</i>\n\n' \
                                                    f'<b>Введите стоимость 1 {data['product_unit']} товара {data['product_name']} в рублях ПМР</b>',
                                                reply_markup=kb.product_cancellation,
                                                parse_mode='HTML')
            return None
        except TelegramBadRequest:
            return None
        
    await state.update_data(product_price=message.text)
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                    message_id=data['message_id'],
                                    text='<b>Проверьте данные о товаре, и подтвердите его добавление</b>\n' \
                                    f'{data['product_name']} - стоимостью {message.text} р за 1 {data['product_unit']}',
                                    reply_markup=kb.product_confirmation,
                                    parse_mode='HTML')
    

# добавляем товары в базу данных
@products_menu.callback_query(F.data == 'product_confirmation')
async def product_confirmation(callback: CallbackQuery, state: FSMContext):
    product_data = await state.get_data() 
    await add_product(product_data)
    await callback.answer('Продукт успешно добавлен в базу', show_alert=True)
    await products_menu_handler(callback, state)
    

# Инициируем просмотр товаров
@products_menu.callback_query(F.data == 'list_product')
async def list_product_handler(callback: CallbackQuery):
    products_data = await get_products()
    
    # Создаем текст со списком всех продуктов
    text = '📙<b> СПИСОК ПРОДУКТОВ </b>\n\n'
    for product_data in products_data:
        text += f'- <b>{product_data.product_name}</b> - {product_data.product_price} р/{product_data.product_unit}\n'

    await callback.message.edit_text(text=text,
                                     reply_markup=kb.list_product_menu,
                                     parse_mode='HTML')
    

# Выбираем товар для изменения
@products_menu.callback_query(F.data == 'change_product_data')
@products_menu.callback_query(F.data.startswith('products_menu_product_page_'))
async def choose_product_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('products_menu_product_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        page = 1
        state.update_data(from_callback=callback.data)
    
    products = await get_products()
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ ИЗМЕНЕНИЯ</b> ❓',
                                     reply_markup=kb.choose_product(products, page=page),
                                     parse_mode='HTML')
    

# Предлагаем выбор категории изменения
@products_menu.callback_query(F.data.startswith('products_menu_product_id_'))
@products_menu.callback_query(F.data == 'back_to_change_product_menu')
async def change_product_menu_handler(callback: CallbackQuery, state: FSMContext):
    # достаем данные продукта
    if callback.data.startswith('products_menu_product_id_'):
        product_id = int(callback.data.split('_')[-1])
        await state.update_data(product_id=product_id)

    data = await state.get_data()
    
    # извлекаем данные одного продукта
    product_data = await get_product(product_id=data['product_id'])
    product_name = product_data.product_name
    product_price = float(product_data.product_price)
    product_unit = product_data.product_unit
    message_id = callback.message.message_id
    chat_id = callback.message.chat.id
    
    await state.update_data(product_name=product_name,
                            product_price=product_price,
                            product_unit=product_unit,
                            message_id=message_id,
                            chat_id=chat_id)
    
    await callback.message.edit_text(text='✍️ <b>МЕНЮ ИЗМЕНЕНИЯ ПРОДУКТА</b> 🧀\n\n' \
                                            f'Вы выбрали товар <b>{product_name}</b> стоимостью ' \
                                            f'<b>{product_price} р</b> за 1 <b>{product_unit}</b>',
                                     reply_markup=kb.change_product_menu,
                                     parse_mode='HTML')


# инициируем изменение имени товара
@products_menu.callback_query(F.data == 'change_product_name')
async def change_product_name_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    await callback.message.edit_text(text='❓ <b>ВВЕДИТЕ НОВОЕ НАЗВАНИЕ ТОВАРА</b> ❓\n\n'
                                            f'Текущее название товара <b>{data['product_name']}</b>',
                                     reply_markup=kb.back_to_change_product_menu,
                                     parse_mode='HTML')
    await state.set_state(Product.change_name)
    

# сохраняем обновленные данные продукта в базу данных и выводим меню изменения продукта
@products_menu.message(Product.change_name)
async def save_product_name_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    
    product_id = data['product_id']
    state_name = (await state.get_state()).split(':')[-1]
    if state_name == 'change_name':
        product_data = {'product_name': message.text}
    elif state_name == 'change_price':
        product_data = {'product_price': message.text}
    
    await change_product_data(product_id, product_data)

    # извлекаем данные одного продукта
    product_data = await get_product(product_id=data['product_id'])
    product_name = product_data.product_name
    product_price = float(product_data.product_price)
    product_unit = product_data.product_unit
    
    await state.update_data(product_name=product_name,
                            product_price=product_price,
                            product_unit=product_unit)
    
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text='✍️ <b>МЕНЮ ИЗМЕНЕНИЯ ПРОДУКТА</b> 🧀\n\n' \
                                            f'Вы выбрали товар <b>{product_name}</b> стоимостью ' \
                                            f'<b>{product_price} р</b> за 1 <b>{product_unit}</b>',
                                        reply_markup=kb.change_product_menu,
                                        parse_mode='HTML')
    


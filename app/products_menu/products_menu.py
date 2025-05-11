from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

import app.products_menu.keyboard as kb
from app.states import Product
from app.database.requests import add_product

products_menu = Router()

# Раздел товаров
@products_menu.callback_query(F.data == 'products')
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
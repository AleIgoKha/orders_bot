from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from decimal import Decimal

import app.main_menu.outlets_menu.outlet_menu.stock_menu.keyboard as kb
from app.states import Stock
from app.database.requests import get_product
from app.database.all_requests.stock import get_stock_product, get_active_stock_products, add_stock, get_out_stock_products
from app.database.all_requests.transactions import transaction_writeoff, transaction_replenish, transaction_delete_product
from app.database.all_requests.outlet import get_outlet


stock_menu = Router()


# функция для формирования сообщения о пополнении товара
async def replenishment_text(outlet_id, product_id, added_pieces):
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data['outlet_name']
    
    # достаем данные о запасах конкретного продукта
    stock_product_data = await get_stock_product(outlet_id, product_id)
    product_unit = stock_product_data['product_unit']
    stock_qty = stock_product_data['stock_qty']
    # stock_id = stock_product_data['stock_id']
    product_name = stock_product_data['product_name']
    
    product_unit_amend = product_unit
    if product_unit == 'кг':
        product_unit_amend = 'граммах'
    else:
        product_unit_amend = 'штуках'
        stock_qty = round(stock_qty)
        
    # # последняя транзакция с товаром
    # last_transaction_data = await get_last_transaction(outlet_id=outlet_id,
    #                                                    stock_id=stock_id,
    #                                                    transaction_type='replenishment')
    # last_transaction_text = ''
    # if last_transaction_data:
    #     transaction_datetime = represent_utc_3(last_transaction_data['transaction_datetime']).strftime('в %H:%M %d-%m-%Y')
    #     transaction_product_qty = last_transaction_data['product_qty']
        
    #     if product_unit != 'кг':
    #         transaction_product_qty = round(transaction_product_qty)
            
    #     last_transaction_text = f'Последнее пополнение товара - <b>➕{transaction_product_qty} {product_unit} ({transaction_datetime})</b>\n'
        
    # корректируем единици измерения и зависимости от них
    product_unit_amend = product_unit
    if product_unit == 'кг':
        product_unit_amend = 'граммах'
        product_unit_pieces = 'г'
    else:
        product_unit_amend = 'штуках'
        product_unit_pieces = 'шт.'
        stock_qty = int(stock_qty)
        
    # формируем список кусков
    added_pieces_text = ''
    if len(added_pieces) != 0:
        added_pieces_text = '\nНа данный момент добавлены части товара размером:\n'
        for added_piece in added_pieces:
            added_pieces_text += f'<b>{added_piece} {product_unit_pieces}</b>\n'
        added_pieces_text += f'Итого к пополнению - <b>{sum(added_pieces)} {product_unit_pieces}</b>\n'
        
    text = '❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА</b>\n\n' \
            f'Вы пытаетесь пополнить запасы товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
            f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
            f'{added_pieces_text}' \
            f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>\n\n'
    
    return text, str(stock_qty), product_unit


# функция для формирования сообщения о списании товара
async def writeoff_text(outlet_id, product_id, added_pieces):
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data['outlet_name']
    
    # достаем данные о запасах конкретного продукта
    stock_product_data = await get_stock_product(outlet_id, product_id)
    product_unit = stock_product_data['product_unit']
    stock_qty = stock_product_data['stock_qty']
    product_name = stock_product_data['product_name']
    
    # корректируем единици измерения и зависимости от них
    product_unit_amend = product_unit
    if product_unit == 'кг':
        product_unit_amend = 'граммах'
        product_unit_pieces = 'г'
    else:
        product_unit_amend = 'штуках'
        product_unit_pieces = 'шт.'
        stock_qty = int(stock_qty)
        
    # формируем список кусков
    added_pieces_text = ''
    if len(added_pieces) != 0:
        added_pieces_text = '\nНа данный момент добавлены части товара размером:\n'
        for added_piece in added_pieces:
            added_pieces_text += f'<b>{added_piece} {product_unit_pieces}</b>\n'
        added_pieces_text += f'Итого к пополнению - <b>{sum(added_pieces)} {product_unit_pieces}</b>\n'
        
    text = '❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА ДЛЯ СПИСАНИЯ</b>\n\n' \
            f'Вы пытаетесь списать часть запасов товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
            f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
            f'{added_pieces_text}' \
            f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>. ' \
            'Для удаления товара введите <i>УДАЛИТЬ</i>.\n\n'
    
    return text, str(stock_qty), product_unit


# функция для формирования сообщения меню запасов
def stock_list_text(stock_products_data):
    text = '📦 <b>УПРАВЛЕНИЕ ЗАПАСАМИ</b>\n\n'
    
    for stock_product_data in stock_products_data:
        product_name = stock_product_data['product_name']
        stock_qty = stock_product_data['stock_qty']
        product_unit = stock_product_data['product_unit']
        
        if product_unit != 'кг':
            stock_qty = round(stock_qty)
        
        text += f'{product_name} - <b>{stock_qty} {product_unit}</b>\n'
    
    return text

# меню операций тороговой точки
@stock_menu.callback_query(F.data == 'outlet:stock')
async def stock_menu_handler(callback: CallbackQuery, state: FSMContext):
    
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    
    stock_products_data = await get_active_stock_products(outlet_id) 
    
    text = stock_list_text(stock_products_data)
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.stock_menu,
                                     parse_mode='HTML')


# операция пополнения запасов на складе
@stock_menu.callback_query(F.data.startswith('outlet:replenishment:page_'))
@stock_menu.callback_query(F.data == 'outlet:replenishment')
async def choose_product_replenishment_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await state.update_data(added_pieces=[])
    
    if callback.data.startswith('outlet:replenishment:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1
    
    data = await state.get_data()
    outlet_id = data['outlet_id']
    stock_data = await get_active_stock_products(outlet_id)
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ ПОПОЛНЕНИЯ ЗАПАСОВ</b>',
                                     reply_markup=kb.choose_product_replenishment(stock_data=stock_data, page=page),
                                     parse_mode='HTML')
    
    
# операция добавления новых продуктов на склад
@stock_menu.callback_query(F.data.startswith('outlet:replenishment:add_product:page_'))
@stock_menu.callback_query(F.data == 'outlet:replenishment:add_product')
async def choose_add_product_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('outlet:replenishment:add_product:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1
        
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    
    products_data = await get_out_stock_products(outlet_id)
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ ДОБАВЛЕНИЯ В ЗАПАСЫ</b>',
                                     reply_markup=kb.choose_product_add(products=products_data, page=page),
                                     parse_mode='HTML')
    

# Подтверждение добавления продукта в запасы
@stock_menu.callback_query(F.data.startswith('outlet:replenishment:add_product:product_id_'))
async def add_product_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data['outlet_name']
    
    if callback.data.startswith('outlet:replenishment:add_product:product_id_'):
        product_id = int(callback.data.split('_')[-1])        
        product_data = await get_product(product_id)
        product_name = product_data.product_name
        await state.update_data(product_id=product_id)
    
    await callback.message.edit_text(text='❓ <b>ПОДТВЕРДИТЕ ДОБАВЛЕНИЕ ТОВАРА В ЗАПАСЫ</b>\n\n' \
                                        f'Вы пытаетесь добавить в запасы торговой точки <b>{outlet_name}</b> товар <b>{product_name}.\n\n</b>' \
                                        'Если все правильно, нажмите <b>Подтвердить</b>, в противном случае нажмите <b>Отмена</b>',
                                        reply_markup=kb.add_product,
                                        parse_mode='HTML')
    

# добавление продукта в запасы
@stock_menu.callback_query(F.data == 'outlet:replenishment:add_product:confirm')
async def confirm_add_product_handler(callback: CallbackQuery, state: FSMContext):
    
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    try:
        await add_stock(outlet_id, product_id)
        await callback.answer(text='Продукт успешно добавлен в запасы')
        await choose_add_product_handler(callback, state)
    except:
        await callback.answer(text='Невозможно создать транзакцию')


# Пополнение запасов продукта
@stock_menu.callback_query(F.data.startswith('outlet:replenishment:product_id_'))
async def product_replenishment_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    # сохранение данных товара если пришли по колбэку
    if callback.data.startswith('outlet:replenishment:product_id_'):
        product_id = int(callback.data.split('_')[-1])
        await state.update_data(product_id=product_id)
    # если пришли по вызову функции
    else:
        product_id = data['product_id']
    
    outlet_id = data['outlet_id']
    added_pieces = data['added_pieces']
    
    text, stock_qty, product_unit = await replenishment_text(outlet_id, product_id, added_pieces)
    await state.update_data(stock_qty=stock_qty, product_unit=product_unit)
    
    await callback.message.edit_text(text=text,
                                        reply_markup=kb.replenish_product(added_pieces),
                                        parse_mode='HTML')
    
    await state.set_state(Stock.replenishment)


# принимаем количество товара на пополнение
@stock_menu.message(Stock.replenishment)
async def product_replenishment_receiver_handler(message: Message, state: FSMContext):
    
    await state.set_state(None)
    
    data = await state.get_data()
    
    product_id = data['product_id']
    chat_id = data['chat_id']
    message_id = data['message_id']
    outlet_id = data['outlet_id']
    product_unit = data['product_unit']
    added_pieces = data['added_pieces']

    text = (await replenishment_text(outlet_id, product_id, added_pieces))[0]
    
    # Проверяем на формат
    try:
        product_qty = Decimal(message.text.replace(',', '.'))
        
        if product_qty <= 0:
            try:
                await state.set_state(Stock.replenishment)
                warning_text = '❗<b>КОЛИЧЕСТВО НЕ МОЖЕТ БЫТЬ МЕНЬШЕ ИЛИ РАВНО НУЛЮ</b>\n\n'
                text = warning_text + text
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text=text,
                                                    parse_mode='HTML',
                                                    reply_markup=kb.replenish_product(added_pieces))
                return None
            except TelegramBadRequest:
                return None
    except:
        try:
            await state.set_state(Stock.replenishment)
            warning_text = '❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>\n\n'
            text = warning_text + text
            await message.bot.edit_message_text(chat_id=chat_id,
                                                message_id=message_id,
                                                text=text,
                                                parse_mode='HTML',
                                                reply_markup=kb.replenish_product(added_pieces))
            return None
        except TelegramBadRequest:
            return None
    
    # добавляем новый кусочек в список кусков
    added_pieces.append(int(product_qty))
    await state.update_data(added_pieces=added_pieces)
    
    text, stock_qty, product_unit = await replenishment_text(outlet_id, product_id, added_pieces)
    await state.update_data(stock_qty=stock_qty, product_unit=product_unit)
    
    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text=text,
                                        reply_markup=kb.replenish_product(added_pieces),
                                        parse_mode='HTML')
    
    await state.set_state(Stock.replenishment)


# даем выбор куска для его изменения
@stock_menu.callback_query(F.data.startswith('outlet:replenishment:correct_piece:piece_id_'))
@stock_menu.callback_query(F.data.startswith('outlet:replenishment:correct_piece:page_'))
@stock_menu.callback_query(F.data == 'outlet:replenishment:correct_piece')
async def choose_balance_replenishment_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    # удаляем из списка кусков
    if callback.data.startswith('outlet:replenishment:correct_piece:piece_id_'):
        piece_id = int(callback.data.split('_')[-1])
        data = await state.get_data()
        added_pieces = data['added_pieces']
        del added_pieces[piece_id]
        await state.update_data(added_pieces=added_pieces)
        
    data = await state.get_data()
    added_pieces = data['added_pieces']
    product_id = data['product_id']
    
    if callback.data.startswith('outlet:replenishment:correct_piece:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1

    if len(added_pieces) != 0:
        await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ КУСОК ТОВАРА ДЛЯ УДАЛЕНИЯ</b>',
                                        reply_markup=kb.choose_replenishment_product_correct_piece(product_id=product_id,
                                                                                                    added_pieces=added_pieces,
                                                                                                    page=page),
                                        parse_mode='HTML')
    else:
        await product_replenishment_handler(callback, state)

    
# просим подтверждения пополнения
@stock_menu.callback_query(F.data == 'outlet:replenishment:calculate')
async def calculate_replenishment_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    product_qty = sum(data['added_pieces'])
    product_unit = data['product_unit']
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    stock_data = await get_stock_product(outlet_id, product_id)
    product_name = stock_data['product_name']
    
    if product_unit == 'кг':
        product_unit = product_unit[-1]
    
    await callback.message.edit_text(text=f'Будет выполнено пополнение товара <b>{product_name}</b> на <b>{product_qty} {product_unit}</b>',
                                        reply_markup=kb.confirm_replenishment_product(product_id),
                                        parse_mode='HTML')

        
# создаем транзакцию для пополнения запаса
@stock_menu.callback_query(F.data == 'outlet:replenishment:confirm')
async def confirm_replenishment_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    product_qty = Decimal(sum(data['added_pieces']))
    product_unit = data['product_unit']

    if product_unit == 'кг':
        product_qty = product_qty / Decimal(1000)

    try:
        # создаем транзакцию для пополнения запасов товара и обновляем его количество
        await transaction_replenish(outlet_id, product_id, product_qty)
        await callback.answer(text='Запасы продукта успешно пополнены')
        await choose_product_replenishment_handler(callback, state)
    except:
        await callback.answer(text='Невозможно создать транзакцию', show_alert=True)
    
    # переходив в меню пополнения


# меню отмены расчета баланса
@stock_menu.callback_query(F.data == 'outlet:replenishment:cancel')
async def cancel_balance_product_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    product_id = data['product_id']
    
    await callback.message.edit_text(text='❗️ <b>Вы пытаетесь выйти из операции пополнения товара. '\
                                            'Несохраненные данные будут утеряны.</b>',
                                            parse_mode='HTML',
                                            reply_markup=kb.cancel_replenishment_product(product_id))


# инициируем списание товара
@stock_menu.callback_query(F.data == 'outlet:writeoff')
@stock_menu.callback_query(F.data.startswith('outlet:writeoff:page_'))
async def choose_product_writeoff_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await state.update_data(added_pieces=[])
    
    if callback.data.startswith('outlet:writeoff:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1
    
    data = await state.get_data()
    outlet_id = data['outlet_id']
    stock_data = await get_active_stock_products(outlet_id)
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ СПИСАНИЯ</b>',
                                     reply_markup=kb.choose_product_writeoff(stock_data=stock_data, page=page),
                                     parse_mode='HTML')
    
    
# запрашиваем количество товара для списания
@stock_menu.callback_query(F.data.startswith('outlet:writeoff:product_id_'))
async def product_writeoff_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    # сохранение данных товара если пришли по колбэку
    if callback.data.startswith('outlet:writeoff:product_id_'):
        product_id = int(callback.data.split('_')[-1])
        await state.update_data(product_id=product_id)
    # если пришли по вызову функции
    else:
        product_id = data['product_id']
    
    outlet_id = data['outlet_id']
    added_pieces = data['added_pieces']
    
    text, stock_qty, product_unit = await writeoff_text(outlet_id, product_id, added_pieces)
    await state.update_data(stock_qty=stock_qty, product_unit=product_unit)

    await callback.message.edit_text(text=text,
                                    reply_markup=kb.writeoff_product(added_pieces),
                                    parse_mode='HTML')
    
    await state.set_state(Stock.writeoff)


# принимаем количество товара на списание
@stock_menu.message(Stock.writeoff)
async def product_writeoff_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    chat_id = data['chat_id']
    message_id = data['message_id']
    stock_qty = Decimal(data['stock_qty'])
    product_unit = data['product_unit']
    added_pieces = data['added_pieces']
    
    if product_unit == 'кг':
        stock_qty = stock_qty * Decimal(1000)
    
    stock_data = await get_stock_product(outlet_id, product_id)
    product_name = stock_data['product_name']
    
    text = (await writeoff_text(outlet_id, product_id, added_pieces))[0]
    
    if message.text.lower().strip() == 'удалить':
        # создаем транзакцию по списанию всех запасов товара и его удаления из торговой точки
        if product_unit == 'кг':
            product_unit = product_unit[-1]
        outlet_data = await get_outlet(outlet_id)
        outlet_name = outlet_data['outlet_name']
        await message.bot.edit_message_text(chat_id=chat_id,
                                    message_id=message_id,
                                    text=f'Будет выполнено списание товара <b>{product_name}</b> на <b>{int(stock_qty)} {product_unit}</b>'\
                                        f' с последующим его удалением из торговой точки <b>{outlet_name}</b>',
                                    reply_markup=kb.confirm_delete,
                                    parse_mode='HTML')
    # если не удаляем, то списываем
    else:
        # Проверяем на формат введенного количества товара
        try:
            product_qty = Decimal(message.text.replace(',', '.'))
            
            total_qty = product_qty + Decimal(sum(added_pieces))
            
            if product_qty <= 0:
                try:
                    await state.set_state(Stock.writeoff)
                    warning_text = '❗<b>КОЛИЧЕСТВО НЕ МОЖЕТ БЫТЬ МЕНЬШЕ ИЛИ РАВНО НУЛЮ</b>\n\n'
                    text = warning_text + text
                    await message.bot.edit_message_text(chat_id=chat_id,
                                                        message_id=message_id,
                                                        text=text,
                                                        parse_mode='HTML',
                                                        reply_markup=kb.writeoff_product(added_pieces))
                    return None
                except TelegramBadRequest:
                    return None
            elif stock_qty - total_qty < 0:
                try:
                    await state.set_state(Stock.writeoff)
                    warning_text = '❗<b>КОЛИЧЕСТВО ДЛЯ СПИСАНИЯ НЕ МОЖЕТ БЫТЬ БОЛЬШЕ ЗАПАСА</b>\n\n'
                    text = warning_text + text
                    await message.bot.edit_message_text(chat_id=chat_id,
                                                        message_id=message_id,
                                                        text=text,
                                                        parse_mode='HTML',
                                                        reply_markup=kb.writeoff_product(added_pieces))
                    return None
                except TelegramBadRequest:
                    return None
        except:
            try:
                await state.set_state(Stock.writeoff)
                warning_text = '❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>\n\n'
                text = warning_text + text
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text=text,
                                                    parse_mode='HTML',
                                                    reply_markup=kb.writeoff_product(added_pieces))
                return None
            except TelegramBadRequest:
                return None

        # добавляем новый кусочек в список кусков
        added_pieces.append(int(product_qty))
        await state.update_data(added_pieces=added_pieces)
        
        text, stock_qty, product_unit = await writeoff_text(outlet_id, product_id, added_pieces)
        await state.update_data(stock_qty=stock_qty, product_unit=product_unit)
        
        await message.bot.edit_message_text(chat_id=chat_id,
                                            message_id=message_id,
                                            text=text,
                                            reply_markup=kb.writeoff_product(added_pieces),
                                            parse_mode='HTML')
        
        await state.set_state(Stock.writeoff)


# даем выбор куска для его изменения в списании
@stock_menu.callback_query(F.data.startswith('outlet:writeoff:correct_piece:piece_id_'))
@stock_menu.callback_query(F.data.startswith('outlet:writeoff:correct_piece:page_'))
@stock_menu.callback_query(F.data == 'outlet:writeoff:correct_piece')
async def correct_piece_writeoff_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    # удаляем из списка кусков
    if callback.data.startswith('outlet:writeoff:correct_piece:piece_id_'):
        piece_id = int(callback.data.split('_')[-1])
        data = await state.get_data()
        added_pieces = data['added_pieces']
        del added_pieces[piece_id]
        await state.update_data(added_pieces=added_pieces)
        
    data = await state.get_data()
    added_pieces = data['added_pieces']
    product_id = data['product_id']
    
    if callback.data.startswith('outlet:writeoff:correct_piece:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1

    if len(added_pieces) != 0:
        await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ КУСОК ТОВАРА ДЛЯ УДАЛЕНИЯ</b>',
                                        reply_markup=kb.choose_writeoff_product_correct_piece(product_id=product_id,
                                                                                                    added_pieces=added_pieces,
                                                                                                    page=page),
                                        parse_mode='HTML')
    else:
        await product_writeoff_handler(callback, state)

    
# просим подтверждения списания
@stock_menu.callback_query(F.data == 'outlet:writeoff:calculate')
async def calculate_replenishment_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    product_qty = sum(data['added_pieces'])
    product_unit = data['product_unit']
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    stock_data = await get_stock_product(outlet_id, product_id)
    product_name = stock_data['product_name']
    
    if product_unit == 'кг':
        product_unit = product_unit[-1]
    
    await callback.message.edit_text(text=f'Будет выполнено списание товара <b>{product_name}</b> на <b>{product_qty} {product_unit}</b>',
                                        reply_markup=kb.confirm_writeoff_product(product_id),
                                        parse_mode='HTML')


# подтверждение списания запасов товара
@stock_menu.callback_query(F.data == 'outlet:writeoff:confirm')
async def confirm_writeoff_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    product_qty = Decimal(sum(data['added_pieces']))
    product_unit = data['product_unit']

    if product_unit == 'кг':
        product_qty = product_qty / Decimal(1000)

    try:
        # создаем транзакцию для пополнения запасов товара и обновляем его количество
        await transaction_writeoff(outlet_id, product_id, product_qty)
        await callback.answer(text='Запасы продукта успешно списаны')
        await choose_product_writeoff_handler(callback, state)
    except:
        await callback.answer(text='Невозможно создать транзакцию', show_alert=True)


# меню отмены расчета баланса
@stock_menu.callback_query(F.data == 'outlet:writeoff:cancel')
async def cancel_writeoff_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    product_id = data['product_id']
    
    await callback.message.edit_text(text='❗️ <b>Вы пытаетесь выйти из операции списания товара. '\
                                            'Несохраненные данные будут утеряны.</b>',
                                            parse_mode='HTML',
                                            reply_markup=kb.cancel_writeoff_product(product_id))


# подтверждение удаления товара из запасов
@stock_menu.callback_query(F.data == 'outlet:stock:delete:confirm')
async def confirm_stock_delete_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_id = data['outlet_id']
    product_id = data['product_id']

    try:
        # создаем транзакцию для пополнения запасов товара и обновляем его количество
        await transaction_delete_product(outlet_id, product_id)
        await callback.answer(text='Продукт успешно удален из запасов торговой точки')
        await choose_product_writeoff_handler(callback, state)
    except:
        await callback.answer(text='Невозможно создать транзакцию', show_alert=True)

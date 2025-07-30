import pytz
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from decimal import Decimal
from datetime import datetime, date


import app.main_menu.outlets_menu.outlet_menu.stock_menu.keyboard as kb
from app.states import Stock
from app.database.requests import get_product
from app.database.all_requests.stock import get_stock_product, get_active_stock_products, add_stock, get_out_stock_products
from app.database.all_requests.transactions import (transaction_writeoff,
                                                    transaction_replenish,
                                                    transaction_delete_product,
                                                    transactions_info,
                                                    transaction_info,
                                                    get_last_transaction,
                                                    rollback_selling,
                                                    rollback_writeoff,
                                                    rollback_replenishment)
from app.database.all_requests.outlet import get_outlet
from app.com_func import represent_utc_3, localize_user_input
from app.states import Transaction


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
        added_pieces_text = '\nДобавлены части:\n'
        for added_piece in added_pieces:
            added_pieces_text += f'<b>{added_piece} {product_unit_pieces}</b>\n'
        added_pieces_text += f'Итого к пополнению - <b>{sum(added_pieces)} {product_unit_pieces}</b>\n'
    else:
        added_pieces_text = f'\nВведите количество продукта в <b>{product_unit_amend}</b>. Количество продукта можно вводить частами или сразу суммарное.\n'
        
    text = '➕ <b>ПОПОЛНЕНИЕ</b>\n\n' \
            f'Вы пытаетесь пополнить запасы товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
            f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
            f'{added_pieces_text}' \
            # '\nПо окончании добавления всех частей товара нажмите <b>Расчитать</b> в противном случае нажмите <b>Отмена</b>.'
    
    return text


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
        available = stock_qty * 1000
    else:
        product_unit_amend = 'штуках'
        product_unit_pieces = 'шт.'
        stock_qty = int(stock_qty)
        available = stock_qty
        
    # формируем список кусков
    if len(added_pieces) != 0:
        added_pieces_text = '\nДобавлены части:\n'
        for added_piece in added_pieces:
            added_pieces_text += f'<b>{added_piece} {product_unit_pieces}</b>\n'
        added_pieces_text += f'Итого к списанию - <b>{sum(added_pieces)} {product_unit_pieces}</b> (доступно <b>{int(available - sum(added_pieces))})</b>\n'
    else:
        added_pieces_text = f'\nВведите количество продукта в <b>{product_unit_amend}</b>. Количество продукта можно вводить частами или сразу суммарное.\n'
        
        
    text = '➖ <b>СПИСАНИЕ</b>\n\n' \
            f'Вы пытаетесь списать часть запасов товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
            f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
            f'{added_pieces_text}' \
            # f'\nПо окончании добавления всех частей товара нажмите <b>Расчитать</b> в противном случае нажмите <b>Отмена</b>.'
    
    return text


# функция для формирования сообщения меню запасов
async def stock_list_text(stock_products_data):
    text = '📦 <b>ЗАПАСЫ</b>\n'
    
    for stock_product_data in stock_products_data:
        stock_id = stock_product_data['stock_id']
        product_name = stock_product_data['product_name']
        stock_qty = stock_product_data['stock_qty']
        product_unit = stock_product_data['product_unit']
        outlet_id = stock_product_data['outlet_id']
        
        last_transaction = await get_last_transaction(outlet_id, stock_id)
        
        transaction_type = last_transaction['transaction_type']
        transaction_info = last_transaction['transaction_info']
        
        if product_unit != 'кг':
            stock_qty = round(stock_qty)
        
        parts_text = ''
        if transaction_type == 'balance':
            transaction_info = [f'{round(part * 1000 if product_unit == 'кг' else part)}' for part in transaction_info]
            parts_text = f' ({', '.join(transaction_info)})'
        
        text += f'\n🧀 {product_name} - <b>{stock_qty} {product_unit}{parts_text}</b>\n'

    text += '<i>\n* - Части товара видно только после фиксации остатков в граммах или штуках</i>'
    
    return text

# меню операций тороговой точки
@stock_menu.callback_query(F.data == 'outlet:stock')
async def stock_menu_handler(callback: CallbackQuery, state: FSMContext):
    
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    
    stock_products_data = await get_active_stock_products(outlet_id)
    
    text = await stock_list_text(stock_products_data)
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.stock_menu,
                                     parse_mode='HTML')


# выбор продукта для выполнения операции над ним
@stock_menu.callback_query(F.data.startswith('outlet:control:page_'))
@stock_menu.callback_query(F.data == 'outlet:control')
@stock_menu.callback_query(F.data == 'outlet:control:back')
async def choose_product_control_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    
    if callback.data.startswith('outlet:control:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    elif callback.data == 'outlet:control':
        page = 1
    else:
        # обновляем данные контекста, избавляемся от лишнего
        data = {
            'outlet_id': data['outlet_id'],
            'outlet_name': data['outlet_name'],
            'outlet_descr': data['outlet_descr'],
            'outlet_arch': data['outlet_arch'],
            'message_id': data['message_id'],
            'chat_id': data['chat_id'],
            'page': data['page'],
            }
        await state.clear()
        await state.update_data(data)
        data = await state.get_data()
        # Сохраняем страницу (лучше это не убирать отсюда)
        page = data['page']
        
    # сохраняем страницу для удобства при возвращении
    await state.update_data(page=page)
    
    outlet_id = data['outlet_id']
    stock_data = await get_active_stock_products(outlet_id)
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ УПРАВЛЕНИЯ</b>',
                                     reply_markup=await kb.choose_product_outlet(stock_data=stock_data, page=page),
                                     parse_mode='HTML')


# операция добавления новых продуктов на склад
@stock_menu.callback_query(F.data.startswith('outlet:control:add_product:page_'))
@stock_menu.callback_query(F.data == 'outlet:control:add_product')
async def choose_add_product_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('outlet:control:add_product:page_'):
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
@stock_menu.callback_query(F.data.startswith('outlet:control:add_product:product_id_'))
async def add_product_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data['outlet_name']
    
    if callback.data.startswith('outlet:control:add_product:product_id_'):
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
@stock_menu.callback_query(F.data == 'outlet:control:add_product:confirm')
async def confirm_add_product_handler(callback: CallbackQuery, state: FSMContext):
    
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    try:
        await add_stock(outlet_id, product_id)
        await callback.answer(text='Продукт успешно добавлен в запасы', show_alert=True)
        await choose_add_product_handler(callback, state)
    except:
        await callback.answer(text='Невозможно создать транзакцию', show_alert=True)

# меню управления товаром
@stock_menu.callback_query(F.data.startswith('outlet:control:product_id_'))
async def product_control_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    
    # Если пришли по вызову функции
    if callback.data.startswith('outlet:control:product_id_'):
        product_id = int(callback.data.split('_')[-1])    
    else:
        product_id = data['product_id']   
    
    outlet_id = data['outlet_id']
    
    # достаем данные о торговой точке
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data['outlet_name']

    # достаем данные о запасах конкретного продукта
    stock_product_data = await get_stock_product(outlet_id, product_id)
    product_unit = stock_product_data['product_unit']
    stock_qty = stock_product_data['stock_qty']
    stock_id = stock_product_data['stock_id']
    product_name = stock_product_data['product_name']

    await state.update_data(stock_qty=str(stock_qty),
                            product_unit=product_unit,
                            product_id=product_id,
                            stock_id=stock_id,
                            product_name=product_name,
                            added_pieces=[], 
                            transaction_datetime=None,
                            from_callback=None)
    
    if product_unit == 'шт.':
        stock_qty = int(stock_qty)

    text = '⚙️ <b>МЕНЮ УПРАВЛЕНИЯ ТОВАРОМ</b>\n\n' \
            f'Название товара - <b>{product_name}</b>\n' \
            f'Текущая торговая точка - <b>{outlet_name}</b>\n' \
            f'Запас товара - <b>{stock_qty} {product_unit}</b>\n\n' \
            f'Выберите операцию управления товаром.'
    

    await callback.message.edit_text(text=text,
                                        reply_markup=kb.product_control_menu,
                                        parse_mode='HTML')


# Пополнение запасов продукта
@stock_menu.callback_query(F.data == 'outlet:replenishment')
async def product_replenishment_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    # проверяем если пришли от вызова функции
    if callback.data == 'outlet:replenishment':
        operation = callback.data.split(':')[-1]
        await state.update_data(operation=operation)
    else:
        operation = data['operation']
    
    product_id = data['product_id']
    outlet_id = data['outlet_id']
    added_pieces = data['added_pieces']
    from_callback = data['from_callback']
    
    text = await replenishment_text(outlet_id, product_id, added_pieces)
    
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.change_stock_qty_menu(operation, added_pieces, product_id, from_callback),
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
    added_pieces = data['added_pieces']
    operation = data['operation']
    from_callback = data['from_callback']

    text = await replenishment_text(outlet_id, product_id, added_pieces)
    
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
                                                    reply_markup=kb.change_stock_qty_menu(operation, added_pieces, product_id, from_callback))
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
                                                reply_markup=kb.change_stock_qty_menu(operation, added_pieces, product_id, from_callback))
            return None
        except TelegramBadRequest:
            return None
    
    # добавляем новый кусочек в список кусков
    added_pieces.append(int(product_qty))
    await state.update_data(added_pieces=added_pieces)
    
    text = await replenishment_text(outlet_id, product_id, added_pieces)
    
    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text=text,
                                        reply_markup=kb.change_stock_qty_menu(operation, added_pieces, product_id, from_callback),
                                        parse_mode='HTML')
    
    await state.set_state(Stock.replenishment)

    
# просим подтверждения пополнения
@stock_menu.callback_query(F.data == 'outlet:replenishment:calculate')
async def calculate_replenishment_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    product_qty = sum(data['added_pieces'])
    product_unit = data['product_unit']
    product_name = data['product_name']
    
    if product_unit == 'кг':
        product_unit = product_unit[-1]
    
    await callback.message.edit_text(text=f'Будет выполнено пополнение товара <b>{product_name}</b> на <b>{product_qty} {product_unit}</b>',
                                        reply_markup=kb.confirm_replenishment_product,
                                        parse_mode='HTML')

        
# создаем транзакцию для пополнения запаса
@stock_menu.callback_query(F.data == 'outlet:replenishment:confirm')
async def confirm_replenishment_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    added_pieces = [Decimal(added_piece) for added_piece in data['added_pieces']]
    product_qty = sum(added_pieces)
    product_unit = data['product_unit']
    transaction_datetime = data['transaction_datetime']
    from_callback = data['from_callback']
    
    if transaction_datetime:
        transaction_datetime = localize_user_input(datetime(**data['transaction_datetime']))

    if product_unit == 'кг':
        product_qty = product_qty / Decimal(1000)
        added_pieces = [added_piece / Decimal(1000) for added_piece in added_pieces]

    try:
        # создаем транзакцию для пополнения запасов товара и обновляем его количество
        await transaction_replenish(outlet_id, product_id, product_qty, added_pieces, transaction_datetime)
        await callback.answer(text='Запасы продукта успешно пополнены', show_alert=True)
        if from_callback is None:
            await choose_product_control_handler(callback, state)
        elif from_callback == 'outlet:control:transactions':
            await choose_transaction_product_handler(callback, state)
    except:
        await callback.answer(text='Невозможно создать транзакцию', show_alert=True)
        
    await state.update_data(transaction_datetime=None)


# меню отмены расчета баланса
@stock_menu.callback_query(F.data == 'outlet:replenishment:cancel')
async def cancel_replenishment_product_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    product_id = data['product_id']
    from_callback = data['from_callback']
    
    await callback.message.edit_text(text='❗️ <b>Вы пытаетесь выйти из операции пополнения товара. '\
                                            'Несохраненные данные будут утеряны.</b>',
                                            parse_mode='HTML',
                                            reply_markup=kb.cancel_replenishment_product(product_id, from_callback))
    
    
# запрашиваем количество товара для списания
@stock_menu.callback_query(F.data == 'outlet:writeoff')
async def product_writeoff_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    # проверяем если пришли от вызова функции
    if callback.data == 'outlet:writeoff':
        operation = callback.data.split(':')[-1]
        await state.update_data(operation=operation)
    else:
        operation = data['operation']
    
    product_id = data['product_id']
    outlet_id = data['outlet_id']
    added_pieces = data['added_pieces']
    stock_qty = Decimal(data['stock_qty'])
    from_callback = data['from_callback']
    
    if stock_qty == Decimal(0):
        await callback.answer(text='У товара нет запасов', show_alert=True)
        return None
    
    text = await writeoff_text(outlet_id, product_id, added_pieces)
    
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.change_stock_qty_menu(operation, added_pieces, product_id, from_callback),
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
    operation = data['operation']
    from_callback = data['from_callback']
    
    if product_unit == 'кг':
        stock_qty = stock_qty * Decimal(1000)
    
    text = await writeoff_text(outlet_id, product_id, added_pieces)
    
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
                                                    reply_markup=kb.change_stock_qty_menu(operation, added_pieces, product_id, from_callback))
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
                                                    reply_markup=kb.change_stock_qty_menu(operation, added_pieces, product_id, from_callback))
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
                                                reply_markup=kb.change_stock_qty_menu(operation, added_pieces, product_id, from_callback))
            return None
        except TelegramBadRequest:
            return None

    # добавляем новый кусочек в список кусков
    added_pieces.append(int(product_qty))
    await state.update_data(added_pieces=added_pieces)
    
    text = await writeoff_text(outlet_id, product_id, added_pieces)
    
    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text=text,
                                        reply_markup=kb.change_stock_qty_menu(operation, added_pieces, product_id, from_callback),
                                        parse_mode='HTML')
    
    await state.set_state(Stock.writeoff)


# даем выбор куска для его изменения в списании
@stock_menu.callback_query(F.data.startswith('outlet:control:correct_piece:piece_id_'))
@stock_menu.callback_query(F.data.startswith('outlet:control:correct_piece:page_'))
@stock_menu.callback_query(F.data == 'outlet:control:correct_piece')
async def correct_piece_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    # удаляем из списка кусков
    if callback.data.startswith('outlet:control:correct_piece:piece_id_'):
        piece_id = int(callback.data.split('_')[-1])
        data = await state.get_data()
        added_pieces = data['added_pieces']
        del added_pieces[piece_id]
        await state.update_data(added_pieces=added_pieces)
        
    data = await state.get_data()
    added_pieces = data['added_pieces']
    operation = data['operation']
    
    if callback.data.startswith('outlet:control:correct_piece:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1

    if len(added_pieces) != 0:
        await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ КУСОК ТОВАРА ДЛЯ УДАЛЕНИЯ</b>',
                                        reply_markup=kb.choose_correct_piece(operation=operation,
                                                                             added_pieces=added_pieces,
                                                                             page=page),
                                        parse_mode='HTML')
    elif operation == 'writeoff':
        await product_writeoff_handler(callback, state)
    elif operation == 'replenishment':
        await product_replenishment_handler(callback, state)

    
# просим подтверждения списания
@stock_menu.callback_query(F.data == 'outlet:writeoff:calculate')
async def calculate_writeoff_handler(callback: CallbackQuery, state: FSMContext):
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
                                        reply_markup=kb.confirm_writeoff_product,
                                        parse_mode='HTML')


# просим подтверждения списания всех запасов продукта
@stock_menu.callback_query(F.data == 'outlet:writeoff:all')
async def all_writeoff_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    product_qty = Decimal(data['stock_qty'])
    product_unit = data['product_unit']
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    stock_data = await get_stock_product(outlet_id, product_id)
    product_name = stock_data['product_name']
    
    if product_unit == 'кг':
        product_unit = product_unit[-1]
        product_qty = product_qty * 1000
    
    await callback.message.edit_text(text=f'Будет выполнено списание товара <b>{product_name}</b> на <b>{int(product_qty)} {product_unit}</b>',
                                        reply_markup=kb.confirm_writeoff_product,
                                        parse_mode='HTML')


# подтверждение списания запасов товара
@stock_menu.callback_query(F.data == 'outlet:writeoff:confirm')
async def confirm_writeoff_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    product_unit = data['product_unit']
    from_callback = data['from_callback']
    
    added_pieces = [Decimal(added_piece) for added_piece in data['added_pieces']]
    product_qty = sum(added_pieces)
            
    # переводим граммы в килограммы
    if product_unit == 'кг':
        product_qty = product_qty / Decimal(1000)
        added_pieces = [added_piece / Decimal(1000) for added_piece in added_pieces]
    
    # если добавленных кусков нет, то это может быть только списание всего продукта
    if len(added_pieces) == 0:
        stock_qty = data['stock_qty']
        product_qty = Decimal(stock_qty)
    
    transaction_datetime = data['transaction_datetime']
    
    if transaction_datetime:
        transaction_datetime = localize_user_input(datetime(**data['transaction_datetime']))

    try:
        # создаем транзакцию для списания запасов товара и обновляем его количество
        await transaction_writeoff(outlet_id, product_id, product_qty, added_pieces, transaction_datetime)
        await callback.answer(text='Запасы продукта успешно списаны', show_alert=True)
        if from_callback is None:
            await choose_product_control_handler(callback, state)
        elif from_callback == 'outlet:control:transactions':
            await choose_transaction_product_handler(callback, state)
    except:
        await callback.answer(text='Невозможно создать транзакцию', show_alert=True)

    await state.update_data(transaction_datetime=None)


# меню отмены расчета баланса
@stock_menu.callback_query(F.data == 'outlet:writeoff:cancel')
async def cancel_writeoff_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    product_id = data['product_id']
    from_callback = data['from_callback']
    
    await callback.message.edit_text(text='❗️ <b>Вы пытаетесь выйти из операции списания товара. '\
                                            'Несохраненные данные будут утеряны.</b>',
                                            parse_mode='HTML',
                                            reply_markup=kb.cancel_writeoff_product(product_id, from_callback))


# инициируем удаление товара из торговой точки
@stock_menu.callback_query(F.data == 'outlet:stock:delete')
async def delete_stock_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    stock_data = await get_stock_product(outlet_id, product_id)
    product_name = stock_data['product_name']
    stock_qty = stock_data['stock_qty']
    product_unit = data['product_unit']
    
    if stock_qty > 0:
        await callback.answer(text='Невозможно удалить товар с запасами', show_alert=True)
        return None
    
    if product_unit == 'кг':
        product_unit = product_unit[-1]
        
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data['outlet_name']
    await callback.message.edit_text(text=f'Товар <b>{product_name}</b> будет удален из торговой точки <b>{outlet_name}</b>',
                                    reply_markup=kb.confirm_delete(product_id),
                                    parse_mode='HTML')


# подтверждение удаления товара из запасов
@stock_menu.callback_query(F.data == 'outlet:stock:delete:confirm')
async def confirm_stock_delete_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_id = data['outlet_id']
    product_id = data['product_id']

    try:
        # создаем транзакцию для пополнения запасов товара и обновляем его количество
        await transaction_delete_product(outlet_id, product_id)
        await callback.answer(text='Продукт успешно удален из торговой точки', show_alert=True)
        await choose_product_control_handler(callback, state)
    except:
        await callback.answer(text='Невозможно создать транзакцию', show_alert=True)


# история транзакций товара
@stock_menu.callback_query(F.data.startswith('outlet:control:transactions:page_'))
@stock_menu.callback_query(F.data == 'outlet:control:transactions')
@stock_menu.callback_query(F.data == 'outlet:control:transactions:back')
async def choose_transaction_product_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    if callback.data.startswith('outlet:control:transactions:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    elif callback.data == 'outlet:control:transactions':
        page = 1
    else:
        page = data['page']
        
    # сохраняем страницу для удобства при возвращении
    await state.update_data(added_pieces=[],
                            page=page)
    
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    stock_data = await get_stock_product(outlet_id, product_id)
    stock_id = stock_data['stock_id']
    product_unit = stock_data['product_unit']
    
    transactions_data = await transactions_info(outlet_id, stock_id)
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ТРАНЗАКЦИЮ</b>',
                                     reply_markup=kb.choose_transaction(transactions_data, product_unit, product_id, page=page),
                                     parse_mode='HTML')
    

# выводим информацию о транзакции товара торговой точки
@stock_menu.callback_query(F.data.startswith('outlet:control:transactions:transaction_id_'))
async def transaction_product_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    transaction_id = int(callback.data.split('_')[-1])
    await state.update_data(transaction_id=transaction_id)
    
    data = await state.get_data()
    outlet_id = data['outlet_id']
    stock_id = data['stock_id']
    
    product_id = data['product_id']
    stock_data = await get_stock_product(outlet_id, product_id)
    product_unit = stock_data['product_unit']
    
    transaction = await transaction_info(transaction_id)
    
    transaction_product_name = transaction['transaction_product_name']
    transaction_datetime = represent_utc_3(transaction['transaction_datetime']).strftime('%H:%M %d-%m-%Y')
    transaction_type_labels = {
        'balance': ['Продажа (ост.)', 'Рассчетное количество проданного товара', 'Части товара в остатке:'],
        'selling': ['Продажа', 'Количество проданного товара',  'Части товара проданного:'],
        'replenishment': ['Пополнение', 'Количество товара в пополнение',  'Части товара в пополнении:'],
        'writeoff': ['Списание', 'Количество товара в списании',  'Части товара в списании:']
    }
    
    try:
        transaction_type = transaction_type_labels[transaction['transaction_type']][0]
        transaction_qty_phrase = transaction_type_labels[transaction['transaction_type']][1]
        transaction_parts_phrase = transaction_type_labels[transaction['transaction_type']][2]
    except KeyError:
        transaction_type = None
        transaction_qty_phrase = 'Количество'
        transaction_parts_phrase = 'Части товара:'
    
    product_qty = transaction['product_qty']
    balance_after = transaction['balance_after']
    
    if product_unit == 'кг':
        product_qty = product_qty * Decimal(1000)
        balance_after = balance_after * Decimal(1000)
        product_unit = 'г'
        
    transaction_id = transaction['transaction_id']
    transaction_parts = transaction['transaction_info']
    
    text = f'<b>ТРАНЗАКЦИЯ №{transaction_id}</b>\n\n' \
            f'Товар - <b>{transaction_product_name}</b>\n' \
            f'Время и дата проведения - <b>{transaction_datetime}</b>\n' \
            f'Тип транзакции - <b>{transaction_type}</b>\n' \
            f'{transaction_qty_phrase} - <b>{round(product_qty)} {product_unit}</b>\n' \
            f'Количество товара после транзакции - <b>{round(balance_after)} {product_unit}</b>\n' \
                
    if not transaction_parts is None and len(transaction_parts) > 1:
        text += f'{transaction_parts_phrase}\n'
        for part in transaction_parts:
            if product_unit != 'шт.':
                part = part * Decimal(1000)
            
            text += f'- <b>{round(part)} {product_unit}</b>\n'
    
    # чтобы кнопка "Откатить" появлялась только у самой последней транзакции
    # делаем проверку на совпадение номера
    last_transaction_data = await get_last_transaction(outlet_id, stock_id)
    last_transaction_id = last_transaction_data['transaction_id']
    
    is_last_transaction = False
    if transaction_id == last_transaction_id:
        is_last_transaction = True
    
    await callback.message.edit_text(text=text,
                                     parse_mode='HTML',
                                     reply_markup=kb.transaction_menu(is_last_transaction))
    

# указываем дату новой транзакции
@stock_menu.callback_query(F.data == 'outlet:control:transactions:new_transaction')
@stock_menu.callback_query(F.data.startswith('outlet:control:transactions:month:prev:'))
@stock_menu.callback_query(F.data.startswith('outlet:control:transactions:month:next:'))
async def new_transaction_handler(callback: CallbackQuery, state: FSMContext):
    # для оповещения о дате последней транзакции
    data = await state.get_data()
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    stock_info = await get_stock_product(outlet_id, product_id)
    stock_id = stock_info['stock_id']
    
    last_transaction_info = await get_last_transaction(outlet_id, stock_id)
    
    if not last_transaction_info is None:
        last_transaction_datetime = represent_utc_3(last_transaction_info['transaction_datetime'])
        last_transaction_datetime_text = f'Дата последней транзакции - {last_transaction_datetime.strftime('%d-%m-%Y')}'
    else:
        last_transaction_datetime_text = ''
        
    now = localize_user_input(datetime.now(pytz.timezone("Europe/Chisinau")))
    year = now.year
    month = now.month
    # Переключаем месяца вперед и назад
    if callback.data.startswith('outlet:control:transactions:month:'):
        calendar_data = callback.data.split(':')
        if calendar_data[4] == 'prev':
            year = int(calendar_data[5])
            month = int(calendar_data[6]) - 1
            if month < 1:
                month = 12
                year -= 1
        elif calendar_data[4] == 'next':
            year = int(calendar_data[5])
            month = int(calendar_data[6]) + 1
            if month > 12:
                month = 1
                year += 1
        await callback.message.edit_reply_markup(reply_markup=kb.transaction_calendar_keyboard(year, month))
    else:
        await callback.message.edit_text(text='<b>❓ УКАЖИТЕ ДАТУ ТРАНЗАКЦИИ</b>\n\n'
                                                f'{last_transaction_datetime_text}',
                                        reply_markup=kb.transaction_calendar_keyboard(year, month),
                                        parse_mode='HTML')
        
    # обозначаем откуда пришли, чтобы после создания транзакции в режиме эксперта возвращаться в правильное меню
    await state.update_data(from_callback='outlet:control:transactions')
    
    
# сохраняем дату в контекст и просим ввести время
@stock_menu.callback_query(F.data.startswith('outlet:control:transactions:date:'))
async def new_transaction_date_handler(callback: CallbackQuery, state: FSMContext):
    date_comp = [int(_) for _ in callback.data.split(':')[-3:]]
    transaction_datetime = {
        'year': date_comp[0],
        'month': date_comp[1],
        'day': date_comp[2]
        }
    
    data = await state.get_data()
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    stock_info = await get_stock_product(outlet_id, product_id)
    stock_id = stock_info['stock_id']
    
    last_transaction_info = await get_last_transaction(outlet_id, stock_id)
    
    if not last_transaction_info is None:
        last_transaction_datetime = represent_utc_3(last_transaction_info['transaction_datetime'])
        last_transaction_datetime_text = f'Дата и время последней транзакции - {last_transaction_datetime.strftime('%H:%M %d-%m-%Y')}\n\n'
        
        # если последняя транзакция новее указанного времени, то ее нельзя создать
        if last_transaction_datetime.date() > date(**transaction_datetime):
            await callback.answer(text='Дата новой транзакции должна быть позднее существующих', show_alert=True)
            return None
    else:
        last_transaction_datetime_text = ''
    
    await state.update_data(transaction_datetime=transaction_datetime)
    
    await callback.message.edit_text(text=f'⌚️ <b>УКАЖИТЕ ВРЕМЯ ТРАНЗАКЦИИ</b>\n\n' \
                                        f'{last_transaction_datetime_text}'
                                        'Формат ввода времени: <i>Например 13:30 можно указать как 1330 без символа " : ". '\
                                        'Важно, чтобы перед компонентами времени с одним заком стоял 0 в начале - 08:05 или 0805.</i>',
                                     reply_markup=kb.cancel_transaction_creation,
                                     parse_mode='HTML')
    
    await state.set_state(Transaction.time)
    

# принимаем время транзакции
@stock_menu.message(Transaction.time)
async def new_transaction_time_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    stock_info = await get_stock_product(outlet_id, product_id)
    stock_id = stock_info['stock_id']
    
    last_transaction_info = await get_last_transaction(outlet_id, stock_id)
    
    if not last_transaction_info is None:
        last_transaction_datetime = represent_utc_3(last_transaction_info['transaction_datetime'])
        last_transaction_datetime_text = f'Дата и время последней транзакции - {last_transaction_datetime.strftime('%H:%M %d-%m-%Y')}\n\n'
    else:
        last_transaction_datetime_text = ''
    
    
    issue_time = message.text.replace(':', '')
    try:
        if len(issue_time) != 4:
            raise(ValueError('Неправильный формат'))
        transaction_datetime = data['transaction_datetime']
        transaction_datetime['hour'] = int(issue_time[:2])
        transaction_datetime['minute'] = int(issue_time[-2:])
        datetime(**transaction_datetime)
    except Exception:
        try:
            await state.set_state(Transaction.time)
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗ <b>НЕВЕРНО УКАЗАНО ВРЕМЯ</b>\n\n' \
                                                    f'⌚️ <b>УКАЖИТЕ ВРЕМЯ ТРАНЗАКЦИИ</b>\n\n' \
                                                    f'{last_transaction_datetime_text}' \
                                                    'Формат ввода времени: <i>Например 13:30 можно указать как 1330 без символа " : ". '\
                                                    'Важно, чтобы перед компонентами времени с одним заком стоял 0 в начале - 08:05 или 0805.</i>',
                                                reply_markup=kb.cancel_transaction_creation,
                                                parse_mode='HTML')
            return None
        except TelegramBadRequest:
            return None
    
    # проверяем указанные дату и время на новизну. новая транзакция не может быть странее самой новой.
    if not last_transaction_info is None:
        if last_transaction_datetime.replace(tzinfo=None) > datetime(**transaction_datetime):
            await state.set_state(Transaction.time)
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗ <b>Дата новой транзакции должна быть позднее существующих</b>\n\n' \
                                                    f'⌚️ <b>УКАЖИТЕ ВРЕМЯ ТРАНЗАКЦИИ</b>\n\n' \
                                                    f'{last_transaction_datetime_text}' \
                                                    'Формат ввода времени: <i>Например 13:30 можно указать как 1330 без символа " : ". '\
                                                    'Важно, чтобы перед компонентами времени с одним заком стоял 0 в начале - 08:05 или 0805.</i>',
                                                reply_markup=kb.cancel_transaction_creation,
                                                parse_mode='HTML')
            return None
        
            
    await state.update_data(transaction_datetime=transaction_datetime)
    data = await state.get_data()
    
    product_id = data['product_id']
    
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                        message_id=data['message_id'],
                                        text='<b>❓ ВЫБЕРИТЕ ТИП ТРАНЗАКЦИИ</b>',
                                        reply_markup=kb.choose_transaction_type(product_id),
                                        parse_mode='HTML')
    
    
# для отката транзакции просим написать слово "ОТКАТИТЬ"
@stock_menu.callback_query(F.data == 'outlet:control:transactions:rollback')
async def rollback_transaction_control_hendler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    transaction_id = data['transaction_id']
    
    await callback.message.edit_text(text=f'Чтобы откатить транзакцию <b>№{transaction_id}</b> введите слово <code>ОТКАТИТЬ</code>',
                                     reply_markup=kb.transaction_rollback_menu(transaction_id),
                                     parse_mode='HTML')
    
    await state.set_state(Transaction.rollback)


# ловим слово "ОТКАТИТЬ"
@stock_menu.message(Transaction.rollback)
async def rollback_transaction_receiver_hendler(message: Message, state: FSMContext):
    await state.set_state(None)
    
    if message.text.lower() != 'откатить':
        await state.set_state(Transaction.rollback)
        return None

    data = await state.get_data()
    stock_id = data['stock_id']
    transaction_id = data['transaction_id']
    chat_id = data['chat_id']
    message_id = data['message_id']

    transaction_data = await transaction_info(transaction_id)
    
    transaction_type = transaction_data['transaction_type']
    
    try:
        if transaction_type in ('selling', 'balance'):
            await rollback_selling(transaction_id, stock_id)
        elif transaction_type == 'replenishment':
            await rollback_replenishment(transaction_id)
        elif transaction_type == 'writeoff':
            await rollback_writeoff(transaction_id)
    except:
        await message.bot.edit_message_text(chat_id=chat_id,
                                            message_id=message_id,
                                            text='❗️ <b>НЕВОЗМОЖНО ОТКАТИТЬ ТРАНЗАКЦИЮ</b>',
                                            reply_markup=kb.transaction_rollback_menu(transaction_id),
                                            parse_mode='HTML')
        return None
    
    # возвращаемся в меню выбора транзакции
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    stock_data = await get_stock_product(outlet_id, product_id)
    stock_id = stock_data['stock_id']
    product_unit = stock_data['product_unit']
    
    transactions_data = await transactions_info(outlet_id, stock_id)
    
    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text='❓ <b>ВЫБЕРИТЕ ТРАНЗАКЦИЮ</b>',
                                        reply_markup=kb.choose_transaction(transactions_data, product_unit, product_id, page=1),
                                        parse_mode='HTML')
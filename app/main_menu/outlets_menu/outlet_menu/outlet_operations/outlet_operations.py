from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from decimal import Decimal
from datetime import datetime
import pytz

import app.main_menu.outlets_menu.outlet_menu.outlet_operations.keyboard as kb
from app.states import Stock
from app.database.all_requests.stock import get_active_stock_products, get_stock_product
from app.database.all_requests.transactions import transaction_selling, transaction_balance, get_last_balance_transaction, rollback_selling, were_stock_transactions
from app.database.all_requests.outlet import get_outlet
from app.main_menu.outlets_menu.outlet_menu.stock_menu.stock_menu import choose_transaction_product_handler
from app.com_func import represent_utc_3, localize_user_input

outlet_operations = Router()


# формирование текстового сообщения с информацией о транзакции с откатом остатка и удалением транзакции расчета остатка
async def rollback_balance_text(outlet_id, product_id):
    # извлекаем некоторые данные выбранного продукта
    stock_product_data = await get_stock_product(outlet_id, product_id)
    product_name = stock_product_data['product_name']
    stock_id = stock_product_data['stock_id']
    product_unit = stock_product_data['product_unit']
    
    last_transaction_data = await get_last_balance_transaction(outlet_id, stock_id)
    product_qty = last_transaction_data['product_qty']
    balance_after = last_transaction_data['balance_after']
    transaction_datetime = represent_utc_3(last_transaction_data['transaction_datetime'])
    
    if product_unit != 'кг':
        product_qty = int(product_qty)
        balance_after = int(balance_after)

    transaction_parts = last_transaction_data['transaction_info']
    
    
    text = f'<b>РАСЧЕТ ПРОДАЖ ПО ОСТАТКУ СЕГОДНЯ</b>\n\n' \
        f'Дата и время - <b>{transaction_datetime.strftime('%H:%M %d-%m-%Y')}</b>\n' \
        f'Название товара - <b>{product_name}</b>\n' \
        f'Запас до расчета остатка - <b>{product_qty + balance_after} {product_unit}</b>\n' \
        f'Новый указанный остаток - <b>{balance_after} {product_unit}</b>\n' \
        f'Рассчетное количество проданного товара - <b>{product_qty} {product_unit}</b>\n'
        
    if not transaction_parts is None and len(transaction_parts) > 1:
        text += f'Части товара в остатке:\n'
        for part in transaction_parts:
            if product_unit != 'шт.':
                part = part * Decimal(1000)
            
            text += f'- <b>{round(part)} {product_unit}</b>\n'
        
    return text


# формирование сообщения при добавлении товаров для расчета продаж
async def selling_text(outlet_id, product_id):
    # извлекаем название торговой точки
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data['outlet_name']
    
    # извлекаем некоторые данные выбранного продукта
    stock_product_data = await get_stock_product(outlet_id, product_id)
    product_name = stock_product_data['product_name']
    product_unit = stock_product_data['product_unit']
    stock_qty = stock_product_data['stock_qty']
    
    # корректируем единици измерения и зависимости от них
    product_unit_amend = product_unit
    if product_unit == 'кг':
        product_unit_amend = 'граммах'
    else:
        product_unit_amend = 'штуках'
        stock_qty = round(stock_qty)
    
    text = '❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА ДЛЯ ПРОДАЖИ</b>\n\n' \
            f'Вы пытаетесь провести продажу товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
            f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
            f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>.'
    
    return text, str(stock_qty), product_unit


# готовим текст для меню с товарами на расчет продаж
async def selling_menu_text(added_products, outlet_id):
    # выводим меню расчета остатка по продажам
    text = '💸 <b>РАСЧЕТ ОСТАТКА ПО ПРОДАЖАМ</b>\n\n'\
            'Для проведения операции добавьте один или несколько товаров и укажите их количество.\n'
            
    # формируем список кусков
    added_pieces_text = ''
    if len(added_products) != 0:
        added_pieces_text = '\nНа данный момент добавлены товары:\n'
        for product_id in added_products.keys():
            added_pieces = added_products[product_id]
            stock_data = await get_stock_product(outlet_id, int(product_id))
            product_name = stock_data['product_name']
            product_unit = stock_data['product_unit']
            added_pieces_text += f'<b>{product_name}:</b>\n'
            
            # корректируем единици измерения и зависимости от них
            if product_unit == 'кг':
                product_unit = 'г'
            
            for added_piece in added_pieces:
                added_pieces_text += f'<b>{added_piece} {product_unit}</b>\n'
            added_pieces_text += f'Итого к продаже - <b>{sum(added_pieces)} {product_unit}</b>\n\n'
    
    text += added_pieces_text
    
    return text


# формирование сообщения для меню баланса
async def balance_text(outlet_id, product_id, added_pieces):
    # извлекаем название торговой точки
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data['outlet_name']
    
    # извлекаем некоторые данные выбранного продукта
    stock_product_data = await get_stock_product(outlet_id, product_id)
    product_name = stock_product_data['product_name']
    product_unit = stock_product_data['product_unit']
    stock_qty = stock_product_data['stock_qty']
    
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
        added_pieces_text += f'Итого остаток - <b>{sum(added_pieces)} {product_unit_pieces}</b>\n'
    
    text = '❓ <b>УКАЖИТЕ ОСТАТОК ПРОДУКТА </b>\n\n' \
            f'Вы пытаетесь зафиксировать остаток продукта <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
            f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
            f'\nВведите количество продукта в <b>{product_unit_amend}</b>. ' \
            'Количество продукта можно вводить частами или сразу суммарное.\n' \
            f'{added_pieces_text}' \
            '\nПо окончании добавления всех частей товара нажмите <b>Расчитать</b> в противном случае нажмите <b>Отмена</b>.'
    
    return text, str(stock_qty), product_unit


# меню операций тороговой точки
@outlet_operations.callback_query(F.data == 'outlet:operations')
async def operations_menu_handler(callback: CallbackQuery, state: FSMContext):
    # чтобы при заходе в продажи было пусто
    await state.update_data(added_products={})
    
    await callback.message.edit_text(text='🧰 <b>МЕНЮ ОПЕРАЦИЙ</b>',
                                     reply_markup=kb.operations_menu,
                                     parse_mode='HTML')


# операция продажи товара из запасов
@outlet_operations.callback_query(F.data == 'outlet:selling')
async def selling_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    added_products = data['added_products']
    outlet_id = data['outlet_id']
    
    text = await selling_menu_text(added_products, outlet_id)
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.selling(added_products),
                                     parse_mode='HTML'
                                        )
  
  
# меню отмены расчета по продажам
@outlet_operations.callback_query(F.data == 'outlet:selling:cancel')
async def cancel_selling_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='❗️ <b>Вы пытаетесь выйти из операции расчета продаж товара. '\
                                            'Несохраненные данные будут утеряны.</b>',
                                            parse_mode='HTML',
                                            reply_markup=kb.selling_cancel)

    
# выбор продукта на продажу
@outlet_operations.callback_query(F.data.startswith('outlet:selling:page_'))
@outlet_operations.callback_query(F.data == 'outlet:selling:add_product')
async def choose_product_selling_handler(callback: CallbackQuery, state: FSMContext):
    
    if callback.data.startswith('outlet:selling:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1
    
    data = await state.get_data()
    outlet_id = data['outlet_id']
    stock_data = await get_active_stock_products(outlet_id)
    stock_data = [stock for stock in stock_data if stock['stock_qty'] != 0]
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ ПРОДАЖИ</b>',
                                     reply_markup=kb.choose_product_selling(stock_data=stock_data, page=page),
                                     parse_mode='HTML')
    

# запрашиваем количество товара для продажи
@outlet_operations.callback_query(F.data.startswith('outlet:selling:product_id_'))
async def product_selling_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    # сохранение данных товара если пришли по колбэку
    if callback.data.startswith('outlet:selling:product_id_'):
        product_id = int(callback.data.split('_')[-1])
        await state.update_data(product_id=product_id)
    # если пришли по вызову функции
    else:
        product_id = data['product_id']
    
    outlet_id = data['outlet_id']
    
    text, stock_qty, product_unit = await selling_text(outlet_id, product_id)
    
    await state.update_data(stock_qty=stock_qty,
                            product_unit=product_unit)
    
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.selling_product,
                                    parse_mode='HTML')
    
    await state.set_state(Stock.selling)


# принимаем количество товара на продажу
@outlet_operations.message(Stock.selling)
async def product_selling_receiver_handler(message: Message, state: FSMContext):
    
    await state.set_state(None)
    
    data = await state.get_data()
    
    outlet_id = data['outlet_id']   
    product_id = data['product_id']
    chat_id = data['chat_id']
    message_id = data['message_id']
    product_unit = data['product_unit']
    stock_qty = Decimal(data['stock_qty'])
    added_products = data['added_products']

    text = (await selling_text(outlet_id, product_id))[0]

    # корректируем единици измерения и зависимости от них
    if product_unit == 'кг':
        stock_qty = stock_qty * (Decimal(1000))
    else:
        stock_qty = round(stock_qty)

    # Проверяем на формат введенного количества товара
    try:
        product_qty = Decimal(message.text.replace(',', '.'))
        
        # количество продукта с учетом последнего добавленного куска
        total_qty = product_qty
        if str(product_id) in added_products.keys():
            total_qty += Decimal(sum(added_products[str(product_id)]))
        
        if product_qty <= 0:
            try:
                await state.set_state(Stock.selling)
                warning_text = '❗<b>КОЛИЧЕСТВО НЕ МОЖЕТ БЫТЬ МЕНЬШЕ ИЛИ РАВНО НУЛЮ</b>\n\n'
                text = warning_text + text
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text=text,
                                                    parse_mode='HTML',
                                                    reply_markup=kb.selling_product)
                return None
            except TelegramBadRequest:
                return None
        elif stock_qty - total_qty < 0:
            try:
                await state.set_state(Stock.selling)
                warning_text = '❗<b>КОЛИЧЕСТВО ТОВАРА НА ПРОДАЖУ НЕ МОЖЕТ БЫТЬ БОЛЬШЕ ЗАПАСА</b>\n\n'
                text = warning_text + text
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text=text,
                                                    parse_mode='HTML',
                                                    reply_markup=kb.selling_product)
                return None
            except TelegramBadRequest:
                return None
    except:
        try:
            await state.set_state(Stock.selling)
            warning_text = '❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>\n\n'
            text = warning_text + text
            await message.bot.edit_message_text(chat_id=chat_id,
                                                message_id=message_id,
                                                text=text,
                                                parse_mode='HTML',
                                                reply_markup=kb.selling_product)
            return None
        except TelegramBadRequest:
            return None
    
    
    if str(product_id) in added_products.keys():
        added_products[str(product_id)].append(int(product_qty))
    else:
        added_products[str(product_id)] = [int(product_qty)]
        
    await state.update_data(added_products=added_products)
    
    text = await selling_menu_text(added_products, outlet_id)
    
    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text=text,
                                        reply_markup=kb.selling(added_products),
                                        parse_mode='HTML'
                                            )
    

# выбираем продукты у которых хотим изменить куски
@outlet_operations.callback_query(F.data == 'outlet:selling:correct_piece')
@outlet_operations.callback_query(F.data.startswith('outlet:selling:choose_product:page_'))
async def choose_selling_correct_product_handler(callback: CallbackQuery, state: FSMContext):       
    data = await state.get_data()
    added_products = [int(product) for product in data['added_products'].keys()]
    outlet_id = data['outlet_id']
    
    if callback.data.startswith('outlet:selling:choose_product:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1

    if len(added_products) != 0:
        await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ ИЗМЕНЕНИЯ</b>',
                                        reply_markup=await kb.choose_product_correct_product(outlet_id=outlet_id,
                                                                                       added_products=added_products,
                                                                                        page=page),
                                        parse_mode='HTML')
    else:
        await selling_handler(callback, state)
        
        
# изменяем отдельные куски выбранных отдельных товаров
@outlet_operations.callback_query(F.data == 'outlet:selling:correct_piece')
@outlet_operations.callback_query(F.data.startswith('outlet:selling:choose_product:page_'))
@outlet_operations.callback_query(F.data.startswith('outlet:selling:choose_product:product_id_'))
@outlet_operations.callback_query(F.data.startswith('outlet:selling:correct_piece:piece_id_'))
async def choose_selling_correct_piece_handler(callback: CallbackQuery, state: FSMContext):
    # сохраняем идентификатор товара по которому пришли
    data = await state.get_data()
    if callback.data.startswith('outlet:selling:choose_product:product_id_'):
        product_id = int(callback.data.split('_')[-1])
        await state.update_data(product_id=product_id)
    else:
        product_id = data['product_id']
    
    # удаляем из списка кусков
    if callback.data.startswith('outlet:selling:correct_piece:piece_id_'):
        piece_id = int(callback.data.split('_')[-1])
        data = await state.get_data()
        added_products = data['added_products']
        added_pieces = added_products[str(product_id)]
        del added_pieces[piece_id]
        added_products[str(product_id)] = added_pieces
        await state.update_data(added_products=added_products)
        
    data = await state.get_data()
    added_pieces = data['added_products'][str(product_id)]
    
    if callback.data.startswith('outlet:selling:correct_piece:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1

    if len(added_pieces) != 0:
        await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ КУСОК ТОВАРА ДЛЯ УДАЛЕНИЯ</b>',
                                        reply_markup=kb.choose_selling_product_correct_piece(added_pieces=added_pieces,
                                                                                            page=page),
                                        parse_mode='HTML')
    else:
        # в случае, если кусков не осталось, удаляем продукт из словаря с продуктами
        del data['added_products'][str(product_id)]
        await state.clear()
        await state.update_data(data)
        await choose_selling_correct_product_handler(callback, state)


# просим подтвердить создание транзакций на продажу продуктов
@outlet_operations.callback_query(F.data == 'outlet:selling:calculate')
async def calculate_selling_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    added_products = data['added_products']
    outlet_id =  data['outlet_id']

    # формируем сообщение
    text = 'Будет создана транзакция на продажу следующих товаров:\n'
    for product_id in added_products.keys():
        product_data = await get_stock_product(outlet_id, int(product_id))
        product_name = product_data['product_name']
        product_unit = product_data['product_unit']
        product_qty = sum(added_products[product_id])
        if product_unit == 'кг':
            product_unit = product_unit[-1]
        
        text += f'{product_name} - <b>{product_qty} {product_unit}</b>\n'
    text += '\nЕсли все правильно нажмите <b>Подтвердить</b>.'
    
    await callback.message.edit_text(text=text,
                                    parse_mode='HTML',
                                    reply_markup=kb.selling_confirm)
    
    
# проводим списание проданных товаров
@outlet_operations.callback_query(F.data == 'outlet:selling:confirm')
async def confirm_selling_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    added_products = data['added_products']
    outlet_id =  data['outlet_id']
    
    try:
        await transaction_selling(outlet_id, added_products)
        await callback.answer(text='Транзакции успешно созданы', show_alert=True)
        await operations_menu_handler(callback, state)
    except:
        await callback.answer(text='Невозможно создать транзакцию', show_alert=True)


# выбираем товар для фиксации остатка
@outlet_operations.callback_query(F.data.startswith('outlet:balance:page_'))
@outlet_operations.callback_query(F.data == 'outlet:balance')
@outlet_operations.callback_query(F.data == 'outlet:balance:back')
async def choose_product_balance_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    if callback.data.startswith('outlet:balance:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    elif callback.data == 'outlet:balance':
        page = 1
    else:
        page = data['page']
    
    await state.update_data(added_pieces=[],
                            page=page, # сохраняем страницу для удобства при возвращении
                            transaction_datetime=None,
                            from_callback=None)

    outlet_id = data['outlet_id']
    stock_data = await get_active_stock_products(outlet_id)
    # проверяем в первую очередь били ли транзакции за день с товаром, если не было то проверяем баланс для отображения
    stock_data = [stock for stock in stock_data if await were_stock_transactions(stock['stock_id'],
                                                                                 datetime.now(pytz.timezone("Europe/Chisinau")),
                                                                                 ['balance'])
                                                or  stock['stock_qty'] != 0
                          ]
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ УКАЗАНИЯ ОСТАТКА</b>',
                                     reply_markup=await kb.choose_product_balance(stock_data=stock_data, page=page),
                                     parse_mode='HTML')


# принимаем продукт для фиксации баланса и предлагаем ввести его количество частями или сразу
# либо предлагаем сделать откатить транзакцию подсчета остатков на сегодняшний день
@outlet_operations.callback_query(F.data.startswith('outlet:balance:product_id_'))
async def product_balance_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    # сохранение данных товара если пришли по колбэку
    if callback.data.startswith('outlet:balance:product_id_'):
        product_id = int(callback.data.split('_')[-1])
        await state.update_data(product_id=product_id)
    # если пришли по вызову функции
    else:
        product_id = data['product_id']
    
    outlet_id = data['outlet_id']
    added_pieces = data['added_pieces']
    from_callback = data['from_callback']
    
    # делаем проверку на наличие транзакции по балансу за текущий день
    # извлекаем id запасов
    stock_product_data = await get_stock_product(outlet_id, product_id)
    stock_id = stock_product_data['stock_id']
    date_time = datetime.now(pytz.timezone("Europe/Chisinau"))
    transaction_types = ['balance']
    check_flag = await were_stock_transactions(stock_id, date_time, transaction_types)
    
    # если транзакция уже была за текущий день, то выводим информацию о ней
    if check_flag and from_callback is None:
        text = await rollback_balance_text(outlet_id, product_id)
        
        await callback.message.edit_text(text=text,
                                        reply_markup=kb.balance_product(added_pieces, from_callback, check_flag),
                                        parse_mode='HTML')
    # если не было транзакций за текущий день, то даем возможность ее сделать
    else:
        # формируем сообщение
        text, stock_qty, product_unit = await balance_text(outlet_id, product_id, added_pieces)
        # запоминаем на будущее
        await state.update_data(stock_qty=stock_qty,
                                product_unit=product_unit)
        
        await callback.message.edit_text(text=text,
                                        reply_markup=kb.balance_product(added_pieces, from_callback, check_flag),
                                        parse_mode='HTML')
        
        await state.set_state(Stock.balance)


# принимаем введенное количество товара для расчета продаж по остатку
@outlet_operations.message(Stock.balance)
async def product_balance_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    chat_id = data['chat_id']
    message_id = data['message_id']
    added_pieces = data['added_pieces']
    stock_qty = Decimal(data['stock_qty'])
    product_unit = data['product_unit']
    from_callback = data['from_callback']

    text = (await balance_text(outlet_id, product_id, added_pieces))[0]
    
    # корректируем единици измерения и зависимости от них
    if product_unit == 'кг':
        stock_qty = stock_qty * (Decimal(1000))
    else:
        stock_qty = round(stock_qty)

    # Проверяем на формат введенного количества товара
    try:
        product_qty = Decimal(message.text.replace(',', '.'))
        
        # количество продукта с учетом последнего добавленного куска
        total_qty = product_qty + Decimal(sum(added_pieces))
        
        if product_qty < 0:
            try:
                await state.set_state(Stock.balance)
                warning_text = '❗<b>КОЛИЧЕСТВО НЕ МОЖЕТ БЫТЬ МЕНЬШЕ НУЛЯ</b>\n\n'
                text = warning_text + text
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text=text,
                                                    parse_mode='HTML',
                                                    reply_markup=kb.balance_product(added_pieces, from_callback))
                return None
            except TelegramBadRequest:
                return None
        elif stock_qty - total_qty < 0:
            try:
                await state.set_state(Stock.balance)
                warning_text = '❗<b>ОСТАТОК НЕ МОЖЕТ БЫТЬ БОЛЬШЕ ЗАПАСА</b>\n\n'
                text = warning_text + text
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text=text,
                                                    parse_mode='HTML',
                                                    reply_markup=kb.balance_product(added_pieces, from_callback))
                return None
            except TelegramBadRequest:
                return None
    except:
        try:
            await state.set_state(Stock.balance)
            warning_text = '❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>\n\n'
            text = warning_text + text
            await message.bot.edit_message_text(chat_id=chat_id,
                                                message_id=message_id,
                                                text=text,
                                                parse_mode='HTML',
                                                reply_markup=kb.balance_product(added_pieces, from_callback))
            return None
        except TelegramBadRequest:
            return None

    # добавляем новый кусочек в список кусков
    added_pieces.append(int(product_qty))
    await state.update_data(added_pieces=added_pieces)

    text = (await balance_text(outlet_id, product_id, added_pieces))[0]

    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text=text,
                                        parse_mode='HTML',
                                        reply_markup=kb.balance_product(added_pieces, from_callback))
    
    await state.set_state(Stock.balance)


# даем выбор куска для его изменения
@outlet_operations.callback_query(F.data.startswith('outlet:balance:correct_piece:piece_id_'))
@outlet_operations.callback_query(F.data.startswith('outlet:balance:correct_piece:page_'))
@outlet_operations.callback_query(F.data == 'outlet:balance:correct_piece')
async def choose_balance_selling_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    # удаляем из списка кусков
    if callback.data.startswith('outlet:balance:correct_piece:piece_id_'):
        piece_id = int(callback.data.split('_')[-1])
        data = await state.get_data()
        added_pieces = data['added_pieces']
        del added_pieces[piece_id]
        await state.update_data(added_pieces=added_pieces)
        
    data = await state.get_data()
    added_pieces = data['added_pieces']
    product_id = data['product_id']
    
    if callback.data.startswith('outlet:balance:correct_piece:page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1

    if len(added_pieces) != 0:
        await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ КУСОК ТОВАРА ДЛЯ УДАЛЕНИЯ</b>',
                                        reply_markup=kb.choose_product_correct_piece(product_id=product_id,
                                                                                    added_pieces=added_pieces,
                                                                                    page=page),
                                        parse_mode='HTML')
    else:
        await product_balance_handler(callback, state)
    

# меню отмены расчета баланса
@outlet_operations.callback_query(F.data == 'outlet:balance:cancel')
async def cancel_balance_product_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    product_id = data['product_id']
    from_callback = data['from_callback']
    
    await callback.message.edit_text(text='❗️ <b>Вы пытаетесь выйти из операции расчета продаж товара по остатку. '\
                                            'Несохраненные данные будут утеряны.</b>',
                                            parse_mode='HTML',
                                            reply_markup=kb.cancel_balance_product(product_id, from_callback))
    
    
# меню финального расчета баланса
@outlet_operations.callback_query(F.data == 'outlet:balance:calculate')
async def calculate_balance_product_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    added_pieces = data['added_pieces']
    product_id = data['product_id']
    outlet_id = data['outlet_id']
    added_pieces_sum = sum(added_pieces)
    
    # извлекаем некоторые данные выбранного продукта
    stock_product_data = await get_stock_product(outlet_id, product_id)
    product_name = stock_product_data['product_name']
    product_unit = stock_product_data['product_unit']
    stock_qty = stock_product_data['stock_qty']

    # корректируем единици измерения и зависимости от них
    if product_unit == 'кг':
        stock_qty = stock_qty * (Decimal(1000))
        product_unit = product_unit[-1]
        
    stock_qty = round(stock_qty)
    
    # если остаток больше запасов, выдаем предупреждение и ничего не меняем
    if Decimal(added_pieces_sum) > stock_qty:
        await callback.answer(text='❗️ Операция невозможна. \n' \
                                    'Остаток не может быть больше запасов.',
                                    show_alert=True)
        return None
    # если остаток равен запасу
    elif Decimal(added_pieces_sum) == stock_qty:
        await callback.message.edit_text(text=f'Остаток <b>{added_pieces_sum} {product_unit}</b> товара <b>{product_name}</b> равен его запасу <b>{stock_qty} {product_unit}</b>\n' \
                                                'Если все правильно нажмите <b>Подтвердить</b>.',
                                                parse_mode='HTML',
                                                reply_markup=kb.confirm_balance_product(product_id))
    # если остаток меньше запас, то все окей
    else:
        stock_diff = stock_qty - added_pieces_sum
        await callback.message.edit_text(text=f'Будет создана транзакция на продажу <b>{stock_diff} {product_unit}</b> товара <b>{product_name}</b>.\n' \
                                                'Если все правильно нажмите <b>Подтвердить</b>.',
                                                parse_mode='HTML',
                                                reply_markup=kb.confirm_balance_product(product_id))
        
        
# после подтверждения создаем транзакцию по обновлению запасов и продаже товаров
@outlet_operations.callback_query(F.data == 'outlet:balance:confirm')
async def confirm_balance_product_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    data = await state.get_data()
    product_id = data['product_id']
    outlet_id = data['outlet_id']
    added_pieces = [Decimal(added_piece) for added_piece in data['added_pieces']]
    product_qty = sum(added_pieces)
    product_unit = data['product_unit']
    from_callback = data['from_callback']

    transaction_datetime = data['transaction_datetime']
    
    if transaction_datetime:
        transaction_datetime = localize_user_input(datetime(**data['transaction_datetime']))

    if product_unit == 'кг':
        product_qty = product_qty / Decimal(1000)
        added_pieces = [added_piece / Decimal(1000) for added_piece in added_pieces]
    
    try:
        await transaction_balance(outlet_id, product_id, product_qty, added_pieces, transaction_datetime)
        await callback.answer(text='Транзакция успешно создана', show_alert=True)
        if from_callback is None:
            await choose_product_balance_handler(callback, state)
        elif from_callback == 'outlet:control:transactions':
            await choose_transaction_product_handler(callback, state)
    except:
        await callback.answer(text='Невозможно создать транзакцию', show_alert=True)
        
    await state.update_data(transaction_datetime=None)
    

# инициируем отмену предыдущей транзакции обновления остатка
@outlet_operations.callback_query(F.data == 'outlet:balance:rollback')
async def rollback_balance_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()

    product_id = data['product_id']
    
    text = '❗️<b> ВНИМАНИЕ</b>\n\n' \
                'Вы пытаетесь удалить последнюю транзакцию расчета продаж товара по остатку.\n\n' \
                'Если вы уверены, что хотите удалить транзакцию, нажмите <b>Подтвердить</b>, в противном случае нажмите <b>Отмена</b>'
    
    await callback.message.edit_text(text=text,
                                     parse_mode='HTML',
                                     reply_markup=kb.confirm_balance_rollback(product_id))
    

# операция отката транзакции баланса
@outlet_operations.callback_query(F.data == 'outlet:balance:rollback:confirm')
async def rollback_balance_confirm_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    product_id = data['product_id']
    
    # извлекаем id запасов
    stock_product_data = await get_stock_product(outlet_id, product_id)
    stock_id = stock_product_data['stock_id']
    
    # извлекаем id транзакции
    last_transaction_data = await get_last_balance_transaction(outlet_id, stock_id)
    transaction_id = last_transaction_data['transaction_id']
    
    try:
        await rollback_selling(transaction_id, stock_id)
        await callback.answer(text='Транзакция успешно удалена', show_alert=True)
        await choose_product_balance_handler(callback, state)
    except:
        await callback.answer(text='Невозможно удалить транзакцию', show_alert=True)
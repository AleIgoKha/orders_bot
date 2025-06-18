from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from decimal import Decimal

import app.main_menu.outlets_menu.outlet_menu.outlet_operations.keyboard as kb
from app.com_func import represent_utc_3
from app.states import Stock
from app.database.all_requests.stock import get_active_stock_products, get_stock_product
from app.database.all_requests.transactions import get_last_transaction, transaction_selling, transaction_balance
from app.database.requests import get_outlet

outlet_operations = Router()


async def balance_text(outlet_id, product_id, added_pieces):
    # извлекаем название торговой точки
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data.outlet_name
    
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
    
    return text, float(stock_qty), product_unit



# меню операций тороговой точки
@outlet_operations.callback_query(F.data == 'outlet:operations')
async def operations_menu_handler(callback: CallbackQuery, state: FSMContext):
    # чтобы при заходе в продажи было пусто
    await state.update_data(added_pieces=[])
    
    await callback.message.edit_text(text='🧰 <b>МЕНЮ ОПЕРАЦИЙ</b>',
                                     reply_markup=kb.operations_menu,
                                     parse_mode='HTML')


# операция продажи товара из запасов
@outlet_operations.callback_query(F.data == 'outlet:selling')
async def selling_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    added_pieces = data['added_pieces']
    
    text = '💸 <b>РАСЧЕТ ОСТАТКА ПО ПРОДАЖАМ</b>\n\n'\
            'Для проведения операции добавьте один или несколько товаров и укажите их количество.\n'
            
    # формируем список кусков
    added_pieces_text = ''
    # if len(added_pieces) != 0:
    #     added_pieces_text = '\nНа данный момент добавлены товары:\n'
    #     for added_piece in added_pieces:
    #         added_pieces_text += f'<b>{added_piece} {product_unit_pieces}</b>\n'
    #     added_pieces_text += f'Итого к продаже - <b>{sum(added_pieces)} {product_unit_pieces}</b>\n'
    
    text += added_pieces_text
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.selling(added_pieces),
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
    
    # извлекаем название торговой точки
    outlet_id = data['outlet_id']
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data.outlet_name
    
    # извлекаем некоторые данные выбранного продукта
    stock_product_data = await get_stock_product(outlet_id, product_id)
    product_name = stock_product_data['product_name']
    product_unit = stock_product_data['product_unit']
    stock_qty = stock_product_data['stock_qty']
    stock_id = stock_product_data['stock_id']
    
    # корректируем единици измерения и зависимости от них
    product_unit_amend = product_unit
    if product_unit == 'кг':
        product_unit_amend = 'граммах'
    else:
        product_unit_amend = 'штуках'
        stock_qty = round(stock_qty)
        
    # последняя транзакция с товаром достаем ее данные и создаем текст
    last_transaction_data = await get_last_transaction(outlet_id=outlet_id,
                                                       stock_id=stock_id,
                                                       transaction_type='selling')
    last_transaction_text = ''
    if last_transaction_data:
        transaction_datetime = represent_utc_3(last_transaction_data['transaction_datetime']).strftime('в %H:%M %d-%m-%Y')
        transaction_product_qty = last_transaction_data['product_qty']
        
        # если не килограмы, убираем нули после запятой
        if product_unit != 'кг':
            transaction_product_qty = round(transaction_product_qty)
        last_transaction_text = f'Последнее продажа товара - <b>💲{transaction_product_qty} {product_unit} ({transaction_datetime})</b>\n'
    
    await callback.message.edit_text(text='❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА ДЛЯ ПРОДАЖИ</b>\n\n' \
                                        f'Вы пытаетесь провести продажу товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
                                        f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
                                        f'{last_transaction_text}' \
                                        f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>.',
                                    reply_markup=kb.selling_product,
                                    parse_mode='HTML')
    
    await state.set_state(Stock.selling)


# принимаем количество товара на продажу
@outlet_operations.message(Stock.selling)
async def product_selling_receiver_handler(message: Message, state: FSMContext):
    
    await state.set_state(None)
    
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data.outlet_name
    
    product_id = data['product_id']
    chat_id = data['chat_id']
    message_id = data['message_id']
    
    stock_product_data = await get_stock_product(outlet_id, product_id)
    product_name = stock_product_data['product_name']
    product_unit = stock_product_data['product_unit']
    stock_qty = stock_product_data['stock_qty']
    stock_id = stock_product_data['stock_id']
    
    product_unit_amend = product_unit
    if product_unit == 'кг':
        product_unit_amend = 'граммах'
    else:
        product_unit_amend = 'штуках'
        stock_qty = round(stock_qty)
        
    # последняя транзакция с товаром
    last_transaction_data = await get_last_transaction(outlet_id=outlet_id,
                                                       stock_id=stock_id,
                                                       transaction_type='selling')
    last_transaction_text = ''
    if last_transaction_data:
        transaction_datetime = represent_utc_3(last_transaction_data['transaction_datetime']).strftime('в %H:%M %d-%m-%Y')
        transaction_product_qty = last_transaction_data['product_qty']
        
        if product_unit != 'кг':
            transaction_product_qty = round(transaction_product_qty)
            
        last_transaction_text = f'Последнее продажа товара - <b>💲{transaction_product_qty} {product_unit} ({transaction_datetime})</b>\n'
    

    # Проверяем на формат введенного количества товара
    try:
        product_qty = Decimal(message.text.replace(',', '.'))
        
        if product_unit == 'кг':
            product_qty = product_qty / Decimal(1000)
        
        if product_qty == 0:
            try:
                await state.set_state(Stock.selling)
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text='❗<b>КОЛИЧЕСТВО НЕ МОЖЕТ БЫТЬ РАВНО НУЛЮ!</b>\n\n' \
                                                        '❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА ДЛЯ ПРОДАЖИ</b>\n\n' \
                                                        f'Вы пытаетесь провести продажу товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
                                                        f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
                                                        f'{last_transaction_text}' \
                                                        f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>.',
                                                    parse_mode='HTML',
                                                    reply_markup=kb.selling_product)
                return None
            except TelegramBadRequest:
                return None
        elif stock_qty - product_qty < 0:
            try:
                await state.set_state(Stock.selling)
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text='❗<b>КОЛИЧЕСТВО ДЛЯ СПИСАНИЯ НЕ МОЖЕТ БЫТЬ МЕНЬШЕ ЗАПАСА</b>\n\n' \
                                                        '❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА ДЛЯ ПРОДАЖИ</b>\n\n' \
                                                        f'Вы пытаетесь провести продажу товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
                                                        f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
                                                        f'{last_transaction_text}' \
                                                        f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>.',
                                                    parse_mode='HTML',
                                                    reply_markup=kb.selling_product)
                return None
            except TelegramBadRequest:
                return None
    except:
        try:
            await state.set_state(Stock.selling)
            await message.bot.edit_message_text(chat_id=chat_id,
                                                message_id=message_id,
                                                text='❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>\n\n' \
                                                    '❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА ДЛЯ ПРОДАЖИ</b>\n\n' \
                                                    f'Вы пытаетесь провести продажу товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
                                                    f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
                                                    f'{last_transaction_text}' \
                                                    f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>.',
                                                parse_mode='HTML',
                                                reply_markup=kb.selling_product)
            return None
        except TelegramBadRequest:
            return None

    # создаем транзакцию по продаже запасов товара
    await transaction_selling(outlet_id, product_id, product_qty)
    
    # Выводим меню выбора товара на продажу
    stock_data = await get_active_stock_products(outlet_id)

    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ ПРОДАЖИ</b>',
                                        reply_markup=kb.choose_product_selling(stock_data=stock_data),
                                        parse_mode='HTML')
    
    
# выбираем товар для фиксации остатка
@outlet_operations.callback_query(F.data.startswith('outlet:balance:page_'))
@outlet_operations.callback_query(F.data == 'outlet:balance')
async def choose_product_balance_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await state.update_data(added_pieces=[])
    
    if callback.data.startswith('outlet:balance:page_'):
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
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ УКАЗАНИЯ ОСТАТКА</b>',
                                     reply_markup=kb.choose_product_balance(stock_data=stock_data, page=page),
                                     parse_mode='HTML')


# принимаем продукт для фиксации баланса и предлагаем ввести его количество частями или сразу
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
    
    # формируем сообщение
    text, stock_qty, product_unit = await balance_text(outlet_id, product_id, added_pieces)
    
    # запоминаем на будущее
    await state.update_data(stock_qty=stock_qty,
                            product_unit=product_unit)
    
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.balance_product(added_pieces),
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

    text = (await balance_text(outlet_id, product_id, added_pieces))[0]
    
    # корректируем единици измерения и зависимости от них
    if product_unit == 'кг':
        stock_qty = stock_qty * (Decimal(1000))
    else:
        stock_qty = round(stock_qty)

    # Проверяем на формат введенного количества товара
    try:
        product_qty = Decimal(message.text.replace(',', '.'))
        
        if product_qty <= 0:
            try:
                await state.set_state(Stock.balance)
                warning_text = '❗<b>КОЛИЧЕСТВО НЕ МОЖЕТ БЫТЬ МЕНЬШЕ ИЛИ РАВНО НУЛЮ</b>\n\n'
                text = warning_text + text
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text=text,
                                                    parse_mode='HTML',
                                                    reply_markup=kb.balance_product(added_pieces))
                return None
            except TelegramBadRequest:
                return None
        elif stock_qty - product_qty < 0:
            try:
                await state.set_state(Stock.balance)
                warning_text = '❗<b>КУСОК НЕ МОЖЕТ ИМЕТЬ МАССУ БОЛЬШЕ ЗАПАСА</b>\n\n'
                text = warning_text + text
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text=text,
                                                    parse_mode='HTML',
                                                    reply_markup=kb.balance_product(added_pieces))
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
                                                reply_markup=kb.balance_product(added_pieces))
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
                                        reply_markup=kb.balance_product(added_pieces))
    
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
    data = await state.get_data()
    product_id = data['product_id']
    
    await callback.message.edit_text(text='❗️ <b>Вы пытаетесь выйти из операции расчета продаж товара по остатку. '\
                                            'Несохраненные данные будут утеряны.</b>',
                                            parse_mode='HTML',
                                            reply_markup=kb.cancel_balance_product(product_id))
    
    
# меню финального расчета баланса
@outlet_operations.callback_query(F.data == 'outlet:balance:calculate')
async def calculate_balance_product_handler(callback: CallbackQuery, state: FSMContext):  
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
        
        
# после подтверждения создаем транзакцию
@outlet_operations.callback_query(F.data == 'outlet:balance:confirm')
async def confirm_balance_product_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    added_pieces = data['added_pieces']
    product_id = data['product_id']
    outlet_id = data['outlet_id']
    product_unit = data['product_unit']
    
    product_qty = Decimal(sum(added_pieces))
    
    # корректируем единици измерения и зависимости от них
    if product_unit == 'кг':
        product_qty = product_qty / (Decimal(1000))
    
    await transaction_balance(outlet_id, product_id, product_qty)
    await callback.answer(text='Транзакция успешно создана', show_alert=True)
    await choose_product_balance_handler(callback, state)
    
    
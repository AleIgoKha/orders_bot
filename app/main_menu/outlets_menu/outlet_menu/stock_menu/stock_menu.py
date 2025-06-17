from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from decimal import Decimal

from app.com_func import represent_utc_3
import app.main_menu.outlets_menu.outlet_menu.stock_menu.keyboard as kb
from app.states import Stock
from app.database.requests import get_outlet, get_product
from app.database.all_requests.stock import get_stock_product, get_active_stock_products, add_stock, get_out_stock_products
from app.database.all_requests.transactions import get_last_transaction, transaction_writeoff, transaction_replenish, transaction_delete_product


stock_menu = Router()


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
async def operations_menu_handler(callback: CallbackQuery, state: FSMContext):
    
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
    outlet_name = outlet_data.outlet_name
    
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
    
    await add_stock(outlet_id, product_id)
    
    await callback.answer(text='Продукт успешно добавлен в запасы', show_alert=True)
    
    await choose_add_product_handler(callback, state)


# Пополнение запасов продукта
@stock_menu.callback_query(F.data.startswith('outlet:replenishment:product_id_'))
async def product_replenishment_handler(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split('_')[-1])
    await state.update_data(product_id=product_id)
    
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    outlet_data = await get_outlet(outlet_id)
    outlet_name = outlet_data.outlet_name
    
    stock_product_data = await get_stock_product(outlet_id, product_id)
    product_unit = stock_product_data['product_unit']
    stock_qty = stock_product_data['stock_qty']
    stock_id = stock_product_data['stock_id']
    product_name = stock_product_data['product_name']
    
    product_unit_amend = product_unit
    if product_unit == 'кг':
        product_unit_amend = 'граммах'
    else:
        product_unit_amend = 'штуках'
        stock_qty = round(stock_qty)
        
    # последняя транзакция с товаром
    last_transaction_data = await get_last_transaction(outlet_id=outlet_id,
                                                       stock_id=stock_id,
                                                       transaction_type='replenishment')
    last_transaction_text = ''
    if last_transaction_data:
        transaction_datetime = represent_utc_3(last_transaction_data['transaction_datetime']).strftime('в %H:%M %d-%m-%Y')
        transaction_product_qty = last_transaction_data['product_qty']
        
        if product_unit != 'кг':
            transaction_product_qty = round(transaction_product_qty)
            
        last_transaction_text = f'Последнее пополнение товара - <b>➕{transaction_product_qty} {product_unit} ({transaction_datetime})</b>\n'
    
    await callback.message.edit_text(text='❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА</b>\n\n' \
                                        f'Вы пытаетесь пополнить запасы товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
                                        f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
                                        f'{last_transaction_text}' \
                                        f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>\n\n',
                                        reply_markup=kb.replenish_product,
                                        parse_mode='HTML')
    
    await state.set_state(Stock.replenishment)


# принимаем количество товара на пополнение
@stock_menu.message(Stock.replenishment)
async def product_replenishment_receiver_handler(message: Message, state: FSMContext):
    
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
                                                       transaction_type='replenishment')
    last_transaction_text = ''
    if last_transaction_data:
        transaction_datetime = represent_utc_3(last_transaction_data['transaction_datetime']).strftime('в %H:%M %d-%m-%Y')
        transaction_product_qty = last_transaction_data['product_qty']
        
        if product_unit != 'кг':
            transaction_product_qty = round(transaction_product_qty)
            
        last_transaction_text = f'Последнее пополнение товара - <b>➕{transaction_product_qty} {product_unit} ({transaction_datetime})</b>\n'
    
    # Проверяем на формат
    try:
        product_qty = Decimal(message.text.replace(',', '.'))
        
        if product_unit == 'кг':
            product_qty = product_qty / Decimal(1000)
        
        if product_qty == 0:
            try:
                await state.set_state(Stock.replenishment)
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text='❗<b>КОЛИЧЕСТВО НЕ МОЖЕТ БЫТЬ РАВНО НУЛЮ!</b>\n\n' \
                                                        '❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА</b>\n\n' \
                                                        f'Вы пытаетесь пополнить запасы товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
                                                        f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
                                                        f'{last_transaction_text}' \
                                                        f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>\n\n',
                                                    parse_mode='HTML',
                                                    reply_markup=kb.replenish_product)
                return None
            except TelegramBadRequest:
                return None
    except:
        try:
            await state.set_state(Stock.replenishment)
            await message.bot.edit_message_text(chat_id=chat_id,
                                                message_id=message_id,
                                                text='❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>\n\n' \
                                                    '❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА</b>\n\n' \
                                                    f'Вы пытаетесь пополнить запасы товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
                                                    f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
                                                    f'{last_transaction_text}' \
                                                    f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>\n\n',
                                                parse_mode='HTML',
                                                reply_markup=kb.replenish_product)
            return None
        except TelegramBadRequest:
            return None
    
    # создаем транзакцию для пополнения запасов товара и обновляем его количество
    await transaction_replenish(outlet_id, product_id, product_qty)
    
    # Выводим меню выбора товара на пополнение
    stock_data = await get_active_stock_products(outlet_id)
    
    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ ПОПОЛНЕНИЯ ЗАПАСОВ</b>',
                                        reply_markup=kb.choose_product_replenishment(stock_data=stock_data),
                                        parse_mode='HTML')


# инициируем списание товара
@stock_menu.callback_query(F.data == 'outlet:writeoff')
@stock_menu.callback_query(F.data.startswith('outlet:writeoff:page_'))
async def choose_product_writeoff_handler(callback: CallbackQuery, state: FSMContext):
    
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
    # сохранение данных товара
    product_id = int(callback.data.split('_')[-1])
    await state.update_data(product_id=product_id)
    
    data = await state.get_data()
    
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
                                                       transaction_type='writeoff')
    last_transaction_text = ''
    if last_transaction_data:
        transaction_datetime = represent_utc_3(last_transaction_data['transaction_datetime']).strftime('в %H:%M %d-%m-%Y')
        transaction_product_qty = last_transaction_data['product_qty']
        # если килограмы, убираем нули после запятой
        if product_unit != 'кг':
            transaction_product_qty = round(transaction_product_qty)
        last_transaction_text = f'Последнее списание товара - <b>➖{transaction_product_qty} {product_unit} ({transaction_datetime})</b>\n'
    
    await callback.message.edit_text(text='❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА ДЛЯ СПИСАНИЯ</b>\n\n' \
                                        f'Вы пытаетесь списать часть запасов товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
                                        f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
                                        f'{last_transaction_text}' \
                                        f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>. ' \
                                        'Для удаления товара введите <i>УДАЛИТЬ</i>.\n\n',
                                    reply_markup=kb.writeoff_product,
                                    parse_mode='HTML')
    
    await state.set_state(Stock.writeoff)


# принимаем количество товара на списание
@stock_menu.message(Stock.writeoff)
async def product_writeoff_receiver_handler(message: Message, state: FSMContext):
    
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
                                                       transaction_type='writeoff')
    last_transaction_text = ''
    if last_transaction_data:
        transaction_datetime = represent_utc_3(last_transaction_data['transaction_datetime']).strftime('в %H:%M %d-%m-%Y')
        transaction_product_qty = last_transaction_data['product_qty']
        
        if product_unit != 'кг':
            transaction_product_qty = round(transaction_product_qty)
            
        last_transaction_text = f'Последнее списание товара - <b>➖{transaction_product_qty} {product_unit} ({transaction_datetime})</b>\n'
    

    if message.text.lower().strip() == 'удалить':
        # создаем транзакцию по списанию всех запасов товара и его удаления из торговой точки
        await transaction_delete_product(outlet_id, product_id)
    # если не удаляем, то списываем
    else:
        # Проверяем на формат введенного количества товара
        try:
            product_qty = Decimal(message.text.replace(',', '.'))
            
            if product_unit == 'кг':
                product_qty = product_qty / Decimal(1000)
            
            if product_qty == 0:
                try:
                    await state.set_state(Stock.writeoff)
                    await message.bot.edit_message_text(chat_id=chat_id,
                                                        message_id=message_id,
                                                        text='❗<b>КОЛИЧЕСТВО НЕ МОЖЕТ БЫТЬ РАВНО НУЛЮ!</b>\n\n' \
                                                            '❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА ДЛЯ СПИСАНИЯ</b>\n\n' \
                                                            f'Вы пытаетесь списать часть запасов товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
                                                            f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
                                                            f'{last_transaction_text}' \
                                                            f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>. ' \
                                                            'Для удаления товара введите <i>УДАЛИТЬ</i>.\n\n',
                                                        parse_mode='HTML',
                                                        reply_markup=kb.writeoff_product)
                    return None
                except TelegramBadRequest:
                    return None
            elif stock_qty - product_qty < 0:
                try:
                    await state.set_state(Stock.writeoff)
                    await message.bot.edit_message_text(chat_id=chat_id,
                                                        message_id=message_id,
                                                        text='❗<b>КОЛИЧЕСТВО ДЛЯ СПИСАНИЯ НЕ МОЖЕТ БЫТЬ МЕНЬШЕ ЗАПАСА</b>\n\n' \
                                                            '❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА ДЛЯ СПИСАНИЯ</b>\n\n' \
                                                            f'Вы пытаетесь списать часть запасов товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
                                                            f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
                                                            f'{last_transaction_text}' \
                                                            f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>. ' \
                                                            'Для удаления товара введите <i>УДАЛИТЬ</i>.\n\n',
                                                        parse_mode='HTML',
                                                        reply_markup=kb.writeoff_product)
                    return None
                except TelegramBadRequest:
                    return None
        except:
            try:
                await state.set_state(Stock.writeoff)
                await message.bot.edit_message_text(chat_id=chat_id,
                                                    message_id=message_id,
                                                    text='❗<b>НЕВЕРНЫЙ ФОРМАТ ВВОДА ДАННЫХ!</b>\n\n' \
                                                        '❓ <b>УКАЖИТЕ КОЛИЧЕСТВО ПРОДУКТА ДЛЯ СПИСАНИЯ</b>\n\n' \
                                                        f'Вы пытаетесь списать часть запасов товара <b>{product_name}</b> в тороговой точке <b>{outlet_name}</b>.\n\n' \
                                                        f'Текущий запас товара - <b>{stock_qty} {product_unit}</b>\n' \
                                                        f'{last_transaction_text}' \
                                                        f'\nЕсли все правильно, введите количество продукта в <b>{product_unit_amend}</b>, в противном случае нажмите <b>Отмена</b>. ' \
                                                        'Для удаления товара введите <i>УДАЛИТЬ</i>.\n\n',
                                                    parse_mode='HTML',
                                                    reply_markup=kb.writeoff_product)
                return None
            except TelegramBadRequest:
                return None

        # создаем транзакцию по списания запасов товара
        await transaction_writeoff(outlet_id, product_id, product_qty)
        
    # Выводим меню выбора товара на списание
    stock_data = await get_active_stock_products(outlet_id)
    
    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ СПИСАНИЯ ЗАПАСОВ</b>',
                                        reply_markup=kb.choose_product_writeoff(stock_data=stock_data),
                                        parse_mode='HTML')
    






# сделать так, чтобы проверка на то, что количество товара на списание не может быть больше чем запасы на стороне запроса в базу данных
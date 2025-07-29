import pytz
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from app.database.all_requests.stock import get_active_stock_products
from app.database.all_requests.transactions import balance_transactions_number_today, were_stock_transactions

# меню сессии
async def report_menu(outlet_id, report):
    today = datetime.now(pytz.timezone('Europe/Chisinau'))
    
    inline_keyboard = []

    # количество транзакций по указанию остатка должно быть равно количеству товаров с нулевым 
    button_text = ''
    stock_data = await get_active_stock_products(outlet_id)
    # проверяем в первую очередь били ли транзакции за день с товаром, если не было то проверяем баланс для отображения
    # если транзакции не было, то вовдим если баланс больше нуля, если транзакция была, то выводим в любом случае
    # таким образом будут выведены все товары, с которыми была или могла быть проведена транзакция
    stock_data = [stock for stock in stock_data if await were_stock_transactions(stock['stock_id'],
                                                                                 today,
                                                                                 ['balance'])
                                                or  stock['stock_qty'] != 0]
    
    transactions_number = await balance_transactions_number_today(outlet_id)
    
    if len(stock_data) == transactions_number:
        button_text = ' ✅'

    inline_keyboard.append([InlineKeyboardButton(text=f'🧮 Остатки товаров{button_text}', callback_data='outlet:balance')])
    
    # проверяем наличие указанного количества чеков
    button_text = ''
    purchases = report['purchases']
    if not purchases is None:
        button_text = ' ✅'
            
    inline_keyboard.append([InlineKeyboardButton(text=f'🧾 Количество чеков{button_text}', callback_data='outlet:report_menu:purchases')])
    
    # проверяем наличие указанной выручки
    button_text = ''
    revenue = report['revenue']
    if not revenue is None:
        button_text = ' ✅'
        
    inline_keyboard.append([InlineKeyboardButton(text=f'💵 Сумма выручки{button_text}', callback_data='outlet:report_menu:revenue')])
    
    # проверяем наличие указанного примечания
    button_text = ''      
    note = report['note']
    if not note is None:
        button_text = ' ✅'

    inline_keyboard.append([InlineKeyboardButton(text=f'✍️ Примечание{button_text}', callback_data='outlet:report_menu:note')])
    
    button_text = ''
    inline_keyboard.append([InlineKeyboardButton(text='◀️ Назад', callback_data='outlet:back'),
                            InlineKeyboardButton(text='☑️ Отправить', callback_data='outlet:report_menu:send_report')])
    
    return  InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# кнопка отмены
cancel_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:report_menu')]

])

# подтвердить создание отчета
confirm_report = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:report_menu'),
    InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:report_menu:send_report:confirm')]
])
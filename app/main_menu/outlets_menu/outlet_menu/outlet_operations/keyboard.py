import pytz
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from app.database.all_requests.transactions import were_stock_transactions
from app.database.all_requests.stock import get_stock_product


# Меню операций
operations_menu = InlineKeyboardMarkup(inline_keyboard=[
    # [InlineKeyboardButton(text='💸 Расчет по продажам', callback_data='outlet:selling')],
    [InlineKeyboardButton(text='🧮 Расчет по остаткам', callback_data='outlet:balance')],
    # [InlineKeyboardButton(text='🐓 Возврат средств', callback_data='otlet:return')],
    # [InlineKeyboardButton(text='💰 Указать выручку', callback_data='otlet:revenue')], # эти две операции относятся к 
    [InlineKeyboardButton(text='◀️ Назад', callback_data='outlet:back')]
])



def selling(added_products):
    inline_keyboard = []
    
    upper_buttons = []
    upper_buttons.append(InlineKeyboardButton(text='➕ Добавить товар', callback_data='outlet:selling:add_product'))
    if len(added_products) != 0:
        upper_buttons.append(InlineKeyboardButton(text='✍🏻 Изменить товар', callback_data='outlet:selling:correct_piece'))
    
    inline_keyboard.append(upper_buttons)
    
    lower_buttons = []
    if len(added_products) != 0:
        lower_buttons.append(InlineKeyboardButton(text='🧮 Расчитать', callback_data='outlet:selling:calculate'))
    lower_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:selling:cancel'))
    
    inline_keyboard.append(lower_buttons)
        
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


selling_cancel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:selling'),
    InlineKeyboardButton(text='❌ Подтвердить выход', callback_data='outlet:operations')]
])


# меню выбора товара для покупки
def choose_product_selling(stock_data: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_items = stock_data[start:end]
    
    for current_item in current_items:
        product_name = current_item['product_name']
        stock_qty = current_item['stock_qty']
        product_unit = current_item['product_unit']
        
        if product_unit != 'кг':
            stock_qty = round(stock_qty)
        
        text = f"{product_name} - {stock_qty} {product_unit}"
        callback_data = f"outlet:selling:product_id_{current_item['product_id']}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:selling:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:selling:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:selling'))
    
    if end < len(stock_data):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:selling:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:selling:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# для меню покупки товара
selling_product = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:selling:add_product')]
])


# меню выбора продукта для корректировки веса его кусков
async def choose_product_correct_product(outlet_id: int, added_products: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    added_products = added_products[start:end]

    for added_product in added_products:
        stock = await get_stock_product(outlet_id, added_product)
        product_name = stock['product_name']
        text = f"{product_name}"
        callback_data = f"outlet:selling:choose_product:product_id_{added_product}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:selling:choose_product:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:selling:choose_product:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:selling'))
    
    if end < len(added_products):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:selling:choose_product:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:selling:choose_product:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# меню выбора куска для корректировки его веса
def choose_selling_product_correct_piece(added_pieces: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    pieces = added_pieces[start:end]

    for i in range(len(pieces)):
        text = f"{pieces[i]}"
        callback_data = f"outlet:selling:correct_piece:piece_id_{i}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:selling:correct_piece:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:selling:correct_piece:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:selling:correct_piece'))
    
    if end < len(added_pieces):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:selling:correct_piece:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:selling:correct_piece:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# подтверждение сощдания транзакции на продажу продкутов
selling_confirm = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:selling'),
        InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:selling:confirm')]
    ])


# меню выбора товара для указания остатка
async def choose_product_balance(stock_data: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_items = stock_data[start:end]
    
    for current_item in current_items:
        product_name = current_item['product_name']
        stock_qty = current_item['stock_qty']
        product_unit = current_item['product_unit']
        stock_id = current_item['stock_id']
        
        if product_unit != 'кг':
            stock_qty = round(stock_qty)
        
        text = f"{product_name} - {stock_qty} {product_unit}"
        
        date_time = datetime.now(pytz.timezone("Europe/Chisinau"))
        transaction_types = ['balance']
        
        check_flag = await were_stock_transactions(stock_id, date_time, transaction_types)
        if check_flag:
            text += ' ✅'
        callback_data = f"outlet:balance:product_id_{current_item['product_id']}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:balance:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:balance:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:back'))
    
    if end < len(stock_data):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:balance:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:balance:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# для меню расчета по остатку
def balance_product(added_pieces, from_callback, check_flag=False):
    inline_keyboard = []
    upper_buttons = []
    lower_buttons = []
    
    if len(added_pieces) != 0:
        upper_buttons.append(InlineKeyboardButton(text='🗑 Удалить кусок', callback_data='outlet:balance:correct_piece'))
        lower_buttons.append(InlineKeyboardButton(text='🧮 Расчитать', callback_data='outlet:balance:calculate'))
        lower_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:balance:cancel'))
    else:
        if from_callback is None:
            lower_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:balance:back'))
        elif from_callback == 'outlet:control:transactions':
            lower_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:control:transactions:back'))
    
    if check_flag and from_callback in None:
        upper_buttons.append(InlineKeyboardButton(text='☠️ Откатить', callback_data='outlet:balance:rollback'))
    
    inline_keyboard.append(upper_buttons)
    
    inline_keyboard.append(lower_buttons)
        
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

# для меню расчета по остатку
def cancel_balance_product(product_id, from_callback):
    if from_callback is None:
        callback_text = f'outlet:balance:back'
    elif from_callback == 'outlet:control:transactions':
        callback_text = f'outlet:control:transactions:back'
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:balance:product_id_{product_id}'),
        InlineKeyboardButton(text='❌ Подтвердить выход', callback_data=callback_text)]
    ])


# для меню расчета по остатку
def confirm_balance_product(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:balance:product_id_{product_id}'),
        InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:balance:confirm')]
    ])


# меню выбора куска для корректировки его веса
def choose_product_correct_piece(product_id: int, added_pieces: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    pieces = added_pieces[start:end]

    for i in range(len(pieces)):
        text = f"{pieces[i]}"
        callback_data = f"outlet:balance:correct_piece:piece_id_{i}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:balance:correct_piece:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:balance:correct_piece:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:balance:product_id_{product_id}'))
    
    if end < len(added_pieces):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:balance:correct_piece:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:balance:correct_piece:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# отмена отката последней транзакции
def cancel_balance_rollback(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:balance:product_id_{product_id}')]
    ])
    
    
# отмена отката последней транзакции
def confirm_balance_rollback(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🗑 Подтвердить', callback_data=f'outlet:balance:rollback:confirm'),
        InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:balance:product_id_{product_id}')]
    ])
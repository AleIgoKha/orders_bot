from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Меню операций
operations_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💸 Продажа', callback_data='outlet:selling')],
    [InlineKeyboardButton(text='🧮 Расчет по остаткам', callback_data='outlet:balance')],
    # [InlineKeyboardButton(text='🐓 Возврат средств', callback_data='otlet:return')],
    # [InlineKeyboardButton(text='💰 Указать выручку', callback_data='otlet:revenue')], # эти две операции относятся к 
    [InlineKeyboardButton(text='◀️ Назад', callback_data='outlet:back')]
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
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:operations'))
    
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
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:selling')]
])


# меню выбора товара для указания остатка
def choose_product_balance(stock_data: list, page: int = 1, products_per_page: int = 8):
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
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:operations'))
    
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
def balance_product(added_pieces):
    inline_keyboard = []
    
    if len(added_pieces) != 0:
        inline_keyboard.append([InlineKeyboardButton(text='✍🏻 Удалить кусок', callback_data='outlet:balance:correct_piece')])
    
    inline_keyboard.append([InlineKeyboardButton(text='🧮 Расчитать', callback_data='outlet:balance:calculate'),
                    InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:balance:cancel')])
        
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

# для меню расчета по остатку
def cancel_balance_product(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:balance:product_id_{product_id}'),
        InlineKeyboardButton(text='❌ Подтвердить выход', callback_data='outlet:balance')]
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
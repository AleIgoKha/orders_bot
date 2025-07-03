from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Меню запасов
stock_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='➕ Пополнение', callback_data='outlet:replenishment')],
    [InlineKeyboardButton(text='➖ Списание', callback_data='outlet:writeoff')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='outlet:back')]
])


# выбор продукта для пополнения
def choose_product_replenishment(stock_data: list, page: int = 1, products_per_page: int = 8):
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
        callback_data = f"outlet:replenishment:product_id_{current_item['product_id']}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    additional_buttons = []
    
    additional_buttons.append(InlineKeyboardButton(text='➕ Добавить товар', callback_data='outlet:replenishment:add_product'))
    
    product_keyboard.row(*additional_buttons)
    
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:replenishment:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:replenishment:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:stock'))
    
    if end < len(stock_data):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:replenishment:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:replenishment:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()



# выбор продукта для добавления
def choose_product_add(products: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_products = products[start:end]
    
    for product in current_products:
        text = f"{product.product_name} - {product.product_price} р/{product.product_unit}"
        callback_data = f"outlet:replenishment:add_product:product_id_{product.product_id}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
       
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:replenishment:add_product:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:replenishment:add_product:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:replenishment'))
    
    if end < len(products):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:replenishment:add_product:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:replenishment:add_product:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# Подтверждение добавления товара в запасы торговой точки
add_product = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:replenishment:add_product:confirm')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:replenishment:add_product')]
])

# для меню пополнения
def replenish_product(added_pieces):
    inline_keyboard = []
    upper_buttons = []
    lower_buttons = []
    
    if len(added_pieces) != 0:
        upper_buttons.append(InlineKeyboardButton(text='🗑 Удалить кусок', callback_data='outlet:replenishment:correct_piece'))
        lower_buttons.append(InlineKeyboardButton(text='🧮 Рассчитать', callback_data='outlet:replenishment:calculate'))
    
    lower_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:replenishment:cancel'))
    
    inline_keyboard.append(upper_buttons)
    
    inline_keyboard.append(lower_buttons)
        
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# меню подтверждения пополнения
def confirm_replenishment_product(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:replenishment:product_id_{product_id}'),
        InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:replenishment:confirm')]
    ])
    
    
# меню отмены пополнения запасов товара
def cancel_replenishment_product(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:replenishment:product_id_{product_id}'),
        InlineKeyboardButton(text='❌ Подтвердить выход', callback_data='outlet:replenishment')]
    ])


# выбор продукта для изменения
def choose_product_writeoff(stock_data: list, page: int = 1, products_per_page: int = 8):
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
        callback_data = f"outlet:writeoff:product_id_{current_item['product_id']}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:writeoff:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:writeoff:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:stock'))
    
    if end < len(stock_data):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:writeoff:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:writeoff:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# для меню списания
def writeoff_product(added_pieces):
    inline_keyboard = []
    upper_buttons = []
    lower_buttons = []
    
    if len(added_pieces) != 0:
        upper_buttons.append(InlineKeyboardButton(text='🗑 Удалить кусок', callback_data='outlet:writeoff:correct_piece'))
        lower_buttons.append(InlineKeyboardButton(text='🧮 Рассчитать', callback_data='outlet:writeoff:calculate'))
    
    lower_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:writeoff:cancel'))
    
    inline_keyboard.append(upper_buttons)
    
    inline_keyboard.append(lower_buttons)
        
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# Подтверждение списания запасов
confirm_writeoff = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:writeoff:confirm')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:writeoff')]
])


# Подтверждение удаления товара из запасов
confirm_delete = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:stock:delete:confirm')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:writeoff')]
])

# меню подтверждения пополнения
def confirm_writeoff_product(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:writeoff:product_id_{product_id}'),
        InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:writeoff:confirm')]
    ])
    
    
# меню отмены пополнения запасов товара
def cancel_writeoff_product(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:writeoff:product_id_{product_id}'),
        InlineKeyboardButton(text='❌ Подтвердить выход', callback_data='outlet:writeoff')]
    ])


# меню выбора куска для корректировки его веса
def choose_replenishment_product_correct_piece(product_id: int, added_pieces: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    pieces = added_pieces[start:end]

    for i in range(len(pieces)):
        text = f"{pieces[i]}"
        callback_data = f"outlet:replenishment:correct_piece:piece_id_{i}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:replenishment:correct_piece:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:replenishment:correct_piece:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:replenishment:product_id_{product_id}'))
    
    if end < len(added_pieces):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:replenishment:correct_piece:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:replenishment:correct_piece:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# меню выбора куска для корректировки его веса
def choose_writeoff_product_correct_piece(product_id: int, added_pieces: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    pieces = added_pieces[start:end]

    for i in range(len(pieces)):
        text = f"{pieces[i]}"
        callback_data = f"outlet:writeoff:correct_piece:piece_id_{i}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:writeoff:correct_piece:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:writeoff:correct_piece:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:writeoff:product_id_{product_id}'))
    
    if end < len(added_pieces):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:writeoff:correct_piece:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:writeoff:correct_piece:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()
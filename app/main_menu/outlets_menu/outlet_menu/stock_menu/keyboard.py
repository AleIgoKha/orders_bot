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
        product_name = current_item.product.product_name
        stock_qty = current_item.stock_qty
        product_unit = current_item.product.product_unit
        
        if product_unit != 'кг':
            stock_qty = round(stock_qty)
        
        text = f"{product_name} - {stock_qty} {product_unit}"
        callback_data = f"outlet:replenishment:product_id_{current_item.product.product_id}"
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

# кнопка для отмены пополнения
replenish_product = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:replenishment')]
])


# выбор продукта для изменения
def choose_product_writeoff(stock_data: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_items = stock_data[start:end]
    
    for current_item in current_items:
        product_name = current_item.product.product_name
        stock_qty = current_item.stock_qty
        product_unit = current_item.product.product_unit
        
        if product_unit != 'кг':
            stock_qty = round(stock_qty)
        
        text = f"{product_name} - {stock_qty} {product_unit}"
        callback_data = f"outlet:writeoff:product_id_{current_item.product.product_id}"
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


# кнопка для отмены списания и списания всего
writeoff_product = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:writeoff')]
])



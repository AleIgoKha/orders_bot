from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Меню запасов
stock_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='➕ Пополнение', callback_data='outlet:replenishment')],
    [InlineKeyboardButton(text='➖ Списание', callback_data='outlet:writeoff')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='outlet:back')]
])


# выбор продукта для изменения
def choose_product_replenishment(products: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_products = products[start:end]
    
    for product in current_products:
        text = f"{product.product_name} - {product.product_price} р/{product.product_unit}"
        callback_data = f"outlet:replenishment:product_id_{product.product_id}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    additional_buttons = []
    
    additional_buttons.append(InlineKeyboardButton(text='➕ Добавить товар', callback_data='outlet:replenishment:new_product'))
    
    product_keyboard.row(*additional_buttons)
    
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:replenishment:product_page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:replenishment:product_page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:stock'))
    
    if end < len(products):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:replenishment:product_page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:replenishment:product_page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder



products_menu = InlineKeyboardMarkup(inline_keyboard=[

    [InlineKeyboardButton(text='📙 Просмотр товаров', callback_data='list_product')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='main:menu')]
])


product_confirmation = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='product_confirmation')],
    [InlineKeyboardButton(text='✍ Изменить', callback_data='add_product')],
    [InlineKeyboardButton(text='❌ Отменить создание товара', callback_data='products:list')]
])

product_units = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='кг', callback_data='кг')],
    [InlineKeyboardButton(text='шт.', callback_data='шт.')],
    [InlineKeyboardButton(text='❌ Отменить создание товара', callback_data='products:list')]
])

product_cancellation = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отменить создание товара', callback_data='products:list')]
])


list_product_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧀 Новый товар', callback_data='add_product')],
    [InlineKeyboardButton(text='✍ Изменить товар', callback_data='change_product_data')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='main:menu')]
])

# выбор продукта для изменения
def choose_product(products: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_products = products[start:end]
    
    for product in current_products:
        text = f"{product.product_name} - {product.product_price} р/{product.product_unit}"
        callback_data = f"products_menu_product_id_{product.product_id}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"products_menu_product_page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="products_menu_product_page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='products:list'))
    
    if end < len(products):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"products_menu_product_page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="products_menu_product_page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()

# меню изменения товара
change_product_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧀 Изменить название', callback_data='change_product_name')],
    [InlineKeyboardButton(text='📐 Изменить единицу измерения', callback_data='change_product_unit')],
    [InlineKeyboardButton(text='💰 Изменить стоимость', callback_data='change_product_price')],
    [InlineKeyboardButton(text='🗑 Удалить товар', callback_data='delete_product')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='products:list')]
])

# кнопка назад при имзенения параметра товара
back_to_change_product_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='back_to_change_product_menu')]
])

# 
confirm_delete_product = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Удалить товар', callback_data='confirm_delete_product')],
    [InlineKeyboardButton(text='❌ Отменить удаление', callback_data='back_to_change_product_menu')]
])

change_product_units = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='кг', callback_data='кг')],
    [InlineKeyboardButton(text='шт.', callback_data='шт.')],
    [InlineKeyboardButton(text='❌ Отменить создание товара', callback_data='back_to_change_product_menu')]
])
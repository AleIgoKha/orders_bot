from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main_menu_button = InlineKeyboardButton(text='🏠 В главное меню', callback_data='main_menu')


products_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧀 Создать товар', callback_data='add_product')],
    [InlineKeyboardButton(text='✍ Изменить товар', callback_data='amend_product')],
    [InlineKeyboardButton(text='📙 Просмотр товаров', callback_data='list_product')],
    [main_menu_button]
])

product_cancellation_button = InlineKeyboardButton(text='❌ Отмена', callback_data='products')


product_confirmation = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='product_confirmation')],
    [InlineKeyboardButton(text='✍ Изменить', callback_data='add_product')],
    [product_cancellation_button]
])

product_units = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='кг', callback_data='кг')],
    [InlineKeyboardButton(text='шт.', callback_data='шт.')],
    [product_cancellation_button]
])

product_cancellation = InlineKeyboardMarkup(inline_keyboard=[
    [product_cancellation_button],
])
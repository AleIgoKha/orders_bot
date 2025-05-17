from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Товары', callback_data='products_menu')],
    [InlineKeyboardButton(text='Заказы', callback_data='orders')],
    # [InlineKeyboardButton(text='Статистика', callback_data='stats')]
])
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Товары', callback_data='products')],
    [InlineKeyboardButton(text='Заказы', callback_data='orders')],
    [InlineKeyboardButton(text='Статистика', callback_data='stats')]
])

main_menu_button = InlineKeyboardButton(text='В главное меню', callback_data='main_menu')

stats_menu = InlineKeyboardMarkup(inline_keyboard=[
    [main_menu_button]
])
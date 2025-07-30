from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='➕ Новый заказ', callback_data='main:new_order')],
    [InlineKeyboardButton(text='🗂 Сессии', callback_data='sessions:choose_session')],
    [InlineKeyboardButton(text='🧀 Продукты', callback_data='products:list')]
])
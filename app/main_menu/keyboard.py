from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='➕ Новый заказ', callback_data='main:new_order')],
    [InlineKeyboardButton(text='🗂 Меню сессий', callback_data='sessions:choose_session')],
    [InlineKeyboardButton(text='🧀 Продукты', callback_data='products:list')],
    # [InlineKeyboardButton(text='Настройки', callback_data='settings:menu')],
    # [InlineKeyboardButton(text='Статистика', callback_data='stats:menu')]
])
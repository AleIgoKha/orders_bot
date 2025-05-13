from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


back_stats_orders_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='◀️ Назад', callback_data='back_from_order_stats')]
    ])
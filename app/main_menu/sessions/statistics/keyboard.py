from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


stats_orders_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='◀️ Назад', callback_data='back_from_order_stats')]
    ])
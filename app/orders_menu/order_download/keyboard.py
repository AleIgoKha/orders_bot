from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


session_downloads_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⬇️ Скачать список заказов', callback_data='download_orders')],
    [InlineKeyboardButton(text='⬇️ Скачать статистику', callback_data='stats_download')],
    [InlineKeyboardButton(text='◀️ Назад в меню', callback_data='back_from_order_download')]
])


back_from_order_download = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='◀️ Назад в меню', callback_data='back_from_order_download')]
])
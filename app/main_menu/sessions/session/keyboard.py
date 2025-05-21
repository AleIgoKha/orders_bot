from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


session_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📋 Создать заказ', callback_data='order_creation')],
    [InlineKeyboardButton(text='⚙️ Обработка заказов', callback_data='order_processing')],
    [InlineKeyboardButton(text='☑️ Готовые заказы', callback_data='completed_orders')],
    [InlineKeyboardButton(text='📈 Статистика сессии', callback_data='stats_orders_menu')],
    [InlineKeyboardButton(text='⬇️ Скачать данные сессии', callback_data='session_downloads')],
    [InlineKeyboardButton(text='🛠 Настройки сессии', callback_data='session_downloads')],
    [InlineKeyboardButton(text='❌ Выйти из сессии', callback_data='main:menu')]
])
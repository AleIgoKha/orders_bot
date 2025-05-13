from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import get_sessions, get_products



stats_orders_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧀 Товары', callback_data='products_stats')],
    [InlineKeyboardButton(text='📋 Заказы', callback_data='orders_stats')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='back_from_order_stats')]
    ])


back_stats_orders_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='◀️ Назад', callback_data='stats_orders_menu')]
    ])
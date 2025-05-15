from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

back_from_order_download = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='◀️ Назад в меню', callback_data='back_from_order_download')]
])
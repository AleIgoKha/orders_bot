from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Меню операций
operations_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💸 Продажа', callback_data='otlet:selling')],
    [InlineKeyboardButton(text='🧮 Ввести остаток', callback_data='otlet:balance')],
    # [InlineKeyboardButton(text='🐓 Возврат средств', callback_data='otlet:return')],
    # [InlineKeyboardButton(text='💰 Указать выручку', callback_data='otlet:revenue')], # эти две операции относятся к 
    [InlineKeyboardButton(text='◀️ Назад', callback_data='outlet:back')]
])
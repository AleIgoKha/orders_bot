from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# меню сессии
report_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧮 Остатки товаров', callback_data='outlet:balance')],
    [InlineKeyboardButton(text='🧾 Количество чеков', callback_data='outlet:report_menu:purchases')],
    [InlineKeyboardButton(text='💵 Сумма выручки', callback_data='outlet:report_menu:revenue')],
    [InlineKeyboardButton(text='✍️ Примечание', callback_data='outlet:report_menu:note')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='outlet:back'),
     InlineKeyboardButton(text='☑️ Отправить', callback_data='outlet:report_menu:send_report')]
])


# кнопка отмены
cancel_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:report_menu')]

])

# подтвердить создание отчета
confirm_report = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:report_menu'),
    InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:report_menu:send_report:confirm')]
])
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# меню сессии
outlet_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧰 Операции', callback_data='outlet:operations')],
    [InlineKeyboardButton(text='📈 Статистика', callback_data='outlet:statistics')],
    [InlineKeyboardButton(text='🛠 Настройки', callback_data='outlet:settings')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='outlets:choose_outlet')]
])


# Настройки сессии
settings_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📋 Изменить название сессии', callback_data='outlet:change_name')],
    [InlineKeyboardButton(text='📝 Изменить описание сессии', callback_data='outlet:change_descr')],
    [InlineKeyboardButton(text='🗄 Архивировать сессию', callback_data='outlet:status')],
    [InlineKeyboardButton(text='🗑 Удалить сессию', callback_data='outlet:delete_outlet')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='outlet:back')]
])


# Отмена изменения имени
cancel_change_outlet = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:settings')]
])

# Отмена изменения описания сессии или ее удаление
cancel_change_descr_outlet = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Удалить описание', callback_data='outlet:delete_descr'),
    InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:settings')]
])


# меню архивации
def change_status_keyboard(outlet_status):
    status_opt = '🗄 Архивировать'
    if outlet_status:
        status_opt = '🗃 Ввести в работу'
        
    change_status = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'{status_opt}', callback_data='outlet:change_status'),
        InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:settings')]
    ])
    
    return change_status

# отмена удаления сессии
cancel_delete_outlet = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:settings')]
])

# подтверждение удаления сессии
confirm_delete_outlet = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Подтвердить', callback_data='outlet:confirm_delete'),
    InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:settings')]
])
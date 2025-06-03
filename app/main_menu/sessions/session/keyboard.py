from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# меню сессии
session_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📋 Создать заказ', callback_data='session:new_order')],
    [InlineKeyboardButton(text='⚙️ Обработка заказов', callback_data='order_processing')],
    [InlineKeyboardButton(text='☑️ Готовые заказы', callback_data='completed_orders')],
    [InlineKeyboardButton(text='👌🏽 Выданные заказы', callback_data='session:issued_orders')],
    [InlineKeyboardButton(text='📈 Статистика сессии', callback_data='stats_orders_menu')],
    [InlineKeyboardButton(text='⬇️ Скачать данные сессии', callback_data='session_downloads')],
    [InlineKeyboardButton(text='🛠 Настройки сессии', callback_data='session:settings')],
    [InlineKeyboardButton(text='❌ Выйти из сессии', callback_data='main:menu')]
])


# Настройки сессии
settings_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📋 Изменить название сессии', callback_data='session:change_name')],
    [InlineKeyboardButton(text='📝 Изменить описание сессии', callback_data='session:change_descr')],
    [InlineKeyboardButton(text='🗄 Архивировать сессию', callback_data='session:status')],
    [InlineKeyboardButton(text='🗑 Удалить сессию', callback_data='session:delete_session')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='session:back')]
])


# Отмена изменения имени
cancel_change_session = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='session:settings')]
])

# Отмена изменения описания сессии или ее удаление
cancel_change_descr_session = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Удалить описание', callback_data='session:delete_descr'),
    InlineKeyboardButton(text='❌ Отмена', callback_data='session:settings')]
])


# меню архивации
def change_status_keyboard(session_status):
    status_opt = '🗄 Архивировать'
    if session_status:
        status_opt = '🗃 Ввести в работу'
        
    change_status = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'{status_opt}', callback_data='session:change_status'),
        InlineKeyboardButton(text='❌ Отмена', callback_data='session:settings')]
    ])
    
    return change_status

# отмена удаления сессии
cancel_delete_session = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='session:settings')]
])

# подтверждение удаления сессии
confirm_delete_session = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Подтвердить', callback_data='session:confirm_delete'),
    InlineKeyboardButton(text='❌ Отмена', callback_data='session:settings')]
])
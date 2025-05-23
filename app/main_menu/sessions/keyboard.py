from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import get_sessions


# Функция для создания клавиатуры-списка сессий с пагинацией
async def choose_session(page: int = 1, sessions_per_page: int = 8):
    sessions = await get_sessions()
    session_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * sessions_per_page
    end = start + sessions_per_page
    current_sessions = sessions[start:end]
    
    for session in current_sessions:
        text = f"{session.session_name} (0/0)"
        callback_data = f"session:session_id_{session.session_id}"
        session_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    session_keyboard.add(InlineKeyboardButton(text='➕ Новая сессия', callback_data='sessions:new_session'))
    
    session_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Более поздние", callback_data=f"session_page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='main:menu'))
    
    if end < len(sessions):
        navigation_buttons.append(
            InlineKeyboardButton(text="Более ранние ➡️", callback_data=f"session_page_{page + 1}")
        )
        
    if navigation_buttons:
        session_keyboard.row(*navigation_buttons)

    return session_keyboard.as_markup()


# Возврат в меню выбора сессии
cancel_new_session = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='sessions:choose_session')]
])


# Меню создания новой сессии
new_session_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить создание', callback_data='sessions:confirm_new_session')],
    [InlineKeyboardButton(text='✍🏻 Изменить название сессии', callback_data='sessions:change_new_session')],
    [InlineKeyboardButton(text='📝 Изменить описание сессии', callback_data='sessions:add_session_descr')],
    [InlineKeyboardButton(text='❌ Отменить создание', callback_data='sessions:confirm_cancel_new_session')]
])


# подтверждение отмены создания сессии
confirm_cancel_new_session = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Подтвердить отмену', callback_data='sessions:choose_session'),
     InlineKeyboardButton(text='🛒 Вернуться сессии', callback_data='sessions:new_session_menu')]
])


# Отмена изменений в сессии
cancel_change_session = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='sessions:new_session_menu')]
])


cancel_change_descr_session = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Удалить описание', callback_data='sessions:delete_descr')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='sessions:new_session_menu')]
])
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import get_outlets


# Функция для создания клавиатуры-списка сессий с пагинацией
async def choose_outlet(page: int = 1, outlets_per_page: int = 8):
    outlets = await get_outlets()
    outlets = [outlet for outlet in outlets if not outlet.outlet_arch]
    outlet_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * outlets_per_page
    end = start + outlets_per_page
    current_outlets = outlets[start:end]
    
    for outlet in current_outlets:
        text = f"{outlet.outlet_name}"
        callback_data = f"outlet:outlet_id_{outlet.outlet_id}"
        outlet_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        
    outlet_keyboard.adjust(1)
    
    additional_buttons = []
    
    additional_buttons.append(InlineKeyboardButton(text='➕ Новая', callback_data='outlets:new_outlet'))
    additional_buttons.append(InlineKeyboardButton(text='🗄 Архив', callback_data='outlets:archive'))
    
    outlet_keyboard.row(*additional_buttons)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlets:outlet_page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlets:outlet_page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='🏠 В главное меню', callback_data='main:menu'))
    
    if end < len(outlets):
        navigation_buttons.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"outlets:outlet_page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlets:outlet_page_edge")
        )
        
    if navigation_buttons:
        outlet_keyboard.row(*navigation_buttons)

    return outlet_keyboard.as_markup()


# Возврат в меню выбора сессии
cancel_new_outlet = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlets:choose_outlet')]
])


# Меню создания новой сессии
new_outlets_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить создание', callback_data='outlets:confirm_new_outlet')],
    [InlineKeyboardButton(text='✍🏻 Изменить название сессии', callback_data='outlets:change_new_outlet')],
    [InlineKeyboardButton(text='📝 Изменить описание сессии', callback_data='outlets:add_outlet_descr')],
    [InlineKeyboardButton(text='❌ Отменить создание', callback_data='outlets:confirm_cancel_new_outlet')]
])


# подтверждение отмены создания сессии
confirm_cancel_new_outlet = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Подтвердить отмену', callback_data='outlets:choose_outlet'),
     InlineKeyboardButton(text='◀️ Вернуться к созданию', callback_data='outlets:new_outlet_menu')]
])


# Отмена изменений в сессии
cancel_change_outlet = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlets:new_outlet_menu')]
])


cancel_change_descr_outlet = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Удалить описание', callback_data='outlets:delete_descr')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlets:new_outlet_menu')]
])


# выбор архивной сессии
async def choose_arch_outlet(page: int = 1, outlets_per_page: int = 8):
    outlets = await get_outlets()
    outlets = [outlet for outlet in outlets if outlet.outlet_arch]
    outlet_keyboard = InlineKeyboardBuilder()

    
    start = (page - 1) * outlets_per_page
    end = start + outlets_per_page
    current_outlets = outlets[start:end]
    
    for outlet in current_outlets:
        text = f"{outlet.outlet_name}"
        callback_data = f"outlet:outlet_id_{outlet.outlet_id}"
        outlet_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        
    outlet_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlets:arch_outlet_page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlets:arch_outlet_page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='🏪 В меню', callback_data='outlets:choose_outlet'))
    
    if end < len(outlets):
        navigation_buttons.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"outlets:arch_outlet_page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlets:arch_outlet_page_edge")
        )
        
    if navigation_buttons:
        outlet_keyboard.row(*navigation_buttons)

    return outlet_keyboard.as_markup()
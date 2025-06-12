from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import timezone
import pytz

from app.com_func import represent_utc_3


# выбор заказа
def choose_order(orders: int, desc: bool, page: int = 1, orders_per_page: int = 10):
    order_keyboard = InlineKeyboardBuilder()
    
    sort_text = '🔼 Сначала старые'
    callback_flag = 'asc'
    if not desc:
        orders = orders[::-1]
        sort_text = '🔽 Сначала новые'
        callback_flag = 'desc'
    
    start = (page - 1) * orders_per_page
    end = start + orders_per_page
    current_orders = orders[start:end]
    
    for order in current_orders:
        formatted_date = represent_utc_3(order.finished_datetime).strftime("%d-%m-%Y")
        
        text = f"{formatted_date} - №{order.order_number} - {order.client_name}"
        callback_data = f"issued_orders:order_id_{order.order_id}"
        order_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    order_keyboard.add(InlineKeyboardButton(text=sort_text, callback_data=f'issued_orders:sorting:{callback_flag}'))
    
    order_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"issued_orders:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="issued_orders:page_edge")
        )
        
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='session:back'))
    
    if end < len(orders):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"issued_orders:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="issued_orders:page_edge")
        )
        
    if navigation_buttons:
        order_keyboard.row(*navigation_buttons)

    return order_keyboard.as_markup()


# меню выданного заказа
issued_order = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='☑️ Изменить статус', callback_data='issued_orders:change_status')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='issued_orders:back')]
])


# меню выданного заказа
def change_status(order_id):
    change_status = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='☑️ Готовый', callback_data='issued_orders:mark_completed')],
        [InlineKeyboardButton(text='⚙️ На обработку', callback_data='issued_orders:mark_processing')],
        [InlineKeyboardButton(text='❌ Отмена', callback_data=f'issued_orders:order_id_{order_id}')]
    ])
    
    return change_status
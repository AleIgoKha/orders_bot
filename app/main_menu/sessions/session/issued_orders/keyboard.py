from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import get_orders_sorted


# выбор заказа
def choose_order(orders: int, page: int = 1, orders_per_page: int = 10):
    order_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * orders_per_page
    end = start + orders_per_page
    current_orders = orders[start:end]
    
    for order in current_orders:
        if order.issue_datetime:
            issue_datetime = order.issue_datetime
        else:
            issue_datetime = order.finished_datetime
        
        text = f"{issue_datetime.strftime("%d-%m-%Y")} - №{order.order_number} - {order.client_name}"
        callback_data = f"issued_orders:order_id_{order.order_id}"
        order_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    order_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"issued_orders:page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='session:back'))
    
    if end < len(orders):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"issued_orders:page_{page + 1}")
        )
        
    if navigation_buttons:
        order_keyboard.row(*navigation_buttons)

    return order_keyboard.as_markup()


# меню выданного заказа
issued_order = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='☑️ Изменить статус', callback_data='issued_orders:change_status')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='session:issued_orders')]
])


# меню выданного заказа
def change_status(order_id):
    change_status = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='☑️ Готовый', callback_data='issued_orders:mark_completed')],
        [InlineKeyboardButton(text='⚙️ На обработку', callback_data='issued_orders:mark_processing')],
        [InlineKeyboardButton(text='❌ Отмена', callback_data=f'issued_orders:order_id_{order_id}')]
    ])
    
    return change_status
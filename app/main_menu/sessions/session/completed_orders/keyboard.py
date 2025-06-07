from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.com_func import represent_utc_3


# # Клавиатура кнопка "Изменить" для заказа
# def change_button(order_id):
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text='✍️ Изменить', callback_data=f'{order_id}_change_order')],
#         [InlineKeyboardButton(text='👌🏽 Отметить как Выдан', callback_data=f'{order_id}_mark_issued')]
#         ])
    

# # Клавиатура кнопка "Назад в меню" для возврата из меню обработки заказов
# def last_change_button(order_id):
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text='✍️ Изменить', callback_data=f'{order_id}_change_order')],
#         [InlineKeyboardButton(text='👌🏽 Отметить как Выдан', callback_data=f'{order_id}_mark_issued')],
#         [InlineKeyboardButton(text='⬅️ Назад в меню', callback_data=f'back_from_order_completed')]
#         ])
    
    
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
        issue_datetime = represent_utc_3(order.issue_datetime)
        
        text = f"{issue_datetime.strftime("%d-%m-%Y")} - №{order.order_number} - {order.client_name}"
        callback_data = f"completed_orders:order_id_{order.order_id}"
        order_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        
    
    order_keyboard.adjust(1)
    
    additional_buttons = [InlineKeyboardButton(text='🧨 Выдать все', callback_data='completed_orders:issue_all'),
                          InlineKeyboardButton(text=sort_text, callback_data=f'completed_orders:sorting:{callback_flag}')]
    
    order_keyboard.row(*additional_buttons)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"completed_orders:page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='session:back'))
    
    if end < len(orders):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"completed_orders:page_{page + 1}")
        )
        
    if navigation_buttons:
        order_keyboard.row(*navigation_buttons)

    return order_keyboard.as_markup()


# меню готового к выдаче заказа
completed_order = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✍️ Изменить', callback_data=f'completed_orders:change_order')],
        [InlineKeyboardButton(text='👌🏽 Отметить как Выдан', callback_data='completed_orders:change_status')],
        [InlineKeyboardButton(text='⬅️ Назад в меню', callback_data=f'completed_orders:back')]
        ])


# подтвердить выдачу заказа
def change_status(order_id):
    change_status = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🌞 Сегодня', callback_data='completed_orders:mark_issued'),
        InlineKeyboardButton(text='❌ Отмена', callback_data=f'completed_orders:order_id_{order_id}')]
    ])
    return change_status


# подтвердить выдачу заказа
def confirm_change_status(order_id):
    change_status = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Подтвердить', callback_data='completed_orders:mark_issued'),
        InlineKeyboardButton(text='❌ Отмена', callback_data=f'completed_orders:order_id_{order_id}')]
    ])
    return change_status


issue_all = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data=f'completed_orders:back')]
    ])


issue_all_confirmation = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='completed_orders:mark_issued_all'),
    InlineKeyboardButton(text='❌ Отмена', callback_data=f'completed_orders:back')]
    ])

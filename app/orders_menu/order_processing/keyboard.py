from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import get_products

# Клавиатура меню сессии
session_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📋 Создать заказ', callback_data='order_creation')],
    [InlineKeyboardButton(text='⚙ Обработка заказов', callback_data='order_processing')],
    [InlineKeyboardButton(text='🗂 Готовые заказы', callback_data='completed_orders')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='orders')]
])

# Клавиатура кнопка "Обработать" для заказа
def process_button(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⚙ Обработка', callback_data=f'process_order_{order_id}')]
        ])

# Клавиатура кнопка "Назад в меню" для возврата из меню обработки заказов
def last_process_button(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⚙ Обработка', callback_data=f'process_order_{order_id}')],
        [InlineKeyboardButton(text='❌ Назад в меню', callback_data=f'back_from_order_processing')]
        ])
    

# Клавиатура для меню обработки заказа
order_processing_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📋 Управление данными заказа', callback_data='change_order_data')],
    [InlineKeyboardButton(text='⚙ Обработка заказа', callback_data='process_order')],
    [InlineKeyboardButton(text='✅ Закончить обработку', callback_data='complete_order')],
    [InlineKeyboardButton(text='❌ Назад к списку', callback_data='order_processing')]
])


# Клавиатура для выбора обрабатываемого продукта
def choose_item_processing(items_data_list: list, page: int = 1, items_per_page: int = 8):
    item_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * items_per_page
    end = start + items_per_page
    current_items = items_data_list[start:end]
    
    for item in current_items:
        text = f"{item['item_name']} - " \
                f"Заказано: {int(item['item_qty'] * 1000)} {item['item_unit'][-1]} - " \
                f"Взвешено: {int(item['item_qty_fact'] * 1000)} {item['item_unit'][-1]}"
        callback_data = f"item_id_{item['item_id']}"
        item_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    item_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"item_page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'back_process_order_menu'))
    
    if end < len(items_data_list):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"item_page_{page + 1}")
        )
        
    if navigation_buttons:
        item_keyboard.row(*navigation_buttons)

    return item_keyboard.as_markup()


# Кнопка для возвращения к списку товаров на обработку
back_to_order_proccessing_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='process_order')]
])
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import get_products


# Клавиатура кнопка "Изменить" для заказа
def change_button(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Изменить', callback_data=f'{order_id}_change_order')]
        ])

# Клавиатура кнопка "Назад в меню" для возврата из меню обработки заказов
def last_change_button(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Изменить', callback_data=f'{order_id}_change_order')],
        [InlineKeyboardButton(text='Назад в меню', callback_data=f'back_from_order_changing')]
        ])









# Клавиатура для меню обработки заказа
order_processing_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Управление данными заказа', callback_data='change_order_data')],
    [InlineKeyboardButton(text='Обработка заказа', callback_data='process_order')],
    [InlineKeyboardButton(text='Закончить обработку', callback_data='complete_order')],
    [InlineKeyboardButton(text='Назад к списку', callback_data='order_processing')]
])


# Клавиатура для выбора обрабатываемого продукта
def choose_item_processing(items_data_list: list, page: int = 1, items_per_page: int = 2):
    item_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * items_per_page
    end = start + items_per_page
    current_items = items_data_list[start:end]
    
    for item in current_items:
        text = f"{item['item_name']}\n" \
                f"Заказано: {item['item_qty']} {item['item_unit']}\n" \
                f"Взвешено: {item['item_qty_fact']} {item['item_unit']}"
        callback_data = f"item_id_{item['item_id']}"
        item_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    item_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"item_page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='Назад', callback_data=f'back_process_order_menu'))
    
    if end < len(items_data_list):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"item_page_{page + 1}")
        )
        
    if navigation_buttons:
        item_keyboard.row(*navigation_buttons)

    return item_keyboard.as_markup()


# Кнопка для возвращения к списку товаров на обработку
back_to_order_proccessing_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Отменить', callback_data='process_order')]
])


# Клавиатура для управления данными о заказе
change_order_data_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Изменить имя клиента', callback_data='change_client_name')],
    [InlineKeyboardButton(text='Изменить заказанное количество товара', callback_data='change_item_qty')],
    [InlineKeyboardButton(text='Изменить взвешенное количество товара', callback_data='change_item_qty_fact')],
    [InlineKeyboardButton(text='Добавить новый товар', callback_data='add_new_item')],
    [InlineKeyboardButton(text='Удалить товар', callback_data='delete_item')],
    [InlineKeyboardButton(text='УДАЛИТЬ ЗАКАЗ', callback_data='delete_order')],
    [InlineKeyboardButton(text='Назад', callback_data='back_process_order_menu')]
])

back_to_change_order_data = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='change_order_data')],
])

# Клавиатура для выбора продукта для изменения его данных о заказанном количестве товара
def choose_change_item_qty(items_data_list: list, page: int = 1, items_per_page: int = 2):
    item_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * items_per_page
    end = start + items_per_page
    current_items = items_data_list[start:end]
    
    for item in current_items:
        text = f"{item['item_name']} " \
                f"Заказано: {item['item_qty']} {item['item_unit']} " \
                f"Взвешено: {item['item_qty_fact']} {item['item_unit']}"
        callback_data = f"change_item_qty_{item['item_id']}"
        item_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    item_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"change_item_qty_page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='Назад', callback_data=f'change_order_data'))
    
    if end < len(items_data_list):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"change_item_qty_page_{page + 1}")
        )
        
    if navigation_buttons:
        item_keyboard.row(*navigation_buttons)

    return item_keyboard.as_markup()


# Меню выбора товара для добавления в существующий заказ
async def choose_add_item(page: int = 1, products_per_page: int = 2):
    products = await get_products()
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_products = products[start:end]
    
    for product in current_products:
        text = f"{product.product_name} - {product.product_price} р/{product.product_unit}"
        callback_data = f"add_item_id_{product.product_id}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"add_item_page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='Назад', callback_data='change_order_data'))
    
    if end < len(products):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"add_item_page_{page + 1}")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# Подтверждаем удаление товара из заказа

confirm_delete_item = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Подтвердить', callback_data='confirm_delete_item')],
    [InlineKeyboardButton(text='Назад', callback_data='change_order_data')]
])

confirm_delete_order = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Подтвердить', callback_data='confirm_delete_order')],
    [InlineKeyboardButton(text='Назад', callback_data='change_order_data')]
])

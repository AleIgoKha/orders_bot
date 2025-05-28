from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import get_sessions, get_products


session_cancellation = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='sessions:choose_session')]
])

issuing_method = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🤝 Самовывоз', callback_data='Самовывоз')],
    [InlineKeyboardButton(text='🚗 Доставка по городу', callback_data='Доставка по городу')],
    [InlineKeyboardButton(text='🚚 Доставка почтой', callback_data='Доставка почтой')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='sessions:choose_session')]
])

session_confirmation = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='session_confirmation')],
    [InlineKeyboardButton(text='✍🏻 Изменить', callback_data='new_session')],
    [InlineKeyboardButton(text='❌ Отменить создание сессии', callback_data='sessions:choose_session')]
])


# Функция для создания клавиатуры-списка сессий с пагинацией
async def choose_session(page: int = 1, sessions_per_page: int = 8):
    sessions = await get_sessions()
    session_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * sessions_per_page
    end = start + sessions_per_page
    current_sessions = sessions[start:end]
    
    for session in current_sessions:
        text = f"{session.session_date.strftime('%d-%m-%Y')} - {session.session_place} - {session.session_method}"
        callback_data = f"session_id_{session.session_id}"
        session_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    session_keyboard.add(InlineKeyboardButton(text='➕ Новая сессия', callback_data='new_session'))
    
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



session_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📋 Создать заказ', callback_data='order_creation')],
    [InlineKeyboardButton(text='⚙️ Обработка заказов', callback_data='order_processing')],
    [InlineKeyboardButton(text='☑️ Готовые заказы', callback_data='completed_orders')],
    [InlineKeyboardButton(text='📈 Статистика сессии', callback_data='stats_orders_menu')],
    [InlineKeyboardButton(text='⬇️ Скачать данные сессии', callback_data='session_downloads')],
    [InlineKeyboardButton(text='❌ Выйти из сессии', callback_data='main:menu')]
])





back_to_change_order_data = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='change_order_data')]
])

back_to_change_item_data = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='change_item_data')]
])

# Клавиатура для управления данными заказа
change_order_data_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧀 Данные о товарах', callback_data='change_item_data')],
    [InlineKeyboardButton(text='👤 Изменить имя клиента', callback_data='change_client_name')],
    [InlineKeyboardButton(text='📉 Изменить размер скидки', callback_data='change_order_disc')],
    [InlineKeyboardButton(text='📝 Изменить комментарий', callback_data='change_note')],
    [InlineKeyboardButton(text='🗑 Удалить заказ', callback_data='delete_order')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_process_order_menu')]
])

# Клавиатура для управления данными обработанного заказа
change_completed_order_data_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧀 Управление данными о товарах', callback_data='change_item_data')],
    [InlineKeyboardButton(text='👤 Изменить имя клиента', callback_data='change_client_name')],
    [InlineKeyboardButton(text='💸 Изменить размер скидки', callback_data='change_order_disc')],
    [InlineKeyboardButton(text='📝 Изменить комментарий', callback_data='change_note')],
    [InlineKeyboardButton(text='☑ Изменить статус заказа', callback_data='change_status')],
    [InlineKeyboardButton(text='🗑 Удалить заказ', callback_data='delete_order')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='completed_orders')]
])

# Меню изменения данных товаров
change_item_data = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧀 Добавить товар в заказ', callback_data='add_new_item')],
    [InlineKeyboardButton(text='🗑 Удалить товар из заказа', callback_data='delete_item')],
    [InlineKeyboardButton(text='📤 Указать товары с вак. уп.', callback_data='change_add_item_vacc')],
    [InlineKeyboardButton(text='📥 Убрать товары с вак. уп.', callback_data='change_delete_item_vacc')],
    [InlineKeyboardButton(text='📋 Изменить заказанное количество товара', callback_data='change_item_qty')],
    [InlineKeyboardButton(text='⚖ Изменить взвешенное количество товара', callback_data='change_item_qty_fact')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='change_order_data')]
])


# Клавиатура для выбора продукта для изменения его данных о заказанном количестве товара
def choose_change_item_qty(items_data_list: list, page: int = 1, items_per_page: int = 8):
    item_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * items_per_page
    end = start + items_per_page
    current_items = items_data_list[start:end]
    
    for item in current_items:
        item_unit = item['item_unit']
        item_qty = item['item_qty']
        item_qty_fact = item['item_qty_fact']
        # переводим в граммы
        if item_unit == 'кг':
            item_qty = item_qty * 1000
            item_qty_fact = item_qty_fact * 1000
            item_unit = item_unit[-1]
            
        text = f"{item['item_name']} - " \
                f"Заказано: {int(item_qty)} {item_unit} - " \
                f"Взвешено: {int(item_qty_fact)} {item_unit}"
        callback_data = f"change_item_qty_{item['item_id']}"
        item_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    item_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"change_item_qty_page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'change_item_data'))
    
    if end < len(items_data_list):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"change_item_qty_page_{page + 1}")
        )
        
    if navigation_buttons:
        item_keyboard.row(*navigation_buttons)

    return item_keyboard.as_markup()


# Меню выбора товара для добавления в существующий заказ
async def choose_add_item(page: int = 1, products_per_page: int = 8):
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
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='change_item_data'))
    
    if end < len(products):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"add_item_page_{page + 1}")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# Подтверждаем удаление товара из заказа
confirm_delete_item = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Удалить товар', callback_data='confirm_delete_item')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='change_item_data')]
])

# Подтверждаем удаление заказа
confirm_delete_order = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Удалить заказ', callback_data='confirm_delete_order')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='change_order_data')]
])

# Просим подтвердить изменение статуса заказа
confirm_change_status = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='☑ Подтвердить', callback_data='confirm_change_status')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='change_order_data')]
])


confirm_change_note = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='change_order_data'),
     InlineKeyboardButton(text='🗑 Удалить комментарий', callback_data='note_removal_from_order')]
])\
    

# выбираем продукт для вакуумации
async def choose_change_product_vacc(products: dict, from_callback: str, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_products_list = list(products.keys())[start:end]
    current_products = {product:products[product] for product in current_products_list}
    
    for product, product_data in current_products.items():
        product_unit = product_data['item_unit']
        item_qty = product_data['item_qty']
        item_qty_fact = product_data['item_qty_fact']
        if product_unit == 'кг':
            product_unit = product_unit[-1]
            item_qty = item_qty * 1000
            item_qty_fact = item_qty_fact * 1000
        
        text = f"{product_data['item_name']} - Заказано: {int(item_qty)} {product_unit} - Взвешено: {int(item_qty_fact)} {product_unit}"
        callback_data = f"change_vacc_item_{product.split('_')[-1]}"
        
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    else:
        if from_callback == 'change_add_item_vacc':
            text = '🧨 Добавить всем продукам 🧨'
            product_keyboard.add(InlineKeyboardButton(text=text, callback_data='change_vacc_all'))
        elif from_callback == 'change_delete_item_vacc':
            text = '🧨 Удалить всем продукам 🧨'
            product_keyboard.add(InlineKeyboardButton(text=text, callback_data='change_vacc_all'))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"change_vacc_page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='change_item_data'))

    if end < len(products):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"change_vacc_page_{page + 1}")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()



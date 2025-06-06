from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import get_sessions, get_products, get_orders
from calendar import monthrange
from datetime import date



back_to_change_order_data = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='change_order_data')]
])

back_to_change_item_data = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='change_item_data')]
])

# Клавиатура для управления данными заказа
def change_order_menu(from_menu, order_id):
    part_1 = [
    [InlineKeyboardButton(text='🧀 Данные о товарах', callback_data='change_item_data')],
    [InlineKeyboardButton(text='🛍 Изменить параметры выдачи', callback_data='change_order:issue_menu')],
    [InlineKeyboardButton(text='👤 Изменить имя клиента', callback_data='change_order_name')],
    [InlineKeyboardButton(text='☎️ Изменить телефон клиента', callback_data='change_order_phone')],
    [InlineKeyboardButton(text='📂 Изменить сессию заказа', callback_data='change_order:change_session')],
    [InlineKeyboardButton(text='🤑 Изменить размер скидки', callback_data='change_order_disc')],
    [InlineKeyboardButton(text='📝 Изменить комментарий', callback_data='change_note')]
    ]
    
    if from_menu == 'completed_orders':
        part_1.append([InlineKeyboardButton(text='☑ Изменить статус заказа', callback_data='change_status')])
    
    part_2 = [
    [InlineKeyboardButton(text='🗑 Удалить заказ', callback_data='delete_order')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data=f'{from_menu}:order_id_{order_id}')]
    ]
    
    inline_keyboard = part_1 + part_2
    
    change_order_menu = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return change_order_menu


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


# изменяем номер телефона
change_phone = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Удалить телефон', callback_data='change_order:delete_phone'),
    InlineKeyboardButton(text='❌ Отмена', callback_data='change_order_data')]
])


# изменяем номер телефона
change_session = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='change_order_data')]
])


# Функция для создания клавиатуры-списка сессий с пагинацией
async def choose_session(page: int = 1, sessions_per_page: int = 8):
    sessions = await get_sessions()
    sessions = [session for session in sessions if not session.session_arch]
    session_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * sessions_per_page
    end = start + sessions_per_page
    current_sessions = sessions[start:end]
    
    for session in current_sessions:
        orders = await get_orders(session_id=session.session_id)
        orders_number = len([order for order in orders if not order[0].order_completed])
        text = f"{session.session_name} ({orders_number})"
        callback_data = f"change_order:change_session_id_{session.session_id}"
        session_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        
    session_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"change_order:change_session_page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='change_order_data'))
    
    if end < len(sessions):
        navigation_buttons.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"change_order:change_session_page_{page + 1}")
        )
        
    if navigation_buttons:
        session_keyboard.row(*navigation_buttons)

    return session_keyboard.as_markup()


# меню изменения параметров выдачи заказа
def issue_menu(issue_method, issue_datetime):
    inline_keyboard = [
        [InlineKeyboardButton(text='🚚 Метод выдачи', callback_data='change_order:issue_method')]
    ]
    
    if issue_method != 'Самовывоз':
         inline_keyboard += [
            [InlineKeyboardButton(text='💲 Стоимость выдачи', callback_data='change_order:delivery_price')],
            [InlineKeyboardButton(text='📍 Адрес выдачи', callback_data='change_order:issue_place')]
        ]
    
    inline_keyboard += [[InlineKeyboardButton(text='📅 Дата выдачи', callback_data='change_order:issue_date')]]
    
    if issue_datetime:
        inline_keyboard += [[InlineKeyboardButton(text='⌚️ Время выдачи', callback_data='change_order:issue_time')]]
        
    inline_keyboard += [[InlineKeyboardButton(text='◀️ Назад', callback_data='change_order_data')]]
    
    issue_menu = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    
    return issue_menu


# выбор способо выдачи
def issue_method_kb(issue_method):
    method_button = InlineKeyboardButton(text='🛍 Самовывоз', callback_data='change_order:self_pickup')
    
    if issue_method == 'Самовывоз':
        method_button = InlineKeyboardButton(text="🚚 Доставка", callback_data='change_order:delivery')
        
    issue_method_kb = InlineKeyboardMarkup(inline_keyboard=[
        [method_button,
        InlineKeyboardButton(text='❌ Отмена', callback_data='change_order:issue_menu')]
    ])
    
    return issue_method_kb


# отмена изменения стоимости доставки
# в зависимости от меню есть возможность обнулить стоимость доставки
def cancel_delivery_price(from_menu):
    inline_keyboard = []
    
    if from_menu != 'completed_orders':
        inline_keyboard.append(InlineKeyboardButton(text='🤖 Автоматически', callback_data='change_order:delete_delivery_price'))
    
    inline_keyboard.append(InlineKeyboardButton(text='❌ Отмена', callback_data='change_order:issue_menu'))
        
    cancel_delivery_price = InlineKeyboardMarkup(inline_keyboard=[inline_keyboard])
    
    return cancel_delivery_price


# отмена изменения адресса
cancel_delivery_address = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Удалить адресс', callback_data='change_order:delete_address'),
    InlineKeyboardButton(text='❌ Отмена', callback_data='change_order:issue_menu')]
])


# Календарь для выбора даты
def create_calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard representing a calendar for the given year and month.
    """
    keyboard = []
    months = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь"}
    keyboard.append([InlineKeyboardButton(text=f'{year} {months[month]}', callback_data="ignore")])
    days_of_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard.append([InlineKeyboardButton(text=day, callback_data="ignore") for day in days_of_week])

    first_day = date(year, month, 1)
    first_day_weekday = first_day.weekday()  # Monday is 0, Sunday is 6
    days_in_month = monthrange(year, month)[1]
    day_counter = 1

    for week in range(6):  # Up to 6 weeks can be displayed
        row = []
        for day_of_week in range(7):
            if week == 0 and day_of_week < first_day_weekday:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            elif day_counter > days_in_month:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                day_text = str(day_counter)
                callback_data = f"change_order:delivery:date:{year}:{month}:{day_counter}"
                row.append(InlineKeyboardButton(text=day_text, callback_data=callback_data))
                day_counter += 1
        keyboard.append(row)
        if day_counter > days_in_month:
            break
    
    additional_buttons = [
        InlineKeyboardButton(text='🗑 Очистить дату', callback_data='change_order:delete_date')
    ]
    
    keyboard.append(additional_buttons)

    navigation_buttons = [
        InlineKeyboardButton(text="⬅️ Ранее", callback_data=f"change_order:delivery:prev:{year}:{month}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="change_order:issue_menu"),
        InlineKeyboardButton(text="➡️ Позднее", callback_data=f"change_order:delivery:next:{year}:{month}"),
    ]
    keyboard.append(navigation_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# отмена времени доставки
cancel_delivery_time = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Очистить время', callback_data='change_order:delete_time'),
    InlineKeyboardButton(text='❌ Отмена', callback_data='change_order:issue_menu')]
])
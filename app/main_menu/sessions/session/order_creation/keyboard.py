from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from calendar import monthrange
from datetime import date

from app.database.requests import get_products, get_sessions, get_orders




def client_phone_cancelation(back_opt):
    client_phone_cancelation = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='▶️ Пропустить', callback_data=f'new_order:skip_phone'),
        InlineKeyboardButton(text='❌ Отмена', callback_data=f'{back_opt}')]
    ])
    return client_phone_cancelation

def client_name_cancelation(back_opt):
    client_name_cancelation = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отмена', callback_data=f'{back_opt}')]
    ])
    return client_name_cancelation


# меню создания заказа
new_order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧀 Добавить товар', callback_data='new_order:add_product')],
    [InlineKeyboardButton(text='📤 Добавить вакуумную упаковку', callback_data='add_vacc_to_order')],
    [InlineKeyboardButton(text='🛍 Выдача заказа', callback_data='new_order:add_delivery')],
    [InlineKeyboardButton(text='✍ Изменить заказ', callback_data='new_order:change_order')],
    [InlineKeyboardButton(text='✅ Сохранить заказ', callback_data='save_order')],
    [InlineKeyboardButton(text='❌ Отменить создание заказа', callback_data=f'confirm_order_cancelation')]
])


# отмена стоимости доставки
def cancel_delivery_price(issue_method):
    method_button = InlineKeyboardButton(text='🛍 Самовывоз', callback_data='new_order:self_pickup')
    skip_button = InlineKeyboardButton(text='▶️ Пропустить', callback_data='new_order:delivery')
    
    if issue_method == 'Самовывоз':
        method_button = InlineKeyboardButton(text="🚚 Доставка", callback_data='new_order:delivery')
        skip_button = InlineKeyboardButton(text='▶️ Пропустить', callback_data='new_order:self_pickup')
        
    cancel_delivery_price = InlineKeyboardMarkup(inline_keyboard=[
        [method_button],
        [skip_button,
        InlineKeyboardButton(text='❌ Отмена', callback_data='new_order:menu')]
    ])
                                                 
    return cancel_delivery_price


# отмена адресса доставки
cancel_delivery_address = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Очистить адресс', callback_data='new_order:delete_address')],
    [InlineKeyboardButton(text='📅 К дате', callback_data='new_order:delivery_date'),
    InlineKeyboardButton(text='🛑 Завершить', callback_data='new_order:menu')]
])


# отмена времени доставки
cancel_delivery_time = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🗑 Очистить время', callback_data='new_order:delete_time'),
    InlineKeyboardButton(text='🛑 Завершить', callback_data='new_order:menu')]
])


# Календарь для выбора даты
def create_calendar_keyboard(year: int, month: int, issue_datetime: dict) -> InlineKeyboardMarkup:
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
                callback_data = f"new_order:delivery:date:{year}:{month}:{day_counter}"
                row.append(InlineKeyboardButton(text=day_text, callback_data=callback_data))
                day_counter += 1
        keyboard.append(row)
        if day_counter > days_in_month:
            break
    
    additional_buttons = [
        InlineKeyboardButton(text='🗑 Очистить дату', callback_data='new_order:delete_date')
    ]
    if issue_datetime:
        additional_buttons.append(InlineKeyboardButton(text='⌚️ К времени', callback_data='new_order:skip_date'))
    
    
    keyboard.append(additional_buttons)

    navigation_buttons = [
        InlineKeyboardButton(text="⬅️ Ранее", callback_data=f"new_order:delivery:prev:{year}:{month}"),
        InlineKeyboardButton(text="🛑 Завершить", callback_data="new_order:menu"),
        InlineKeyboardButton(text="➡️ Позднее", callback_data=f"new_order:delivery:next:{year}:{month}"),
    ]
    keyboard.append(navigation_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# выбор продукта
async def choose_product(page: int = 1, products_per_page: int = 8):
    products = await get_products()
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_products = products[start:end]
    
    for product in current_products:
        text = f"{product.product_name} - {product.product_price} р/{product.product_unit}"
        callback_data = f"product_id_{product.product_id}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"product_page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='new_order:menu'))
    
    if end < len(products):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"product_page_{page + 1}")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# 
change_order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👤 Изменить имя клиента', callback_data='new_order:change_name')],
    [InlineKeyboardButton(text='☎️ Изменить телефон клиента', callback_data='new_order:change_phone')],
    [InlineKeyboardButton(text='⚖️ Изменить количество продукта', callback_data='change_product')],
    [InlineKeyboardButton(text='📤 Удалить вакуумную упаковку', callback_data='delete_vacc')],
    [InlineKeyboardButton(text='📝 Комментарий к заказу', callback_data='add_note')],
    [InlineKeyboardButton(text='📉 Применить скидку', callback_data='disc_all')],
    [InlineKeyboardButton(text='📂 Изменить сессию', callback_data='new_order:change_session')],
    [InlineKeyboardButton(text='⬅️ Назад', callback_data='new_order:menu')]
])


# выбор продукта для изменения
async def change_product_keyboard(products: dict, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_products_list = list(products.keys())[start:end]
    current_products = {product:products[product] for product in current_products_list}
    
    for product, product_data in current_products.items():
        product_unit = product_data['product_unit']
        if product_unit == 'кг':
            product_unit == 'г'
        
        text = f"{product_data['product_name']} - {product_data['product_qty']} {product_unit}"
        callback_data = product
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"product_data_page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='new_order:change_order'))
    
    if end < len(products):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"product_data_page_{page + 1}")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()

order_confirmation = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_order_creation'),
     InlineKeyboardButton(text='⬅️ Назад', callback_data='new_order:menu')]
])

back_to_order_changing = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⬅️ Назад', callback_data='new_order:change_order')]])

back_to_order_creation = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⬅️ Назад', callback_data='new_order:menu')]])

def confirm_order_cancelation(back_opt):
    confirm_order_cancelation = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Подтвердить отмену', callback_data=f'{back_opt}'),
        InlineKeyboardButton(text='🛒 Вернуться к заказу', callback_data='new_order:menu')]
    ])
    return confirm_order_cancelation

note_removal = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='new_order:change_order'),
     InlineKeyboardButton(text='🗑 Удалить комментарий', callback_data='note_removal')]
])


# выбираем продукт для вакуумации
async def choose_product_vacc(products: dict, from_callback: str, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_products_list = list(products.keys())[start:end]
    current_products = {product:products[product] for product in current_products_list}
    
    for product, product_data in current_products.items():
        product_unit = product_data['product_unit']
        if product_unit == 'кг':
            product_unit == 'г'
        
        text = f"{product_data['product_name']} - {product_data['product_qty']} {product_unit}"
        callback_data = f"add_vacc_item_{product.split('_')[-1]}"
        
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    else:
        if from_callback == 'add_vacc_to_order':
            text = '🧨 Добавить всем продукам 🧨'
            product_keyboard.add(InlineKeyboardButton(text=text, callback_data='vacc_all'))
        elif from_callback == 'delete_vacc':
            text = '🧨 Удалить всем продукам 🧨'
            product_keyboard.add(InlineKeyboardButton(text=text, callback_data='vacc_all'))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"add_vacc_page_{page - 1}")
        )
    
    if from_callback == 'add_vacc_to_order':
        navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='new_order:menu'))
    elif from_callback == 'delete_vacc':
        navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='new_order:change_order'))
    

    
    if end < len(products):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"add_vacc_page_{page + 1}")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


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
        orders_number = len([order for order in orders if not order.order_completed])
        text = f"{session.session_name} ({orders_number})"
        callback_data = f"new_order:change_session_id_{session.session_id}"
        session_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
        
    session_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"new_order:change_session_page_{page - 1}")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='new_order:menu'))
    
    if end < len(sessions):
        navigation_buttons.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data=f"new_order:change_session_page_{page + 1}")
        )
        
    if navigation_buttons:
        session_keyboard.row(*navigation_buttons)

    return session_keyboard.as_markup()












# # Временно не работает для отдельных товаров
# async def choose_add_disc(products: dict, page: int = 1, products_per_page: int = 8):
#     product_keyboard = InlineKeyboardBuilder()
    
#     start = (page - 1) * products_per_page
#     end = start + products_per_page
#     current_products_list = list(products.keys())[start:end]
#     current_products = {product:products[product] for product in current_products_list}
    
#     for product, product_data in current_products.items():
#         product_unit = product_data['product_unit']
#         if product_unit == 'кг':
#             product_unit == 'г'
        
#         text = f"{product_data['product_name']} - {product_data['product_qty']} {product_unit} - {product_data['item_disc']}%"
#         callback_data = f"add_disc_item_{product.split('_')[-1]}"
#         product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
#     else:
#         text = '🧨 Применить для всех продуктов 🧨'
#         product_keyboard.add(InlineKeyboardButton(text=text, callback_data='disc_all'))
    
#     product_keyboard.adjust(1)
    
#     navigation_buttons = []
    
#     if page > 1:
#         navigation_buttons.append(
#             InlineKeyboardButton(text="⬅️ Назад", callback_data=f"add_disc_page_{page - 1}")
#         )
    
#     navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='new_order:change_order'))
    
#     if end < len(products):
#         navigation_buttons.append(
#             InlineKeyboardButton(text="Далее ➡️", callback_data=f"add_disc_page_{page + 1}")
#         )
        
#     if navigation_buttons:
#         product_keyboard.row(*navigation_buttons)

#     return product_keyboard.as_markup()
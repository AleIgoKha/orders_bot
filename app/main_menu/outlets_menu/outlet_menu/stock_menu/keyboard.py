import pytz
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, date
from decimal import Decimal
from calendar import monthrange

from app.database.all_requests.transactions import were_stock_transactions
from app.com_func import represent_utc_3


# Меню запасов
stock_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📊 Анализ запасов', url='https://apache-superset-production.up.railway.app/superset/dashboard/p/Oj5Mrk9Jxe9/')],
    [InlineKeyboardButton(text='⚙️ Управление', callback_data='outlet:control')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='outlet:back')]
])


# выбор продукта для пополнения
async def choose_product_outlet(stock_data: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_items = stock_data[start:end]
    
    for current_item in current_items:
        product_name = current_item['product_name']
        stock_qty = current_item['stock_qty']
        product_unit = current_item['product_unit']
        stock_id = current_item['stock_id']
        
        if product_unit != 'кг':
            stock_qty = round(stock_qty)
        
        text = f"{product_name} - {stock_qty} {product_unit}"
        
        # проверяем были ли пополнения сегодня
        date_time = datetime.now(pytz.timezone("Europe/Chisinau"))
        check_flag = await were_stock_transactions(stock_id, date_time, ['replenishment'])
        if check_flag:
            text += ' ✅'
        
        callback_data = f"outlet:control:product_id_{current_item['product_id']}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    if page == 1:
        additional_buttons = []
        additional_buttons.append(InlineKeyboardButton(text='➕ Добавить товар', callback_data='outlet:control:add_product'))
        product_keyboard.row(*additional_buttons)
    
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:control:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:control:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:stock'))
    
    if end < len(stock_data):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:control:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:control:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# выбор продукта для добавления
def choose_product_add(products: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_products = products[start:end]
    
    for product in current_products:
        text = f"{product.product_name} - {product.product_price} р/{product.product_unit}"
        callback_data = f"outlet:control:add_product:product_id_{product.product_id}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
       
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:control:add_product:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:control:add_product:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:control'))
    
    if end < len(products):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:control:add_product:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:control:add_product:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# Подтверждение добавления товара в запасы торговой точки
add_product = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:control:add_product:confirm')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='outlet:control:add_product')]
])

# меню управления запасами продукта
product_control_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='➕ Пополнить', callback_data='outlet:replenishment'),
    InlineKeyboardButton(text='➖ Списать', callback_data='outlet:writeoff')],
    [InlineKeyboardButton(text='📓 Транзакции', callback_data='outlet:control:transactions'),
    InlineKeyboardButton(text='🗑 Удалить', callback_data='outlet:stock:delete')],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='outlet:control:back')]
])


# для меню пополнения
def change_stock_qty_menu(operation, added_pieces, product_id, from_callback):
    inline_keyboard = []
    upper_buttons = []
    lower_buttons = []
    
    if len(added_pieces) != 0:
        upper_buttons.append(InlineKeyboardButton(text='🗑 Удалить кусок', callback_data=f'outlet:control:correct_piece'))
        lower_buttons.append(InlineKeyboardButton(text='🧮 Расчитать', callback_data=f'outlet:{operation}:calculate'))
        lower_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:{operation}:cancel'))
    else:
        if operation == 'writeoff':
            upper_buttons.append(InlineKeyboardButton(text='🧨Списать все', callback_data=f'outlet:writeoff:all'))
        if from_callback is None:
            lower_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:control:product_id_{product_id}'))
        elif from_callback == 'outlet:control:transactions':
            lower_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:control:transactions:back'))
        
    
    inline_keyboard.append(upper_buttons)
    
    inline_keyboard.append(lower_buttons)
        
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


# меню подтверждения пополнения
confirm_replenishment_product = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:replenishment'),
        InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:replenishment:confirm')]
    ])
    
    
# меню отмены пополнения запасов товара
def cancel_replenishment_product(product_id, from_callback):
    # в зависимости от того, из какого меню пришли
    if from_callback is None:
        callback_text = f'outlet:control:product_id_{product_id}'
    elif from_callback == 'outlet:control:transactions':
        callback_text = f'outlet:control:transactions:back'
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data='outlet:replenishment'),
        InlineKeyboardButton(text='❌ Подтвердить выход', callback_data=callback_text)]
    ])


# Подтверждение удаления товара из запасов
def confirm_delete(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:stock:delete:confirm'),
        InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:control:product_id_{product_id}')]
    ])

# меню подтверждения пополнения
confirm_writeoff_product = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:writeoff'),
        InlineKeyboardButton(text='✅ Подтвердить', callback_data='outlet:writeoff:confirm')]
    ])
    
    
# меню отмены пополнения запасов товара
def cancel_writeoff_product(product_id, from_callback):
    # в зависимости от того, из какого меню пришли
    if from_callback is None:
        callback_text = f'outlet:control:product_id_{product_id}'
    elif from_callback == 'outlet:control:transactions':
        callback_text = f'outlet:control:transactions:back'
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Вернуться к операции', callback_data=f'outlet:writeoff'),
        InlineKeyboardButton(text='❌ Подтвердить выход', callback_data=callback_text)]
    ])


# меню выбора куска для корректировки его веса
def choose_correct_piece(operation: str, added_pieces: list, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    pieces = added_pieces[start:end]

    for i in range(len(pieces)):
        text = f"{pieces[i]}"
        callback_data = f"outlet:control:correct_piece:piece_id_{i}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:control:correct_piece:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:control:correct_piece:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:{operation}'))
    
    if end < len(added_pieces):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:control:correct_piece:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:control:correct_piece:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# выбор транзакции
def choose_transaction(transactions: list, product_unit: str, product_id: int, page: int = 1, products_per_page: int = 8):
    product_keyboard = InlineKeyboardBuilder()
    
    start = (page - 1) * products_per_page
    end = start + products_per_page
    current_transactions = transactions[start:end]
    
    for transaction in current_transactions:
        transaction_datetime = represent_utc_3(transaction['transaction_datetime']).strftime('%H:%M %d-%m-%Y')
        
        transaction_type_labels = {
            'balance': 'Продажа (ост.)',
            'selling': 'Продажа',
            'replenishment': 'Пополнение',
            'writeoff': 'Списание'
        }
        
        try:
            transaction_type = transaction_type_labels[transaction['transaction_type']]
        except KeyError:
            transaction_type = None
            
        product_qty = transaction['product_qty']
        
        
        product_amended = product_unit
        if product_unit == 'кг':
            product_qty = product_qty * Decimal(1000)
            product_amended = 'г'
            
        transaction_id = transaction['transaction_id']
        
        text = f"{transaction_datetime} - {transaction_type} - {round(product_qty)} {product_amended}"
        callback_data = f"outlet:control:transactions:transaction_id_{transaction_id}"
        product_keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    product_keyboard.adjust(1)
       
    if page == 1:
        additional_buttons = []
        additional_buttons.append(InlineKeyboardButton(text='➕ Создать транзакцию', callback_data='outlet:control:transactions:new_transaction'))
        product_keyboard.row(*additional_buttons)
    
    navigation_buttons = []
    
    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"outlet:control:transactions:page_{page - 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="outlet:control:transactions:page_edge")
        )
    
    navigation_buttons.append(InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:control:product_id_{product_id}'))
    
    if end < len(transactions):
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"outlet:control:transactions:page_{page + 1}")
        )
    else:
        navigation_buttons.append(
            InlineKeyboardButton(text="Далее ➡️", callback_data="outlet:control:transactions:page_edge")
        )
        
    if navigation_buttons:
        product_keyboard.row(*navigation_buttons)

    return product_keyboard.as_markup()


# меню транзакции
transaction_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Назад', callback_data=f'outlet:control:transactions:back')]
    ])


# Календарь для выбора даты
def transaction_calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
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
          
                if day_counter == date.today().day and month == date.today().month and year == date.today().year:
                    day_text = '🌞'

                callback_data = f"outlet:control:transactions:date:{year}:{month}:{day_counter}"
                row.append(InlineKeyboardButton(text=day_text, callback_data=callback_data))
                day_counter += 1
        keyboard.append(row)
        if day_counter > days_in_month:
            break

    navigation_buttons = [
        InlineKeyboardButton(text="⬅️ Ранее", callback_data=f"outlet:control:transactions:month:prev:{year}:{month}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="outlet:control:transactions:back"),
        InlineKeyboardButton(text="➡️ Позднее", callback_data=f"outlet:control:transactions:month:next:{year}:{month}"),
    ]
    keyboard.append(navigation_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# отмена создания новой транзакции
cancel_transaction_creation = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:control:transactions:back')]
])


# выбираем вид транзакции
def choose_transaction_type(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='➕ Пополнение', callback_data=f'outlet:replenishment')],
        [InlineKeyboardButton(text='➖ Списание', callback_data=f'outlet:writeoff')],
        [InlineKeyboardButton(text='🧮 Расчет по остаткам', callback_data=f'outlet:balance:product_id_{product_id}')],
        # [InlineKeyboardButton(text='💸 Расчет продажам', callback_data=f'outlet:control:transactions:back')],
        [InlineKeyboardButton(text='❌ Отмена', callback_data=f'outlet:control:transactions:back')]
    ])
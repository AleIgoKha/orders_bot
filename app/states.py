from aiogram.fsm.state import StatesGroup, State

class Product(StatesGroup):
    name = State()
    change_name = State()
    unit = State()
    price = State()
    change_price = State()
    qty = State()
    new_qty = State()
    disc = State()

class Session(StatesGroup):
    date = State()
    date_error = State()
    # with_time = State() в будущем можно будет создавать сессии с привязкой ко времени и без привязки ко времени
    place = State()
    method = State()
    
class Order(StatesGroup):
    client_name = State()
    change_client_name = State()
    delete_order = State()
    add_note = State()
    change_note = State()
    change_disc = State()
    
class Item(StatesGroup):
    item_qty_fact = State() # Количество при обработке товара
    change_item_qty = State() # Количество при изменении веса товара в заказе
    item_qty = State() # Количество при добавлении нового товара в заказ
    
class Order_Change(StatesGroup):
    client_name = State()
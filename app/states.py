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
    name = State()
    change_name = State()
    description = State()
    change_description = State()
    delete = State()
    

class Outlet(StatesGroup):
    name = State()
    change_name = State()
    description = State()
    change_description = State()
    delete = State()
    
    
class Stock(StatesGroup):
    replenishment = State()
    writeoff = State()
    selling = State()
    balance = State()
    rollback_balance = State()
    
    
class Order(StatesGroup):
    client_phone = State()
    change_client_phone = State()
    change_order_phone = State()
    client_name = State()
    change_client_name = State()
    change_order_name = State()
    delivery_price = State()
    issue_place = State()
    change_issue_place = State()
    issue_datetime = State()
    change_issue_datetime = State()
    issue_time = State()
    change_issue_time = State()
    delete_order = State()
    add_note = State()
    change_note = State()
    change_disc = State()
    finished_datetime = State()
    finished_datetime_all = State()
    
class Item(StatesGroup):
    item_qty_fact = State() # Количество при обработке товара
    change_item_qty = State() # Количество при изменении веса товара в заказе
    item_qty = State() # Количество при добавлении нового товара в заказ
      
class Stats(StatesGroup):
    date = State()
    
class Transaction(StatesGroup):
    time = State()
    rollback = State()
    
    
class Report(StatesGroup):
    purchases = State()
    revenue = State()
    note = State()
    purchases_only = State()
    revenue_only = State()
    note_only = State()
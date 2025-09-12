import os
import pytz
from datetime import datetime, timedelta
from functools import wraps
from contextlib import asynccontextmanager
from aiogram.types import Message
from aiogram.filters import Filter
from dotenv import load_dotenv


from app.database.models import async_session


load_dotenv()

admin_list = list(map(int, (os.getenv("ADMINS").split(','))))


class User(Filter):
    async def __call__(self, message: Message):
        return message.from_user.id in admin_list


# session context manager
@asynccontextmanager
async def get_session():
    async with async_session() as session:
        try:
            yield session
        finally:
            pass


# decorator factory
def with_session(commit: bool = False):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with get_session() as session:
                try:
                    result = await func(session, *args, **kwargs)
                    if commit:
                        await session.commit()
                    return result
                except Exception:
                    if commit:
                        await session.rollback()
                    raise
        return wrapper
    return decorator


# границы начала и конца дня
def get_utc_day_bounds(date_time: datetime):
    # Ensure datetime is timezone-aware in Chisinau
    
    # Если это были цифры введенные человеком
    if date_time.tzinfo is None:
        tz = pytz.timezone("Europe/Chisinau")
        date_time = tz.localize(date_time)
    
    date_time = date_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    start_of_day = date_time.astimezone(pytz.utc)
    end_of_day = start_of_day + timedelta(days=1)
    
    return start_of_day, end_of_day


# функция для локализации инпута и now()
def localize_user_input(date_time):
    """Used for naive user input: assume it's in Chisinau local time."""
    if date_time is None:
        return None
    tz = pytz.timezone("Europe/Chisinau")
    return tz.localize(date_time) if date_time.tzinfo is None else date_time.astimezone(tz)

# Фурнкция для правильного отображения времени с часовым поясом
def represent_utc_3(date_time):
    """Used for UTC datetime from DB: convert to Chisinau local time."""
    if date_time is None:
        return None
    tz = pytz.timezone("Europe/Chisinau")
    if date_time.tzinfo is None:
        date_time = pytz.utc.localize(date_time)
    return date_time.astimezone(tz)

# функция для подсчета стоимости вакуумной упаковки
def vacc_price_counter(item_vacc, qty, unit):
    if item_vacc:
        qty_gramms = qty * 1000
        if unit != 'кг':
            vacc_price = 5 * qty
        elif qty == 0:
            vacc_price = 0
        elif 0 < qty_gramms:
            vacc_price = (qty_gramms * 2) / 100
    else:
        vacc_price = 0
    
    return vacc_price


# Функция группирует данные полученные из запроса
def group_orders_items(orders_items):
    order_id = 0
    orders_items_data = []
    for order, item in orders_items:
        if order_id != order.order_id:
            order_id = order.order_id
            if item != None:
                orders_items_data.append({'order_number': order.order_number,
                                        'client_name': order.client_name,
                                        'order_id': order.order_id,
                                        'order_completed': order.order_completed,
                                        'order_note': order.order_note,
                                        'order_disc': order.order_disc,
                                        'client_phone': order.client_phone,
                                        'issue_method': order.issue_method,
                                        'issue_place': order.issue_place,
                                        'issue_datetime': order.issue_datetime,
                                        'delivery_price': order.delivery_price,
                                        'order_text': order.order_text,
                                        'order_issued': order.order_issued,
                                        f'item_{item.item_id}': {
                                            'item_id': item.item_id,
                                            'item_name': item.item_name,
                                            'item_unit': item.item_unit,
                                            'item_price': item.item_price,
                                            'item_qty': item.item_qty,
                                            'item_qty_fact': item.item_qty_fact,
                                            'item_disc': item.item_disc,
                                            'item_vacc': item.item_vacc
                                        }})
            else:
                orders_items_data.append({'order_number': order.order_number,
                                        'client_name': order.client_name,
                                        'order_id': order.order_id,
                                        'order_completed': order.order_completed,
                                        'order_note': order.order_note,
                                        'order_disc': order.order_disc,
                                        'client_phone': order.client_phone,
                                        'issue_method': order.issue_method,
                                        'issue_place': order.issue_place,
                                        'issue_datetime': order.issue_datetime,
                                        'delivery_price': order.delivery_price,
                                        'order_text': order.order_text,
                                        'order_issued': order.order_issued})
        else:
            orders_items_data[-1][f'item_{item.item_id}'] = {
                                    'item_id': item.item_id,
                                    'item_name': item.item_name,
                                    'item_unit': item.item_unit,
                                    'item_price': item.item_price,
                                    'item_qty': item.item_qty,
                                    'item_qty_fact': item.item_qty_fact,
                                    'item_disc': item.item_disc,
                                    'item_vacc': item.item_vacc
                                }
    return orders_items_data

# формирует сообщение для меню заказа и изменения заказа
def order_text(order_items_data):
    text = f'📋 <b>ЗАКАЗ №{order_items_data['order_number']}</b>\n\n'
    
    text += f'👤 Имя клиента - <b>{order_items_data['client_name']}</b>\n'
    
    if order_items_data['client_phone']:
        text += f'☎️ Номер телефона - <b>{order_items_data['client_phone']}</b>\n'
    
    items_list = [item for item in order_items_data.keys() if item.startswith('item_')]
    total_price = 0
    
    if items_list: # Проверяем пуст ли заказ
        for item in items_list:
            item_name = order_items_data[item]['item_name']
            item_price = float(order_items_data[item]['item_price'])
            item_qty = float(order_items_data[item]['item_qty'])
            item_unit = order_items_data[item]['item_unit']
            item_qty_fact = float(order_items_data[item]['item_qty_fact'])
            item_vacc = order_items_data[item]['item_vacc']
            
            if item_vacc:
                item_vacc = ' (вак. уп.)'
            else:
                item_vacc = ''
                
            text += f'\n🧀 <b>{item_name}{item_vacc}</b>\n'
            
            if item_unit == 'кг': # Переводим килограмы в граммы
                text += f'Заказано - <b>{int(item_qty * 1000)} {item_unit[-1]}</b>\n' \
                        f'Взвешено - <b>{int(item_qty_fact * 1000)} {item_unit[-1]}</b>\n'
            else:
                text += f'Заказано - <b>{int(item_qty)} {item_unit}</b>\n' \
                        f'Взвешено - <b>{int(item_qty_fact)} {item_unit}</b>\n'
            
            # считаем стоимость вакуума
            vacc_price = vacc_price_counter(item_vacc,
                                            item_qty_fact,
                                            item_unit)

            item_price = round(item_qty_fact * item_price + vacc_price, 2)
            total_price += item_price
            
            text += f'Стоимость - <b>{item_price} р</b>\n'
                
    else:
        text += '\n<b>Заказ пуст 🤷‍♂️</b>\n'
        
    
    issue_method = order_items_data['issue_method']
    issue_place = order_items_data['issue_place']
    issue_place = order_items_data['issue_place']
    delivery_price = order_items_data['delivery_price']
    issue_datetime = order_items_data['issue_datetime']
    
    if issue_method:
        text += f'\n🛍 Метод выдачи - <b>{issue_method}</b>\n'
    
    issue_opt = 'выдачи'
    if issue_method != 'Самовывоз':
        issue_opt = 'доставки'
        if delivery_price == None:
            if total_price >= 300:
                delivery_price = 0
            else:
                delivery_price = 20
        
        text += f'💲 Стоимость доставки - <b>{int(delivery_price)} руб</b>\n'
    else:
        delivery_price = 0
    
    if issue_place:
        text += f'📍 Место доставки - <b>{issue_place}</b>\n'
        
    if issue_datetime:
        issue_datetime = represent_utc_3(issue_datetime)
        
        text += f'📅 Дата {issue_opt} - <b>{issue_datetime.day:02d}-{issue_datetime.month:02d}-{issue_datetime.year}</b>\n'
        if any((issue_datetime.hour, issue_datetime.minute)):
            text += f'⌚️ Время {issue_opt} - <b>{issue_datetime.hour:02d}:{issue_datetime.minute:02d}</b>\n'
    
    
    order_disc = order_items_data['order_disc']
    if order_disc > 0:
        disc = f' (Скидка - {order_disc}% - {round(total_price * order_disc / 100, 2)} р)'
    else:
        disc = ''
    
    text += f'\n🧾 <b>К ОПЛАТЕ</b> - <b>{round(total_price * ((100 - order_disc) / 100) + int(delivery_price), 2)} р</b>{disc}\n'
    order_note = order_items_data['order_note']
    if order_note:
        text += f'\n<b>📝 Комментарий к заказу</b>\n{order_note}'  
    return text
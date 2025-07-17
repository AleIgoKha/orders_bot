from app.database.models import async_session, Product, Session, Order, Item, Outlet, Stock

from sqlalchemy import select, update, desc, asc, func, delete, cast, Integer, extract
from sqlalchemy.orm import joinedload
from decimal import Decimal
from datetime import datetime
from app.com_func import get_utc_day_bounds


def connection(func):
    async def inner(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return inner


@connection
async def add_product(session, product_data):
    session.add(Product(product_name=product_data['product_name'],
                        product_unit=product_data['product_unit'],
                        product_price=product_data['product_price']))
    await session.commit()


@connection
async def add_session(session, session_data):
    session.add(Session(**session_data))
    await session.commit()
    
    
@connection
async def add_outlet(session, outlet_data):
    session.add(Outlet(**outlet_data))
    await session.commit()    


@connection
async def add_order(session, order_data, session_id):
    await session.execute(
        select(Order.order_id)
        .where(Order.session_id == session_id)
        .with_for_update()
    )
    
    order_number = await session.execute(
        select(func.coalesce(func.max(Order.order_number), 0) + 1)
        .where(Order.session_id == session_id)
    )
    
    order_data['order_number'] = order_number.scalar_one()
    
    new_order = Order(**order_data)
    session.add(new_order)
    await session.commit()
    await session.refresh(new_order)
    return new_order.order_id


@connection
async def add_order_items(session, items_data):
    items = [
        Item(order_id=item_data['order_id'],
            item_name=item_data['product_name'],
            item_unit=item_data['product_unit'],
            item_price=item_data['product_price'],
            item_qty=Decimal(item_data['product_qty']) if item_data['product_unit'] == 'шт.' else  (Decimal(item_data['product_qty']) / 1000), # переводим граммы в килограммы
            # item_qty_fact=0, # проверить когда буду переделывать базу данных, можно ли переделать
            item_disc=item_data['item_disc'],
            item_vacc=item_data['item_vacc']
        )
        for item_data in items_data]
    
    session.add_all(items)
    await session.commit()


@connection
async def get_sessions(session):
    result = await session.scalars(select(Session).order_by(asc(Session.session_name)))
    return result.all()


@connection
async def get_outlets(session):
    result = await session.scalars(select(Outlet).order_by(asc(Outlet.outlet_name)))
    return result.all()


@connection
async def get_session(session, session_id):
    order_session = await session.scalar(select(Session).where(Session.session_id == session_id))
    return order_session


@connection
async def get_outlet(session, outlet_id):
    outlet_data = await session.scalar(select(Outlet).where(Outlet.outlet_id == outlet_id))
    return outlet_data


@connection
async def get_session_by_name(session, session_name):
    order_session = await session.scalar(select(Session).where(Session.session_name == session_name))
    return order_session


@connection
async def get_products(session):
    result = await session.scalars(select(Product).order_by(asc(Product.product_name)))
    return result.all()


@connection
async def get_product(session, product_id):
    product = await session.scalar(select(Product).where(Product.product_id == product_id))
    return product


@connection
async def get_orders_items(session, session_id):
    orders_data = await session.execute(select(Order, Item).outerjoin(Item, Order.order_id == Item.order_id) \
                                                            .where(Order.session_id == session_id) \
                                                            .order_by(desc(Order.order_number)))
    
    
    return orders_data.all()

# получаем всю информацию по заказу
@connection
async def get_order_items(session, order_id):
    order_data = await session.execute(select(Order, Item).outerjoin(Item, Order.order_id == Item.order_id) \
                                                            .where(Order.order_id == order_id) \
                                                            .order_by(asc(Order.order_number)))
    
    
    return order_data.all()


# получаем только товары одного заказа
@connection
async def get_items(session, order_id):
    item_data = await session.scalars(select(Item).where(Item.order_id == order_id))
    
    return item_data.all()


@connection
async def get_item(session, item_id):
    item_data = await session.scalar(select(Item).where(Item.item_id == item_id))
    
    return item_data


@connection
async def get_order(session, order_id):
    order_data = await session.scalar(select(Order).where(Order.order_id == order_id))
    
    return order_data

@connection
async def get_orders(session, session_id):
    order_data = await session.scalars(select(Order).where(Order.session_id == session_id))
    
    return order_data.all()



# выводим выданные заказы по дате выдачи или без нее
@connection
async def get_orders_by_date(session, session_id, issued, date_time: datetime=None):
    if not date_time is None:
        start, end = get_utc_day_bounds(date_time)
    
    
    stmt = select(Order).where(Order.session_id == session_id)
    
    if issued:
        if date_time:
            stmt = stmt.where(
                Order.order_issued == True,
                Order.finished_datetime >= start,
                Order.finished_datetime < end
            )
        else:
            stmt = stmt.where(Order.order_issued == True,
                              Order.finished_datetime.isnot(None))
    else:
        if date_time:
            stmt = stmt.where(
                Order.order_issued == False,
                Order.creation_datetime >= start,
                Order.creation_datetime < end
            )
        else:
            stmt = stmt.where(Order.order_issued == False,
                              Order.creation_datetime.isnot(None))
    
    issued_orders = await session.scalars(stmt)
    
    return issued_orders.all()


# для законченых заказов
@connection
async def get_orders_sorted(session, session_id):
    order_data = await session.scalars(select(Order) \
                                       .where(Order.session_id == session_id) \
                                       .order_by(desc(Order.finished_datetime),
                                                 desc(Order.issue_datetime)))
    
    return order_data.all()


@connection
async def get_not_issued_orders_sorted(session, session_id):
    order_data = await session.scalars(select(Order) \
                                       .where(Order.session_id == session_id) \
                                       .order_by(desc(func.coalesce(Order.issue_datetime, Order.creation_datetime)),
                                                 desc(Order.order_number)))
    
    return order_data.all()


# изменение данных сессии
@connection
async def change_session_data(session, session_id, session_data):
    await session.execute(update(Session).where(Session.session_id == session_id).values(session_data))
    await session.commit()


# изменение данных торговой точки
@connection
async def change_outlet_data(session, outlet_id, outlet_data):
    await session.execute(update(Outlet).where(Outlet.outlet_id == outlet_id).values(outlet_data))
    await session.commit()


@connection
async def change_item_data(session, item_id, item_data):
    await session.execute(update(Item).where(Item.item_id == item_id).values(item_data))
    await session.commit()

    
# Множественное обновление товаров, принимает два list
@connection
async def change_items_data(session, items_id, items_data):
    for i in range(len(items_id)):
        await session.execute(update(Item).where(Item.item_id == items_id[i]).values(items_data[i]))
    await session.commit()
    

@connection
async def change_order_data(session, order_id, order_data):
    await session.execute(update(Order).where(Order.order_id == order_id).values(order_data))
    await session.commit()
    
    
@connection
async def change_product_data(session, product_id, product_data):
    await session.execute(update(Product).where(Product.product_id == product_id).values(product_data))
    await session.commit()
    

# изменяем session_id для созданного заказа
@connection
async def change_order_session_id(session, order_id, old_session_id, new_session_id):
    await session.execute(
        select(Order.order_id)
        .where(Order.session_id.in_([old_session_id, new_session_id]))
        .with_for_update()
    )
    
    order_number = await session.execute(
        select(func.coalesce(func.max(Order.order_number), 0) + 1)
        .where(Order.session_id == new_session_id)
    )
    
    order_data = {'session_id': new_session_id, 'order_number': order_number.scalar_one()}
    await session.execute(update(Order).where(Order.order_id == order_id).values(order_data))
    await session.commit()
    

@connection
async def delete_items(session, item_ids):
    await session.execute(delete(Item).where(Item.item_id.in_(item_ids)))
    await session.commit()
    
@connection
async def delete_order(session, order_id):
    await session.execute(delete(Order).where(Order.order_id == order_id))
    await session.commit()
    
@connection
async def delete_product(session, product_id):
    await session.execute(delete(Product).where(Product.product_id == product_id))
    await session.commit()
    
@connection
async def delete_session(session, session_id):
    await session.execute(delete(Session).where(Session.session_id == session_id))
    await session.commit()
 
    
# удаление торговой точки
@connection
async def delete_outlet(session, outlet_id):
    await session.execute(delete(Outlet).where(Outlet.outlet_id == outlet_id))
    await session.commit()


# Подсчет статистики по товарам
@connection
async def get_session_items_stats(session, session_id):
    stmt = (
        select(
            Item.item_name,
            Item.item_unit,
            func.sum(Item.item_qty).label('total_qty'),
            func.sum(Item.item_qty_fact).label('total_qty_fact'),
            func.sum(Item.item_price * Item.item_qty).label('est_revenue'),
            func.sum(Item.item_price * Item.item_qty_fact).label('exp_revenue'),
            func.sum(cast(Item.item_vacc, Integer)).label('vacc_count')
        )
        .select_from(Order)
        .join(Item, Order.order_id == Item.order_id)
        .where(Order.session_id == session_id)
        .group_by(Item.item_name, Item.item_unit)
        .order_by(asc(Item.item_name))
    )
    
    result = await session.execute(stmt)
    return result.all()


# Подсчет статистики по товарам для заказов сессии
@connection
async def get_session_stats(session, session_id, issued, date_time: datetime=None):
    if not date_time is None:
        start, end = get_utc_day_bounds(date_time)
    
    stmt = select(
                Item.item_name,
                Item.item_unit,
                func.sum(Item.item_qty).label('total_qty'),
                func.sum(Item.item_qty_fact).label('total_qty_fact'),
                # func.sum(Item.item_price * Item.item_qty).label('est_revenue'),
                # func.sum(Item.item_price * Item.item_qty_fact).label('exp_revenue'),
                func.sum(cast(Item.item_vacc, Integer)).label('vacc_count')
            ) \
            .select_from(Order) \
            .join(Item, Order.order_id == Item.order_id)
        
        
    if issued:
        if date_time:
            stmt = stmt.where(Order.session_id == session_id,
                Order.order_issued == True,
                Order.finished_datetime >= start,
                Order.finished_datetime < end)
        else:
            stmt = stmt.where(Order.session_id == session_id,
                Order.order_issued == True,
                Order.finished_datetime.isnot(None))
    else:
        if date_time:
            stmt = stmt.where(Order.session_id == session_id,
                            Order.order_issued == False,
                            Order.creation_datetime >= start,
                            Order.creation_datetime < end)
        else:
            stmt = stmt.where(Order.session_id == session_id,
                Order.order_issued == False,
                Order.creation_datetime.isnot(None))
    
    stmt = stmt.group_by(Item.item_name, Item.item_unit) \
                .order_by(asc(Item.item_name))
    
    result = await session.execute(stmt)
    
    return result.all()



# @connection
# async def drop_table(session):
#     await session.execute(text('DROP TABLE orders'))
#     await session.commit()
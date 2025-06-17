from app.database.models import async_session, Transaction, Stock, Product
from functools import wraps
from contextlib import asynccontextmanager

from sqlalchemy import select, update, desc, asc, func, delete, cast, Integer, extract
from sqlalchemy.orm import joinedload
from decimal import Decimal
from datetime import datetime


# session context manager
@asynccontextmanager
async def get_session():
    print("📥 Opening DB session")
    async with async_session() as session:
        try:
            yield session
        finally:
            print("📤 Closing DB session")


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


# добавляем новую транзакцию 
@with_session(commit=True)
async def add_transaction(session, transaction_data):
    session.add(Transaction(**transaction_data))
    
    


# удаление транзакции
@with_session(commit=True)
async def delete_transaction(session, transaction_id):
    await session.execute(delete(Transaction).where(Transaction.transaction_id == transaction_id))

# последняя транзакция с товаром торговой точки по типу транзакции
@with_session()
async def get_last_transaction(session, outlet_id, stock_id, transaction_type):
    
    max_datetime = select(func.max(Transaction.transaction_datetime)) \
                    .where(Transaction.outlet_id == outlet_id,
                            Transaction.stock_id == stock_id,
                            Transaction.transaction_type == transaction_type)
    
    stmt = select(Transaction) \
            .where(Transaction.outlet_id == outlet_id,
                   Transaction.stock_id == stock_id,
                   Transaction.transaction_type == transaction_type,
                   Transaction.transaction_datetime == max_datetime)
    
    last_transaction = await session.scalar(stmt)
    
    if last_transaction is not None:
        last_transaction_data = {
            'transaction_id': last_transaction.transaction_id,
            'outlet_id': last_transaction.outlet_id,
            'stock_id': last_transaction.stock_id,
            'transaction_datetime': last_transaction.transaction_datetime,
            'transaction_type': last_transaction.transaction_type,
            'transaction_product_name': last_transaction.transaction_product_name,
            'product_qty': last_transaction.product_qty,
            'transaction_product_price': last_transaction.transaction_product_price
            }
    else:
        last_transaction_data = None
    
    return last_transaction_data


# проводим транзакцию пополнения товара
@with_session(commit=True)
async def transaction_replenish(session, outlet_id, product_id, product_qty):
    stock_data = await session.scalar(
        select(Stock) \
        .options(joinedload(Stock.product)) \
        .where(Stock.outlet_id == outlet_id, Stock.product_id == product_id)
    )
    
    if not stock_data:
        raise ValueError(f"Stock for product ID {product_id} at outlet ID {outlet_id} not found.")
    
    product_name = stock_data.product.product_name
    stock_id = stock_data.stock_id 
    product_price = stock_data.product.product_price
    
    transaction_data = {
        'outlet_id': outlet_id,
        'stock_id': stock_id,
        'transaction_type': 'replenishment',
        'transaction_product_name': product_name,
        'product_qty': product_qty,
        'transaction_product_price': product_price
        }
    
    # добавляем транзакцию
    session.add(Transaction(**transaction_data))
    
    # обновляем склад
    await session.execute(update(Stock)
                          .where(Stock.stock_id == stock_id)
                          .values({'stock_qty' : Stock.stock_qty + product_qty})
                    )


# проводим транзакцию списания товара
@with_session(commit=True)
async def transaction_writeoff(session, outlet_id, product_id, product_qty):
    stock_data = await session.scalar(
        select(Stock) \
        .options(joinedload(Stock.product)) \
        .where(Stock.outlet_id == outlet_id, Stock.product_id == product_id)
    )
    
    if not stock_data:
        raise ValueError(f"Stock for product ID {product_id} at outlet ID {outlet_id} not found.")
    
    product_name = stock_data.product.product_name
    stock_id = stock_data.stock_id 
    product_price = stock_data.product.product_price
    
    transaction_data = {
        'outlet_id': outlet_id,
        'stock_id': stock_id,
        'transaction_type': 'writeoff',
        'transaction_product_name': product_name,
        'product_qty': product_qty,
        'transaction_product_price': product_price
        }
    
    # добавляем транзакцию
    session.add(Transaction(**transaction_data))
    
    # обновляем склаж
    await session.execute(update(Stock)
                          .where(Stock.stock_id == stock_id)
                          .values({'stock_qty' : Stock.stock_qty - product_qty})
                    )
    
    
# проводим транзакцию списания товара и удаляем товар из торговой точки
@with_session(commit=True)
async def transaction_delete_product(session, outlet_id, product_id):
    stock_data = await session.scalar(
        select(Stock) \
        .options(joinedload(Stock.product)) \
        .where(Stock.outlet_id == outlet_id, Stock.product_id == product_id)
    )
    
    if not stock_data:
        raise ValueError(f"Stock for product ID {product_id} at outlet ID {outlet_id} not found.")
    
    product_name = stock_data.product.product_name
    stock_id = stock_data.stock_id 
    product_price = stock_data.product.product_price
    stock_qty = stock_data.stock_qty
    
    transaction_data = {
        'outlet_id': outlet_id,
        'stock_id': stock_id,
        'transaction_type': 'writeoff',
        'transaction_product_name': product_name,
        'product_qty': stock_qty,
        'transaction_product_price': product_price
        }
    
    # добавляем транзакцию
    session.add(Transaction(**transaction_data))
    
    # удаляем товар из запасов торговой точки
    await session.execute(update(Stock)
                          .where(Stock.stock_id == stock_id)
                          .values({"stock_active": False,
                                   "stock_qty": 0}))


# проводим транзакцию списания товара
@with_session(commit=True)
async def transaction_selling(session, outlet_id, product_id, product_qty):
    stock_data = await session.scalar(
        select(Stock) \
        .options(joinedload(Stock.product)) \
        .where(Stock.outlet_id == outlet_id, Stock.product_id == product_id)
    )
    
    if not stock_data:
        raise ValueError(f"Stock for product ID {product_id} at outlet ID {outlet_id} not found.")
    
    product_name = stock_data.product.product_name
    stock_id = stock_data.stock_id 
    product_price = stock_data.product.product_price
    
    transaction_data = {
        'outlet_id': outlet_id,
        'stock_id': stock_id,
        'transaction_type': 'selling',
        'transaction_product_name': product_name,
        'product_qty': product_qty,
        'transaction_product_price': product_price
        }
    
    # добавляем транзакцию
    session.add(Transaction(**transaction_data))
    
    # обновляем склаж
    await session.execute(update(Stock)
                          .where(Stock.stock_id == stock_id)
                          .values({'stock_qty' : Stock.stock_qty - product_qty})
                    )


# переделать все на возвращение словаря и одиночных значений вместо возвращения ORM объектов (хотябы новые)
# переделать мои двойные запросы на атомарные
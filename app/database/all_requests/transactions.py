from app.database.models import async_session, Transaction, Stock, Product

from sqlalchemy import select, update, desc, asc, func, delete, cast, Integer, extract
from sqlalchemy.orm import joinedload
from decimal import Decimal
from datetime import datetime

def connection(func):
    async def inner(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return inner

# добавляем новую транзакцию 
@connection
async def add_transaction(session, transaction_data):
    session.add(Transaction(**transaction_data))
                
    await session.commit()
    

# удаление транзакции
@connection
async def delete_transaction(session, transaction_id):
    
    new_transaction = await session.execute(delete(Transaction).where(Transaction.transaction_id == transaction_id))
    await session.commit()
    
    return new_transaction.transaction_id


# последняя транзакция с товаром торговой точки по типу транзакции
@connection
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
    
    last_transaction_data = await session.scalar(stmt)
    
    return last_transaction_data


# проводим транзакцию списания товара
@connection
async def transaction_writeoff(session, outlet_id, stock_id, product_id, product_qty):
    stock_data = await session.scalar(
        select(Stock, Product) \
        .join(Stock, Product.product_id == Stock.product_id) \
        .where(Stock.outlet_id == outlet_id, Product.product_id == product_id) \
        .options(joinedload(Stock.product)) \
        .order_by(asc(Product.product_name))
    )
    
    product_name = stock_data.product.product_name
    stock_qty = stock_data.stock_qty
    stock_id = stock_data.stock_id
    product_price = stock_data.product.product_price
    
    transaction_data = {
    'outlet_id': outlet_id,
    'stock_id': stock_id,
    'transaction_type': 'writeoff',
    'product_name': product_name,
    'product_qty': product_qty,
    'product_price': product_price
    }
    
    # добавляем транзакцию
    session.add(Transaction(**transaction_data))
    
    stock_data = {
        'stock_qty' : stock_qty - product_qty
    }
    
    # обновляем склаж
    await session.execute(update(Stock)
                          .where(Stock.stock_id == stock_id)
                          .values(stock_data)
                    )
                
    await session.commit()
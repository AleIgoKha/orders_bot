from app.database.models import async_session, Transaction

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
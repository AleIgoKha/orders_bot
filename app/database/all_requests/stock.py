from app.database.models import async_session, Product, Outlet, Stock

from sqlalchemy import select, update, desc, asc, func, delete, cast, Integer, extract
from sqlalchemy.orm import joinedload, aliased
from decimal import Decimal
from datetime import datetime

def connection(func):
    async def inner(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return inner


# добавление продукта в запасы торговой точки
@connection
async def add_stock(session, stock_data):
    session.add(Stock(**stock_data))
                
    await session.commit()


# данные всех продуктов торговой точки по ее id
@connection
async def get_stock_products(session, outlet_id):
    
    stock_date = await session.scalars(
        select(Stock, Product) \
        .join(Stock, Product.product_id == Stock.product_id) \
        .where(Stock.outlet_id == outlet_id) \
        .options(joinedload(Stock.product)) \
        .order_by(asc(Product.product_name))
    )
    
    return stock_date.all()


# данные всех продуктов торговой точки по ее id
@connection
async def get_out_stock_products(session, outlet_id):
    
    stmt = (
        select(Product)
        .outerjoin(
            Stock,
            (Product.product_id == Stock.product_id) &
            (Stock.outlet_id == outlet_id)
        )
        .where(
            Stock.stock_id.is_(None)
        )
        .order_by(asc(Product.product_name))
    )
    
    result = await session.scalars(stmt)
    
    return result.all()



# данные одного продукта по его id и id его торговой точки
@connection
async def get_stock_product(session, outlet_id, product_id):
    stock_data = await session.scalar(
        select(Stock, Product) \
        .join(Stock, Product.product_id == Stock.product_id) \
        .where(Stock.outlet_id == outlet_id, Product.product_id == product_id) \
        .options(joinedload(Stock.product)) \
        .order_by(asc(Product.product_name))
    )
    
    return stock_data


# изменение данных запасов продукта
@connection
async def change_stock_data(session, stock_id, stock_data):
    await session.execute(update(Stock).where(Stock.stock_id == stock_id).values(stock_data))
    await session.commit()
    
    
# Удаляем товар из запасов торговой точки
@connection
async def delete_stock(session, stock_id):
    await session.execute(delete(Stock).where(Stock.stock_id == stock_id))
    await session.commit()
from sqlalchemy import select, update, desc, asc, func, delete, cast, Integer, extract, or_
from sqlalchemy.orm import joinedload, aliased
from decimal import Decimal
from datetime import datetime
from functools import wraps
from contextlib import asynccontextmanager

from app.database.models import async_session, Product, Outlet, Stock


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


# добавление продукта в запасы торговой точки
@with_session(commit=True)
async def add_stock(session, outlet_id, product_id):
    print(product_id)
    
    
    stock_active = await session.scalar(
                                select(Stock.stock_active) \
                                .where(Stock.outlet_id == outlet_id,
                                    Stock.product_id == product_id))
    
    if stock_active is not None:
        print(stock_active)
        await session.execute(update(Stock) \
                    .where(Stock.outlet_id == outlet_id,
                        Stock.product_id == product_id) \
                    .values({'stock_active': True}))
    else:
        session.add(Stock(**{
                        'outlet_id': outlet_id,
                        'product_id': product_id
                    }))


# данные всех продуктов торговой точки по ее id
@with_session()
async def get_active_stock_products(session, outlet_id):
    
    result = await session.execute(
        select(Stock, Product) \
        .join(Stock, Product.product_id == Stock.product_id) \
        .where(Stock.outlet_id == outlet_id,
               Stock.stock_active == True) \
        .order_by(asc(Product.product_name))
    )

    rows = result.all()
    
    return [
        {
            'stock_id': stock.stock_id,
            'outlet_id': stock.outlet_id,
            'product_id': stock.product_id,
            'stock_qty': stock.stock_qty,
            'stock_active': stock.stock_active,
            'product_name': product.product_name,
            'product_unit': product.product_unit,
            'product_price': product.product_price
        }
        
        for stock, product in rows
    ]


# данные всех продуктов ВНЕ торговой точки по ее id
@with_session()
async def get_out_stock_products(session, outlet_id):
    
    stmt = select(Product) \
            .outerjoin(Stock,
                        (Product.product_id == Stock.product_id) &
                        (Stock.outlet_id == outlet_id)) \
            .where(or_(Stock.stock_id.is_(None),
                        Stock.stock_active == False)) \
            .order_by(asc(Product.product_name))
    
    out_stock_products = await session.scalars(stmt)
    
    return out_stock_products.all()



# данные одного продукта по его id и id его торговой точки
@with_session()
async def get_stock_product(session, outlet_id, product_id):
    result = await session.execute(
                                select(Stock, Product) \
                                .join(Stock, Product.product_id == Stock.product_id) \
                                .where(Stock.outlet_id == outlet_id,
                                       Product.product_id == product_id)
                            )
    
    stock, product = result.first()
    
    return {
            'stock_id': stock.stock_id,
            'outlet_id': stock.outlet_id,
            'product_id': stock.product_id,
            'stock_qty': stock.stock_qty,
            'stock_active': stock.stock_active,
            'product_name': product.product_name,
            'product_unit': product.product_unit,
            'product_price': product.product_price
        }
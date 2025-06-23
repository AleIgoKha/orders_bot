from functools import wraps
from contextlib import asynccontextmanager
from sqlalchemy import select, func
from sqlalchemy.orm import aliased

from app.database.models import async_session, Transaction, Product
from app.com_func import get_chisinau_day_bounds





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


# статистика по продажам торговой точки за день
@with_session()
async def selling_statistics(session, outlet_id, date_time):
    start, end = get_chisinau_day_bounds(date_time)

    ProductAlias = aliased(Product)

    stmt = (
        select(
            Transaction.transaction_product_name,
            func.sum(Transaction.product_qty).label('product_sum_qty'),
            ProductAlias.product_unit,
            func.sum(Transaction.transaction_product_price * Transaction.product_qty).label('product_revenue')
        )
        .join(ProductAlias, ProductAlias.product_name == Transaction.transaction_product_name)
        .where(
            Transaction.outlet_id == outlet_id,
            Transaction.transaction_type.in_(["balance", "selling"]),
            Transaction.transaction_datetime >= start,
            Transaction.transaction_datetime < end
        )
        .group_by(
            Transaction.transaction_product_name,
            ProductAlias.product_unit
        )
    )

    result = (await session.execute(stmt)).all()

    return [{
        'product_name': row.transaction_product_name,
        'product_sum_qty': row.product_sum_qty,
        'product_unit': row.product_unit,
        'product_revenue': row.product_revenue
    } for row in result]
    
    
from functools import wraps
from contextlib import asynccontextmanager
from sqlalchemy import select, update, desc, asc, func, delete, cast, Integer, extract
from sqlalchemy.orm import joinedload, aliased
from decimal import Decimal
from datetime import datetime, timedelta, time
import pytz

from app.database.models import async_session, Transaction, Stock, Product
from app.com_func import represent_utc_3


# границы начала и конца дня
def get_chisinau_day_bounds(date_time: datetime):
    tz = pytz.timezone("Europe/Chisinau")
    
    # Ensure datetime is timezone-aware in Chisinau
    if date_time.tzinfo is None:
        date_time = tz.localize(date_time)
    else:
        date_time = date_time.astimezone(tz)
    
    start_of_day = datetime.combine(date_time.date(), time.min, tzinfo=tz)
    end_of_day = start_of_day + timedelta(days=1)
    
    return start_of_day, end_of_day


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

    # Subquery to fetch the latest transaction per product within the time window
    latest_tx = (
        select(Stock)
        .where(Stock.outlet_id == outlet_id)
        .subquery()
    )

    ProductAlias = aliased(Product)

    stmt = (
        select(
            Transaction.transaction_product_name,
            func.sum(Transaction.product_qty).label('product_sum_qty'),
            ProductAlias.product_unit,
            func.sum(Transaction.transaction_product_price * Transaction.product_qty).label('product_revenue'),
            latest_tx.c.stock_qty.label('product_balance')
        )
        .join(ProductAlias, ProductAlias.product_name == Transaction.transaction_product_name)
        .join(latest_tx, latest_tx.c.stock_id == Transaction.stock_id)
        .where(
            Transaction.outlet_id == outlet_id,
            Transaction.transaction_type.in_(["balance", "selling"]),
            Transaction.transaction_datetime >= start,
            Transaction.transaction_datetime < end
        )
        .group_by(
            Transaction.transaction_product_name,
            ProductAlias.product_unit,
            latest_tx.c.stock_qty
        )
    )

    result = (await session.execute(stmt)).all()

    return [{
        'product_name': row.transaction_product_name,
        'product_sum_qty': row.product_sum_qty,
        'product_unit': row.product_unit,
        'product_revenue': row.product_revenue,
        'product_balance': row.product_balance
    } for row in result]
    
    
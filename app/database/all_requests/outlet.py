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


@with_session()
async def get_outlet(session, outlet_id):
    outlet_data = await session.scalar(select(Outlet).where(Outlet.outlet_id == outlet_id))
    return {
        'outlet_id': outlet_data.outlet_id,
        'outlet_name': outlet_data.outlet_name,
        'outlet_descr': outlet_data.outlet_descr,
        'outlet_arch': outlet_data.outlet_arch
    }
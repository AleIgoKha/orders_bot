from functools import wraps
from contextlib import asynccontextmanager
from sqlalchemy import select, update, delete, func, desc, extract
from sqlalchemy.orm import selectinload
from decimal import Decimal
from datetime import datetime

from app.database.models import async_session, Transaction, Stock, Product, Report
from app.com_func import get_utc_day_bounds


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


# сохранение отчета
@with_session(commit=True)
async def save_report(session, report_data):
    
    session.add(Report(**report_data))
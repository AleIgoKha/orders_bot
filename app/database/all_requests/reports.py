import pytz
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
    # проверяем есть ли сегодня уже отчеты, чтобы не дать создать более одного за день
    outlet_id = report_data['outlet_id']
    
    # если в данных не была указана дата, то считаем, что это сегодня
    if not 'report_datetime' in list(report_data.keys()):
        report_datetime = datetime.now(pytz.timezone('Europe/Chisinau'))
    else:
        report_datetime = report_data['report_datetime']
    
    start_of_day, end_of_day = get_utc_day_bounds(report_datetime)
    
    stmt = select(func.count(Report.report_id) > 0) \
            .where(Report.outlet_id == outlet_id,
                   Report.report_datetime >= start_of_day,
                   Report.report_datetime < end_of_day)
            
    result = await session.scalar(stmt)
    
    if not result:
        session.add(Report(**report_data))
    else:
        await session.execute(update(Report) \
                              .where(Report.report_datetime >= start_of_day,
                                     Report.report_datetime < end_of_day) \
                              .values(report_data))
    

    

# проверяем наличие отчета сегодня
@with_session()
async def is_there_report(session, outlet_id, date_time):
    start_of_day, end_of_day = get_utc_day_bounds(date_time)
    
    stmt = select(func.count(Report.report_id) > 0) \
            .where(Report.outlet_id == outlet_id,
                   Report.report_datetime >= start_of_day,
                   Report.report_datetime < end_of_day)
            
    result = await session.scalar(stmt)
            
    return result


# получаем данные об отчете
@with_session()
async def get_report_data(session, outlet_id, date_time):
    start_of_day, end_of_day = get_utc_day_bounds(date_time)
    
    stmt = select(Report) \
            .where(Report.outlet_id == outlet_id,
                   Report.report_datetime >= start_of_day,
                   Report.report_datetime < end_of_day)
            
    result = await session.scalar(stmt)
    
    return {
            'report_id': result.report_id,
            'outlet_id': result.outlet_id,
            'report_datetime': result.report_datetime,
            'report_purchases': result.report_purchases,
            'report_revenue': result.report_revenue,
            'report_note': result.report_note
        }
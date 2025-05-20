import os
from dotenv import load_dotenv
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Float, Boolean, Integer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from decimal import Decimal
from datetime import datetime


load_dotenv()
engine = create_async_engine(url=os.getenv('DB_URL'), echo=True)

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

# База данных с продукцией
class Product(Base):
    __tablename__ = 'products'
    
    product_id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String)
    product_unit: Mapped[str] = mapped_column(String(5))
    product_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    
# База данных с сессиями заказов
class Session(Base):
    __tablename__ = 'sessions'
    
    session_id: Mapped[int] = mapped_column(primary_key=True)
    session_date: Mapped[datetime] = mapped_column(DateTime)
    session_place: Mapped[str] = mapped_column(String)
    session_method: Mapped[str] = mapped_column(String(20))
    # session_name: Mapped[str] = mapped_column(String)
    
class Order(Base):
    __tablename__ = 'orders'
    
    order_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('sessions.session_id'))
    order_completed: Mapped[bool] = mapped_column(Boolean)
    client_name: Mapped[str] = mapped_column(String)
    order_number: Mapped[int] = mapped_column(Integer)
    order_note: Mapped[str | None] = mapped_column(String, nullable=True)
    order_disc: Mapped[Decimal] = mapped_column(Integer)

    
class Item(Base):
    __tablename__ = 'items'
    
    item_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.order_id'))
    item_name: Mapped[str] = mapped_column(String)
    item_unit: Mapped[str] = mapped_column(String(5))
    item_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    item_qty: Mapped[Decimal] = mapped_column(Float)
    item_qty_fact: Mapped[Decimal] = mapped_column(Float, default=0.0)
    item_disc: Mapped[Decimal] = mapped_column(Integer)
    item_vacc: Mapped[bool] = mapped_column(Boolean)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
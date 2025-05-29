import os
from dotenv import load_dotenv
from sqlalchemy import String, Numeric, ForeignKey, Boolean, Integer, DateTime, text, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from decimal import Decimal
from datetime import datetime, timezone


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
    session_name: Mapped[str] = mapped_column(String, nullable=False)
    session_descr: Mapped[str] = mapped_column(String, nullable=True)
    session_arch: Mapped[bool] = mapped_column(Boolean, default=False)
    
    orders: Mapped[list["Order"]] = relationship(back_populates="session", cascade="all, delete-orphan")

    
class Order(Base):
    __tablename__ = 'orders'
    
    order_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('sessions.session_id', ondelete="CASCADE"))
    order_number: Mapped[int] = mapped_column(Integer)
    client_phone: Mapped[str | None] = mapped_column(String, nullable=True)
    client_name: Mapped[str | None] = mapped_column(String, nullable=True)
    issue_method: Mapped[str | None] = mapped_column(String, nullable=True)
    issue_place: Mapped[str | None] = mapped_column(String, nullable=True)
    issue_datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivery_price: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("0.00"), server_default=text("0.00"))
    order_note: Mapped[str | None] = mapped_column(String, nullable=True)
    order_text: Mapped[str | None] = mapped_column(String, nullable=True)
    order_disc: Mapped[int] = mapped_column(Integer, default=0)
    order_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    order_issued: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("FALSE"))
    order_source: Mapped[str | None] = mapped_column(String, nullable=True)
    creation_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["Session"] = relationship(back_populates="orders")
    
    items: Mapped[list["Item"]] = relationship(back_populates='order', cascade="all, delete-orphan")
    
class Item(Base):
    __tablename__ = 'items'
    
    item_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.order_id', ondelete="CASCADE"))
    item_name: Mapped[str] = mapped_column(String)
    item_unit: Mapped[str] = mapped_column(String(5))
    item_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    item_qty: Mapped[Decimal] = mapped_column(Numeric(9, 3))
    item_qty_fact: Mapped[Decimal] = mapped_column(Numeric(9, 3), default=Decimal("0.000"))
    item_disc: Mapped[int] = mapped_column(Integer)
    item_vacc: Mapped[bool] = mapped_column(Boolean)
    
    order: Mapped["Order"] = relationship(back_populates='items')

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
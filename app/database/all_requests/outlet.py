from sqlalchemy import select, update, desc, asc, func, delete, cast, Integer, extract, or_
from sqlalchemy.orm import joinedload, aliased
from decimal import Decimal
from datetime import datetime
from functools import wraps
from contextlib import asynccontextmanager

from app.database.models import async_session, Product, Outlet, Stock



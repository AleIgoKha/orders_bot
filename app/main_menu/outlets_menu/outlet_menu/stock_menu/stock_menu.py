from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

import app.main_menu.outlets_menu.outlet_menu.stock_menu.keyboard as kb
from app.main_menu.main_menu import main_menu_handler 
from app.states import Outlet
from app.database.requests import get_stock_products

stock_menu = Router()


# меню операций тороговой точки
@stock_menu.callback_query(F.data == 'outlet:stock')
async def operations_menu_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='📦 <b>УПРАВЛЕНИЕ ЗАПАСАМИ</b>',
                                     reply_markup=kb.stock_menu,
                                     parse_mode='HTML')


# операция пополнения запасов на складе
@stock_menu.callback_query(F.data.startswith('outlet:replenishment:product_page_'))
@stock_menu.callback_query(F.data == 'outlet:replenishment')
async def replenishment_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('outlet:replenishment:product_page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1
    
    data = await state.get_data()
    outlet_id = data['outlet_id']
    stock_data = await get_stock_products(outlet_id)
    
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ТОВАР ДЛЯ ПОПОЛНЕНИЯ</b>',
                                     reply_markup=kb.choose_product_replenishment(products=stock_data, page=page),
                                     parse_mode='HTML')
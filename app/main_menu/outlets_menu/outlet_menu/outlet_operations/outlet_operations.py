from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

import app.main_menu.outlets_menu.outlet_menu.outlet_operations.keyboard as kb
from app.main_menu.main_menu import main_menu_handler 
from app.states import Outlet
from app.database.requests import get_outlet, change_outlet_data, delete_outlet

outlet_operations = Router()


# меню операций тороговой точки
@outlet_operations.callback_query(F.data == 'outlet:operations')
async def operations_menu_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='🧰 <b>МЕНЮ ОПЕРАЦИЙ</b>',
                                     reply_markup=kb.operations_menu,
                                     parse_mode='HTML')
    
    
# # операция пополнения запасов на складе
# @outlet_operations.callback_query(F.data == 'outlet:replenishment')
# async def replenishment_handler(callback: CallbackQuery, state: FSMContext):
    
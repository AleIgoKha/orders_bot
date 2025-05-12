from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Filter, Command
from aiogram.fsm.context import FSMContext

import app.keyboard as kb

main_menu = Router()

admin_list = [524794800, 405514693, 450847990]

class Admin(Filter):
    async def __call__(self, message: Message):
        return message.from_user.id in admin_list


# Главное меню
@main_menu.message(Admin(), Command('start'))
@main_menu.callback_query(F.data == 'main_menu')
async def main_menu_handler(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    if isinstance(event, Message):
        await event.delete()
        await event.answer(text='🏠 <b>ГЛАВНОЕ МЕНЮ</b> 🏠', reply_markup=kb.main_menu, parse_mode='HTML')
    else:
        await event.message.edit_text(text='🏠 <b>ГЛАВНОЕ МЕНЮ</b> 🏠', reply_markup=kb.main_menu, parse_mode='HTML')
        
        
##########################
# 1. При нажатии на команду старт нужно сделать очистку чата от любых других сообщений



# ###########################
# ВСЕ УЛУЧШЕНИЯ
# 2. Изменение данных сессии и удаление сессии
# 4. Проверить работу с двумя пользователями одновременно (сделать так, чтобы когда пользователь удалил один из заказов или сессию, а второй видит этот заказ или сессию, чтобы не было ошибки и чтобы был выход в меню)
# 5. Продумать как делать скидку на каждый товар по отдельности
# 6. Возможно добавить прайс для item который будет фактический и чтобы можно было менять его вне зависимости от рассчетного

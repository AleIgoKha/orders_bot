from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext


import app.main_menu.outlets_menu.keyboard as kb
from app.states import Outlet
from app.database.requests import add_outlet

outlets_menu = Router()


def outlets_menu_text(data):
    outlet_name = data['outlet_name']
    text = f'Название торговой точки - <b>{outlet_name}</b>'
    
    # Если есть описание, добавляем его
    if 'outlet_descr' in data.keys():
        outlet_descr = data['outlet_descr']
        text += f'.\n\n<b>Описание торговой точки</b>\n<blockquote expandable>{outlet_descr}</blockquote>'
        
    return text


# Открываем существующую торговую точку
@outlets_menu.callback_query(F.data.startswith('outlets:outlet_page_'))
@outlets_menu.callback_query(F.data == 'outlets:choose_outlet')
async def choose_outlet_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.data.startswith('outlets:outlet_page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1
    await callback.message.edit_text('🏪 <b>МЕНЮ ТОРГОВОЙ ТОЧКИ</b>',
                                     reply_markup=await kb.choose_outlet(page=page),
                                     parse_mode='HTML')


# Инициируем создание новой торговой точки
@outlets_menu.callback_query(F.data == 'outlets:new_outlet')
async def new_outlet_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=callback.message.message_id,
                            chat_id=callback.message.chat.id)
    await callback.message.edit_text('❓ <b>Введите название торговой точки</b>',
                                     reply_markup=kb.cancel_new_outlet,
                                     parse_mode='HTML')
    await state.set_state(Outlet.name)
    

# Принимаем название торговой точки и попадаем в меню создания торговой точки
# Просим подтвердить создание, добавить описание или отменить создание торговой точки
@outlets_menu.message(Outlet.name)
@outlets_menu.message(Outlet.description)
async def outlet_name_handler(message: Message, state: FSMContext):
    state_name = str(await state.get_state()).split(':')[-1]
    await state.set_state(None)
    
    # В зависимости от названия состояния сохраняем соответствующие данные
    if state_name == 'name':
        await state.update_data(outlet_name=message.text)
    elif state_name == 'description':
        await state.update_data(outlet_descr=message.text)
    
    # Выгружаем данные из FSM и создаем сообщение для меню
    data = await state.get_data()
    text = outlets_menu_text(data)

    message_id = data['message_id']
    chat_id = data['chat_id']

    await message.bot.edit_message_text(message_id=message_id,
                                        chat_id=chat_id,
                                        text=text,
                                        reply_markup=kb.new_outlets_menu,
                                        parse_mode='HTML')


# Возврат назад в меню создания новой торговой точки или приходи из callback
@outlets_menu.callback_query(F.data == 'outlets:new_outlet_menu')
async def new_outlets_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    # Выгружаем данные из FSM и создаем сообщение для меню
    data = await state.get_data()
    text = outlets_menu_text(data)
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.new_outlets_menu,
                                     parse_mode='HTML')


# Добавляем описание торговой точки
@outlets_menu.callback_query(F.data == 'outlets:add_outlet_descr')
async def add_outlet_descr_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    text = '❓ <b>Введите описание торговой точки</b>'
    if 'outlet_descr' in data.keys():
        outlet_descr = data['outlet_descr']
        text += f'.\n\n<b>Текущее описание торговой точки</b>\n<blockquote expandable>{outlet_descr}</blockquote>'
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.cancel_change_descr_outlet,
                                     parse_mode='HTML')
    await state.set_state(Outlet.description)


# Удаляем описание торговой точки
@outlets_menu.callback_query(F.data == 'outlets:delete_descr')
async def change_outlet_descr_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data_refreshed = {
        'message_id': data['message_id'],
        'chat_id': data['chat_id'],
        'outlet_name': data['outlet_name'],
        }
    await state.clear()
    await state.update_data(data_refreshed)
    await new_outlets_menu_handler(callback, state)


# Инициируем изменение названия торговой точки
@outlets_menu.callback_query(F.data == 'outlets:change_new_outlet')
async def change_new_outlet_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_name = data['outlet_name']
    await callback.message.edit_text(text=f'❓ <b>Введите название торговой точки.</b>\n\nТекущее название торговой точки <b>{outlet_name}</b>',
                                     reply_markup=kb.cancel_change_outlet,
                                     parse_mode='HTML')
    await state.set_state(Outlet.name)


# Сохраняем новую торговую точку
@outlets_menu.callback_query(F.data == 'outlets:confirm_new_outlet')
async def confirm_new_outlet_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_data = {
        'outlet_name': data['outlet_name'],
        'outlet_descr': data['outlet_descr'] if 'outlet_descr' in data.keys() else None
    }
    await add_outlet(outlet_data=outlet_data)
    await callback.answer(text='Торговая точка успешно создана', show_alert=True)
    await choose_outlet_handler(callback, state)
    

# Отмена создания торговой точки
@outlets_menu.callback_query(F.data == 'outlets:confirm_cancel_new_outlet')
async def confirm_new_outlet_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='⁉️ <b>Вы уверены, что хотите отменить создание торговой точки?</b>',
                                     reply_markup=kb.confirm_cancel_new_outlet,
                                     parse_mode='HTML')
    
    
# архив торговых точек
@outlets_menu.callback_query(F.data.startswith('outlets:arch_outlet_page_'))
@outlets_menu.callback_query(F.data == 'outlets:archive')
async def archive_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.data.startswith('outlets:arch_outlet_page_'):
        try:
            page = int(callback.data.split('_')[-1])
        except ValueError:
            return None
    else:
        page = 1
    await callback.message.edit_text('🗄 <b>АРХИВ ТОРГОВЫХ ТОЧЕК</b>',
                                     reply_markup=await kb.choose_arch_outlet(page=page),
                                     parse_mode='HTML')
    

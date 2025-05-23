from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext


import app.main_menu.sessions.keyboard as kb
from app.states import Session
from app.database.requests import add_session

sessions_menu = Router()


def session_menu_text(data):
    session_name = data['session_name']
    text = f'Название сессии - <b>{session_name}</b>'
    
    # Если есть описание, добавляем его
    if 'session_descr' in data.keys():
        session_descr = data['session_descr']
        text += f'.\n\n<b>Описание сессии</b>\n<blockquote expandable>{session_descr}</blockquote>'
        
    return text


# Открываем существующую сессию
@sessions_menu.callback_query(F.data.startswith('session_page_'))
@sessions_menu.callback_query(F.data == 'sessions:choose_session')
async def choose_session_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.data.startswith('session_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        page = 1
    await callback.message.edit_text('🗂 <b>МЕНЮ СЕССИЙ</b>',
                                     reply_markup=await kb.choose_session(page=page),
                                     parse_mode='HTML')


# Инициируем создание новой сессии
@sessions_menu.callback_query(F.data == 'sessions:new_session')
async def new_session_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await callback.message.edit_text('❓ <b>Введите название сессии</b>',
                                     reply_markup=kb.cancel_new_session,
                                     parse_mode='HTML')
    await state.set_state(Session.name)
    

# Принимаем название сессии и попадаем в меню создания сессии
# Просим подтвердить создание, добавить описание или отменить создание сессии
@sessions_menu.message(Session.name)
@sessions_menu.message(Session.description)
async def session_name_handler(message: Message, state: FSMContext):
    state_name = str(await state.get_state()).split(':')[-1]
    await state.set_state(None)
    
    # В зависимости от названия состояния сохраняем соответствующие данные
    if state_name == 'name':
        await state.update_data(session_name=message.text)
    elif state_name == 'description':
        await state.update_data(session_descr=message.text)
    
    # Выгружаем данные из FSM и создаем сообщение для меню
    data = await state.get_data()
    text = session_menu_text(data)

    message_id = data['message_id']
    chat_id = data['chat_id']

    await message.bot.edit_message_text(message_id=message_id,
                                        chat_id=chat_id,
                                        text=text,
                                        reply_markup=kb.new_session_menu,
                                        parse_mode='HTML')


# Возврат назад в меню создания новой сессии или приходи из callback
@sessions_menu.callback_query(F.data == 'sessions:new_session_menu')
async def new_session_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    
    # Выгружаем данные из FSM и создаем сообщение для меню
    data = await state.get_data()
    text = session_menu_text(data)
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.new_session_menu,
                                     parse_mode='HTML')


# Добавляем описание сессии
@sessions_menu.callback_query(F.data == 'sessions:add_session_descr')
async def add_session_descr_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    text = '❓ <b>Введите описание сессии</b>'
    if 'session_descr' in data.keys():
        session_descr = data['session_descr']
        text += f'.\n\n<b>Текущее описание сессии</b>\n<blockquote expandable>{session_descr}</blockquote>'
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.cancel_change_descr_session,
                                     parse_mode='HTML')
    await state.set_state(Session.description)


# Удаляем описание сессии
@sessions_menu.callback_query(F.data == 'sessions:delete_descr')
async def change_session_descr_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data_refreshed = {
        'message_id': data['message_id'],
        'chat_id': data['chat_id'],
        'session_name': data['session_name'],
        }
    await state.clear()
    await state.update_data(data_refreshed)
    await new_session_menu_handler(callback, state)


# Инициируем изменение названия сессии
@sessions_menu.callback_query(F.data == 'sessions:change_new_session')
async def change_new_session_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_name = data['session_name']
    await callback.message.edit_text(text=f'❓ <b>Введите название сессии.</b>\n\nТекущее название сессии <b>{session_name}</b>',
                                     reply_markup=kb.cancel_change_session,
                                     parse_mode='HTML')
    await state.set_state(Session.name)


# Сохраняем новую сессию
@sessions_menu.callback_query(F.data == 'sessions:confirm_new_session')
async def confirm_new_session_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_data = {
        'session_name': data['session_name'],
        'session_descr': data['session_descr'] if 'session_descr' in data.keys() else None
    }
    await add_session(session_data=session_data)
    await callback.answer(text='Сессия успешно создана', show_alert=True)
    await choose_session_handler(callback, state)
    

# Отмена создания сессии
@sessions_menu.callback_query(F.data == 'sessions:confirm_cancel_new_session')
async def confirm_new_session_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='⁉️ <b>Вы уверены, что хотите отменить создание сессии?</b>',
                                     reply_markup=kb.confirm_cancel_new_session,
                                     parse_mode='HTML')
    
    
# архив сессий
@sessions_menu.callback_query(F.data.startswith('arch_session_page_'))
@sessions_menu.callback_query(F.data == 'sessions:archive')
async def archive_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.data.startswith('arch_session_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        page = 1
    await callback.message.edit_text('🗄 <b>АРХИВ СЕССИЙ</b>',
                                     reply_markup=await kb.choose_arch_session(page=page),
                                     parse_mode='HTML')
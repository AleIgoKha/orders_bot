from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

import app.main_menu.sessions.session.keyboard as kb
from app.main_menu.main_menu import main_menu_handler 
from app.states import Session
from app.database.requests import get_session, change_session_data, delete_session

session_menu = Router()


# функция для формирования сообщения меню сессии
async def session_menu_text(data, state):
    # Для начала обновляем контекст, для актуализации данных из базы
    session_id = data['session_id']
    session_data = await get_session(session_id=session_id)
    await state.clear()
    data_refreshed = {
        'session_id': session_data.session_id,
        'session_name': session_data.session_name,
        'session_descr': session_data.session_descr,
        'session_arch': session_data.session_arch,
        'message_id': data['message_id'],
        'chat_id': data['chat_id']
        }
    await state.update_data(data_refreshed)
    
    
    session_name = data_refreshed['session_name']
    session_descr = data_refreshed['session_descr']
    
    text = f'📋 <b>{session_name.upper()}</b>'
    if session_descr:
        text += f'\n\n📝 <b>Описание сессии:</b>\n<blockquote expandable>{session_descr}</blockquote>'
        
    return text


# функция для формирования сообщения меню настроек сессии
async def session_settings_menu_text(data, state):
    # Для начала обновляем контекст, для актуализации данных из базы
    session_id = data['session_id']
    session_data = await get_session(session_id=session_id)
    await state.clear()
    data_refreshed = {
        'session_id': session_data.session_id,
        'session_name': session_data.session_name,
        'session_descr': session_data.session_descr,
        'session_arch': session_data.session_arch,
        'message_id': data['message_id'],
        'chat_id': data['chat_id']
        }
    await state.update_data(data_refreshed)
    
    session_name = data_refreshed['session_name']
    session_descr = data_refreshed['session_descr']
    session_arch = data_refreshed['session_arch']
    text = f'🛠 <b>Меню настроек сессии - {session_name}</b>.'
    
    # Если архивирован
    if session_arch:
        text += f'\n\n<b>Статус - АРХИВ</b>'
    
    # Если есть описание, добавляем его
    if session_descr:
        text += f'\n\n<b>Описание сессии</b>\n<blockquote expandable>{session_descr}</blockquote>'
        
    return text


# Заходим в меню выбранной сеществующей сессии
@session_menu.callback_query(F.data.startswith('session:session_id_'))
async def session_menu_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('session:session_id_'):
        session_id = int(callback.data.split('_')[-1])
        await state.update_data(session_id=session_id,
                                message_id=callback.message.message_id,
                                chat_id=callback.message.chat.id)
    data = await state.get_data()
    text = await session_menu_text(data, state)
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.session_menu,
                                    parse_mode='HTML')
    

# Возврат в меню сессии
@session_menu.callback_query(F.data == 'session:back')
@session_menu.callback_query(F.data == 'back_from_order_download')
@session_menu.callback_query(F.data == 'back_from_order_stats')
@session_menu.callback_query(F.data == 'back_from_order_creation')
@session_menu.callback_query(F.data == 'back_from_order_processing')
@session_menu.callback_query(F.data == 'back_from_order_completed')
async def back_to_session_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot = Bot):
    data = await state.get_data()
            
    # Если вернулись из загрузки файлов
    if callback.data == 'back_from_order_download':
        
        # удаляем все сообщения которые уже были напечатаны
        redis = bot.redis
        chat_id = callback.message.chat.id
        key = f"chat:{chat_id}:messages"
        message_ids = await redis.lrange(key, 0, -1)  # Get all stored message IDs

        for msg_id in message_ids:
            try:
                await bot.delete_message(chat_id, int(msg_id))
            except Exception:
                pass  # Ignore errors (e.g., message already deleted)

        await redis.delete(key)  # Clear the stored list
        await redis.close()
        
        # печатаем сообщение и запоминаем его id
        text = await session_menu_text(data, state)
        message = await callback.bot.send_message(chat_id=data['chat_id'],
                                        text=text,
                                        reply_markup=kb.session_menu,
                                        parse_mode='HTML')
        message_id = message.message_id
        await redis.rpush(f"chat:{chat_id}:messages", message_id)
        await redis.close()
        
        await state.update_data(message_id=message.message_id)
        
        
        
        
    else:
        data = await state.get_data()
        text = await session_menu_text(data, state)

        await callback.message.edit_text(text=text,
                                        reply_markup=kb.session_menu,
                                        parse_mode='HTML')
        
        
# Открываем настройки сессии
@session_menu.callback_query(F.data == 'session:settings')
async def settings_handler(callback: CallbackQuery, state: FSMContext):
    # Обновляем данные в соответствии с базой данных
    data = await state.get_data()
    text = await session_settings_menu_text(data, state)
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.settings_menu,
                                     parse_mode='HTML')


# Инициируем изменение названия сессии
@session_menu.callback_query(F.data == 'session:change_name')
async def change_name_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_name = data['session_name']
    await callback.message.edit_text(text=f'❓ <b>Введите название сессии.</b>\n\nТекущее название сессии <b>{session_name}</b>',
                                     reply_markup=kb.cancel_change_session,
                                     parse_mode='HTML')
    await state.set_state(Session.change_name)


# Изменяем описание сессии
@session_menu.callback_query(F.data == 'session:change_descr')
async def change_session_descr_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_descr = data['session_descr']
    
    text = '❓ <b>Введите описание сессии</b>'
    if session_descr:
        text += f'.\n\n<b>Текущее описание сессии</b>\n<blockquote expandable>{session_descr}</blockquote>'
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.cancel_change_descr_session,
                                     parse_mode='HTML')
    await state.set_state(Session.change_description)
    
    
# Удаляем описание сессии
@session_menu.callback_query(F.data == 'session:delete_descr')
async def change_session_descr_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    session_id = data['session_id']
    session_data = {'session_descr': None}
    await change_session_data(session_id=session_id,
                                session_data=session_data)
    await settings_handler(callback, state)


# Принимаем название сессии и попадаем в меню создания сессии
# Просим подтвердить создание, добавить описание или отменить создание сессии
@session_menu.message(Session.change_name)
@session_menu.message(Session.change_description)
@session_menu.message(Session.delete)
async def session_change_data_handler(message: Message, state: FSMContext):
    state_name = str(await state.get_state()).split(':')[-1]
    await state.set_state(None)
    data = await state.get_data()
    session_id = data['session_id']
    message_id = data['message_id']
    chat_id = data['chat_id']
    
    # В зависимости от названия состояния сохраняем соответствующие данные
    if state_name == 'change_name':
        session_data = {'session_name': message.text}
        await change_session_data(session_id=session_id,
                                  session_data=session_data)
    elif state_name == 'change_description':
        session_data = {'session_descr': message.text}
        await change_session_data(session_id=session_id,
                                  session_data=session_data)
    elif state_name == 'delete':
        if message.text.lower() == 'удалить':
            await message.bot.edit_message_text(message_id=message_id,
                                                chat_id=chat_id,
                                                text='❗️ <b>ВНИМАНИЕ</b>\n\nПосле удаления сессии безвозвратно удалятся все ее данные.\n\n' \
                                                    'Если вы уверены что хотите удалить сессию нажмите <b>"Подтвердить"</b>',
                                                reply_markup=kb.confirm_delete_session,
                                                parse_mode='HTML')
        else:
            session_name = data['session_name']
            try:
                await state.set_state(Session.delete)
                await message.bot.edit_message_text(message_id=message_id,
                                                    chat_id=chat_id,
                                                    text=f'❗️ <b>НЕВЕРНОЕ КЛЮЧЕВОЕ СЛОВО</b>\n\nВы пытаетесь удалить сессию - <b>{session_name}</b>.\n' \
                                                        'Для подтверждения введите слово: <code>УДАЛИТЬ</code>',
                                                    reply_markup=kb.cancel_delete_session,
                                                    parse_mode='HTML')
            except TelegramBadRequest:
                return None
        return None
    
    # Выгружаем данные из FSM и создаем сообщение для меню

    text = await session_settings_menu_text(data, state)

    await message.bot.edit_message_text(message_id=message_id,
                                        chat_id=chat_id,
                                        text=text,
                                        reply_markup=kb.settings_menu,
                                        parse_mode='HTML')


# Инициируем изменение статуса сессии Архив/В работу
@session_menu.callback_query(F.data == 'session:status')
async def status_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_status = data['session_arch']
    # Если архивирован
    status_opt = '<b>В РАБОТЕ</b>'
    status_opt_opp = '<b>АРХИВ</b>'
    if session_status:
        status_opt = '<b>АРХИВ</b>'
        status_opt_opp = '<b>В РАБОТЕ</b>'
    await callback.message.edit_text(text=f'Текущий статус сессии - {status_opt}. ' \
                                     f'Если вы ходите изменить статус на {status_opt_opp} нажмите на кнопку ниже.',
                                     reply_markup=kb.change_status_keyboard(session_status),
                                     parse_mode='HTML')


# изменяем статус на противоположные
@session_menu.callback_query(F.data == 'session:change_status')
async def change_status_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_status = data['session_arch']
    session_id = data['session_id']
    if session_status:
        session_data = {'session_arch': False}
    else:
        session_data = {'session_arch': True}
    await change_session_data(session_id=session_id, session_data=session_data)
    await callback.answer(text='Сессия успешно заархивирована')
    await settings_handler(callback, state)
    
    
# Удаление сессии и всех ее заказов
@session_menu.callback_query(F.data == 'session:delete_session')
async def delete_session_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_name = data['session_name']
    await callback.message.edit_text(text=f'❗️ <b>ПРЕДУПРЕЖДЕНИЕ</b>\n\nВы пытаетесь удалить сессию - <b>{session_name}</b>.\n' \
                                        'Для подтверждения введите слово: <code>УДАЛИТЬ</code>',
                                        reply_markup=kb.cancel_delete_session,
                                        parse_mode='HTML')
    await state.set_state(Session.delete)
    

@session_menu.callback_query(F.data == 'session:confirm_delete')
async def confirm_delete_session_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_id = data['session_id']
    await delete_session(session_id)
    await callback.answer(text='Сессия была успешно удалена', show_alert=True)
    await main_menu_handler(callback, state)
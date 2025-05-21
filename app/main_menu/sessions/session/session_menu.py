from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime


import app.main_menu.sessions.session.keyboard as kb
from app.states import Session
from app.database.requests import add_session, get_session

session_menu = Router()


# функция для формирования сообщения меню сессии
def session_menu_text(data):
    session_name = data['session_name']
    session_descr = data['session_descr']
    
    text = f'📋 <b>{session_name.upper()}</b>'
    if session_descr:
        text += f'\n\n📝 <b>Описание сессии:</b>\n<blockquote expandable>{session_descr}</blockquote>'
        
    return text


# Заходим в меню выбранной сеществующей сессии
@session_menu.callback_query(F.data.startswith('session:session_id_'))
async def session_menu_handler(callback: CallbackQuery, state: FSMContext):
    # Если только зашли в сессию впервые, то сохраняем данные делая запрос в базу данных
    if callback.data.startswith('session:session_id_'):
        await state.clear()
        session_id = int(callback.data.split('_')[-1])
        session_data = await get_session(session_id)
        await state.update_data(session_id=session_id,
                                session_name=session_data.session_name,
                                session_descr=session_data.session_descr,
                                message_id=callback.message.message_id,
                                chat_id=callback.message.chat.id)
    # Если зашли в меню после сохранения заказа, то пересохраняем только необходимые данные
    else:
        data = await state.get_data()
        data_refreshed = {
                'session_id': data['session_id'],
                'session_name': data['session_name'],
                'session_descr': data['session_descr'],
                'message_id': data['message_id'],
                'chat_id': data['chat_id']
                }
        await state.clear()
        await state.update_data(data_refreshed)
        
    data = await state.get_data()
    text = session_menu_text(data)
        
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.session_menu,
                                    parse_mode='HTML')
    

# Возврат в меню сессии
@session_menu.callback_query(F.data == 'back_from_order_download')
@session_menu.callback_query(F.data == 'back_from_order_stats')
@session_menu.callback_query(F.data == 'back_from_order_creation')
@session_menu.callback_query(F.data == 'back_from_order_processing')
@session_menu.callback_query(F.data == 'back_from_order_completed')
async def back_to_session_menu_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Удаляем все сообщения из меню со списком заказов
    if callback.data in ['back_from_order_processing', 'back_from_order_completed']:
        for i in range(data['messages_sent']):
            try:
                message_id = data['message_id'] - i
                if callback.message.message_id != message_id:
                    await callback.bot.delete_message(chat_id=data['chat_id'], message_id=message_id)
            except TelegramBadRequest:
                continue
            
    # Если вернулись из загрузки файлов
    if callback.data == 'back_from_order_download':
        await callback.bot.delete_message(chat_id=data['chat_id'],
                                          message_id=callback.message.message_id)
        
        text = session_menu_text(data)
        message = await callback.bot.send_message(chat_id=data['chat_id'],
                                        text=text,
                                        reply_markup=kb.session_menu,
                                        parse_mode='HTML')
        await state.update_data(message_id=message.message_id)
    else:
    # Перезаписываем только данные о сессии
        data_refreshed = {
                'session_id': data['session_id'],
                'session_name': data['session_name'],
                'session_descr': data['session_descr'],
                'message_id': data['message_id'],
                'chat_id': data['chat_id']
                }
        await state.clear()
        await state.update_data(data_refreshed)
            
        data = await state.get_data()
        text = session_menu_text(data)

        await callback.message.edit_text(text=text,
                                        reply_markup=kb.session_menu,
                                        parse_mode='HTML')
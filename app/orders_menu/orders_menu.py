from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime, date


import app.orders_menu.keyboard as kb
from app.states import Session
from app.database.requests import add_session, get_session

orders_menu = Router()

# Раздел заказов
@orders_menu.callback_query(F.data == 'orders')
async def orders_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text='📦 <b>МЕНЮ ЗАКАЗОВ</b> 📦', reply_markup=kb.orders_menu, parse_mode='HTML')


# добавление новой сессии
@orders_menu.callback_query(F.data.startswith('session:month:prev:'))
@orders_menu.callback_query(F.data.startswith('session:month:next:'))
@orders_menu.callback_query(F.data == 'new_session')
async def new_session_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.update_data(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    now = datetime.now()
    year = now.year
    month = now.month
    # Переключаем месяца вперед и назад
    if callback.data.startswith('session:month'):
        calendar_data = callback.data.split(':')
        if calendar_data[2] == 'prev':
            year = int(calendar_data[3])
            month = int(calendar_data[4]) - 1
            if month < 1:
                month = 12
                year -= 1
        elif calendar_data[2] == 'next':
            year = int(calendar_data[3])
            month = int(calendar_data[4]) + 1
            if month > 12:
                month = 1
                year += 1
        await callback.message.edit_reply_markup(reply_markup=kb.create_calendar_keyboard(year, month))
    else:
        await callback.message.edit_text(text='📅 <b>Выберите дату новой сессии или введите вручную в следующем формате:</b>\n<i>ДД-ММ-ГГГГ</i>',
                                        reply_markup=kb.create_calendar_keyboard(year, month),
                                        parse_mode='HTML')
    await state.set_state(Session.date)


# Указание даты
@orders_menu.message(Session.date_error)
@orders_menu.message(Session.date)
async def session_date_state_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        date_comp = [int(_) for _ in message.text.split('-')]
        if len(date_comp) != 3 or len(str(date_comp[2])) != 4:
            raise ValueError('Неправильный формат')
        datetime(year=date_comp[2],
                month=date_comp[1],
                day=date_comp[0])
        await state.update_data(date=message.text)
        await state.set_state(Session.place)
        await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text='🏙️ <b>Введите название населенного пункта</b>',
                                            reply_markup=kb.session_cancellation,
                                            parse_mode='HTML')
    except Exception:
        state_name = await state.get_state()
        if not 'date_error' in state_name:
            await state.set_state(Session.date_error)
            await message.bot.edit_message_text(chat_id=data['chat_id'],
                                                message_id=data['message_id'],
                                                text='❗ <b>НЕВЕРНО УКАЗАНА ДАТА</b> ❗\n\n' \
                                                    '<b>Введите дату в соответствии с форматом:</b>\n<i>ДД-ММ-ГГГГ</i>',
                                                reply_markup=kb.session_cancellation,
                                                parse_mode='HTML')
        return None


# Обработка и сохранение даты при нажатии на кнопку
@orders_menu.callback_query(F.data.startswith('session:date:'))
async def session_date_callback_handler(callback: CallbackQuery, state: FSMContext):
    date_data = callback.data.split(':')[-3:]
    await state.update_data(date=f'{date_data[2]}-{date_data[1]}-{date_data[0]}')
    await state.set_state(Session.place)
    await callback.message.edit_text(text='🏙️ <b>Введите название населенного пункта</b>',
                                    reply_markup=kb.session_cancellation,
                                    parse_mode='HTML')

# Указание местоположения
@orders_menu.message(Session.place)
async def session_place(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(session_place=message.text)
    await state.set_state(Session.method)
    await message.bot.edit_message_text(chat_id=data['chat_id'],
                                            message_id=data['message_id'],
                                            text='<b>Выберите метод выдачи заказа из вариантов ниже</b>',
                                            reply_markup=kb.issuing_method,
                                            parse_mode='HTML')


# Указываем метод сессии доставка/самовывоз/почта
@orders_menu.callback_query(F.data.in_(['Самовывоз', 'Доставка по городу', 'Доставка почтой']))
async def session_method(callback: CallbackQuery, state: FSMContext):
    session_data = await state.get_data()
    date_comp = [int(_) for _ in session_data['date'].split('-')]
    session_date = datetime(year=date_comp[2],
                            month=date_comp[1],
                            day=date_comp[0])
    await state.update_data(session_method=callback.data)
    await callback.message.edit_text("<b>Подтвердите данные сессии ниже:</b>\n" \
                                    f'📅 Дата сессии: <b>{session_date.strftime('%d-%m-%Y')}</b>\n' \
                                    f'🏙️ Место: <b>{session_data['session_place']}</b>\n' \
                                    f'📦 Метод выдачи заказов: <b>{callback.data}</b>\n',
                                    reply_markup=kb.session_confirmation,
                                    parse_mode='HTML')


# Подтвержденте создания новой сессии и ее сохранение
@orders_menu.callback_query(F.data == 'session_confirmation')
async def session_confirmation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    date_comp = [int(_) for _ in data['date'].split('-')]
    date = datetime(year=date_comp[2],
                    month=date_comp[1],
                    day=date_comp[0])
    session_data = {
        'session_date': date,
        'session_place': data['session_place'],
        'session_method': data['session_method']
    }
    await add_session(session_data)
    await callback.answer('Новая сессия успешно создана', show_alert=True)
    await orders_menu_handler(callback, state)


# Открываем существующую сессию
@orders_menu.callback_query(F.data.startswith('session_page_'))
@orders_menu.callback_query(F.data == 'choose_session')
async def choose_session(callback: CallbackQuery):
    if callback.data.startswith('session_page_'):
        page = int(callback.data.split('_')[-1])
    else:
        page = 1
    await callback.message.edit_text('<b>Выберите сессию из списка ниже</b>',
                                     reply_markup=await kb.choose_session(page=page),
                                     parse_mode='HTML')


# Заходим в меню выбранной сеществующей сессии
@orders_menu.callback_query(F.data.startswith('session_id_'))
async def session_menu_handler(callback: CallbackQuery, state: FSMContext):
    
    # Если только зашли в сессию впервые, то сохраняем данные делая запрос в базу данных
    if callback.data.startswith('session_id_'):
        await state.clear()
        session_id = int(callback.data.split('_')[-1])
        session_data = await get_session(session_id)
        await state.update_data(session_id=session_id,
                                session_date=session_data.session_date.strftime('%d-%m-%Y'),
                                session_place=session_data.session_place,
                                session_method=session_data.session_method,
                                message_id=callback.message.message_id,
                                chat_id=callback.message.chat.id)
    # Если зашли в меню после сохранения заказа, то пересохраняем только необходимые данные
    else:
        data = await state.get_data()
        data_refreshed = {'session_id': data['session_id'],
                'session_date': data['session_date'],
                'session_place': data['session_place'],
                'session_method': data['session_method'],
                'message_id': data['message_id'],
                'chat_id': data['chat_id']}
        await state.clear()
        await state.update_data(data_refreshed)
        
    data = await state.get_data()
        
    await callback.message.edit_text('📋 <b>МЕНЮ СЕССИИ</b> 📋\n\n' \
                                    f'📅 Дата сессии: <b>{data['session_date']}</b>\n' \
                                    f'🏙️ Место: <b>{data['session_place']}</b>\n' \
                                    f'📦 Метод выдачи заказов: <b>{data['session_method']}</b>\n',
                                    reply_markup=kb.session_menu,
                                    parse_mode='HTML')
    

# Возврат в меню сессии
@orders_menu.callback_query(F.data == 'back_from_order_stats')
@orders_menu.callback_query(F.data == 'back_from_order_creation')
@orders_menu.callback_query(F.data == 'back_from_order_processing')
@orders_menu.callback_query(F.data == 'back_from_order_changing')
async def back_to_orders_menu_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Удаляем все сообщения из меню со списком заказов
    if callback.data in ['back_from_order_processing', 'back_from_order_changing']:
        for i in range(data['messages_sent']):
            try:
                message_id = data['message_id'] - i
                if callback.message.message_id != message_id:
                    await callback.bot.delete_message(chat_id=data['chat_id'], message_id=message_id)
            except TelegramBadRequest:
                continue
    
    # Перезаписываем только данные о сессии
    data_refreshed = {'session_id': data['session_id'],
            'session_date': data['session_date'],
            'session_place': data['session_place'],
            'session_method': data['session_method'],
            'message_id': data['message_id'],
            'chat_id': data['chat_id']}
    await state.clear()
    await state.update_data(data_refreshed)
        
    data = await state.get_data()
        
    await callback.message.edit_text('📋 <b>МЕНЮ СЕССИИ</b> 📋\n\n' \
                                    f'📅 Дата сессии: <b>{data['session_date']}</b>\n' \
                                    f'🏙️ Место: <b>{data['session_place']}</b>\n' \
                                    f'📦 Метод выдачи заказов: <b>{data['session_method']}</b>\n',
                                    reply_markup=kb.session_menu,
                                    parse_mode='HTML')



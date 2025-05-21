from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime


from app.states import Session
from app.database.requests import add_session, get_session

# # добавление новой сессии
# @orders_menu.callback_query(F.data.startswith('session:month:prev:'))
# @orders_menu.callback_query(F.data.startswith('session:month:next:'))
# @orders_menu.callback_query(F.data == 'new_session')
# async def new_session_handler(callback: CallbackQuery, state: FSMContext):
#     await state.clear()
#     await state.update_data(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
#     now = datetime.now()
#     year = now.year
#     month = now.month
#     # Переключаем месяца вперед и назад
#     if callback.data.startswith('session:month'):
#         calendar_data = callback.data.split(':')
#         if calendar_data[2] == 'prev':
#             year = int(calendar_data[3])
#             month = int(calendar_data[4]) - 1
#             if month < 1:
#                 month = 12
#                 year -= 1
#         elif calendar_data[2] == 'next':
#             year = int(calendar_data[3])
#             month = int(calendar_data[4]) + 1
#             if month > 12:
#                 month = 1
#                 year += 1
#         await callback.message.edit_reply_markup(reply_markup=kb.create_calendar_keyboard(year, month))
#     else:
#         await callback.message.edit_text(text='📅 <b>Выберите дату новой сессии или введите вручную в следующем формате:</b>\n<i>ДД-ММ-ГГГГ</i>',
#                                         reply_markup=kb.create_calendar_keyboard(year, month),
#                                         parse_mode='HTML')
#     await state.set_state(Session.date)


# # Указание даты
# @orders_menu.message(Session.date_error)
# @orders_menu.message(Session.date)
# async def session_date_state_handler(message: Message, state: FSMContext):
#     data = await state.get_data()
#     try:
#         date_comp = [int(_) for _ in message.text.split('-')]
#         if len(date_comp) != 3 or len(str(date_comp[2])) != 4:
#             raise ValueError('Неправильный формат')
#         datetime(year=date_comp[2],
#                 month=date_comp[1],
#                 day=date_comp[0])
#         await state.update_data(date=message.text)
#         await state.set_state(Session.place)
#         await message.bot.edit_message_text(chat_id=data['chat_id'],
#                                             message_id=data['message_id'],
#                                             text='🏙️ <b>Введите название населенного пункта</b>',
#                                             reply_markup=kb.session_cancellation,
#                                             parse_mode='HTML')
#     except Exception:
#         state_name = await state.get_state()
#         if not 'date_error' in state_name:
#             await state.set_state(Session.date_error)
#             await message.bot.edit_message_text(chat_id=data['chat_id'],
#                                                 message_id=data['message_id'],
#                                                 text='❗ <b>НЕВЕРНО УКАЗАНА ДАТА</b> ❗\n\n' \
#                                                     '<b>Введите дату в соответствии с форматом:</b>\n<i>ДД-ММ-ГГГГ</i>',
#                                                 reply_markup=kb.session_cancellation,
#                                                 parse_mode='HTML')
#         return None


# # Обработка и сохранение даты при нажатии на кнопку
# @orders_menu.callback_query(F.data.startswith('session:date:'))
# async def session_date_callback_handler(callback: CallbackQuery, state: FSMContext):
#     date_data = callback.data.split(':')[-3:]
#     await state.update_data(date=f'{date_data[2]}-{date_data[1]}-{date_data[0]}')
#     await state.set_state(Session.place)
#     await callback.message.edit_text(text='🏙️ <b>Введите название населенного пункта</b>',
#                                     reply_markup=kb.session_cancellation,
#                                     parse_mode='HTML')

# Указание местоположения
# @orders_menu.message(Session.place)
# async def session_place(message: Message, state: FSMContext):
#     data = await state.get_data()
#     await state.update_data(session_place=message.text)
#     await state.set_state(Session.method)
#     await message.bot.edit_message_text(chat_id=data['chat_id'],
#                                             message_id=data['message_id'],
#                                             text='<b>Выберите метод выдачи заказа из вариантов ниже</b>',
#                                             reply_markup=kb.issuing_method,
#                                             parse_mode='HTML')


# # Указываем метод сессии доставка/самовывоз/почта
# @orders_menu.callback_query(F.data.in_(['Самовывоз', 'Доставка по городу', 'Доставка почтой']))
# async def session_method(callback: CallbackQuery, state: FSMContext):
#     session_data = await state.get_data()
#     date_comp = [int(_) for _ in session_data['date'].split('-')]
#     session_date = datetime(year=date_comp[2],
#                             month=date_comp[1],
#                             day=date_comp[0])
#     await state.update_data(session_method=callback.data)
#     await callback.message.edit_text("<b>Подтвердите данные сессии ниже:</b>\n" \
#                                     f'📅 Дата сессии: <b>{session_date.strftime('%d-%m-%Y')}</b>\n' \
#                                     f'🏙️ Место: <b>{session_data['session_place']}</b>\n' \
#                                     f'📦 Метод выдачи заказов: <b>{callback.data}</b>\n',
#                                     reply_markup=kb.session_confirmation,
#                                     parse_mode='HTML')


# # Подтвержденте создания новой сессии и ее сохранение
# @orders_menu.callback_query(F.data == 'session_confirmation')
# async def session_confirmation(callback: CallbackQuery, state: FSMContext):
#     data = await state.get_data()
#     date_comp = [int(_) for _ in data['date'].split('-')]
#     date = datetime(year=date_comp[2],
#                     month=date_comp[1],
#                     day=date_comp[0])
#     session_data = {
#         'session_date': date,
#         'session_place': data['session_place'],
#         'session_method': data['session_method']
#     }
#     await add_session(session_data)
#     await callback.answer('Новая сессия успешно создана', show_alert=True)
#     await choose_session(callback)






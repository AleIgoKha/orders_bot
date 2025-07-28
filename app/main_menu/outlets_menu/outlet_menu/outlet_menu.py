from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

import app.main_menu.outlets_menu.outlet_menu.keyboard as kb
from app.main_menu.main_menu import main_menu_handler 
from app.states import Outlet
from app.database.requests import get_outlet, change_outlet_data, delete_outlet

outlet_menu = Router()


# функция для формирования меню торговой точки
async def outlet_menu_text(data, state):
    # Для начала обновляем контекст, для актуализации данных из базы
    outlet_id = data['outlet_id']
    outlet_data = await get_outlet(outlet_id=outlet_id)
    
    # сохраняем отчет если он есть и если нет, ставим None
    if not 'report' in list(data.keys()):
        report = {
                'purchases': None,
                'revenue': None,
                'note': None
                }
        
        await state.update_data(report=report)
    else:
        report = data['report']
    
    await state.clear()
    data_refreshed = {
        'outlet_id': outlet_data.outlet_id,
        'outlet_name': outlet_data.outlet_name,
        'outlet_descr': outlet_data.outlet_descr,
        'outlet_arch': outlet_data.outlet_arch,
        'message_id': data['message_id'],
        'chat_id': data['chat_id'],
        'report': report
        }
    await state.update_data(data_refreshed)
    
    
    outlet_name = data_refreshed['outlet_name']
    outlet_descr = data_refreshed['outlet_descr']
    outlet_arch = data_refreshed['outlet_arch']
    
    text = f'📋 <b>{outlet_name.upper()}</b>'
    if outlet_descr:
        text += f'\n\n📝 <b>Описание торговой точки:</b>\n<blockquote expandable>{outlet_descr}</blockquote>'
        
    # Если архивирован
    if outlet_arch:
        text += f'\n\n<b>Статус - АРХИВ</b>'    
    
    return text


# функция для формирования сообщения меню настроек торговой точки
async def outlet_settings_menu_text(data, state):
    # Для начала обновляем контекст, для актуализации данных из базы
    outlet_id = data['outlet_id']
    outlet_data = await get_outlet(outlet_id=outlet_id)
    await state.clear()
    data_refreshed = {
        'outlet_id': outlet_data.outlet_id,
        'outlet_name': outlet_data.outlet_name,
        'outlet_descr': outlet_data.outlet_descr,
        'outlet_arch': outlet_data.outlet_arch,
        'message_id': data['message_id'],
        'chat_id': data['chat_id']
        }
    await state.update_data(data_refreshed)
    
    outlet_name = data_refreshed['outlet_name']
    outlet_descr = data_refreshed['outlet_descr']
    outlet_arch = data_refreshed['outlet_arch']
    text = f'🛠 <b>Меню настроек торговой точки - {outlet_name}</b>.'
    
    # Если архивирован
    if outlet_arch:
        text += f'\n\n<b>Статус - АРХИВ</b>'
    
    # Если есть описание, добавляем его
    if outlet_descr:
        text += f'\n\n<b>Описание торговой точки</b>\n<blockquote expandable>{outlet_descr}</blockquote>'
        
    return text


# Заходим в меню выбранной сеществующей торговой точки
@outlet_menu.callback_query(F.data == 'outlet:back')
@outlet_menu.callback_query(F.data.startswith('outlet:outlet_id_'))
async def outlet_menu_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith('outlet:outlet_id_'):
        outlet_id = int(callback.data.split('_')[-1])
        await state.update_data(outlet_id=outlet_id,
                                message_id=callback.message.message_id,
                                chat_id=callback.message.chat.id)
    data = await state.get_data()
    text = await outlet_menu_text(data, state)
    await callback.message.edit_text(text=text,
                                    reply_markup=kb.outlet_menu,
                                    parse_mode='HTML')
 
        
# Открываем настройки торговой точки
@outlet_menu.callback_query(F.data == 'outlet:settings')
async def settings_handler(callback: CallbackQuery, state: FSMContext):
    # Обновляем данные в соответствии с базой данных
    data = await state.get_data()
    text = await outlet_settings_menu_text(data, state)
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.settings_menu,
                                     parse_mode='HTML')


# Инициируем изменение названия торговой точки
@outlet_menu.callback_query(F.data == 'outlet:change_name')
async def change_name_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_name = data['outlet_name']
    await callback.message.edit_text(text=f'❓ <b>Введите название торговой точки.</b>\n\nТекущее название торговой точки <b>{outlet_name}</b>',
                                     reply_markup=kb.cancel_change_outlet,
                                     parse_mode='HTML')
    await state.set_state(Outlet.change_name)


# Изменяем описание торговой точки
@outlet_menu.callback_query(F.data == 'outlet:change_descr')
async def change_outlet_descr_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_descr = data['outlet_descr']
    
    text = '❓ <b>Введите описание торговой точки</b>'
    if outlet_descr:
        text += f'.\n\n<b>Текущее описание торговой точки</b>\n<blockquote expandable>{outlet_descr}</blockquote>'
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.cancel_change_descr_outlet,
                                     parse_mode='HTML')
    await state.set_state(Outlet.change_description)
    
    
# Удаляем описание торговой точки
@outlet_menu.callback_query(F.data == 'outlet:delete_descr')
async def change_outlet_descr_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    outlet_id = data['outlet_id']
    outlet_data = {'outlet_descr': None}
    await change_outlet_data(outlet_id=outlet_id,
                                outlet_data=outlet_data)
    await settings_handler(callback, state)


# Принимаем название торговой точки и попадаем в меню создания торговой точки
# Просим подтвердить создание, добавить описание или отменить создание торговой точки
@outlet_menu.message(Outlet.change_name)
@outlet_menu.message(Outlet.change_description)
@outlet_menu.message(Outlet.delete)
async def outlet_change_data_handler(message: Message, state: FSMContext):
    state_name = str(await state.get_state()).split(':')[-1]
    await state.set_state(None)
    data = await state.get_data()
    outlet_id = data['outlet_id']
    message_id = data['message_id']
    chat_id = data['chat_id']
    
    # В зависимости от названия состояния сохраняем соответствующие данные
    if state_name == 'change_name':
        outlet_data = {'outlet_name': message.text}
        await change_outlet_data(outlet_id=outlet_id,
                                  outlet_data=outlet_data)
    elif state_name == 'change_description':
        outlet_data = {'outlet_descr': message.text}
        await change_outlet_data(outlet_id=outlet_id,
                                  outlet_data=outlet_data)
    elif state_name == 'delete':
        if message.text.lower() == 'удалить':
            await message.bot.edit_message_text(message_id=message_id,
                                                chat_id=chat_id,
                                                text='❗️ <b>ВНИМАНИЕ</b>\n\nПосле удаления торговой точки безвозвратно удалятся все ее данные.\n\n' \
                                                    'Если вы уверены что хотите удалить торговую точку нажмите <b>"Подтвердить"</b>',
                                                reply_markup=kb.confirm_delete_outlet,
                                                parse_mode='HTML')
        else:
            outlet_name = data['outlet_name']
            try:
                await state.set_state(Outlet.delete)
                await message.bot.edit_message_text(message_id=message_id,
                                                    chat_id=chat_id,
                                                    text=f'❗️ <b>НЕВЕРНОЕ КЛЮЧЕВОЕ СЛОВО</b>\n\nВы пытаетесь удалить торговую точку - <b>{outlet_name}</b>. ' \
                                                        'Для подтверждения введите слово: <i>УДАЛИТЬ</i>',
                                                    reply_markup=kb.cancel_delete_outlet,
                                                    parse_mode='HTML')
            except TelegramBadRequest:
                return None
        return None
    
    # Выгружаем данные из FSM и создаем сообщение для меню

    text = await outlet_settings_menu_text(data, state)

    await message.bot.edit_message_text(message_id=message_id,
                                        chat_id=chat_id,
                                        text=text,
                                        reply_markup=kb.settings_menu,
                                        parse_mode='HTML')


# Инициируем изменение статуса торговой точки Архив/В работу
@outlet_menu.callback_query(F.data == 'outlet:status')
async def status_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_status = data['outlet_arch']
    # Если архивирован
    status_opt = '<b>В РАБОТЕ</b>'
    status_opt_opp = '<b>АРХИВ</b>'
    if outlet_status:
        status_opt = '<b>АРХИВ</b>'
        status_opt_opp = '<b>В РАБОТЕ</b>'
    await callback.message.edit_text(text=f'Текущий статус торговой точки - {status_opt}. ' \
                                     f'Если вы ходите изменить статус на {status_opt_opp} нажмите на кнопку ниже.',
                                     reply_markup=kb.change_status_keyboard(outlet_status),
                                     parse_mode='HTML')


# изменяем статус на противоположные
@outlet_menu.callback_query(F.data == 'outlet:change_status')
async def change_status_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_status = data['outlet_arch']
    outlet_id = data['outlet_id']
    if outlet_status:
        outlet_data = {'outlet_arch': False}
    else:
        outlet_data = {'outlet_arch': True}
    await change_outlet_data(outlet_id=outlet_id, outlet_data=outlet_data)
    await callback.answer(text='Торговая точка успешно заархивирована')
    await settings_handler(callback, state)
    
    
# Удаление торговой точки и всех ее заказов
@outlet_menu.callback_query(F.data == 'outlet:delete_outlet')
async def delete_outlet_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_name = data['outlet_name']
    await callback.message.edit_text(text=f'❗️ <b>ПРЕДУПРЕЖДЕНИЕ</b>\n\nВы пытаетесь удалить торговую точку - <b>{outlet_name}</b>. ' \
                                        'Для подтверждения введите слово: <i>УДАЛИТЬ</i>',
                                        reply_markup=kb.cancel_delete_outlet,
                                        parse_mode='HTML')
    await state.set_state(Outlet.delete)
    

# подтверждение удаления торговой точки
@outlet_menu.callback_query(F.data == 'outlet:confirm_delete')
async def confirm_delete_outlet_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_id = data['outlet_id']
    await delete_outlet(outlet_id)
    await callback.answer(text='Торговая точка была успешно удалена', show_alert=True)
    await main_menu_handler(callback, state)
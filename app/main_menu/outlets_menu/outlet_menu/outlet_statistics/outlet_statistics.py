import pytz
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from datetime import datetime
from decimal import Decimal

import app.main_menu.outlets_menu.outlet_menu.outlet_statistics.keyboard as kb
from app.database.all_requests.transactions import get_expected_revenue, were_stock_transactions, balance_transactions_number
from app.database.all_requests.reports import is_there_report, get_report_data
from app.database.all_requests.stock import get_active_stock_products
from app.database.all_requests.reports import save_report
from app.com_func import localize_user_input
from app.states import Report

outlet_statistics = Router()


def report_menu_text(report):   
    purchases = report['purchases']
    revenue = report['revenue']
    note = report['note']
    report_datetime = report['report_datetime']
    report_datetime = datetime(**report_datetime)
    
    text = f'<b>ОТЧЕТ ЗА {report_datetime.strftime("%d-%m-%Y")}</b>\n\n'
    
    if any((purchases, revenue, note)):
        if not purchases is None:
            text += f'🧾 <b>Количество чеков</b> - {purchases}\n'
            
        if not revenue is None:
            text += f'💵 <b>Выручка</b> - {revenue} руб.\n'
            
        if not note is None:
            text += f'✍️ <b>Примечание:</b>\n' \
                    f'{note}\n'
    
        text += '\nВнимательно заполните все пункты, затем нажмите <b>Отправить</b>'
    else:
        text += 'Внимательно заполните все пункты, затем нажмите <b>Отправить</b>'
    
    return text


# меню статистики
@outlet_statistics.callback_query(F.data == 'outlet:statistics')
async def stats_menu_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='❓ <b>ВЫБЕРИТЕ ВИД СТАТИСТИКИ</b>',
                                     reply_markup=kb.stats_menu,
                                     parse_mode='HTML')


# меню выбора дня для экспресс статистики
@outlet_statistics.callback_query(F.data == 'outlet:statistics:express')
@outlet_statistics.callback_query(F.data.startswith('outlet:statistics:month:prev:'))
@outlet_statistics.callback_query(F.data.startswith('outlet:statistics:month:next:'))
async def outlet_statistics_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    outlet_id = data['outlet_id']
    
    # избавляемся от данных об отчете на случай, если кнопки назад
    if 'report' in list(data.keys()):
        del data['report']
        await state.clear()
        await state.update_data(**data)
    
    now = localize_user_input(datetime.now(pytz.timezone("Europe/Chisinau")))
    year = now.year
    month = now.month
    # Переключаем месяца вперед и назад
    if callback.data.startswith('outlet:statistics:month:'):
        calendar_data = callback.data.split(':')
        if calendar_data[3] == 'prev':
            year = int(calendar_data[4])
            month = int(calendar_data[5]) - 1
            if month < 1:
                month = 12
                year -= 1
        elif calendar_data[3] == 'next':
            year = int(calendar_data[4])
            month = int(calendar_data[5]) + 1
            if month > 12:
                month = 1
                year += 1
        await callback.message.edit_reply_markup(reply_markup=await kb.calendar_keyboard(outlet_id, year, month))
    else:
        await callback.message.edit_text(text=f'❓ <b>УКАЖИТЕ ДАТУ СТАТИСТИКИ</b>\n\n',
                                        reply_markup=await kb.calendar_keyboard(outlet_id, year, month),
                                        parse_mode='HTML')
        

# заходим в статистику дня
@outlet_statistics.callback_query(F.data.startswith('outlet:statistics:date:'))
async def outlet_statistics_date_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    
    date_comp = [int(_) for _ in callback.data.split(':')[-3:]]
    finished_datetime = datetime(year=date_comp[0],
                            month=date_comp[1],
                            day=date_comp[2])
    
    check_flag = await is_there_report(outlet_id, finished_datetime)
    
    # если отчета в выбранный день не существует, то предлагаем его создать
    if not check_flag:
        await callback.message.edit_text(text='В этот день нет отчета. Для создания нажмите <b>Создать отчет</b>',
                                         reply_markup=kb.report_creation,
                                         parse_mode='HTML')
        await state.update_data(report={'report_datetime': {'year': date_comp[0],
                                                            'month':date_comp[1],
                                                            'day':date_comp[2]},
                                        'revenue': None,
                                        'purchases': None,
                                        'note': None})
        return None
    
    report_data = await get_report_data(outlet_id, finished_datetime)
    
    report_id = report_data['report_id']
    purchases = report_data['report_purchases']
    revenue = round(report_data['report_revenue'], 2)
    note = report_data['report_note']
    expected_revenue = round(await get_expected_revenue(outlet_id, finished_datetime), 2)
    revenue_difference = revenue - expected_revenue
    revenue_difference_percent = round(((revenue - expected_revenue) * 100) / expected_revenue, 2)
    
    text = f'📝 <b>ОТЧЕТ №{report_id} ЗА {finished_datetime.strftime('%d-%m-%Y')}</b>\n\n' \
            '💵 <b>Выручка:</b>\n' \
            f'Расчетная - <b>{expected_revenue} руб</b>\n' \
            f'Фактическая - <b>{revenue} руб</b>\n' \
            f'Разница  - <b>{revenue_difference} руб ({revenue_difference_percent}%)</b>\n\n' \
            f'🧾 <b>Количество покупок - {purchases}</b>\n\n' \
            f'✍️ <b>Примечание:</b>\n - {note}' \
    
    # на случай, если захочу изменить
    await state.update_data(report={'report_datetime': {'year': date_comp[0],
                                                        'month':date_comp[1],
                                                        'day':date_comp[2]},
                                    'revenue': str(revenue),
                                    'purchases': purchases,
                                    'note': note})
            
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.back_button,
                                     parse_mode='HTML')
    

# меню создания отчета
@outlet_statistics.callback_query(F.data == 'outlet:statistics:amend_report')
@outlet_statistics.callback_query(F.data == 'outlet:statistics:create_report')
async def create_report_statistics_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    
    report = data['report']
    
    text = report_menu_text(report)
    
    await callback.message.edit_text(text=text,
                                     reply_markup=kb.report_menu(report),
                                     parse_mode='HTML')

# просим указать количество чеков
@outlet_statistics.callback_query(F.data == 'outlet:statistics:create_report:purchases')
async def purchases_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='<b>Укажите общее количество покупок в течение торгового дня</b>\n\n'
                                            'Формат ввода предполагает использование цифр: <i>123</i>',
                                     reply_markup=kb.cancel_button,
                                     parse_mode='HTML')
    await state.set_state(Report.purchases_only)
    

# принимаем количество покупок
@outlet_statistics.message(Report.purchases_only)
async def purchases_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    
    purchases = message.text
    
    # проверяем на тип данных
    if not purchases.isdigit():
        # если не целое число, то ничего не происходит
        await state.set_state(Report.purchases_only)
        return None
    
    # если целое число без лишних знаков, то сохраняем в контекст
    purchases = int(purchases)
    report = data['report']
    report['purchases'] = purchases
    
    await state.update_data(report=report)
    
    # формируем меню отчетов

    chat_id = data['chat_id']
    message_id = data['message_id']
    outlet_id = data['outlet_id']
    
    report = data['report']
    
    text = report_menu_text(report)
    
    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text=text,
                                        reply_markup=kb.report_menu(report),
                                        parse_mode='HTML')
    

# просим указать сумму выручки за день
@outlet_statistics.callback_query(F.data == 'outlet:statistics:create_report:revenue')
async def revenue_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='<b>Укажите сумму выручки</b>\n\n'
                                            'Формат ввода предполагает использование цифр с десятичным разделителем: <i>123.45</i>',
                                     reply_markup=kb.cancel_button,
                                     parse_mode='HTML')
    await state.set_state(Report.revenue_only)


# принимаем сумму выручки
@outlet_statistics.message(Report.revenue_only)
async def revenue_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    
    revenue = message.text
    
    # проверяем формат ввода данных
    try:
        revenue = str(Decimal(message.text.replace(',', '.')))
    except:
        # если формат ввода не подходит, то ничего не делаем
        await state.set_state(Report.revenue_only)
        return None
    
    # если формат подходит, то сохраняем в контекст
    report = data['report']
    report['revenue'] = revenue
    
    await state.update_data(report=report)
    
    # формируем меню отчетов

    chat_id = data['chat_id']
    message_id = data['message_id']
    outlet_id = data['outlet_id']
    
    report = data['report']
    
    text = report_menu_text(report)
    
    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text=text,
                                        reply_markup=kb.report_menu(report),
                                        parse_mode='HTML')
    

# просим указать примечание к отчету 
@outlet_statistics.callback_query(F.data == 'outlet:statistics:create_report:note')
async def revenue_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='<b>Укажите дополнительную информацию касаемо торгового дня.\n\n'
                                            'Опишите следующее:</b>\n' \
                                            '1. Чем обусловлены потери\n' \
                                            '2. Нестандартные ситуации\n' \
                                            '3. Что-либо, что необходимо знать и учесть',
                                     reply_markup=kb.cancel_button,
                                     parse_mode='HTML')
    await state.set_state(Report.note_only)


# принимаем примечание к отчету
@outlet_statistics.message(Report.note_only)
async def note_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    
    note = message.text
    
    # если формат подходит, то сохраняем в контекст
    report = data['report']
    report['note'] = note
    
    await state.update_data(report=report)
    
    # формируем меню отчетов

    chat_id = data['chat_id']
    message_id = data['message_id']
    
    report = data['report']
    
    text = report_menu_text(report)
    
    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text=text,
                                        reply_markup=kb.report_menu(report),
                                        parse_mode='HTML')
    

# просим подтверждения на сохранение отчета
@outlet_statistics.callback_query(F.data == 'outlet:statistics:create_report:send_report')
async def send_report_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    report = data['report']
    report_datetime = report['report_datetime']
    report_datetime = datetime(**report_datetime)
    
    purchases = report['purchases']
    revenue = report['revenue']
    note = report['note']
    
    # сначала проверяем были ли заполнены все данные, в противном случае не даем отправить отчет
    if not all((purchases, revenue, note)):
        await callback.answer(text='Не все данные были заполнены', show_alert=True)
        return None
    
    await callback.message.edit_text(text='Чтобы отправить отчет, нажмите <b>Подтвердить</b>',
                                     reply_markup=kb.confirm_report,
                                     parse_mode='HTML')
    

# При подтверждении отправки отчета создаем его и выходим в меню торговой точки
@outlet_statistics.callback_query(F.data == 'outlet:statistics:create_report:send_report:confirm')
async def confirm_send_report_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    report = data['report']
    report_datetime = report['report_datetime']
    report_datetime = datetime(**report_datetime)
    
    report_data = {
        'report_datetime': localize_user_input(report_datetime),
        'outlet_id': outlet_id,
        'report_purchases': report['purchases'],
        'report_revenue': Decimal(report['revenue']),
        'report_note': report['note']
    }
    
    try:
        await save_report(report_data)
    except:
        await callback.answer(text='Невозможно отправить отчет', show_alert=True)
        return None
    
    # переходим в меню торговой точки
    await outlet_statistics_handler(callback, state)
    await callback.answer(text='Отчет успешно отправлен', show_alert=True)
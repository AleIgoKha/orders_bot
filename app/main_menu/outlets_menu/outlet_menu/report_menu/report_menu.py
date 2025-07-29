from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from decimal import Decimal
from datetime import datetime
import pytz

import app.main_menu.outlets_menu.outlet_menu.report_menu.keyboard as kb
from app.states import Report
from app.database.all_requests.stock import get_active_stock_products, get_stock_product
from app.database.all_requests.reports import save_report, is_there_report
from app.database.all_requests.outlet import get_outlet
from app.database.all_requests.transactions import were_stock_transactions, balance_transactions_number_today
from app.main_menu.outlets_menu.outlet_menu.outlet_menu import outlet_menu_handler
from app.com_func import represent_utc_3, localize_user_input

report_menu = Router()


def report_menu_text(report):
    
    today = datetime.now(pytz.timezone('Europe/Chisinau'))
    
    purchases = report['purchases']
    revenue = report['revenue']
    note = report['note']
    
    text = f'<b>ОТЧЕТ ЗА {today.strftime("%d-%m-%Y")}</b>\n\n'
    
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


# меню отчета
@report_menu.callback_query(F.data == 'outlet:report_menu')
async def report_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    
    report = data['report']
    outlet_id = data['outlet_id']
    
    date_time = datetime.now(pytz.timezone('Europe/Chisinau'))
    
    check_flag = await is_there_report(outlet_id, date_time)
    
    if check_flag:
        await callback.answer(text='Невозможно создать отчет повторно', show_alert=True)
        return None
    
    text = report_menu_text(report)
    
    await callback.message.edit_text(text=text,
                                     reply_markup=await kb.report_menu(outlet_id, report),
                                     parse_mode='HTML')
    

# просим указать количество чеков
@report_menu.callback_query(F.data == 'outlet:report_menu:purchases')
async def purchases_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='<b>Укажите общее количество покупок в течение торгового дня</b>\n\n'
                                            'Формат ввода предполагает использование цифр: <i>123</i>',
                                     reply_markup=kb.cancel_button,
                                     parse_mode='HTML')
    await state.set_state(Report.purchases)
    

# принимаем количество покупок
@report_menu.message(Report.purchases)
async def purchases_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    
    purchases = message.text
    
    # проверяем на тип данных
    if not purchases.isdigit():
        # если не целое число, то ничего не происходит
        await state.set_state(Report.purchases)
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
                                        reply_markup=await kb.report_menu(outlet_id, report),
                                        parse_mode='HTML')
    

# просим указать сумму выручки за день
@report_menu.callback_query(F.data == 'outlet:report_menu:revenue')
async def revenue_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='<b>Укажите сумму выручки</b>\n\n'
                                            'Формат ввода предполагает использование цифр с десятичным разделителем: <i>123.45</i>',
                                     reply_markup=kb.cancel_button,
                                     parse_mode='HTML')
    await state.set_state(Report.revenue)


# принимаем сумму выручки
@report_menu.message(Report.revenue)
async def revenue_receiver_handler(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    
    revenue = message.text
    
    # проверяем формат ввода данных
    try:
        revenue = str(Decimal(message.text.replace(',', '.')))
    except:
        # если формат ввода не подходит, то ничего не делаем
        await state.set_state(Report.purchases)
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
                                        reply_markup=await kb.report_menu(outlet_id, report),
                                        parse_mode='HTML')
    

# просим указать примечание к отчету 
@report_menu.callback_query(F.data == 'outlet:report_menu:note')
async def revenue_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='<b>Укажите дополнительную информацию касаемо торгового дня.\n\n'
                                            'Опишите следующее:</b>\n' \
                                            '1. Чем обусловлены потери\n' \
                                            '2. Нестандартные ситуации\n' \
                                            '3. Что-либо, что необходимо знать и учесть',
                                     reply_markup=kb.cancel_button,
                                     parse_mode='HTML')
    await state.set_state(Report.note)


# принимаем примечание к отчету
@report_menu.message(Report.note)
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
    outlet_id = data['outlet_id']
    
    report = data['report']
    
    text = report_menu_text(report)
    
    await message.bot.edit_message_text(chat_id=chat_id,
                                        message_id=message_id,
                                        text=text,
                                        reply_markup=await kb.report_menu(outlet_id, report),
                                        parse_mode='HTML')
    

# просим подтверждения на сохранение отчета
@report_menu.callback_query(F.data == 'outlet:report_menu:send_report')
async def send_report_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    report = data['report']
    outlet_id = data['outlet_id']
    today = datetime.now(pytz.timezone('Europe/Chisinau'))
    
    # количество транзакций по указанию остатка должно быть равно количеству товаров с нулевым 
    balance = None
    stock_data = await get_active_stock_products(outlet_id)
    # проверяем в первую очередь били ли транзакции за день с товаром, если не было то проверяем баланс для отображения
    # если транзакции не было, то вовдим если баланс больше нуля, если транзакция была, то выводим в любом случае
    # таким образом будут выведены все товары, с которыми была или могла быть проведена транзакция
    stock_data = [stock for stock in stock_data if await were_stock_transactions(stock['stock_id'],
                                                                                 today,
                                                                                 ['balance'])
                                                or  stock['stock_qty'] != 0]
    
    transactions_number = await balance_transactions_number_today(outlet_id)
    
    if len(stock_data) == transactions_number:
        balance = True
    
    purchases = report['purchases']
    revenue = report['revenue']
    note = report['note']
    
    # сначала проверяем были ли заполнены все данные, в противном случае не даем отправить отчет
    if not all((balance, purchases, revenue, note)):
        await callback.answer(text='Не все данные были заполнены', show_alert=True)
        return None
    
    await callback.message.edit_text(text='Чтобы отправить отчет, нажмите <b>Подтвердить</b>',
                                     reply_markup=kb.confirm_report,
                                     parse_mode='HTML')
    

# При подтверждении отправки отчета создаем его и выходим в меню торговой точки
@report_menu.callback_query(F.data == 'outlet:report_menu:send_report:confirm')
async def confirm_send_report_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    outlet_id = data['outlet_id']
    report = data['report']
    
    report_data = {
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

    # удаляем данные об отчете
    report = {
            'purchases': None,
            'revenue': None,
            'note': None
            }
    await state.update_data(report=report)
    
    # переходим в меню торговой точки
    await outlet_menu_handler(callback, state)
    await callback.answer(text='Отчет успешно отправлен', show_alert=True)
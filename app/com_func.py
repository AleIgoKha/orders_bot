

# Функция группирует данные полученные из запроса
def group_orders_items(orders_items):
    order_id = 0
    orders_items_data = []
    for order, item in orders_items:
        if order_id != order.order_id:
            order_id = order.order_id
            if item != None:
                orders_items_data.append({'order_number': order.order_number,
                                        'client_name': order.client_name,
                                        'order_id': order.order_id,
                                        'order_completed': order.order_completed,
                                        'order_note': order.order_note,
                                        'order_disc': order.order_disc,
                                        f'item_{item.item_id}': {
                                            'item_id': item.item_id,
                                            'item_name': item.item_name,
                                            'item_unit': item.item_unit,
                                            'item_price': item.item_price,
                                            'item_qty': item.item_qty,
                                            'item_qty_fact': item.item_qty_fact,
                                            'item_disc': item.item_disc,
                                            'item_vacc': item.item_vacc
                                        }})
            else:
                orders_items_data.append({'order_number': order.order_number,
                                        'client_name': order.client_name,
                                        'order_id': order.order_id,
                                        'order_completed': order.order_completed,
                                        'order_note': order.order_note,
                                        'order_disc': order.order_disc})
        else:
            orders_items_data[-1][f'item_{item.item_id}'] = {
                                    'item_id': item.item_id,
                                    'item_name': item.item_name,
                                    'item_unit': item.item_unit,
                                    'item_price': item.item_price,
                                    'item_qty': item.item_qty,
                                    'item_qty_fact': item.item_qty_fact,
                                    'item_disc': item.item_disc,
                                    'item_vacc': item.item_vacc
                                }
    return orders_items_data


# формирует сообщение для меню заказа и изменения заказа
def order_text(order_items_data):
    text = f'📋 <b>ЗАКАЗ №{order_items_data['order_number']}</b>\n\n' \
            f'👤 Клиент - <b>{order_items_data['client_name']}</b>\n\n'
    
    items_list = [item for item in order_items_data.keys() if item.startswith('item_')]
    total_price = 0
    
    if items_list: # Проверяем пуст ли заказ
        for item in items_list:
            item_name = order_items_data[item]['item_name']
            item_price = order_items_data[item]['item_price']
            item_qty = order_items_data[item]['item_qty']
            item_unit = order_items_data[item]['item_unit']
            item_qty_fact = order_items_data[item]['item_qty_fact']
            item_vacc = order_items_data[item]['item_vacc']
            
            if item_vacc:
                item_vacc = ' (вак. уп.)'
            else:
                item_vacc = ''
                
            text += f'🧀 <b>{item_name}{item_vacc}</b>\n'
            
            if item_unit == 'кг': # Переводим килограмы в граммы
                text += f'Заказано - <b>{int(item_qty * 1000)} {item_unit[-1]}</b>\n' \
                        f'Взвешено - <b>{int(item_qty_fact * 1000)} {item_unit[-1]}</b>\n'
            else:
                text += f'Заказано - <b>{int(item_qty)} {item_unit}</b>\n' \
                        f'Взвешено - <b>{int(item_qty_fact)} {item_unit}</b>\n'
            # Рассчитываем стоимость всключая вакуум
            
            if item_vacc:
                if item_qty_fact == 0:
                    vacc_price = 0
                elif 0 < item_qty_fact < 200:
                    vacc_price = 5
                elif 200 <= item_qty_fact < 300:
                    vacc_price = 6
                elif 300 <= item_qty_fact:
                    vacc_price = (item_qty_fact * 2) / 100
            else:
                vacc_price = 0

            item_price = round(item_qty_fact * float(item_price) + vacc_price)
            total_price += item_price
            
            text += f'Стоимость - <b>{item_price} р</b>\n\n'
                
    else:
        text += '<b>Заказ пуст 🤷‍♂️</b>\n\n'
    
    order_disc = order_items_data['order_disc']
    if order_disc > 0:
        disc = f' (Скидка - {order_disc}% - {round(total_price * ((100 - order_disc) / 100))} р)'
    else:
        disc = ''
    
    text += f'🧾 <b>К ОПЛАТЕ</b> - <b>{round(total_price * ((100 - order_disc) / 100))} р</b>{disc}\n\n'
    
    order_note = order_items_data['order_note']
    if order_note:
        text += f'<b>📝 Комментарий к заказу</b>\n{order_note}'  
    return text
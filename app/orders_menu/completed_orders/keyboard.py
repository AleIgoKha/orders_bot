from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Клавиатура кнопка "Изменить" для заказа
def change_button(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✍️ Изменить', callback_data=f'{order_id}_change_order')]
        ])

# Клавиатура кнопка "Назад в меню" для возврата из меню обработки заказов
def last_change_button(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✍️ Изменить', callback_data=f'{order_id}_change_order')],
        [InlineKeyboardButton(text='⬅️ Назад в меню', callback_data=f'back_from_order_changing')]
        ])
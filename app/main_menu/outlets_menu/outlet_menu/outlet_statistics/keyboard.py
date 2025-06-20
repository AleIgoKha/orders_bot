from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date
from calendar import monthrange


# Календарь для выбора даты
def calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard representing a calendar for the given year and month.
    """
    keyboard = []
    months = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь"}
    keyboard.append([InlineKeyboardButton(text=f'{year} {months[month]}', callback_data="ignore")])
    days_of_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard.append([InlineKeyboardButton(text=day, callback_data="ignore") for day in days_of_week])

    first_day = date(year, month, 1)
    first_day_weekday = first_day.weekday()  # Monday is 0, Sunday is 6
    days_in_month = monthrange(year, month)[1]
    day_counter = 1

    for week in range(6):  # Up to 6 weeks can be displayed
        row = []
        for day_of_week in range(7):
            if week == 0 and day_of_week < first_day_weekday:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            elif day_counter > days_in_month:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                day_text = str(day_counter)
                if day_counter == date.today().day and month == date.today().month and year == date.today().year:
                    day_text = '🌞'
                callback_data = f"outlet:statistics:date:{year}:{month}:{day_counter}"
                row.append(InlineKeyboardButton(text=day_text, callback_data=callback_data))
                day_counter += 1
        keyboard.append(row)
        if day_counter > days_in_month:
            break
    
    additional_buttons = [
        InlineKeyboardButton(text='📊 За все время', callback_data=f'outlet:statistics:total_stats')
    ]

    keyboard.append(additional_buttons)

    navigation_buttons = [
        InlineKeyboardButton(text="⬅️ Ранее", callback_data=f"outlet:statistics:month:prev:{year}:{month}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="outlet:back"),
        InlineKeyboardButton(text="➡️ Позднее", callback_data=f"outlet:statistics:month:next:{year}:{month}"),
    ]
    keyboard.append(navigation_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# кнопка назад для выхода из статистики
back_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='outlet:back')]
])
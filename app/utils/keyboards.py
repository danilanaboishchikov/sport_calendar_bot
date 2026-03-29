from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup, )

from app.utils import utils
from config import access_price


menu_button = InlineKeyboardButton(text=f'В меню 🔙', callback_data='menu')

def get_access_keyboard(access_request):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text=f'💸 Оплатить {access_price} ₽', callback_data=f'access:pay:{access_price}'),
        InlineKeyboardButton(text=f'🤝 Запросить доступ', callback_data='access:request:0') if not access_request else
        InlineKeyboardButton(text=f'📥 Запрос уже отправлен ', callback_data='access:send:0'),
    )
    return keyboard

def make_menu_button():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(menu_button)
    return keyboard

def get_main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text=f'🏃 Мой спорт', callback_data='user:sport'),
        InlineKeyboardButton(text=f'🧘 Добавить в дневной отчёт', callback_data='user:daily-report'),
        InlineKeyboardButton(text=f'👤 Мой аккаунт', callback_data='user:account'),
        InlineKeyboardButton(text=f'🫗 Питьё воды', callback_data='user:water'),
    )
    return keyboard


def get_my_sport_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text=f'🏋️ Мои тренировки', callback_data='user:trains'),
        InlineKeyboardButton(text=f'🤸 Мои упражнения', callback_data='user:exercises'),
        InlineKeyboardButton(text=f'🛠️ Добавить тренировку', callback_data='user:add_train'),
        InlineKeyboardButton(text=f'⚒️ Добавить упражнение', callback_data='user:add_exercise'),
        menu_button,
    )
    return keyboard


def get_check_payment_keyboard(url, label, price):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        InlineKeyboardButton(text=f'Оплатить 💸', url=url),
        InlineKeyboardButton(text=f'Проверить оплату 💱', callback_data=f'check-payment:{label}')
    )
    return keyboard


def get_admin_access_to_user_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text=f'Доступ на неделю 📅', callback_data=f'access:admin:7:{user_id}'),
        InlineKeyboardButton(text=f'Доступ на месяц 📅', callback_data=f'access:admin:30:{user_id}'),
    )
    keyboard.row(
        InlineKeyboardButton(text=f'Доступ на год 🌍', callback_data=f'access:admin:365:{user_id}'),
        InlineKeyboardButton(text=f'Доступ навсегда ♾️', callback_data=f'access:admin:0:{user_id}')
    )
    keyboard.row(
        InlineKeyboardButton(text=f'Отказать ❌', callback_data=f'access:admin:-1:{user_id}'),
    )
    return keyboard


def get_admin_choice(days):
    keyboard = InlineKeyboardMarkup(row_width=1)
    if int(days) > 0: message = f'Одобрен доступ на {days} дней 📅'
    elif int(days) == 0: message = 'Одобрен доступ навсегда ♾️'
    else: message = 'Запрос отклонён ❌'
    keyboard.add(
        InlineKeyboardButton(text=message, callback_data='free')
    )
    return keyboard


def make_user_sports_keyboard(sports):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for sport in sports:
        keyboard.add(
            InlineKeyboardButton(text=sport['name']+' ➡️🗑️', callback_data=f'delete-sport:{sport['sport_id']}:{sport['type']}'),
        )
    keyboard.add(menu_button)

    return keyboard


def make_cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(text='Отменить'))
    return keyboard


def make_delete_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(text='Удалить'))
    return keyboard


def make_daily_report_keyboard(user_id, sports, data, comment=None, emotion=None, evening=False):
    keyboard = InlineKeyboardMarkup(row_width=2)

    print(sports)
    trains = [i for i in sports if i['type'] == 'train']
    exercises = [i for i in sports if i['type'] == 'exercise']

    trl, exl = len(trains), len(exercises)
    if trl > exl:
        for _ in range(trl-exl):
            exercises.append({'sport_id': '-'})
    else:
        for _ in range(exl-trl):
            trains.append({'sport_id': '-'})

    keyboard.row(
        InlineKeyboardButton(text='Тренировки ⬇️', callback_data='no'),
        InlineKeyboardButton(text='Упражнения ⬇️', callback_data='no'),
    )

    for i in range(max(trl, exl)):
        train = trains[i]
        train_id = trains[i]['sport_id']

        exercise = exercises[i]
        exercise_id = exercise['sport_id']

        if train_id == '-': train_button = InlineKeyboardButton(text='-', callback_data='no')
        elif any(i for i in data if i[0] == train_id): train_button = InlineKeyboardButton(text='✅ '+train['name'] , callback_data=f'daily-report:edit:{train_id}')
        else: train_button = InlineKeyboardButton(text=train['name'], callback_data=f'daily-report:add:{train_id}')

        if exercise_id == '-': exercise_button = InlineKeyboardButton(text='-', callback_data='no')
        elif any(i for i in data if i[0] == exercise_id): exercise_button = InlineKeyboardButton(text='✅ '+exercise['name'] ,callback_data=f'daily-report:edit:{exercise_id}')
        else: exercise_button = InlineKeyboardButton(text=exercise['name'], callback_data=f'daily-report:add:{exercise_id}')

        keyboard.row(train_button, exercise_button)

    keyboard.row(
        InlineKeyboardButton(text='Выберите свое настроение/состояние ⬇️', callback_data='no'),
    )

    chosen_emotion = emotion

    if not chosen_emotion:
        keyboard.row(
            InlineKeyboardButton(text='😇', callback_data='daily-report:emotion:best'),
            InlineKeyboardButton(text='🙂', callback_data='daily-report:emotion:good'),
            InlineKeyboardButton(text='😐', callback_data='daily-report:emotion:norm'),
            InlineKeyboardButton(text='😭', callback_data='daily-report:emotion:cry'),
            InlineKeyboardButton(text='😡', callback_data='daily-report:emotion:angry'),
        )
    else:
        keyboard.row(
            InlineKeyboardButton(text='😇 ✅' if chosen_emotion=='best' else '😇', callback_data='daily-report:emotion:best'),
            InlineKeyboardButton(text='🙂 ✅' if chosen_emotion=='good' else '🙂', callback_data='daily-report:emotion:good'),
            InlineKeyboardButton(text='😐 ✅' if chosen_emotion=='norm' else '😐', callback_data='daily-report:emotion:norm'),
            InlineKeyboardButton(text='😭 ✅' if chosen_emotion=='cry' else '😭', callback_data='daily-report:emotion:cry'),
            InlineKeyboardButton(text='😡 ✅' if chosen_emotion=='angry' else '😡', callback_data='daily-report:emotion:angry'),
        )

    if not comment:
        keyboard.row(
            InlineKeyboardButton(text='Ввести комментарий 📤', callback_data='daily-report:comment:0'),
        )
    else:
        keyboard.row(
            InlineKeyboardButton(text='Комментарий введён ✅', callback_data='no'),
        )

    if not evening:
        keyboard.row(
            InlineKeyboardButton(text='Сохранить ✅', callback_data='daily-report:save:0'),
        )

    keyboard.row(
        InlineKeyboardButton(text='Загрузить ☁️', callback_data='daily-report:load:0'),
    )

    return keyboard


def make_my_account_keyboard(user):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text=f'📃 Получить подробный отчёт', callback_data=f'account:full_review:0'),
    )
    keyboard.row(
        InlineKeyboardButton(text=f'✍️ Заполнить "О себе"', callback_data=f'account:about_me:0'),
    )
    keyboard.row(
        InlineKeyboardButton(text=f'⏰ Напоминания', callback_data=f'account:full_review:0'),
    )
    keyboard.row(
        InlineKeyboardButton(text=f'💦 Питьё воды', callback_data=f'account:reminder:water'),
        InlineKeyboardButton(text=f'🏃‍♂️‍➡️ Активность', callback_data=f'account:reminder:active'),
    )
    keyboard.row(
        InlineKeyboardButton(text=f'⬇️ Утреннее ⬇️', callback_data=f'no'),
        InlineKeyboardButton(text=f'⬇️ Вечернее ⬇️', callback_data=f'no'),
    )
    keyboard.row(
        InlineKeyboardButton(text=f'🏙️ {user['morning_reminder']}', callback_data=f'account:morning:0'),
        InlineKeyboardButton(text=f'🌇 {user['evening_reminder']}', callback_data=f'account:evening:0'),
    )
    keyboard.row(menu_button)
    return keyboard


def make_water_remind_keyboard(user, arg=None):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text=f'🎯 Цель: {user['water_limit']} л. в день', callback_data=f'no'),
    )
    if not arg:
        keyboard.row(
            InlineKeyboardButton(text=f'Выберите объём выпитой воды', callback_data=f'no'),
        )
        keyboard.row(
            InlineKeyboardButton(text=f'150 мл', callback_data=f'water:drink:0.15'),
            InlineKeyboardButton(text=f'200 мл', callback_data=f'water:drink:0.2'),
            InlineKeyboardButton(text=f'300 мл', callback_data=f'water:drink:0.3'),
        )
        keyboard.row(
            InlineKeyboardButton(text=f'400 мл', callback_data=f'water:drink:0.4'),
            InlineKeyboardButton(text=f'500 мл', callback_data=f'water:drink:0.5'),
            InlineKeyboardButton(text=f'600 мл', callback_data=f'water:drink:0.6'),
        )
        keyboard.row(
            InlineKeyboardButton(text=f'700 мл', callback_data=f'water:drink:0.7'),
            InlineKeyboardButton(text=f'850 мл', callback_data=f'water:drink:0.85'),
            InlineKeyboardButton(text=f'1 л', callback_data=f'water:drink:1'),
        )
    keyboard.row(menu_button)

    return keyboard


def make_water_menu_keyboard(user, arg=None):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text=f'🎯 Цель: {user['water_limit']} л. в день', callback_data=f'no'),
    )
    keyboard.row(
        InlineKeyboardButton(text=f'🖋️ Изменить дневную цель', callback_data=f'water:change:0'),
    )

    keyboard.row(
        InlineKeyboardButton(text=f'Выберите объём выпитой воды', callback_data=f'no'),
    )
    keyboard.row(
        InlineKeyboardButton(text=f'150 мл', callback_data=f'water:drink:0.150'),
        InlineKeyboardButton(text=f'200 мл', callback_data=f'water:drink:0.200'),
        InlineKeyboardButton(text=f'300 мл', callback_data=f'water:drink:0.300'),
    )
    keyboard.row(
        InlineKeyboardButton(text=f'400 мл', callback_data=f'water:drink:0.400'),
        InlineKeyboardButton(text=f'500 мл', callback_data=f'water:drink:0.500'),
        InlineKeyboardButton(text=f'600 мл', callback_data=f'water:drink:0.600'),
    )
    keyboard.row(
        InlineKeyboardButton(text=f'700 мл', callback_data=f'water:drink:0.700'),
        InlineKeyboardButton(text=f'850 мл', callback_data=f'water:drink:0.850'),
        InlineKeyboardButton(text=f'1 л', callback_data=f'water:drink:1'),
    )
    keyboard.row(menu_button)
    return keyboard


def choose_reminder_edit_times_keyboard(user, case):
    times = sorted(user[f'{case}_times'].split('!'))
    buttons = utils.split_for_parts(times, 4)
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text=f'✍️ Добавить время', callback_data=f'add_time;add;{case}'),
    )
    keyboard.row(
        InlineKeyboardButton(text=f'🕑 Выберите время для напоминаний:', callback_data=f'no'),
    )
    for row in buttons:
        keyboard.row(
            InlineKeyboardButton(text=row[0], callback_data=f'add_time;{case};{row[0]}') if len(row) >= 1 else InlineKeyboardButton(text='-', callback_data=f'no'),
            InlineKeyboardButton(text=row[1], callback_data=f'add_time;{case};{row[1]}') if len(row) >= 2 else InlineKeyboardButton(text='-', callback_data=f'no'),
            InlineKeyboardButton(text=row[2], callback_data=f'add_time;{case};{row[2]}') if len(row) >= 3 else InlineKeyboardButton(text='-', callback_data=f'no'),
            InlineKeyboardButton(text=row[3], callback_data=f'add_time;{case};{row[3]}') if len(row) >= 4 else InlineKeyboardButton(text='-', callback_data=f'no'),
        )
    keyboard.row(menu_button)
    return keyboard


def make_daily_report_button():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text=f'🧘 Добавить в дневной отчёт', callback_data='user:daily-report'))
    return keyboard
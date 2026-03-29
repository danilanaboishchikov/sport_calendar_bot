from telebot.util import user_link

import config
from app.database import database as db
from app.utils import utils


AI_FULL_REPORT_MESSAGE = '''Проанализируй данные тренировок пользователя за неделю. Отчёт должен содержать 6 обязательных разделов (эмодзи и теги — часть структуры):

<b>🔍 Обзор активности</b>

Что включать:

Количество тренировочных дней vs пропуски (с датами).

Диапазон интенсивности (макс./мин. нагрузка).

Формат: "Тренировочные дни: X из Y (даты), Пропуски: [даты, если есть]".

<b>💪 Прогресс по упражнениям</b>

Что включать:

Динамику по каждому упражнению (рост/спад в %).

Выделять рекорды и аномалии (⚠️).

Формат: "Упражнение: значение1 (дата) → значение2 (дата) — изменение на X%".

<b>😌 Состояние и мотивация</b>

Что включать:

Корреляцию эмоций (комментарии пользователя) с нагрузкой.

Тренды настроения (например, "пик позитива при рекорде").

Формат: "Состояние: [эмодзи] + цитата/описание".

<b>⚠️ Проблемные зоны</b>

Что включать:

3 ключевые проблемы (например, неравномерность, пропуски).

Конкретные примеры из данных.

Формат: Нумерованный список с пояснениями.

<b>🎯 РЕКОМЕНДАЦИИ</b>

Что включать:

4-5 действий для улучшения (стабилизация, систематизация, вариативность).

Конкретные цифры/диапазоны (например, "диапазон 40-50 повторов").

Формат: Нумерованный список с подпунктами.

<b>💡 План на следующую неделю</b>

Что включать:

Примерный график (дни + тип нагрузки).

Цели (+X% к упражнениям, минимум пропусков).

Формат: "День: Упражнение (объём) + Новое упражнение (опционально)".

🔹 ТРЕБОВАНИЯ К ФОРМАТУ:

Объём: ≤ 3000 символов.

Язык: только русский.

Стиль: профессиональный, но с эмодзи для наглядности.

Акцент: на структуру данных, а не на конкретные упражнения.'''


def make_access_user_message(message):
    answer = f'🔔 Новая заявка на получение доступа!\n<b>Пользователь:</b> {user_link(message.from_user)}\n<b>Комментарий:</b> {message.text}\n\nПожалуйста, выберите один из вариантов ниже.'
    return answer


def make_user_access_notification(days):
    if int(days) > 0: message = f'Вам одобрен доступ на {days} дней 📅'
    elif int(days) == 0: message = 'Вам одобрен доступ навсегда ♾️'
    else: message = 'Ваш запрос на доступ отклонён ❌\nВы можете оплатить доступ.'
    return message

def make_user_sport_message(user, users_sport):
    cnt_trains, cnt_exercise = 0, 0
    for sport in users_sport:
        if sport['type'] == 'train':
            cnt_trains += 1
        else:
            cnt_exercise += 1

    message = f'Вы в меню вашего спорта 🏋️\n\nЗдесь можно добавить или удалить тренировки и упражнения.\n\nСейчас в вашем аккаунте:\n{cnt_exercise} упражнений\n{cnt_trains} тренировок\nВсего: {cnt_exercise+cnt_trains} позиций.\n\nВыберите одну из кнопок ниже.'

    return message

def make_sport_list_for_ai(users_sport):
    trains_message = 'Тренировки пользователя: '
    exercises_message = 'Упражнения пользователя: '
    for sport in users_sport:
        if sport['type'] == 'train':
            trains_message += sport['name'] + ' - ' + sport['description'] + '; '
        else:
            exercises_message += sport['name'] + '; '
    return trains_message + '\n' + exercises_message

def make_my_sports_message(sports, sport_type):
    message = f'Всего у вас {"тренировок" if sport_type == 'trains' else 'упражнений'}: {len(sports)}.\n\nЕсли вы хотите удалить какую-либо {"тренировку" if sport_type == 'train' else 'упражнение'}, то нажмите на соответствующую кнопку ниже.'
    return message


def make_sport_report_message(report, user): # = - разделитель значений, ! - разделителей позиций
    message = f'<b>Отчёт за {report['date']} 📋</b>\n'
    comment = report['comment']
    emotion = report['emotion']
    data = sorted([i.split('=') if '=' in i else [i] for i in report['sports'].split('!')], key=lambda x: -len(x))
    exercises = [i for i in data if len(i) == 2]
    trains = [i[0] for i in data if len(i) == 1]

    i = 1

    if exercises:
        message += '\n🔺 Упражнения:\n'

        for exercise_id, value in exercises:
            exercise = db.get_sport_by_id(exercise_id)
            message += f'   {i}. {exercise['name']} - {value}.\n'
            i += 1

    if trains:
        message += '\n🔺 Тренировки:\n'

        for train_id in trains:
            train = db.get_sport_by_id(train_id)
            message += f'   {i}. {train['name']}.\n'
            i += 1
    if emotion:
        message += f'\nСостояние: {config.emotions[report['emotion']]}\n'
    if comment:
        message += f'\nКомментарий: {report['comment']}'


    return message


def make_long_sport_report(report, user): # = - разделитель значений, ! - разделителей позиций
    message = f'<b>Отчёт за {report['date']} 📋</b>\n'

    data = sorted([i.split('=') if '=' in i else i for i in report['sports'].split('!')], key=lambda x: -len(x))
    exercises = [i for i in data if len(i) == 2]
    trains = [i for i in data if len(i) == 1]

    comment, emotion = report['comment'], report['emotion']

    i = 1

    if exercises:
        message += '\n🔺 Упражнения:\n'

        for exercise_id, value in exercises:
            exercise = db.get_sport_by_id(exercise_id)
            message += f'   {i}. {exercise['name']} - {value}.\n'
            i+=1

    if trains:
        message += '\n🔺 Тренировки:\n'

        for train_id in trains:
            exercise = db.get_sport_by_id(train_id)
            message += f'   {i}. {exercise['name']} - {exercise['description']}.\n'
            i+=1
    if emotion:
        message += f'\nСостояние: {config.emotions[report['emotion']]}\n'
    if comment:
        message += f'Комментарий пользователя к тренировке: {report['comment']}\n'

    message += f'\n{user['info']}'

    return message


def make_daily_report_message(user, data, comment=None, emotion='-', evening=False):
    trains = [i[0] for i in data if len(i) == 1]
    exercises = [i for i in data if len(i) == 2]

    i=1

    message = f'✍️ Дополняем отчёт за {utils.get_current_date()}:\n' if not evening else f'🚩 Завершаем отчёт за {utils.get_current_date()}:\n'
    if exercises:
        message += '\n🔺 Упражнения:\n'

        for exercise_id, value in exercises:
            exercise = db.get_sport_by_id(exercise_id)
            message += f'   {i}. {exercise['name']} - {value}.\n'
            i+=1
    if trains:
        message += '\n🔺 Тренировки:\n'

        for train_id in trains:
            exercise = db.get_sport_by_id(train_id)
            message += f'   {i}. {exercise['name']} - <i>{exercise['description'][:30]}...</i>.\n'
            i+=1

    if emotion:
        message += f'\nСостояние: {config.emotions.get(emotion, '-')}\n'
    if comment:
        message += f'Личный комментарий: {comment}\n'

    if not trains and not exercises: message += '\nПока пусто...\n'
    message += '\nИспользуй кнопки ниже для редактирования отчёта:\n- Нажатие на тренировку добавляет её в отчёт, повторное нажатие удаляет её из отчёта\n- После нажатия на "Загрузить ☁️" изменить отчёт нельзя. Для промежуточного сохранения используйте "Сохранить ✅"'

    return message


def make_account_message(user, reports):
    strike = db.count_strike(user['user_id'])
    strike_data = utils.get_strike_sticker(strike)
    message = f' 👤<b> Информация об аккаунте #{user['user_id']}:</b>\n\n<b>⚡ СТРАЙК</b> - <i>дни тренировок подряд:</i> {strike}\n<b>🪪 Статус страйка:</b> {strike_data[1]} {strike_data[0]}\n\n<b>Всего тренировок: </b>{len(reports)}\n\n<b>Информация о себе:</b> {user['info'] if user['info'] else '<i>не заполнено</i>'}'
    #TODO: ДОБАВИТЬ ПОДРОБНУЮ СТАТИСТИКУ
    return message


def make_water_menu_message(user, current_water):
    message = f'🔔 {user['first_name']}, меню воды 🫗\n\n<b>Ваш прогресс:</b> {round(current_water.get('drink', 0), 2)} л. / {user['water_limit']} л.\n{utils.format_taskbar(current_water.get('drink', 0), user['water_limit'])}. \nВыберите объём выпитой воды ниже 👇'
    return message


def make_water_reminder_message(user, current_water):
    message = f'🔔 {user['first_name']}, пора выпить стакан воды 🫗\n\n<b>Ваш прогресс:</b> {round(current_water.get('drink', 0), 2)} л. / {user['water_limit']} л.\n{utils.format_taskbar(current_water.get('drink', 0), user['water_limit'])}\n\nВам нужно выпить стакан воды. \nВыберите объём выпитой воды ниже 👇'
    return message


def make_reminder_edit_time(user, case):
    times = ', '.join(user[f'{case}_times'].split('!'))
    message = f'🕡 Меню редактирования напоминаний <b>{'активности 🏃‍♂️‍➡️' if case == 'active' else 'питья воды 💦'}</b>\n\n<b>Выбранные для напоминаний времена: </b>{times}\n\nВы можете добавить время, удалить или выбрать существующее.'
    return message
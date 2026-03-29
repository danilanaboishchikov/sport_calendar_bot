from app.database import database as db
from app.utils import keyboards
from config import access_price, bot, admin_id, user_states, user_data
from app.utils import messages
from app.utils import utils


async def send_main_menu(first_name, chat_id, user_id):
    user_exists, user = db.check_or_return_user_registration(user_id)
    access, access_request = user.get('access', False), user.get('access_request', False)

    if not access:
        await bot.send_message(chat_id,
                               f'У вас нет доступа к боту. Вы можете или оплатить {access_price} рублей, или запросить доступ у администратора.',
                               reply_markup=keyboards.get_access_keyboard(access_request))
    else:
        await bot.send_message(chat_id,
                               f'👋 Доброго времени суток, {first_name}!\nВы в главном меню:',
                               reply_markup=keyboards.get_main_menu_keyboard())

async def command_handler(message):
    # Обработчик команд
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    # Проверка регистрации и получение данных, если пользователь существует
    user_exists, user = db.check_or_return_user_registration(user_id)

    if not user_exists: # если не существует, регистрируем
        db.register_user(user_id, message.from_user.first_name, message.from_user.username if message.from_user.username else '')

    if text == '/start':
        await send_main_menu(message.from_user.first_name, message.chat.id, message.from_user.id)


async def update_daily_report(chat_id, user_id, edit=False, message_id=0, evening=False):
    user = db.check_or_return_user_registration(user_id)
    sports = db.get_user_sport(user_id, 'all')

    if user_id not in user_data: user_data[user_id] = {}
    if 'report' not in user_data[user_id]: user_data[user_id]['report'] = []

    current_report = user_data[user_id]['report']

    if edit:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=messages.make_daily_report_message(user, current_report, user_data[user_id].get('comment', None), user_data[user_id].get('emotion', None), evening),
                               reply_markup=keyboards.make_daily_report_keyboard(user_id, sports, current_report, user_data[user_id].get('comment', None), user_data[user_id].get('emotion', None), evening))
    else:
        await bot.send_message(chat_id, messages.make_daily_report_message(user, current_report, user_data[user_id].get('comment', None), user_data[user_id].get('emotion', None), evening),
                               reply_markup=keyboards.make_daily_report_keyboard(user_id, sports, current_report, user_data[user_id].get('comment', None), user_data[user_id].get('emotion', None), evening))


async def update_water_message(chat_id, user_id, edit=False, message_id=0, arg=None):
    exist, user = db.check_or_return_user_registration(user_id)
    if 'water' in user_data[user_id]:
        current_water = user_data[user_id]['water'].get(utils.get_current_date(), {'drink': 0})
        if utils.get_current_date() not in user_data[user_id]['water']:
            user_data[user_id]['water'][utils.get_current_date()] = {}
    else:
        user_data[user_id]['water'] = {utils.get_current_date(): {'drink': 0}}
        current_water = {'drink': 0}

    if edit:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=messages.make_water_menu_message(user, current_water),
                               reply_markup=keyboards.make_water_menu_keyboard(user, arg))

    else:
        await bot.send_message(chat_id, messages.make_water_menu_message(user, current_water),
                               reply_markup=keyboards.make_water_menu_keyboard(user))


async def update_reminder_time_editing_message(chat_id, user_id, case, edit=False, message_id=0):
    exist, user = db.check_or_return_user_registration(user_id)

    if edit:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=messages.make_reminder_edit_time(user, case),reply_markup=keyboards.choose_reminder_edit_times_keyboard(user, case))
    else:
        await bot.send_message(chat_id, messages.make_reminder_edit_time(user, case), reply_markup=keyboards.choose_reminder_edit_times_keyboard(user, case))


async def handler_new_reminder_time_to_add(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    case = user_data[user_id]['reminder_time_data']['case']
    message_id = user_data[user_id]['reminder_time_data']['message_id']
    if utils.time_validator(text):
        db.edit_reminder_times(user_id, case, 'add', text)
        await update_reminder_time_editing_message(chat_id, user_id, case, True, message_id)
        user_states[user_id] = ''
    else:
        await bot.send_message(chat_id, 'Что-то не так. Введите время в формате hh:mm, например 17:30.')

async def access_comment_handler(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    await bot.send_message(chat_id, 'Спасибо 🤝\nВаш запрос отправлен администратору. Ожидайте!')
    await bot.send_message(admin_id, messages.make_access_user_message(message), reply_markup=keyboards.get_admin_access_to_user_keyboard(user_id))
    db.set_user_send_access_request(user_id)
    user_states[user_id] = ''


async def handler_new_water_limit(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    try:
        new_limit = float(message.text.replace(',','.'))
        db.change_user_data(user_id, ['water_limit'], [new_limit])
        await bot.send_message(chat_id, f'Новый лимит в {new_limit} л. в день установлен.')
        await update_water_message(chat_id, user_id, True, user_data[user_id]['water'][utils.get_current_date()]['message_id'])
        user_states[user_id] = ''
    except Exception as er:
        print(er)
        await bot.send_message(chat_id, f'Введите число с плавающей точкой, например 4.5.')





async def train_name_handler(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    if message.text.lower() == 'отменить':
        await bot.send_message(chat_id, 'Действие отменено!')
        await send_main_menu(message.from_user.first_name, chat_id, user_id)
        user_states[user_id] = ''
    else:
        user_states[user_id] = 'wait_train_description'
        user_data[user_id] = {'name': text, 'type': 'train'}
        await bot.send_message(chat_id, 'Введите описание тренировки или нажмите "отменить":', reply_markup=keyboards.make_cancel_keyboard())


async def exercise_name_handler(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    if message.text.lower() == 'отменить':
        await bot.send_message(chat_id, 'Действие отменено!')
        await send_main_menu(message.from_user.first_name, chat_id, user_id)
        user_states[user_id] = ''
    else:
        user_states[user_id] = 'wait_exercise_question'
        user_data[user_id] = {'name': text, 'type': 'exercise'}
        await bot.send_message(chat_id, 'Введите вопрос для ввода данных по упражнению (например: "Сколько отжиманий вы сделали?") или нажмите "отменить":', reply_markup=keyboards.make_cancel_keyboard())

async def exercise_question_handler(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    if message.text.lower() == 'отменить':
        await bot.send_message(chat_id, 'Действие отменено!')
        await send_main_menu(message.from_user.first_name, chat_id, user_id)
        user_states[user_id] = ''
    else:
        user_data[user_id]['question'] = text
        db.add_sport(user_id, user_data[user_id])
        await bot.send_message(chat_id, f'Упражнение "{user_data[user_id]['name']}" успешно добавлено!')
        await send_main_menu(message.from_user.first_name, chat_id, user_id)

    user_states[user_id] = ''



async def train_description_handler(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    if message.text.lower() == 'отменить':
        await bot.send_message(chat_id, 'Действие отменено!')
        await send_main_menu(message.from_user.first_name, chat_id, user_id)
        user_states[user_id] = ''
    else:
        user_data[user_id]['description'] = text
        db.add_sport(user_id, user_data[user_id])
        await bot.send_message(chat_id, f'Тренировка "{user_data[user_id]['name']}" успешно добавлена!')
        await send_main_menu(message.from_user.first_name, chat_id, user_id)

    user_states[user_id] = ''


async def report_date_handler(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    if utils.check_date(text):
        result, data = db.check_date_for_report_exist(text, user_id)
        _, user = db.check_or_return_user_registration(user_id)
        if result:
            await bot.send_message(chat_id, messages.make_sport_report_message(data, user))
        else:
            pass
            # заполняем отчёт за день

        user_states[user_id] = ''
    else:
        await bot.send_message(chat_id, 'Вы ввели некорректную дату. Пример: 03.04.25')


async def exercise_added_value_handler(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    user_data[user_id]['report'].append([user_data[user_id]['wait_added_exercise_value'], text])
    await update_daily_report(chat_id, user_id, True, user_data[user_id]['wait_added_exercise_value_message_id'])

    user_states[user_id] = ''


async def exercise_changed_value_handler(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id
    # wait_changed_exercise_value
    if text.lower() == 'удалить':
        for i in range(len(user_data[user_id]['report'])):
            if user_data[user_id]['report'][i][0] == user_data[user_id]['wait_changed_exercise_value']:
                user_data[user_id]['report'].pop(i)
                break

    else:
        if utils.is_digit(text):
            for i in range(len(user_data[user_id]['report'])):
                if user_data[user_id]['report'][i][0] == user_data[user_id]['wait_changed_exercise_value']:
                    print(text, user_data[user_id]['report'][i][1])
                    if '+' not in text:
                        user_data[user_id]['report'][i][1] = int(text)
                    else:
                        user_data[user_id]['report'][i][1] = int(user_data[user_id]['report'][i][1]) + int(text[1:])
                    break
        else:
            await bot.send_message(chat_id, 'Введено не число. Попробуйте ещё раз.')
            return

    await update_daily_report(chat_id, user_id, True, user_data[user_id]['wait_changed_exercise_value_message_id'])
    user_states[user_id] = ''

async def report_comment_handler(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id
    if text.lower() == 'отменить':
        user_states[user_id] = ''
    elif len(text) > 128:
        await bot.send_message(chat_id, f'Ограничение 128 символов, сейчас {len(text)}')
    else:
        user_data[user_id]['comment'] = text
        await update_daily_report(chat_id, user_id, True, user_data[user_id]['wait_comment_message_id'])
        user_states[user_id] = ''


async def new_reminder_time_handler(message, case):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    if utils.time_validator(text):
        db.change_user_data(user_id, [case+'_reminder'], [text])
        await bot.send_message(chat_id, 'Время успешно изменено!')
        user_states[user_id] = ''
    else:
        await bot.send_message(chat_id, 'Вы ввели время в неправильно формате. Попробуйте ещё раз или нажмите "отменить"')


async def handler_user_about(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    db.change_user_data(user_id, ['info'], [message.text])
    user_states[user_id] = ''

    await bot.send_message(chat_id, 'Информация успешно изменена!')
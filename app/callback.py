import os
from telebot.types import InlineKeyboardMarkup
import config
from app.utils.keyboards import make_menu_button
from config import bot, access_price, user_states, user_data, ai_reports
from app.utils import keyboards
from app.utils import logger
from app.database import database as db
from app.payment import payment
from app.utils import utils
from app.main_handler import send_main_menu, update_daily_report, update_water_message, \
    update_reminder_time_editing_message
from app.utils import messages
from app.database import excel
from app import ai

async def delete(call):
    try:
        await bot.delete_message(call.message.chat.id, call.message.id)
    except Exception as er:
        print(er)


async def access_callback_handler(call):
    chat_id, user_id = call.message.chat.id, call.from_user.id
    case = call.data.split(':')[1]
    data = call.data.split(':')[2:]

    if case == 'pay':
        label = utils.generate_label()
        payment_url = payment.make_payment_url(access_price, label)
        qrcode = utils.create_qr_code(payment_url)

        await bot.send_photo(chat_id, qrcode,
            caption=f'Перейдите по ссылке и оплатите {access_price} рублей, чтобы получить доступ.\n\n<b>Распределение ваших донатов:</b>\n25% - чаевые создателю\n25% - оплата сервере для бота\n50% - пожертвование на сбор для СВО.',
            reply_markup=keyboards.get_check_payment_keyboard(payment_url, label, access_price)
        )
    elif case == 'request':
        _, user = db.check_or_return_user_registration(user_id)
        if not bool(int(user['access_request'])):
            await bot.send_message(chat_id, 'Укажите комментарий для администратора:')
            config.user_states[user_id] = 'wait_access_comment'
        else:
            await bot.answer_callback_query(call.id, 'Вы уже отправили заявку. Ожидайте, пожалуйста.')
    elif case == 'send':
        await bot.answer_callback_query(call.id, 'Вы уже отправили заявку. Ожидайте, пожалуйста.')
    elif case == 'admin':
        time, client_id = int(data[0]), int(data[1])
        await bot.edit_message_reply_markup(chat_id, call.message.id, reply_markup=keyboards.get_admin_choice(time))
        await bot.send_message(client_id, messages.make_user_access_notification(time))

        if time != -1:
            if time == 0:
                db.give_unlimited_access(client_id)
            else:
                db.give_temporary_access(client_id, time)


async def check_payment_handler(call):
    chat_id, user_id = call.message.chat.id, call.from_user.id

    _, label = call.data.split(':')

    if payment.check_payment(label):
        await delete(call)
        await bot.send_message(chat_id, 'Оплата прошла успешно! Теперь у вас есть бессрочный доступ к боту.')
        db.give_unlimited_access(user_id)

        await send_main_menu(call.from_user.first_name, chat_id, user_id)
    else:
        await bot.answer_callback_query(call.id, 'Оплата не прошла. Попробуйте ещё раз позже.', show_alert=True)


async def delete_sport(call):
    chat_id, user_id = call.message.chat.id, call.from_user.id
    _, sport_id, sport_type = call.data.split(':')

    db.delete_sport_by_sport_id(sport_id)
    sports = db.get_user_sport(user_id, sport_type)
    await bot.edit_message_text(chat_id=chat_id, message_id=call.message.id,
                                text=messages.make_my_sports_message(sports, sport_type),
                                reply_markup=keyboards.make_user_sports_keyboard(sports))


async def water_handler(call):
    chat_id, user_id = call.message.chat.id, call.from_user.id

    _, case, data = call.data.split(':')
    if case == 'drink':
        if utils.get_current_date() not in user_data[user_id]['water']:
            user_data[user_id]['water'][utils.get_current_date()] = {'drink': 0}
        else:
            if 'drink' not in user_data[user_id]['water'][utils.get_current_date()]:
                user_data[user_id]['water'][utils.get_current_date()]['drink'] = float(data)
            else: user_data[user_id]['water'][utils.get_current_date()]['drink'] += float(data)

        db.edit_water_report(user_id, user_data[user_id]['water'][utils.get_current_date()]['drink'], utils.get_current_date())
        await update_water_message(chat_id, user_id, True, call.message.id)

    elif case == 'change':
        user_data[user_id]['water'][utils.get_current_date()]['message_id'] = call.message.id
        user_states[user_id] = 'wait_new_water_limit'

        await bot.send_message(chat_id, 'Введите число - новую дневную цель по выпитой воде, например 4.5 означает цель в 4.5 литра воды в день.')



async def user_handler(call):
    chat_id, user_id = call.message.chat.id, call.from_user.id

    _, case = call.data.split(':')
    if case == 'sport':
        _, user = db.check_or_return_user_registration(user_id)
        user_sports = db.get_user_sport(user_id, 'all')
        await bot.send_message(chat_id, messages.make_user_sport_message(user, user_sports), reply_markup=keyboards.get_my_sport_keyboard())
    elif case == 'daily-report':
        result, data = db.check_date_for_report_exist(utils.get_current_date(), user_id)
        _, user = db.check_or_return_user_registration(user_id)

        if result:
            await bot.send_message(chat_id, messages.make_sport_report_message(data, user))
        else:
            await update_daily_report(chat_id, user_id)
    elif case == 'account':
        exist, user = db.check_or_return_user_registration(user_id)
        reports = db.get_all_reports(user_id)
        await bot.send_message(chat_id, messages.make_account_message(user, reports), reply_markup=keyboards.make_my_account_keyboard(user))
    elif case == 'water':
        await update_water_message(chat_id, user_id)
    elif case == 'active':
        pass

    elif case == 'trains' or case == 'exercises':
        sports = db.get_user_sport(user_id, case[:-1])
        await bot.send_message(chat_id, messages.make_my_sports_message(sports, case), reply_markup=keyboards.make_user_sports_keyboard(sports))

    elif case == 'add_train':
        await bot.send_message(chat_id, 'Начинаем создание новой тренировки!\nВведите название или нажмите "отменить":', reply_markup=keyboards.make_cancel_keyboard())
        user_states[user_id] = 'wait_train_name'
    elif case == 'add_exercise':
        await bot.send_message(chat_id, 'Начинаем создание нового упражнения!\nВведите название или нажмите "отменить":', reply_markup=keyboards.make_cancel_keyboard())
        user_states[user_id] = 'wait_exercise_name'


async def edit_daily_report_handler(call):
    chat_id, user_id = call.message.chat.id, call.from_user.id

    _, case, sport_id = call.data.split(':')

    if case == 'add':
        sport = db.get_sport_by_id(sport_id)
        if sport['type'] == 'train':
            user_data[user_id]['report'].append([sport_id])
            await update_daily_report(chat_id, user_id, True, call.message.id)
        else:
            await bot.send_message(chat_id, sport['question'])
            user_data[user_id]['wait_added_exercise_value'] = sport_id
            user_data[user_id]['wait_added_exercise_value_message_id'] = call.message.id
            user_states[user_id] = 'wait_added_exercise_value'

    elif case == 'edit':
        sport = db.get_sport_by_id(sport_id)
        if sport['type'] == 'train':
            for i in range(len(user_data[user_id]['report'])):
                if user_data[user_id]['report'][i][0] == sport_id:
                    user_data[user_id]['report'].pop(i)
                    break
            await update_daily_report(chat_id, user_id, True, call.message.id)
        else:
            await bot.send_message(chat_id, sport['question'] +f'\nВведите число в формате +10, если хотите прибавить к текущему результату 10.\n Нажмите "удалить", чтобы убрать его из отчёта.', reply_markup=keyboards.make_delete_keyboard())
            user_data[user_id]['wait_changed_exercise_value'] = sport_id
            user_data[user_id]['wait_changed_exercise_value_message_id'] = call.message.id
            user_states[user_id] = 'wait_changed_exercise_value'
    elif case == 'save':
        await bot.answer_callback_query(call.id, 'Данные успешно сохранены!')
        await send_main_menu(call.from_user.first_name, chat_id, user_id)
        await delete(call)
    elif case == 'load':
        if len(user_data[user_id]['report']) > 0 and 'emotion' in user_data[user_id]:
            db.save_report(user_id, utils.get_current_date(), user_data[user_id]['report'], user_data[user_id]['emotion'], user_data[user_id].get('comment', '-'))
            await bot.answer_callback_query(call.id, 'Данные успешно загружены!')
            await delete(call)

            user_data[user_id]['report'] = []
            del user_data[user_id]['emotion']
            del user_data[user_id]['comment']
            await send_main_menu(call.from_user.first_name, chat_id, user_id)
        elif len(user_data[user_id]['report']) <= 0:
            await bot.answer_callback_query(call.id, 'Вы не заполнили отчёт. Нельзя загрузить пустой отчёт.', show_alert=True)
        elif 'emotion' not in user_data[user_id]:
            await bot.answer_callback_query(call.id, 'Вы не выбрали своё настроение.', show_alert=True)
    elif case == 'emotion':
        emotion = sport_id
        user_data[user_id]['emotion'] = emotion
        await update_daily_report(chat_id, user_id, True, call.message.id)
    elif case == 'comment':
        user_states[user_id] = 'wait_report_comment'
        user_data[user_id]['wait_comment_message_id'] = call.message.id
        await bot.send_message(chat_id, 'Введите ваш комментарий: ')


async def account_handler(call):
    chat_id, user_id = call.message.chat.id, call.from_user.id

    _, case, value = call.data.split(':')

    if case in ['morning', 'evening']:
        await bot.send_message(chat_id, f'Отправьте новое время {'утреннего' if case == 'morning' else 'вечернего'} напоминания в формате hh:mm, например: 8:40.', reply_markup=keyboards.make_cancel_keyboard())
        user_states[user_id] = f'wait_new_{case}_reminder_time'
    elif case == 'reminder':
        await update_reminder_time_editing_message(chat_id, user_id, value)
    elif case == 'full_review':
        await bot.answer_callback_query(call.id, 'Подождите... Готовим ваш отчёт 📃\nЭто может занять до 10 секунд 🕒')
        week_report = 'ОТЧЁТ ПОЛЬЗОВАТЕЛЯ ЗА НЕДЕЛЮ:\n'
        today = utils.get_current_date()
        exist, user = db.check_or_return_user_registration(user_id)
        for i in range(6):
            exist, report = db.check_date_for_report_exist(today, user_id)
            if exist:
                week_report += messages.make_long_sport_report(report, user) + '\n\n'
            today = utils.get_yesterday_date(today)

        today = utils.get_current_date()
        if user_id not in ai_reports:
            ai_reports[user_id] = {}
        if today not in ai_reports[user_id]:
            ai_reports[user_id][today] = ai.ask_ai(user_id, week_report, messages.AI_FULL_REPORT_MESSAGE)

        filename = excel.make_main_report(user_id)

        with open(filename, 'rb+') as file:
            await bot.send_document(chat_id, file)
        await  bot.send_message(chat_id, ai_reports[user_id][today], reply_markup=make_menu_button())

        os.remove(filename)
    elif case == 'about_me':
        user_states[user_id] = f'wait_user_about'
        await bot.send_message(chat_id, 'Введите информацию о себе. Например, возраст, вес, цели, образ жизни. Эта информация будет использоваться для персонализации контента.')


async def add_reminder_times_handler(call):
    chat_id, user_id = call.message.chat.id, call.from_user.id

    _, case, value = call.data.split(';')

    if case in ['water', 'active']:
        db.edit_reminder_times(user_id, case, 'delete', value)
        await update_reminder_time_editing_message(chat_id, user_id, case, True, call.message.id)
    elif case == 'add':
        user_data[user_id]['reminder_time_data'] = {'message_id': call.message.id, 'case': value}
        user_states[user_id] = 'wait_new_reminder_time_to_add'

        await bot.send_message(chat_id, 'Введите время для напоминания в формате hh:mm, например 17:30.')

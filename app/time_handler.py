import asyncio
import datetime
from datetime import timedelta

from app.main_handler import update_daily_report
from app.utils import messages, utils
from app.utils.keyboards import make_daily_report_button

from config import bot, user_data
from app.utils import keyboards
from app import ai


from app.database import database as db

async def reminder():
    print('Уведомления запущены')
    while True:
        users = db.get_all_users()
        current_time = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        for user in users:

            user_id = user['user_id']
            exist, user = db.check_or_return_user_registration(user_id)
            today = utils.get_current_date()
            if (not user['access_date'] or ('.' in user['access_date'] and utils.d1_less_d2(today, user['access_date']))) and user['access'] == 1:
                print(user_id, current_time, user['morning_reminder'], user['evening_reminder'], db.get_times(user['user_id'], 'water'), db.get_times(user['user_id'], 'active'))
                if user['morning_reminder'] == current_time:
                    ai_message = f'Личная информация о пользователе: {user['info']}' if user[
                        'info'] else 'Сгенерируй мотивацию'
                    build_on = 'профессиональном опыте, '
                    yesterday_date = datetime.datetime.now() - timedelta(days=1)
                    yesterday_date = datetime.datetime.strftime(yesterday_date, '%d.%m.%y')
                    result, yesterday_data = db.check_date_for_report_exist(yesterday_date, user['user_id'])
                    if result:
                        ai_message += messages.make_long_sport_report(yesterday_data, user)
                        build_on += 'вчерашней тренировке пользователя'
                    if user['info']: build_on += 'личной информации о пользователе'

                    message = '<b>Утрення мотивация</b> 🌞\n\n' + ai.ask_ai(user_id, ai_message,
                                                                           f'Ты профессиональный фитнес-тренер, сгенерируй профессиональную утреннюю мотивацию для человека {user['first_name']}. Твоя мотивация должна основываться на {build_on}. ТВОЙ ОТВЕТ ДОЛЖЕН СОДЕРЖАТЬ ТОЛЬКО МОТИВАЦИЮ БЕЗ ЛИШНИХ СИМВОЛОВ И Т.Д. ДЛИНОЙ НЕ БОЛЕЕ 150 СИМВОЛОВ! ТОЛЬКО HTML ТЕГИ <b>, <i> НЕЛЬЗЯ ИСПОЛЬЗОВАТЬ MARKDOWN')
                    print(message)
                    await bot.send_message(user['user_id'], message)
                elif user['evening_reminder'] == current_time:
                    await update_daily_report(user['user_id'], user['user_id'], False, 0, True)
                elif current_time in db.get_times(user['user_id'], 'water'):
                    if user_id in user_data and 'water' in user_data[user_id]:
                        if utils.get_current_date() not in user_data[user_id]['water']:
                            user_data[user_id]['water'][utils.get_current_date()] = {}
                    else:
                        if user_id not in user_data:
                            user_data[user_id] = {}
                        user_data[user_id]['water'] = {utils.get_current_date(): {'drink': 0}}
                    await bot.send_message(user_id, messages.make_water_reminder_message(user, user_data[user_id][
                        'water'].get(utils.get_current_date(), {'drink': 0}) if user_id in user_data else {'drink': 0}),
                                           reply_markup=keyboards.make_water_menu_keyboard(user))
                elif current_time in db.get_times(user['user_id'], 'active'):
                    message = f'🔔 Напоминание об активности\n\n{ai.ask_ai(user_id, 'Ты профессиональный фитнес-тренер, сгенерируй короткое напоминание о необходимости физической активности.', f'Ты профессиональный фитнес-тренер, сгенерируй короткое напоминание о необходимости физической активности. В своём напоминании предложи пользователю сделать одну или несколько тренировок или упражнений из его списка: {messages.make_sport_list_for_ai(db.get_user_sport(user_id, 'all'))}.\nИнформация о пользователе: {user['info']}. Сделай напоминание на русском языке, используй немного эмодзи и HTML теги ТОЛЬКО <b>жирный текст</b> и <i>курсивный текст</i>, напоминание до 200 символов.')}'
                    await bot.send_message(user_id, message)
                    await bot.send_message(user_id, '🔔 Не забудьте заполнить информацию в дневном отчёте!',
                                           reply_markup=make_daily_report_button())
                elif current_time == '23:59':
                    for user_id,  user_report in user_data.items():
                        db.save_report(user_id, utils.get_current_date(), user_data[user_id]['report'],
                                       user_data[user_id]['emotion'], user_data[user_id].get('comment', '-'))

        await asyncio.sleep(60)


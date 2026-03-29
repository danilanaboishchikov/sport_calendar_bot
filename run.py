import logging
import threading

from app.utils import logger
from config import bot, user_states
from telebot.async_telebot import  AsyncTeleBot
import asyncio
from app.database import database as db
from app.main_handler import *
from app.callback import *
from app.time_handler import reminder

#time_checking_thread = threading.Thread(target=reminder, daemon=True)
#time_checking_thread.start()

@bot.message_handler(commands=['start'])
async def handle_command(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {}

    if user_id not in user_states:
        user_states[user_id] = ''

    if 'water' not in user_data[user_id]:
        user_data[user_id]['water'] = {}

    await command_handler(message)



@bot.message_handler(content_types=['text'])
async def text_handler(message):
    text, chat_id, user_id = message.text, message.chat.id, message.from_user.id

    exist, user = db.check_or_return_user_registration(user_id)
    today = utils.get_current_date()

    if user['access'] == 1 and (not user['access_date'] or len(str(user['access_date'])) <= 2  or utils.d1_less_d2(today, user['access_date'])):
        if text.lower() == 'отменить': user_states[user_id] = ''; await bot.send_message(chat_id, 'Действие отменено.')

        if user_states[user_id]:
            if user_states[user_id] == 'wait_exercise_name':
                await exercise_name_handler(message)
            elif user_states[user_id] == 'wait_train_name':
                await train_name_handler(message)
            elif user_states[user_id] == 'wait_exercise_question':
                await exercise_question_handler(message)
            elif user_states[user_id] == 'wait_train_description':
                await train_description_handler(message)
            elif user_states[user_id] == 'wait_added_exercise_value':
                await exercise_added_value_handler(message)
            elif user_states[user_id] == 'wait_changed_exercise_value':
                await exercise_changed_value_handler(message)
            elif user_states[user_id] == 'wait_report_comment':
                await report_comment_handler(message)
            elif user_states[user_id] == 'wait_new_morning_reminder_time':
                await new_reminder_time_handler(message, 'morning')
            elif user_states[user_id] == 'wait_new_evening_reminder_time':
                await new_reminder_time_handler(message, 'evening')
            elif user_states[user_id] == 'wait_new_water_limit':
                await handler_new_water_limit(message)
            elif user_states[user_id] == 'wait_new_reminder_time_to_add':
                await handler_new_reminder_time_to_add(message)
            elif user_states[user_id] == 'wait_user_about':
                await handler_user_about(message)
    else:
        if user_states[user_id] == 'wait_access_comment':
            await access_comment_handler(message)
        else:
            db.set_access_false(user_id)
            await bot.send_message(user_id, 'К сожалению, ваш пробный доступ закончился :(')
            await send_main_menu(message.from_user.first_name, message.chat.id, user_id)


@bot.callback_query_handler(func=lambda x: True)
async def callback_handler(call):
    print(call.from_user.id, call.data)
    user_id = call.from_user.id
    exist, user = db.check_or_return_user_registration(user_id)
    today = utils.get_current_date()

    if user['access'] == 1 and (not user['access_date'] or len(str(user['access_date'])) <= 2  or utils.d1_less_d2(today, user['access_date'])):
        if call.data == 'menu':
            await send_main_menu(call.from_user.first_name, call.message.chat.id, call.from_user.id)
            await bot.delete_message(call.message.chat.id, call.message.id)

        elif 'user:' in call.data:
            await user_handler(call)
        elif 'delete-sport:' in call.data:
            await delete_sport(call)
        elif 'daily-report:' in call.data:
            await edit_daily_report_handler(call)
        elif 'account:' in call.data:
            await account_handler(call)
        elif 'water:' in call.data:
            await water_handler(call)
        elif 'add_time;' in call.data:
            await add_reminder_times_handler(call)
        elif 'access:' in call.data:
            await access_callback_handler(call)
        elif 'check-payment:' in call.data:
            await check_payment_handler(call)
        else:
            db.set_access_false(user_id)
            await bot.send_message(user_id, 'К сожалению, ваш пробный доступ закончился :(')
            await send_main_menu(call.from_user.first_name, call.message.chat.id, user_id)
    else:
        if 'access:' in call.data:
            await access_callback_handler(call)
        elif 'check-payment:' in call.data:
            await check_payment_handler(call)
        else:
            db.set_access_false(user_id)
            await bot.send_message(user_id, 'К сожалению, ваш пробный доступ закончился :(')
            await send_main_menu(call.from_user.first_name, call.message.chat.id, user_id)


async def poll():
    print('Бот запущен')
    await bot.polling(
        skip_pending=True,
        non_stop=True,
        none_stop=True,
        request_timeout=90,
        timeout=600  # Увеличьте таймаут
    )


async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(poll())
    loop.create_task(reminder())
    await asyncio.Event().wait()  # Бесконечное ожидание


asyncio.run(main())
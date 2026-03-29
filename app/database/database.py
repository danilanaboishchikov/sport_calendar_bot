
import sqlite3 as sqlite
from random import randint
from string import ascii_lowercase, digits

import config
from app.utils import utils
from config import database_path, admin_id
import datetime


def create_conn(): # Создаёт соединение
    conn = sqlite.connect(database_path)
    conn.row_factory = sqlite.Row
    cur = conn.cursor()
    return cur, conn


def generate_sport_id():
    alphabet = ascii_lowercase + digits
    sport_id = ''.join(alphabet[randint(0, len(alphabet) - 1)] for _ in range(10))
    if exist_sport_id(sport_id):
        return generate_sport_id()
    else: return sport_id


def exist_sport_id(sport_id):
    cursor, conn = create_conn()
    result = cursor.execute('SELECT * from sport WHERE sport_id = ?', (sport_id,))
    result = result.fetchall()
    conn.close()
    return True if result else False


def get_user_sport(user_id, need='all'):
    cursor, conn = create_conn()
    if need == 'all':
        result = cursor.execute('SELECT * from sport WHERE user_id = ?', (user_id,))
    else:
        result = cursor.execute('SELECT * from sport WHERE user_id = ? AND type = ?', (user_id, need))

    result = result.fetchall()
    conn.close()

    return [dict(i) for i in result]


def get_user_sport_id(user_id, need='all'):
    cursor, conn = create_conn()
    if need == 'all':
        result = cursor.execute('SELECT * from sport WHERE user_id = ?', (user_id,))
    else:
        result = cursor.execute('SELECT * from sport WHERE user_id = ? AND type = ?', (user_id, need))

    result = result.fetchall()
    conn.close()

    return [i['sport_id'] for i in result]


def check_or_return_user_registration(user_id): # Проверяет зарегистрирован ли пользователь в боте
    cursor, conn = create_conn()
    result = cursor.execute('SELECT * from users WHERE user_id = ?', (user_id,))
    data = result.fetchone()
    conn.close()
    return [True, dict(data)] if data else [False, []]


def delete_sport_by_sport_id(sport_id):
    cursor, conn = create_conn()
    cursor.execute('DELETE from sport WHERE sport_id = ?', (sport_id,))
    conn.commit()
    conn.close()


def add_sport(user_id, data):
    cursor, conn = create_conn()
    if data['type'] == 'train':
        cursor.execute('INSERT into sport (user_id, sport_id, type, name, description) VALUES (?,?,?,?,?)',
                       (user_id, generate_sport_id(), 'train', data['name'], data['description']))
    else:
        cursor.execute('INSERT into sport (user_id, sport_id, type, name, question) VALUES (?,?,?,?,?)',
                       (user_id, generate_sport_id(), 'exercise', data['name'], data['question']))
    conn.commit()
    conn.close()


def register_user(user_id, first_name, username=''):
    cursor, conn = create_conn()
    cursor.execute('INSERT or IGNORE into users (user_id, username, first_name) VALUES (?,?,?)', (user_id, username, first_name))

    for sport_type, name, description, question in config.default_sports:
        if sport_type == 'train':
            cursor.execute('INSERT into sport (user_id, sport_id, type, name, description) VALUES (?,?,?,?,?)',
                           (user_id, generate_sport_id(), sport_type, name, description))
        else:
            cursor.execute('INSERT into sport (user_id, sport_id, type, name, question) VALUES (?,?,?,?,?)',
                           (user_id, generate_sport_id(), sport_type, name, question))

    conn.commit()
    conn.close()


def set_user_send_access_request(user_id):
    cursor, conn = create_conn()
    cursor.execute('UPDATE users SET access_request = ? WHERE user_id = ?', (1, user_id))
    conn.commit()
    conn.close()

def give_unlimited_access(user_id):
    cursor, conn = create_conn()
    cursor.execute('UPDATE users SET access = ? WHERE user_id = ?',(1, user_id))
    conn.commit()
    conn.close()


def give_temporary_access(user_id, days):
    cursor, conn = create_conn()
    end_date =  datetime.datetime.now() + datetime.timedelta(days=days)
    end_date = datetime.datetime.strftime(end_date, '%d.%m.%y')
    cursor.execute('UPDATE users SET access_date = ?, access = ? WHERE user_id = ?',(end_date, 1, user_id))
    conn.commit()
    conn.close()


def set_access_false(user_id):
    cursor, conn = create_conn()
    cursor.execute('UPDATE users SET access = ? WHERE user_id = ?', (0, user_id))
    conn.commit()
    conn.close()


def get_all_users():
    cursor, conn = create_conn()
    result = cursor.execute('SELECT * from users')
    result = result.fetchall()
    conn.close()
    return [dict(i) for i in result]


def check_date_for_report_exist(date, user_id):
    cursor, conn = create_conn()
    result = cursor.execute('SELECT * from reports WHERE date = ? AND user_id = ?', (date, user_id))
    result = result.fetchone()
    conn.close()
    return [True, dict(result)] if result else [False, {}]


def get_sport_by_id(sport_id):
    cursor, conn = create_conn()
    result = cursor.execute('SELECT * from sport WHERE sport_id = ?', (sport_id,))
    data = result.fetchone()
    conn.close()
    return dict(data)


def save_report(user_id, date, data, emotion, comment='-'):
    cursor, conn = create_conn()
    sports = []
    for i in data:
        if len(i) == 2:
            sports.append('='.join(i))
        else:
            sports.append(i[0])
    sports = '!'.join(sports)

    cursor.execute('INSERT into reports (user_id, date, sports, comment, emotion) VALUES (?,?,?,?,?)', (user_id, date, sports, comment, emotion))
    conn.commit()
    conn.close()


def count_strike(user_id):
    today = utils.get_current_date()
    yesterday = utils.get_yesterday_date(today)
    strike = 1 if check_date_for_report_exist(today, user_id)[0] else 0

    exist, report = check_date_for_report_exist(yesterday, user_id)

    while exist:
        strike += 1
        yesterday = utils.get_yesterday_date(yesterday)
        exist, report = check_date_for_report_exist(yesterday, user_id)

    return strike


def change_user_data(user_id, keys, vals):
    data = [f'{keys[i]}=?' for i in range(len(keys))]
    cursor, conn = create_conn()
    cursor.execute(f'UPDATE users SET {','.join(data)} WHERE user_id = ?', (*vals, user_id))
    conn.commit()
    conn.close()


def get_all_reports(user_id):
    cursor, conn = create_conn()
    result = cursor.execute('SELECT * from reports WHERE user_id = ?', (user_id, ))
    result = [dict(i) for i in result.fetchall()]
    conn.close()
    return result


def get_times(user_id, kind):
    _, user = check_or_return_user_registration(user_id)
    data = user[f'{kind}_times']
    if '!' in data:
        return data.split('!')
    elif data: return [data]
    else: return []


def edit_reminder_times(user_id, case, do, time):
    times = get_times(user_id, case)
    if do == 'delete': times.remove(time)
    elif do == 'add': times.append(time)
    new_times = '!'.join(times) if times else ''
    change_user_data(user_id, [f'{case}_times'], [new_times])


def edit_water_report(user_id, drinked, date):
    cursor, conn = create_conn()
    result = cursor.execute("SELECT * from water WHERE user_id = ? AND date = ?", (user_id, date))
    if result.fetchone():
        cursor.execute("UPDATE water SET drinked = ? WHERE user_id = ? AND date = ?", (drinked, user_id, date))
    else:
        cursor.execute("INSERT into water (user_id, date, drinked) VALUES (?,?,?)", (user_id, date, drinked))

    conn.commit()
    conn.close()


def get_all_water_reports(user_id):
    cursor, conn = create_conn()
    result = cursor.execute("SELECT * from water WHERE user_id = ?", (user_id,))
    result.fetchall()
    return [dict(i) for i in result.fetchall()]


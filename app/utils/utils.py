import datetime
from io import BytesIO
import qrcode
from pandas.core.interchange.from_dataframe import primitive_column_to_ndarray

import config
from config import labels
from string import  ascii_lowercase, digits
from random import randint
import re
from math import ceil

def generate_label():
    alphabet = ascii_lowercase + digits
    label = ''.join(alphabet[randint(0, len(alphabet)-1)] for _ in range(10))
    if label not in labels:
        labels.add(label)
        return label
    else:
        return generate_label()


def create_qr_code(url):
    """Генерация QR-кода для оплаты"""
    img = qrcode.make(url)
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


def check_date(date):
    pattern = r'[0-9]{1,2}.{1}[0-9]{1,2}.{1}[0-9]{1,2}'
    if re.match(pattern, date) and date.count('.') == 2:
        return True
    return False


def get_current_date():
    return datetime.datetime.strftime(datetime.datetime.now(), '%d.%m.%y')


def get_yesterday_date(date):
    date = datetime.datetime.strptime(date, '%d.%m.%y').date()
    return datetime.datetime.strftime(date - datetime.timedelta(days=1), '%d.%m.%y')


def d1_less_d2(d1, d2):
    d1 = datetime.datetime.strptime(d1, '%d.%m.%y').date()
    d2 = datetime.datetime.strptime(d2, '%d.%m.%y').date()
    return d1 < d2


def d1_between_delta(d1, d, delta):
    d1 = datetime.datetime.strptime(d1, '%d.%m.%y').date()
    d = datetime.datetime.strptime(d, '%d.%m.%y').date()
    d2 = d1 - datetime.timedelta(days=delta)
    return d2 <= d <= d1


def get_strike_sticker(strike):
    for days, data in config.strike_stickers.items():
        if strike <= days: return data
    return config.strike_stickers[31]


def time_validator(time):
    pattern = r'[0-9]{1,2}:[0-9]{1,2}'
    if re.match(pattern, time) and int(time.split(':')[0]) < 24  and int(time.split(':')[1]) <= 59:
        return True
    return False


def str_to_date(s, form):
    return datetime.datetime.strptime(s, form)


def format_taskbar(done, all):
    if done < all:
        i = int(ceil(done / all * 10))
        bar = '🟩' * i + '⬜' * (10 - i) + f' - {ceil(done / all * 100)}%'
    else:
        return '🟩' * 10  + f' - 100%'

    return bar


def split_for_parts(lst, n):
    result = [[] for _ in range(ceil(len(lst) / n))]
    cnt, x = 0, 0
    while x < len(lst):
        result[cnt] = lst[x:x+n]
        x+=n; cnt+=1
    return result
    
    
import re
def is_digit(s):
    pattern = '[+]{0,1}[0-9]{1,}'
    if re.fullmatch(pattern, s): return True
    return False
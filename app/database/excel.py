import xlsxwriter as x
from app.database.database import *
from config import *
from app.utils import utils
from config import emotions
from app.database import database as db


def make_formats(workbook):
    header = workbook.add_format({'bold': True, 'font_size': 16, 'bg_color': '0x2F4F4F', 'font_color': '0xFFFFFF', 'border': 1})
    header.set_align('center')
    header.set_align('vcenter')
    sport_ok = workbook.add_format({'bg_color': 'green', 'font_size': 13, 'border': 1})
    sport_ok.set_align('center')
    sport_ok.set_align('vcenter')
    sport_bad = workbook.add_format({'bg_color': 'red', 'font_size': 13, 'border': 1})
    sport_bad.set_align('center')
    sport_bad.set_align('vcenter')
    bold = workbook.add_format({'bold': True, 'font_size': 14, 'border': 1})
    bold.set_align('center')
    bold.set_align('vcenter')
    simple = workbook.add_format({'font_size': 13, 'bg_color': '0xC0C0C0', 'border': 1})
    simple.set_align('center')
    simple.set_align('vcenter')
    return {
        'header': header,
        'sport_ok': sport_ok,
        'sport_bad': sport_bad,
        'bold': bold,
        'simple': simple
    }


def make_headers_list(sports):
    headers = ['№', 'Дата', 'Состояние', 'Комментарий', 'Вода']
    sport_headers = {}
    place_id = 6

    for sport in sorted(sports, key=lambda x: x['type'], reverse=True):
        sport_id, type, name = sport['sport_id'], sport['type'], sport['name']
        if type == 'train':
            sport_headers[sport_id] = {'name': '🏋️ ' + name, 'type': type, 'place_id': place_id, 'value': -1, 'id': sport_id}
        else:
            sport_headers[sport_id] = {'name': '🏃‍♂️‍➡️' + name, 'type': type, 'place_id': place_id, 'value': -1, 'id': sport_id}

    return headers, sport_headers


def make_stats_dict(sports):
    stats = {}

    for sport in sorted(sports, key=lambda x: x['type'], reverse=True):
        sport_id, type, name = sport['sport_id'], sport['type'], sport['name']
        stats[sport_id] = []

    return stats


def sort_reports_and_water(reports, water):
    result = []

    def find_water(date):
        for day in water:
            if day['date'] == date: return day['drinked']
        return None

    for report in reports:
        water_report = find_water(report['date'])
        if not water_report:
            report['water'] = -1
        else:
            report['water'] = water_report
        result.append(report)
    return sorted(result, key=lambda x: x['date'])


def write_line(sheet, row, data, cell_format=None, need='all', start=0):
    if need == 'all':
        for col_id in range(start, len(data)+start):
            sheet.write(row, col_id, data[col_id-start], cell_format)
    elif need == 'sport':

        for col_id in range(start, len(data)+start):
            if '✅' in str(data[col_id]):
                sheet.write(row, col_id, data[col_id-start], cell_format['sport_ok'])
            elif '❎' in str(data[col_id]):
                sheet.write(row, col_id, data[col_id-start], cell_format['sport_bad'])
            else:
                if col_id == 0:
                    sheet.write(row, col_id, data[col_id-start], cell_format['header'])
                else:
                    sheet.write(row, col_id, data[col_id-start], cell_format['simple'])


def make_reports_sheet(sheet, info, sports_dict, formats):
    reports, water, sports, headers, sport_ids = info
    row_x = 0
    writen_id = 1
    reports = sort_reports_and_water(reports, water)
    stats = make_stats_dict(sports)
    headers += [i['name'] for i in sorted(sports_dict.values(), key=lambda x: (x['type'],x['id']), reverse=True)]
    for report in reports:
        sport_headers = sports_dict.copy()
        data = sorted([i.split('=') if '=' in i else [i] for i in report['sports'].split('!')], key=lambda x: -len(x))
        exercises = [i for i in data if len(i) == 2]
        trains = [i[0] for i in data if len(i) == 1]
        for exercise_id, value in exercises:
            sport_headers[exercise_id]['value'] = value
            if exercise_id in stats:
                stats[exercise_id].append({'date': report['date'], 'value': value, 'sport_id': exercise_id, 'type': 'exercise'})

        for train_id in trains:
            sport_headers[train_id] = '✅'
            if train_id in stats:
                stats[train_id].append({'date': report['date'], 'sport_id': train_id, 'type': 'train'})

        if row_x % 8 == 0 or row_x == 1:
            write_line(sheet, row_x, headers, formats['header'], 'all')
            row_x += 1

        data = [f'{'✅' if i['id'] in report['sports'] else '❎'}' if i['type'] == 'train'  else f'{'✅: ' + str(i['value']) if int(i['value']) > 0 else '❎'}' for i in sorted(sports_dict.values(), key=lambda x: (x['type'], x['id']), reverse=True)]
        write_line(sheet, row_x, [writen_id, report['date'], emotions[report['emotion']], report['comment'], '❎' if report['water'] == -1 else '✅:' + report['water']] + data, formats, 'sport')

        row_x += 1
        writen_id += 1

    sheet.autofit()
    return stats


def make_sport_sheet(book, sheet, help_sheet, stats, formats):
    today = utils.get_current_date()
    date_format = book.add_format({'num_format': 'yyyy-mm-dd'})
    help_cell = 0
    table_row = 0
    print(153,len(stats.values()))
    for sport_id, data in stats.items():
        sport_name = db.get_sport_by_id(sport_id)['name']
        days = [7, 30, 90, 365]
        days_x = 0
        data.sort(key=lambda x: x['date'])
        d7, d30, d90, d365 = [], [], [], []
        table_cell = 0
        for stat in data:
            if utils.d1_between_delta(today, stat['date'], 7):
                d7.append(stat)
            if utils.d1_between_delta(today, stat['date'], 30):
                d30.append(stat)
            if utils.d1_between_delta(today, stat['date'], 90):
                d90.append(stat)
            if utils.d1_between_delta(today, stat['date'], 365):
                d365.append(stat)
        for d in [d7, d30, d90, d365]:
            help_row = 0

            for stat in d:
                write_line(help_sheet, help_row, [stat['date'], int(stat['value']) if 'value' in stat else 1], None, 'all', help_cell)
                help_row += 1
            chart = book.add_chart(
                {'type': 'column',
                 'name': sport_name + f' за {days[days_x]} дней',
                 })
            chart.set_x_axis({
                'name': sport_name + f' за {days[days_x]} дней'})
            chart.add_series({
                'categories': ['Вспомогательный лист', 0, help_cell, len(d), help_cell],
                'values': ['Вспомогательный лист', 0, help_cell + 1, len(d), help_cell + 1],
            })

            sheet.insert_chart(table_row, table_cell, chart)
            write_line(sheet, table_row+16, [f'Всего: {sum(int(i['value']) if 'value' in i else 1 for i in d)}'], formats['bold'], 'all', table_cell)

            table_cell += 10
            help_cell += 3
            days_x += 1


        table_row += 18


def make_main_report(user_id):
    _, user = check_or_return_user_registration(user_id)
    reports = get_all_reports(user_id)
    water = get_all_water_reports(user_id)
    sports = get_user_sport(user_id, 'all')
    sport_ids = sport_ids = get_user_sport_id(user_id)
    headers, sports_dict = make_headers_list(sports)

    name = path+f'/{user_id}_{utils.get_current_date()}_full_report.xlsx'
    workbook = x.Workbook(name)
    formats = make_formats(workbook)
    reports_sheet = workbook.add_worksheet('📃 Отчёты по дням' )
    sport_sheet = workbook.add_worksheet('🏃‍♂️‍➡️ Отчёты по спорту')
    help_sheet = workbook.add_worksheet('Вспомогательный лист')

    stats = make_reports_sheet(reports_sheet, [reports, water, sports, headers, sport_ids], sports_dict, formats)
    make_sport_sheet(workbook, sport_sheet, help_sheet, stats, formats)

    workbook.close()

    return name

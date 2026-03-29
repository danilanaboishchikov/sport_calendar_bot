'''import logging
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

#logging.basicConfig(level=logging.DEBUG, filename='logs.log', filemode='w')

def log(log_type, text, error=''):

    message = text + f'\nОшибка: {error}' if error else text
    if log_type == 'DEBUG':
        logging.debug('⚙️ ' + message)
        print('⚙️ ' + message)
    elif log_type == 'INFO':
        logging.info('ℹ️ ' + message)
        print('ℹ️ ' + message)
    elif log_type == 'WARN':
        logging.warning('⚠️ ' + message)
        print('⚠️ ' + message)
    elif log_type == 'ERR':
        logging.error('🚫 ' + message)
        print('🚫 ' + message)
    elif log_type == 'CRIT':
        logging.critical('☠️ ' + message)
        print('☠️ ' + message)'''
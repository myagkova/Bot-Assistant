import logging
import os
import time
from json import JSONDecodeError

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BASE_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

logging.basicConfig(filename='bot.log', filemode='w', level=logging.DEBUG)


def parse_homework_status(homework):
    if 'homework_name' not in homework:
        raise Exception('Неверный формат, homework_name не существует.')
    if 'status' not in homework:
        raise Exception('Неверный формат, status не существует.')
    homework_name = homework['homework_name']
    status = homework['status']
    if status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif status == 'reviewing':
        verdict = 'Работа находится на ревью.'
    elif status == 'approved':
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    else:
        raise Exception(f'Неизвестный статус: {status}.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {"from_date": current_timestamp}
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    homework_statuses = requests.get(
        BASE_URL, headers=headers, params=params
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.info('Отправлено сообщение в Telegram')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def handle_error(bot_client, error):
    logging.error(error)
    bot_client.send_message(chat_id=CHAT_ID, text=error)
    time.sleep(5)


def main():
    logging.debug('Запуск Telegram-бота')
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]), bot_client)
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(300)
        except requests.exceptions.RequestException as e:
            handle_error(
                bot_client, f'Сервис Яндекс.Практикум недоступен: {e}'
            )
        except JSONDecodeError as e:
            handle_error(
                bot_client, f'Ответ сервера не содержит валидный json: {e}'
            )
        except Exception as e:
            handle_error(bot_client, f'Бот столкнулся с ошибкой: {e}')


if __name__ == '__main__':
    main()

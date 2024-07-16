import threading
import time
from datetime import datetime
import random

import telebot
from telebot import types

import config
from db import Vent, User

TOKEN = config.token

bot = telebot.TeleBot(TOKEN)


def restricted(func):
    def wrapped(message):
        user_id = message.from_user.id
        if get_user(user_id):
            func(message)
        else:
            bot.send_message(message.chat.id, "Извините, у вас нет доступа к этому боту.")

    return wrapped


@bot.message_handler(commands=['start'])
def begin_handler(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = types.KeyboardButton('Начать')
    keyboard.add(start_button)
    bot.send_message(message.chat.id, 'Привет! Это бот диспетчера системы вентиляции.', reply_markup=keyboard)
    bot.send_message(message.chat.id, 'Чтобы начать работу, нажмите кнопку "Начать".')


@bot.message_handler(func=lambda message: message.text.lower() in ('начать', 'главное меню'))
def start_handler(message):
    if user := get_user(message.from_user.id):
        bot.send_message(message.chat.id, f'Здравствуйте, {user.name}!')
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        get_logs_button = types.KeyboardButton('Получить данные')
        finish_work = types.KeyboardButton('Завершить работу')
        keyboard.add(get_logs_button)
        keyboard.add(finish_work)
        bot.send_message(message.chat.id, 'Что вы хотите сделать?', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Упс, пользователь не найден.')


@bot.message_handler(func=lambda message: message.text.lower() == 'получить данные')
@restricted
def get_logs_handler(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    last_button = types.KeyboardButton('Последние данные')
    menu_button = types.KeyboardButton('Главное меню')
    keyboard.add(last_button)
    keyboard.add(menu_button)
    bot.send_message(message.chat.id, 'За какой период вы хотите получить данные?', reply_markup=keyboard)
    bot.register_next_step_handler(message, get_period_handler)


@bot.message_handler(func=lambda message: message.text.lower() == 'завершить работу')
@restricted
def finish_work_handler(message):
    User.set_on_work(message.from_user.id, False)
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True).add(types.KeyboardButton('Главное меню'))
    bot.send_message(message.chat.id, 'Спасибо за использование нашего бота. Хорошего отдыха!', reply_markup=keyboard)


def get_period_handler(message):
    User.set_on_work(message.from_user.id, True)
    if message.text.lower() == 'главное меню':
        start_handler(message)
        return
    elif message.text.lower() == 'последние данные':
        data = get_last_data()
        send_logs(message, data, 'последний период')
    else:
        bot.send_message(message.chat.id, 'Неизвестный период.')


@bot.message_handler(content_types=['text'])
def other_message(message):
    if message.text.lower() in ('главное меню', 'меню', 'menu'):
        start_handler(message)
    else:
        bot.send_message(message.chat.id, "Ой, я вас немного недопонял. Перенаправляю вас в главное меню.")
        start_handler(message)


def get_user(user_id):
    return User.check_user(user_id)


def get_last_data():
    return Vent.get_last_record()


def send_logs(message, data, date):
    bot.send_message(message.chat.id, f'Данные за {date}:')
    bot.send_message(message.chat.id, f'Дата: {data.date}\nTemp: {data.temperature}°C\nFlow: {data.current_flow} A\n'
                                      f'alarm1: {data.alarm1}\nalarm2: {data.alarm2}\nalarm3: {data.alarm3}')
    get_logs_handler(message)


def periodic_task():
    while True:
        print("Фоновая задача выполняется")
        generate_data()
        data = get_last_data()
        if data.alarm1 or data.alarm2 or data.alarm3:
            for user in User.get_on_work_users():
                for _ in range(3):
                    bot.send_message(user.telegram_id,
                                     f'Обнаружены аварии!\nalarm1: {data.alarm1}, alarm2: {data.alarm2}, alarm3: {data.alarm3}')
        time.sleep(60)


def generate_data():
    temperature = random.randint(-20, 30)
    current_flow = round(random.uniform(0, 100), 2)
    alarm1 = random.choice([True, *[False] * 5])
    alarm2 = random.choice([True, *[False] * 8])
    alarm3 = random.choice([True, *[False] * 10])
    Vent.add_record(temperature=temperature, current_flow=current_flow, alarm1=alarm1, alarm2=alarm2, alarm3=alarm3)


background_thread = threading.Thread(target=periodic_task)
background_thread.daemon = True
background_thread.start()

print('\nБот запущен\n')
bot.polling(none_stop=True)

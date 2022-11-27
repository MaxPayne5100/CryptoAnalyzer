import subprocess
import telebot
import configparser
import os
import prettytable as pt
import csv
from telebot import types
from bob_telegram_tools.bot import TelegramBot
from bob_telegram_tools.utils import TelegramTqdm
from telegram import ParseMode
import datetime as dt

config_obj = configparser.ConfigParser()

try:
    config_obj.read("configfile.ini")
except Exception as e:
    print(f"Failed to read config file: {e}")

# variables
bot_params = config_obj["bot"]
bot = telebot.TeleBot(bot_params["token"])


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, "Hi there, I am ARFIMACryptoAnalyzer bot.\nI am "
                          "here to forecast the "
                          "price of the desired cryptocurrency for selected "
                          "days using ARFIMA model from R language.")


@bot.message_handler(commands=['start'])
def set_currency(message):
    user_id = message.chat.id

    markup = types.ReplyKeyboardMarkup()
    currency_1 = types.KeyboardButton('BNB')
    currency_2 = types.KeyboardButton('BTC')
    currency_3 = types.KeyboardButton('ADA')
    currency_4 = types.KeyboardButton('ETH')
    currency_5 = types.KeyboardButton('XLM')
    markup.row(currency_1, currency_2)
    markup.row(currency_3, currency_4, currency_5)
    message = bot.send_message(user_id,
                               "Please, choose the desired cryptocurrency:",
                               reply_markup=markup)
    bot.register_next_step_handler(message, process_currency_selection,
                                   user_id)


def process_currency_selection(message, user_id):
    markup = types.ReplyKeyboardRemove(selective=False)

    if message.text in ['BNB', 'BTC', 'ADA', 'ETH', 'XLM']:
        cryptocurrency = message.text
        message = bot.send_message(user_id,
                                   "Thank you, cryptocurrency "
                                   "selected, please, choose the desired "
                                   "forecast period [1-30]:",
                                   reply_markup=markup)
        bot.register_next_step_handler(message, process_horizon_selection,
                                       cryptocurrency, user_id)
    else:
        set_currency(message)


def set_horizon_data(cryptocurrency_, user_id):
    message = bot.send_message(user_id,
                               "Please, choose the desired "
                               "forecast period [1-30]:")
    bot.register_next_step_handler(message, process_horizon_selection,
                                   cryptocurrency_, user_id)


def process_horizon_selection(message, cryptocurrency_, user_id):
    if message.text.isnumeric():
        horizon = int(message.text)
        if 1 <= horizon <= 30:
            bot.send_message(user_id,
                                       "Thank you, forecast horizon "
                                       "selected")
            arfima_invocation(cryptocurrency_, horizon, user_id)
        else:
            set_horizon_data(cryptocurrency_, user_id)
    else:
        set_horizon_data(cryptocurrency_, user_id)


def arfima_invocation(cryptocurrency_, horizon_, user_id):
    bot.send_message(user_id,
                     "ARFIMA training started:")
    bot2 = TelegramBot(bot_params["token"], user_id)
    pb = TelegramTqdm(bot2)
    current_timestamp = int(dt.datetime.now().timestamp())
    with pb(total=100) as pbar:
        command = 'C:/Program Files/R/R-4.1.3/bin/Rscript'
        path2script = 'E:/Projects/Master-Diploma/CryptoAnalyzer/R' \
                      '-crypto_forecasting/AutoArfimaForecast.R'
        arg1 = f'{cryptocurrency_}ClosePrice.csv'
        arg2 = f'{cryptocurrency_}ClosePriceForecasted_{current_timestamp}.csv'
        arg3 = f'{horizon_}'
        arg4 = f'{current_timestamp}'
        subprocess.call([command, path2script, arg1, arg2, arg3, arg4],
                        shell=True)
        pbar.update(100)
    bot.send_message(user_id,
                     "ARFIMA training finished!!!")

    markup = types.ReplyKeyboardMarkup(row_width=1)
    itembt_yes = types.KeyboardButton('Yes')
    itembt_no = types.KeyboardButton('No')
    markup.add(itembt_yes, itembt_no)
    message = bot.send_message(user_id,
                               "Do you want to see full model description?",
                               reply_markup=markup)
    bot.register_next_step_handler(message, process_print_selection,
                                   cryptocurrency_, user_id, current_timestamp)


def process_print_selection(message, cryptocurrency_, user_id,
                            current_timestamp):
    markup = types.ReplyKeyboardRemove(selective=False)
    path = "E://Projects/Master-Diploma/CryptoAnalyzer/R-crypto_forecasting" \
           "/results"
    if message.text.lower() == "yes":
        send_image_result(path, markup, user_id, current_timestamp)
        send_model_desc(path, markup, user_id, current_timestamp)
    send_results(path, markup, cryptocurrency_, user_id, current_timestamp)


def send_image_result(path, markup, user_id, current_timestamp):
    bot.send_message(user_id,
                     "ARFIMA forecast visual representation:\n\nBlue line "
                     "shows forecasted close prices and light blue area "
                     "shows price discrepancy with 95% probability.",
                     reply_markup=markup)
    bot.send_photo(user_id, photo=open(os.path.join(
        path, f"ARFIMA_visual_forecast_{current_timestamp}.png"), 'rb'))


def send_model_desc(path, markup, user_id, current_timestamp):
    table = pt.PrettyTable(['AR', 'D', 'MA'])
    table.title = "ARFIMA model parameters:"

    with open(os.path.join(path, f'ARFIMA_output_{current_timestamp}.txt')) \
            as f:
        contents = f.read()

    params = contents.splitlines()[1].split()
    table.add_row([f'{float(params[0]):.3f}',
                   f'{float(params[2]):.3f}',
                   f'{float(params[1]):.3f}'])

    bot.send_message(user_id, f'```{table}```',
                     reply_markup=markup,
                     parse_mode=ParseMode.MARKDOWN_V2)


def send_results(path, markup, cryptocurrency_, user_id, current_timestamp):
    file_path = os.path.join(path, f'{cryptocurrency_}' +
                                        f'ClosePriceForecasted'
                                        f'_{current_timestamp}.csv')
    if os.path.isfile(file_path):
        table = pt.PrettyTable(['Date', 'Price'])
        table.align['Date'] = 'c'
        table.align['Price'] = 'c'

        with open(file_path, 'r') as file:
            csvreader = csv.reader(file)
            csvreader.__next__()
            for row in csvreader:
                table.add_row([row[0], f'{float(row[1]):.3f}'])

        bot.send_message(user_id,
                         f'```{table}```',
                         reply_markup=markup,
                         parse_mode=ParseMode.MARKDOWN_V2)


bot.infinity_polling()

import requests
import json
import pandas as pd
import datetime as dt
import os

# global vars
url = 'https://api.binance.com/api/v3/klines'
interval = '1d'


# helper function to create folder
def create_folder(folder_name: str):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


# function to get last executed data to capture only latter data
def get_last_executed_data(file_name: str):
    last_executed_data = ""
    if os.path.isfile(file_name):
        if os.stat(file_name).st_size > 0:
            with open(file_name, "r") as f:
                last_executed_data = f.readlines()[-1].split(",")[0]
    return last_executed_data


# function to implement incremental load for crypto data
def incremental_data_load(symbol_: str, last_exec_data: int):
    start = last_exec_data
    end = int(dt.datetime.today().timestamp() * 1000)

    diff = (dt.datetime.fromtimestamp(end / 1000) - dt.datetime.fromtimestamp(
        start / 1000)).days

    repeats = diff // 1000 + 1
    final_data = pd.DataFrame()

    for i in range(repeats):
        par = {'symbol': symbol_,
               'interval': interval,
               'startTime': start,
               'endTime': end,
               'limit': 1000}

        data = pd.DataFrame(json.loads(requests.get(url, params=par).text))
        data.columns = ['datetime', 'open',
                        'high', 'low',
                        'close', 'volume',
                        'close_time', 'qav',
                        'num_trades', 'taker_base_vol',
                        'taker_quote_vol', 'ignore']

        data = data[['datetime', 'close']]
        data = data.astype(float)
        final_data = pd.concat([final_data, data])

        start = int(final_data.iloc[-1]['datetime'] + 24*3600)
        end = int(dt.datetime.today().timestamp() * 1000)

    final_data.index = [dt.datetime.fromtimestamp(x / 1000.0).date()
                        for x in final_data.datetime]
    final_data = final_data['close']
    final_data = final_data.astype(float)
    return final_data


# main function to combine all the logic
def update_crypto_data(sign: str):
    database = os.path.abspath("historical_crypto_data")
    create_folder(database)

    crypto = os.path.join(database, sign)
    create_folder(crypto)

    historical_data = os.path.join(crypto, "ClosePrice.csv")

    symbol = f'{sign}USDT'
    last_executed_data = get_last_executed_data(historical_data)
    if last_executed_data != "":
        last_executed_data = [int(i) for i in last_executed_data.split("-")]
    else:
        last_executed_data = [2017, 10, 2]

    final_data = incremental_data_load(symbol,
                                       int(dt.datetime(last_executed_data[0],
                                                       last_executed_data[1],
                                                       last_executed_data[2]+1)
                                           .timestamp() * 1000))
    final_data.index.name = 'Date'
    final_data = final_data.rename('Close')
    final_data.to_csv(historical_data, mode='a+', header=not os.path.exists(
        historical_data), sep=',', encoding='utf-8')


if __name__ == "__main__":
    update_crypto_data("XLM")

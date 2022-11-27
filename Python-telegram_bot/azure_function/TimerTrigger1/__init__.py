import logging
import requests
import json
import pandas as pd
import datetime as dt
import azure.functions as func
import configparser
from azure.storage.blob import BlobClient

config_obj = configparser.ConfigParser()

try:
    config_obj.read("configfile.ini")
except Exception as e:
    print(f"Failed to read config file: {e}")

# variables
azure_params = config_obj["azure"]
account_name = azure_params['acc_name']
account_key = azure_params['acc_key']
url = 'https://api.binance.com/api/v3/klines'
interval = '1d'


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
    try:
        account_url = f"https://{account_name}.blob.core.windows.net/"

        historical_data = sign + "/ClosePrice.csv"
        blob_url = f"{account_url}/sourcedata/{historical_data}"

        blob_client = BlobClient.from_blob_url(
            blob_url=blob_url,
            credential=account_key
        )

        symbol = f'{sign}USDT'
        last_executed_data = [2017, 10, 2]

        final_data = incremental_data_load(symbol,
                                           int(dt.datetime(
                                               last_executed_data[0],
                                               last_executed_data[1],
                                               last_executed_data[2]+1)
                                               .timestamp() * 1000))
        final_data.index.name = 'Date'
        final_data = final_data.rename('Close')

        final_data = final_data.to_csv(sep=',').strip('\n').split('\n')
        df_bytes = '\n'.join(final_data).encode('utf-8')
        blob_client.upload_blob(data=df_bytes, overwrite=True)
    except Exception as ex:
        print(ex)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    crypto_list_names = ["BTC", "ADA", "BNB", "ETH", "XLM"]
    [update_crypto_data(crypto) for crypto in crypto_list_names]

    crypto_list_str = ", ".join(crypto_list_names)
    return func.HttpResponse(f"Crypto data updated for the following currencies: {crypto_list_str}.")


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = dt.datetime.utcnow().replace(
        tzinfo=dt.timezone.utc).isoformat()

    crypto_list_names = ["BTC", "ADA", "BNB", "ETH", "XLM"]
    [update_crypto_data(crypto) for crypto in crypto_list_names]
    crypto_list_str = ", ".join(crypto_list_names)
    print(f"Crypto data updated for the following currencies: {crypto_list_str}.")

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

import time
import schedule
import os
import datetime as dt


# data retention manager job to remove files older than today
def job():
    path = "E://Projects/Master-Diploma/CryptoAnalyzer/R-crypto_forecasting" \
           "/results"
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,
                                                                      f))]
    yesterday = (dt.datetime.now() - dt.timedelta(days=1)).timestamp()
    yesterday = int(yesterday)

    removing_files = ([f for f in files if int(f.split("_")[-1].split(".")[
                                                  0]) <= yesterday])
    [os.remove(os.path.join(path, f)) for f in removing_files]


if __name__ == "__main__":
    schedule.every(1).days.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

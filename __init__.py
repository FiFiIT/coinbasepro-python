from pathlib import Path
import cbpro
import time
import os
import slack
from slack import WebClient
from slack.errors import SlackApiError
from dotenv import load_dotenv

public_client = cbpro.PublicClient()
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
slack_token = os.environ['SLACK_TOKEN']

client = WebClient(token=slack_token)

WAITTING_TIME = 60
last_notification = 0


def time_passed():
    global last_notification
    global WAITTING_TIME

    if last_notification == 0:
        last_notification = time.time()
        return True
    else:
        return time.time() - last_notification >= WAITTING_TIME


def check_price(crypto):
    try:
        ticker = public_client.get_product_ticker(crypto.name)
        result = float(ticker['price'])
    except:
        result = -1

    return result


def slack(crypto, price, result):
    action = 'SELL'
    if result == 1:
        action = 'BUY'

    message = '{cr} {act}: {price}EUR'.format(
        cr=crypto.name, act=action, price=price)

    try:
        response = client.chat_postMessage(
            channel="#cb",
            text=message,
        )
    except SlackApiError as e:
        assert e.response["error"]

    return response


class Crypto:
    def __init__(self, product_id, buy_price=0, sell_price=0):
        self._product_id = product_id
        self._buy_price = buy_price
        self._sell_price = sell_price
        self._notify = 0

    def buySellOrWait(self, price):
        if self._sell_price and price > self._sell_price:
            return -1
        elif self._buy_price and price < self._buy_price:
            return 1

        return 0

    @property
    def name(self):
        return self._product_id


cryptos = [
    Crypto('ICP-EUR', 0, 150),
    Crypto('ETH-EUR', 2000),
    Crypto('ADA-EUR', 1.2, 1.44),
    Crypto('LINK-EUR', 20, 28),
    Crypto('MATIC-EUR', 1.27, 1.76)
]


while True:
    for crypto in cryptos:
        current_price = check_price(crypto)
        if current_price == -1:
            break

        result = crypto.buySellOrWait(current_price)

        if result != 0 and crypto._notify < 2:
            crypto._notify += 1
            slack(crypto, current_price, result)
        else:
            print("{c}: {p}".format(c=crypto.name, p=current_price))

    time.sleep(60)

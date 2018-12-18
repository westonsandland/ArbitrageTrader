import json
import pysher
import threading
import requests

currency_pair = None
app_key = 'de504dc5763aeef9ff52'
order_book = None
running_thread = None
pusherWorker = None


class PusherWorker(threading.Thread):
    def __init__(self, _currency_pair):
        global currency_pair
        currency_pair = _currency_pair

        global order_book
        order_book = _get_order_book()

        threading.Thread.__init__(self)

    def run(self):
        global pusher
        pusher = pysher.Pusher(app_key)

        pusher.connection.bind('pusher:connection_established', connect_handler)
        pusher.connect()


def channel_callback(data):
    json_data = json.loads(data)
    bids = json_data['bids']
    asks = json_data['asks']
    global order_book
    global currency_pair
    order_book = dict(asks=asks, bids=bids)
    return order_book


def connect_handler(data):
    global currency_pair
    channel = pusher.subscribe('order_book_' + currency_pair)
    channel.bind('data', channel_callback)


def _get_order_book_url():
    global currency_pair
    return 'https://www.bitstamp.net/api/v2/order_book/'+currency_pair+'/'


def _get_order_book():
    global currency_pair
    tmp = requests.get(_get_order_book_url()).json()
    return dict(asks=tmp[u'asks'], bids=tmp[u'bids'])


def get_order_book():
    global order_book
    return order_book


def set_currency_pair(new_currency_pair):
    global pusherWorker
    if pusherWorker is not None:
        pusherWorker.join()
        pusherWorker = None
    pusherWorker = PusherWorker(_currency_pair=new_currency_pair)
    pusherWorker.start()


def current_currency_pair():
    global currency_pair
    return currency_pair


if __name__ == '__main__':
    pass

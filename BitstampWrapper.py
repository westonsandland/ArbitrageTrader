import hmac
import hashlib
from datetime import datetime
import requests
import sys
import BitstampWebSocketWrapper

def setupRequests():
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=1)
    s.mount('http://', a)

def nonce_gen():
    nonce = str(datetime.now().timestamp()).replace('.', '')
    while len(nonce) < 16:
        nonce = nonce + '0'
    return nonce


def signature(customer_id, api_key, api_secret, nonce):
    message = nonce + customer_id + api_key
    return hmac.new(api_secret.encode(), msg=message.encode(), digestmod=hashlib.sha256).hexdigest().upper()


def balance_url(currency_pair):
    return 'https://www.bitstamp.net/api/v2/balance/' + currency_pair + '/'


def buy_url(currency_pair):
    return 'https://www.bitstamp.net/api/v2/buy/market/' + currency_pair + '/'


def sell_url(currency_pair):
    return 'https://www.bitstamp.net/api/v2/sell/market/' + currency_pair + '/'

def btc_withdraw_url():
    return 'https://www.bitstamp.net/api/bitcoin_withdrawal/'

def ltc_withdraw_url():
    return 'https://www.bitstamp.net/api/v2/ltc_withdrawal/'

def payload(customer_id, api_key, api_secret, amount='undefined', address='undefined', instant='undefined'):
    amount = str(amount)
    nonce = nonce_gen()
    if amount == 'undefined':
        return {'key': api_key, 'signature': signature(customer_id, api_key, api_secret, nonce), 'nonce': nonce}
    elif address == 'undefined':
        return {'key': api_key, 'signature': signature(customer_id, api_key, api_secret, nonce), 'nonce': nonce,
                'amount': amount}
    elif instant == 'undefined':
        return {'key': api_key, 'signature': signature(customer_id, api_key, api_secret, nonce), 'nonce': nonce,
                'amount': amount, 'address': address}
    else:
        return {'key': api_key, 'signature': signature(customer_id, api_key, api_secret, nonce), 'nonce': nonce,
                'amount': amount, 'address': address, 'instant': instant}


def balance_response(currency_pair, customer_id, api_key, api_secret):
    return requests.post(balance_url(currency_pair), data=payload(customer_id, api_key, api_secret)).json()


def fee(currency_pair, customer_id, api_key, api_secret):
    return float(balance_response(currency_pair, customer_id, api_key, api_secret)['fee'])


def balance(currency_pair, currency_to_get_balance_from, customer_id, api_key, api_secret):
    return float(
        balance_response(currency_pair, customer_id, api_key, api_secret)[currency_to_get_balance_from + '_balance'])


def withdraw(currency, amount, address, customer_id, api_key, api_secret):
    if currency == 'btc':
        return requests.post(btc_withdraw_url(), data=payload(customer_id, api_key, api_secret, amount, address, 0))
    elif currency == 'ltc':
        return requests.post(ltc_withdraw_url(), data=payload(customer_id, api_key, api_secret, amount, address))


def order_book(currency_pair):
    if currency_pair is not BitstampWebSocketWrapper.current_currency_pair():
        BitstampWebSocketWrapper.set_currency_pair(currency_pair)
    return BitstampWebSocketWrapper.get_order_book()


def make_market_buy_order(currency_pair, amount, customer_id, api_key, api_secret):
    return requests.post(buy_url(currency_pair), data=payload(customer_id, api_key, api_secret, amount)).json()


def make_market_sell_order(currency_pair, amount, customer_id, api_key, api_secret):
    return requests.post(sell_url(currency_pair), data=payload(customer_id, api_key, api_secret, amount)).json()


def buy_with(currency_pair, amount, customer_id, api_key, api_secret):
    make_market_buy_order(currency_pair, amount/conversion_rate_buying(currency_pair, amount, 10000000.0)[1], customer_id, api_key, api_secret)


def check_buy(currency_pair, amount, limit, customer_id, api_key, api_secret):
    return conversion_rate_buying(currency_pair, amount, limit)[0]


def check_sell(currency_pair, amount, limit, customer_id, api_key, api_secret):
    currentLtcAmount = balance(currency_pair, 'ltc', customer_id, api_key, api_secret)
    if currentLtcAmount < amount:
        amount = currentLtcAmount
    total = 0.0
    orderBook = list(order_book(currency_pair).values())[1]
    for i in range(0, len(orderBook)):
        if float(orderBook[i][0]) > limit and total < amount:
            total += float(orderBook[i][1])
        else:
            return min(amount, total)
    return min(amount, total)


def conversion_rate_buying(currency_pair, amount, limit, customer_id, api_key, api_secret):
    if limit >= 100000.0: #referring to arbitrarily large number set in the make market buy order of buy_with method
        currentBtcAmount = 100000.0
    else:
        currentBtcAmount = balance(currency_pair, 'btc', customer_id, api_key, api_secret)
    print("conversion rate buying info")
    ltcTotal = 0.0
    total = 0.0
    orderBook = list(order_book(currency_pair).values())[0]
    for i in range(0, len(orderBook)):
        print(float(orderBook[i][0]))
        print(limit)
        print(total)
        print(amount)
        if float(orderBook[i][0]) < limit and ltcTotal < amount:
            total += float(orderBook[i][0]) * float(orderBook[i][1])
            if total > currentBtcAmount:
                return [ltcTotal, 1.0]
            ltcTotal += float(orderBook[i][1])
            print("ltc total is "+str(ltcTotal))
        else:
            return [min(amount, ltcTotal), float(total/ltcTotal)]
    return None


def get_currency_pair(currency_from, currency_to):
    currency_pair = 'undefined'
    if currency_from == 'btc' and currency_to == 'usd' or currency_from == 'usd' and currency_to == 'btc':
        currency_pair = 'btcusd'
    elif currency_from == 'btc' and currency_to == 'eur' or currency_from == 'eur' and currency_to == 'btc':
        currency_pair = 'btceur'
    elif currency_from == 'eur' and currency_to == 'usd' or currency_from == 'usd' and currency_to == 'eur':
        currency_pair = 'eurusd'
    elif currency_from == 'xrp' and currency_to == 'usd' or currency_from == 'usd' and currency_to == 'xrp':
        currency_pair = 'xrpusd'
    elif currency_from == 'xrp' and currency_to == 'eur' or currency_from == 'eur' and currency_to == 'xrp':
        currency_pair = 'xrpeur'
    elif currency_from == 'xrp' and currency_to == 'btc' or currency_from == 'btc' and currency_to == 'xrp':
        currency_pair = 'xrpbtc'
    elif currency_from == 'ltc' and currency_to == 'usd' or currency_from == 'usd' and currency_to == 'ltc':
        currency_pair = 'ltcusd'
    elif currency_from == 'ltc' and currency_to == 'eur' or currency_from == 'eur' and currency_to == 'ltc':
        currency_pair = 'ltceur'
    elif currency_from == 'ltc' and currency_to == 'btc' or currency_from == 'btc' and currency_to == 'ltc':
        currency_pair = 'ltcbtc'
    elif currency_from == 'eth' and currency_to == 'usd' or currency_from == 'usd' and currency_to == 'eth':
        currency_pair = 'ethusd'
    elif currency_from == 'eth' and currency_to == 'eur' or currency_from == 'eur' and currency_to == 'eth':
        currency_pair = 'etheur'
    elif currency_from == 'eth' and currency_to == 'btc' or currency_from == 'btc' and currency_to == 'eth':
        currency_pair = 'ethbtc'
    elif currency_from == 'bch' and currency_to == 'usd' or currency_from == 'usd' and currency_to == 'bch':
        currency_pair = 'bchusd'
    elif currency_from == 'bch' and currency_to == 'eur' or currency_from == 'eur' and currency_to == 'bch':
        currency_pair = 'bcheur'
    elif currency_from == 'bch' and currency_to == 'btc' or currency_from == 'btc' and currency_to == 'bch':
        currency_pair = 'bchbtc'
    if currency_pair == 'undefined':
        sys.exit('Wrong currency pair!')
    return currency_pair


if __name__ == '__main__':
    print(balance('ltcbtc', 'ltc', 'apqo2163', 'hJdLOsHnV1oAkRQlhvZ9apkVWmD6NolG', 'WaLHVSfdGY20JoKt7kdeAmErW4AG72Ne'))
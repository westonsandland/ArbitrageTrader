import requests
import pusher
from pusher import Pusher
from requests.auth import HTTPDigestAuth

def setTimeFrame(daily):
	global timeFrame
	timeFrame=daily

def setCurrency(newCurrency):
	global currency
	currency=newCurrency

def getInfoURL():
	return getTickerURL() if timeFrame else getHourlyTickerURL()
	
def getTickerURL():
	return "https://www.bitstamp.net/api/v2/ticker/"+currency+"/"
	
def getHourlyTickerURL():
	return "https://www.bitstamp.net/api/v2/ticker_hour/"+currency+"/"
	
def getOrderBookURL():
	return "https://www.bitstamp.net/api/v2/order_book/"+currency+"/"
	
def getTransactionsURL():
	return "https://www.bitstamp.net/api/v2/transactions/"+currency+"/"
	
def getTradingPairlsInfoURL():
	return "https://www.bitstamp.net/api/v2/trading-pairs-info/"

def getBid():
	return float(requests.get(getInfoURL()).json()['bid'])

def getAsk():
	return float(requests.get(getInfoURL()).json()['ask'])

def getLast():
	return float(requests.get(getInfoURL()).json()['last'])
	
def getVwap():
	return float(requests.get(getInfoURL()).json()['vwap'])

def getHigh():
	return float(requests.get(getInfoURL()).json()['high'])

def getLow():
	return float(requests.get(getInfoURL()).json()['low'])

def getOpen():
	return float(requests.get(getInfoURL()).json()['open'])

def getVolume():
	return float(requests.get(getInfoURL()).json()['volume'])
	
def getOrderBookURL(currency):
	return "https://www.bitstamp.net/api/v2/order_book/"+currency+"/"

def getOrderBook():
	return [requests.get(getOrderBookURL(currency)).json()[u'bids'], requests.get(getOrderBookURL(currency)).json()[u'asks']]

def printOrderBook():
	for order in getOrderBook():
		print(order)

setCurrency("ltcbtc")
setTimeFrame(True)

def main():
	printOrderBook()

if __name__ == "__main__":
	main()
	
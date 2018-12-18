import gdax
import json
import time
import BitstampWrapper as bits
import datetime
from enum import Enum
class ArbitrageState(Enum):
    NONE = 0
    GDAX_LTC_HIGH = 1
    BITS_LTC_HIGH = 2
global gdaxSecret, gdaxPass, gdaxKey ##CHANGE THESE TO USE WITH THE APPROPRIATE ACCOUNT
gdaxSecret = 'REDACTED'
gdaxPass = 'REDACTED'
gdaxKey = 'REDACTED'
global bitsSecret, bitsKey, bitsID ##CHANGE THESE TO USE WITH THE APPROPRIATE ACCOUNT
bitsSecret = 'REDACTED'
bitsID = 'REDACTED'
bitsKey = 'REDACTED'
global trading
trading = False ##CHANGE THIS IF YOU WANT TO START TRADING
global gdaxCurrencyPair, bitsCurrencyPair
gdaxCurrencyPair = "LTC-BTC"
bitsCurrencyPair = "ltcbtc"
global BTC_BUFFER, LTC_BUFFER
BTC_BUFFER = .001
LTC_BUFFER = .075
global totalFees, optimalRate
totalFees = bits.fee(bitsCurrencyPair, bitsID, bitsKey, bitsSecret)/2
#totalFees = 0
optimalRate = 0.2
global BITS_BTC_ADDRESS, BITS_LTC_ADDRESS, GDAX_BTC_ADDRESS, GDAX_LTC_ADDRESS ##CHANGE THESE TO USE WITH THE APPROPRIATE ACCOUNT
BITS_BTC_ADDRESS = '35dGRhjbEQQvh6Md8U8ZaAbQU7TPZSVkkc'
BITS_LTC_ADDRESS = '34i1qbyySP4atvBar5Gw8eeZT9qXLHxrkr'
GDAX_BTC_ADDRESS = '1EifLER5ALyqvMSip36qwBh9jTmRunmxtz'
GDAX_LTC_ADDRESS = 'LMbELHagXEthkLqjbVjc5P1PEjHqnVV6E5'
global gdaxLTCID, gdaxBTCID ##CHANGE THESE TO USE WITH MARKS
gdaxLTCID = '9edbec24-39cf-42e5-9ce6-8e65e8968794'
gdaxBTCID = 'a83ee9b2-81a2-4893-bd47-e60b33ac1d65'
global gdax_spread_cross
gdax_spread_cross = float(.00001)

def is_gdax_ltc_high(gdax, bits_order_book):
    # print("gdax")
    # print(gdax_bid_price(gdax))
    # print(bits_ask_price(bits))
    return gdax_bid_price(gdax) + gdax_spread_cross - float(bits_ask_price(bits_order_book))
def is_bits_ltc_high(gdax, bits_order_book):
    # print("gdax")
    # print(gdax_bid_price(gdax))
    # print("bits")
    # print(bits_ask_price(bits))
    return float(bits_bid_price(bits_order_book)) - gdax_ask_price(gdax) - gdax_spread_cross
def gdax_bid_price(orderBook):
    # print("gdaxbid")
    # print(orderBook)
    # print(orderBook[1])
    # print(orderBook[1][0])
    # print(orderBook[1][0][0])
    return float(orderBook[1][0][0])
def gdax_ask_price(orderBook):
    # print("gdaxask")
    # print(orderBook)
    # print(orderBook[2])
    # print(orderBook[2][0])
    # print(orderBook[2][0][0])
    return float(orderBook[2][0][0])
def bits_bid_price(orderBook):
    #print("bitsbid")
    # print(orderBook)
    # print(orderBook[0])
    # print(orderBook[0][0])
    return list(orderBook['bids'])[0][0]
def bits_ask_price(orderBook):
    # print("bitsask")
    # print(orderBook[1])
    # print(orderBook[1][0])
    return list(orderBook['asks'])[0][0]
def attempt_gdax_buy(authClient, orderBook, lastOffer, arblog):
    toBuyAt = gdax_ask_price(orderBook) - .00001
    #print(toBuyAt)
    #print("e"+str(lastOffer))
    if lastOffer != toBuyAt or orders_count(authClient) > 1:
        #print(float('%.7f'%(float(list(authClient.get_accounts()[0].values())[3]) / toBuyAt))-.0000002)
        #print("by"+str(float('%.5f'%(toBuyAt))))
        cancel_all_gdax(authClient)
        #authClient.cancel_all(product=gdaxCurrencyPair)
        amount = bits.check_sell(bitsCurrencyPair, float(get_btc_account(authClient)[3]) / toBuyAt, toBuyAt) #feeding litecoin, expects litecoin
        print("max amount: "+str(float(get_btc_account(authClient)[3]) / toBuyAt)+" actual amount: "+str(amount))
        print(float('%.5f'%(toBuyAt)))
        print(float('%.7f'%((float(amount))-.0000002)))
        temp = authClient.buy(price=float('%.5f'%(toBuyAt)), size=float('%.7f'%((float(amount))-.0000002)), product_id=gdaxCurrencyPair, post_only=True)
        print(temp)
        if len(list(temp)) < 2:
            toBuyAt = -1
        arblog.write("num of buy orders open "+str(orders_count(authClient))+"\n")
    return toBuyAt


def attempt_gdax_sell(authClient, orderBook, lastOffer, arblog):
    toSellAt = gdax_bid_price(orderBook) + gdax_spread_cross
    if lastOffer != toSellAt or orders_count(authClient) > 1:
        cancel_all_gdax(authClient)
        #authClient.cancel_all(product=gdaxCurrencyPair)
        amount = bits.check_buy(bitsCurrencyPair, float(get_ltc_account(authClient)[3]), toSellAt) #feeding litecoin, expects litecoin
        print("max amount: "+str(float(get_ltc_account(authClient)[3]))+" actual amount: "+str(amount))
        print(float('%.5f'%(toSellAt)))
        print(float('%.7f'%(float(amount)-.0000002)))
        temp = authClient.sell(price=float('%.5f'%(toSellAt)), size=float('%.7f'%(float(amount)-.0000002)), product_id=gdaxCurrencyPair, post_only=True)
        print(temp)
        if len(list(temp)) < 2:
            toSellAt = -1
        arblog.write("num of sell orders open " + str(orders_count(authClient))+"\n")
    return toSellAt

def cancel_all_gdax(authClient):
    orders = authClient.get_orders()
    for i in orders[0]:
        authClient.cancel_order(list(i.values())[0])

def orders_count(authClient):
    return len(authClient.get_orders()[0])

def get_btc_account(authClient):
    return list(authClient.get_account(gdaxBTCID).values())

def get_ltc_account(authClient):
    return list(authClient.get_account(gdaxLTCID).values())

def detectArbitrage(gdaxOrderBook, bitsOrderBook, arblog):
    relativeGdaxValue = is_gdax_ltc_high(gdaxOrderBook, bitsOrderBook)
    relativeBitsValue = is_bits_ltc_high(gdaxOrderBook, bitsOrderBook)
    gdaxArbPercentage = (relativeGdaxValue / float(gdax_bid_price(gdaxOrderBook) + float(str(bits_ask_price(bitsOrderBook))))) * 100
    bitsArbPercentage = (relativeBitsValue / float(float(str(bits_bid_price(bitsOrderBook))) + gdax_ask_price(gdaxOrderBook))) * 100
    # print("data:")
    # print(str(gdax_ask_price(gdaxOrderBook)) + bits_bid_price(bitsOrderBook))
    # print(bits_ask_price(bitsOrderBook) + str(gdax_bid_price(gdaxOrderBook)))
    print(gdaxArbPercentage)
    print(bitsArbPercentage)
    # print(relativeGdaxValue*100)
    # print(relativeBitsValue*100)
    if gdaxArbPercentage > 0.0 and bitsArbPercentage > 0.0:
        print(datetime.datetime.now())
        print("ERROR: impossible two way arbitrage. Improper calculations")
        print("bitsArb: " + str(bitsArbPercentage))
        print("gdaxArb: " + str(gdaxArbPercentage))
        print(relativeGdaxValue)
        print(gdax_ask_price(gdaxOrderBook))
        print(bits_bid_price(bitsOrderBook))
        print(relativeBitsValue)
        print(bits_ask_price(bitsOrderBook))
        print(gdax_bid_price(gdaxOrderBook))
    if gdaxArbPercentage > totalFees:
        arblog.write(str(datetime.datetime.now())+"\n")
        arblog.write("Arbitrage for selling GDAX LTC and buying Bits LTC. Approximate raw price difference is " + str(
            gdaxArbPercentage) + "%\n")
        print("Arbitrage for selling GDAX LTC and buying Bits LTC. Approximate raw price difference is " + str(
            gdaxArbPercentage))
        # print(relativeGdaxValue)
        # print(gdax_ask_price(gdaxOrderBook))
        # print(bits_bid_price(bitsOrderBook))
        return ArbitrageState.GDAX_LTC_HIGH
    if bitsArbPercentage > totalFees:
        arblog.write(str(datetime.datetime.now())+"\n")
        arblog.write("Arbitrage for selling Bits LTC and buying GDAX LTC. Approximate raw price difference is " + str(
            bitsArbPercentage) + "%\n")
        print("Arbitrage for selling Bits LTC and buying GDAX LTC. Approximate raw price difference is " + str(
            bitsArbPercentage))
        # print(relativeBitsValue)
        # print(bits_ask_price(bitsOrderBook))
        # print(gdax_bid_price(gdaxOrderBook))
        return ArbitrageState.BITS_LTC_HIGH
    return ArbitrageState.NONE
# lastOffer = 0
# lastOffer2 = 0
# gdaxClient = gdax.AuthenticatedClient(gdaxKey, gdaxSecret, gdaxPass)
# while True:
#     gdaxOrderBook = list(gdaxClient.get_product_order_book(gdaxCurrencyPair).values())
#     detectArbitrage(list(gdax.PublicClient().get_product_order_book(gdaxCurrencyPair).values()), bits.order_book(bitsCurrencyPair))
#     #lastOffer = attempt_gdax_buy(gdaxClient, gdaxOrderBook, lastOffer)
#     #lastOffer2 = attempt_gdax_sell(gdaxClient, gdaxOrderBook, lastOffer2)
#     # if lastOffer != list(authClient.get_accounts()[2].values())[3]:
#     #     print(list(authClient.get_accounts()[2].values())[3])
#     #     lastOffer = list(authClient.get_accounts()[2].values())[3]
#     time.sleep(3)
#     gdaxOrderBook = list(gdaxClient.get_product_order_book(gdaxCurrencyPair).values())
# while True:
#     detectArbitrage(list(gdax.PublicClient().get_product_order_book(gdaxCurrencyPair).values()), bits.order_book(bitsCurrencyPair))
#     time.sleep(2)
def main():
    with open('arbitragelog', "a") as arblog:
        gdaxClient = gdax.AuthenticatedClient(gdaxKey, gdaxSecret, gdaxPass)
        if not trading:
            while True:
                #print("ok")
                gdaxOrderBook = list(gdaxClient.get_product_order_book(gdaxCurrencyPair).values())
                bitsOrderBook = bits.order_book(bitsCurrencyPair)
                #print(bitsOrderBook)
                detectArbitrage(gdaxOrderBook, bitsOrderBook, arblog)
                time.sleep(2)
        while True:
            #print("ok")
            gdaxOrderBook = list(gdaxClient.get_product_order_book(gdaxCurrencyPair).values())
            bitsOrderBook = bits.order_book(bitsCurrencyPair)
            #print(bitsOrderBook)
            arbState = detectArbitrage(gdaxOrderBook, bitsOrderBook, arblog)
            reset = False
            lastOffer = 0
            #print(gdaxClient.get_accounts())
            try:
                oldLTCBalance = get_ltc_account(gdaxClient)[2]
                oldBTCBalance = get_btc_account(gdaxClient)[2]
            except:
                oldLTCBalance = 0
                oldBTCBalance = 0
            #print(arbState)
            while arbState != ArbitrageState.NONE and ((float(list(gdaxClient.get_accounts()[0].values())[3]) >= 0.01 and float(list(gdaxClient.get_accounts()[2].values())[3]) >= 0.1) or orders_count(gdaxClient) > 0):
                arblog.write(str(arbState))
                if arbState == ArbitrageState.BITS_LTC_HIGH:
                    lastOffer = attempt_gdax_buy(gdaxClient, gdaxOrderBook, lastOffer, arblog)
                    newLTCBalance = get_ltc_account(gdaxClient)[2]
                    arblog.write("old litecoin balance:"+str(oldLTCBalance))
                    arblog.write("new litecoin balance:"+str(newLTCBalance))
                    if newLTCBalance > oldLTCBalance:
                        print(bits.make_market_sell_order(bitsCurrencyPair, float('%.7f'%float(newLTCBalance - oldLTCBalance)), bitsID, bitsKey, bitsSecret)) # sell [newLTCBalance - oldLTCBalance] LTC on Bitstamp
                    elif newLTCBalance < oldLTCBalance:
                        print("ERROR: WE NOW HAVE LESS LTC THAN EARLIER. MAJOR TRADE ERROR")
                    oldLTCBalance = newLTCBalance
                if arbState == ArbitrageState.GDAX_LTC_HIGH:
                    lastOffer = attempt_gdax_sell(gdaxClient, gdaxOrderBook, lastOffer, arblog)
                    newBTCBalance = get_btc_account(gdaxClient)[2]
                    arblog.write("old bitcoin balance:"+str(oldBTCBalance))
                    arblog.write("new bitcoin balance:"+str(newBTCBalance))
                    if newBTCBalance > oldBTCBalance:
                        print(bits.buy_with(bitsCurrencyPair, float('%.7f'%float(newBTCBalance - oldBTCBalance)), bitsID, bitsKey, bitsSecret))
                    elif newBTCBalance < oldBTCBalance:
                        print("ERROR: WE NOW HAVE LESS BTC THAN EARLIER. MAJOR TRADE ERROR")
                    oldBTCBalance = newBTCBalance
                gdaxOrderBook = list(gdaxClient.get_product_order_book(gdaxCurrencyPair).values())
                bitsOrderBook = dict(bits.order_book(bitsCurrencyPair))
                arbState = detectArbitrage(gdaxOrderBook, bitsOrderBook)
                time.sleep(2)
            #print("finna cancel")
            try:
                cancel_all_gdax(gdaxClient)
            except:
                print("internet connection lost")
            #gdaxClient.cancel_all(product=gdaxCurrencyPair)
            gdaxFinalLtcBalance = float(get_ltc_account(gdaxClient)[2])
            gdaxFinalBtcBalance = float(get_btc_account(gdaxClient)[2])
            bitsFinalLtcBalance = bits.balance(bitsCurrencyPair, 'ltc', bitsID, bitsKey, bitsSecret) - LTC_BUFFER
            bitsFinalBtcBalance = bits.balance(bitsCurrencyPair, 'btc', bitsID, bitsKey, bitsSecret) - BTC_BUFFER
            if bitsFinalBtcBalance < 0 or bitsFinalLtcBalance < 0:
                print("ERROR: BALANCE NEGATIVE FOR BITSTAMP. BUFFER NOT RESPECTED")
            if gdaxFinalLtcBalance - bitsFinalLtcBalance > .1:
                print("1")
                print(gdaxFinalLtcBalance)
                print(bitsFinalLtcBalance)
                print(gdaxClient.crypto_withdraw(float('%.5f'%((gdaxFinalLtcBalance - bitsFinalLtcBalance) / 2)), 'LTC', BITS_LTC_ADDRESS))
                reset = True
            elif bitsFinalLtcBalance - gdaxFinalLtcBalance > .1:
                print("2")
                print(bits.withdraw('ltc', float('%.5f'%((bitsFinalLtcBalance - gdaxFinalLtcBalance) / 2)), GDAX_LTC_ADDRESS, bitsID, bitsKey, bitsSecret))
                reset = True
            if gdaxFinalBtcBalance - bitsFinalBtcBalance > .01:
                print("3")
                print(gdaxClient.crypto_withdraw(float('%.5f'%((gdaxFinalBtcBalance - bitsFinalBtcBalance) / 2)), 'BTC', BITS_BTC_ADDRESS))
                reset = True
            elif bitsFinalBtcBalance - gdaxFinalBtcBalance > .01:
                print("4")
                print(bits.withdraw('btc', float('%.5f'%((bitsFinalBtcBalance - gdaxFinalBtcBalance) / 2)), GDAX_BTC_ADDRESS, bitsID, bitsKey, bitsSecret))
                reset = True
            if reset:
                print("gdax bitc amount"+str(float(list(gdaxClient.get_accounts()[0].values())[3])))
                print("bits bitc amount" + str(bits.balance(bitsCurrencyPair, 'btc', bitsID, bitsKey, bitsSecret)))
                print("gdax ltc amount" + str(float(list(gdaxClient.get_accounts()[2].values())[3])))
                print("bits ltc amount" + str(bits.balance(bitsCurrencyPair, 'ltc', bitsID, bitsKey, bitsSecret)))
                count = 0
                while float(get_btc_account(gdaxClient)[3]) - (bits.balance(bitsCurrencyPair, 'btc', bitsID, bitsKey, bitsSecret) - BTC_BUFFER) > .01 or float(get_btc_account(gdaxClient)[3]) - (bits.balance(bitsCurrencyPair, 'btc', bitsID, bitsKey, bitsSecret) - BTC_BUFFER) < (-0.01) or count < 90:
                    print("waiting for BTC transfer")
                    count+=1
                    time.sleep(60)
                count = 0
                while float(get_ltc_account(gdaxClient)[3]) - (bits.balance(bitsCurrencyPair, 'ltc', bitsID, bitsKey, bitsSecret) - LTC_BUFFER) > .1 or float(get_ltc_account(gdaxClient)[3]) - (bits.balance(bitsCurrencyPair, 'ltc', bitsID, bitsKey, bitsSecret) - LTC_BUFFER) < (-0.1) or count < 90:
                    print("waiting for LTC transfer")
                    count+=1
                    time.sleep(60)
                print("Process complete. GDAX Balance (BTC):"+str(list(gdaxClient.get_accounts()[0].values())[3])+" GDAX Balance (LTC):"+str(list(gdaxClient.get_accounts()[2].values())[3]))
                print("Process complete. BITS Balance (BTC):" + str(bits.balance(bitsCurrencyPair, 'btc', bitsID, bitsKey, bitsSecret)) + " BITS Balance (LTC):" + str(bits.balance(bitsCurrencyPair, 'ltc', bitsID, bitsKey, bitsSecret)))
                time.sleep(10)
            else:
                time.sleep(2)

if __name__ == '__main__':
    print("starting")
    bits.setupRequests()
    while True:
        try:
            main()
        except:
            print("main method failed")
    # last = 0
    # while True:
    # gdaxClient = gdax.AuthenticatedClient(gdaxKey, gdaxSecret, gdaxPass)
    # gdaxOrderBook = list(gdaxClient.get_product_order_book(gdaxCurrencyPair).values())
    #last = attempt_gdax_sell(gdaxClient, gdaxOrderBook, last)
    # oldLTCBalance = get_ltc_account(gdaxClient)[2]
    # newLTCBalance = get_ltc_account(gdaxClient)[2]
    # print(gdaxClient.get_accounts())
    # print(oldLTCBalance)
    # print(newLTCBalance)
    # print(bits.make_market_sell_order(bitsCurrencyPair, float('%.7f'%float(newLTCBalance)), bitsID, bitsKey, bitsSecret))


    #print(get_btc_account(gdaxClient))
    #print(get_ltc_account(gdaxClient))
    #cancel_all_gdax(gdaxClient)
    #print(orders_count(gdaxClient))
    #print(gdax_bid_price(list(gdaxClient.get_product_order_book(gdaxCurrencyPair).values())))
    #print(gdax_ask_price(list(gdaxClient.get_product_order_book(gdaxCurrencyPair).values())))

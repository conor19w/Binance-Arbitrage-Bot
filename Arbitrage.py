import json,pprint
import asyncio
import time
import websockets
import sys, os
from binance.client import Client
from copy import copy
from binance.exceptions import BinanceAPIException
from binance.enums import *
import datetime
from time import sleep
client = Client(api_key='',api_secret='') ##Binance keys needed to get get price data/ Trade on an account
DOGE = "wss://stream.binance.com:9443/ws/dogeusdt@ticker"  ##coin1
DOGE_Bitcoin = "wss://stream.binance.com:9443/ws/dogebtc@ticker"  ##coin1_coin2
Bitcoin = "wss://stream.binance.com:9443/ws/btcusdt@ticker" ##coin2


pp = pprint.PrettyPrinter()
AccountSize = 20
fee=.00075 ##what fee you pay
mul=1-fee ##multiplier
trading=0 ##actually trade on binance
async def runWS():
    async with websockets.connect(DOGE) as ws1, websockets.connect(DOGE_Bitcoin) as ws2, websockets.connect(Bitcoin) as ws3:
        global AccountSize,mul
        old_AccountSize=0
        while True:
            #print(client.get_asset_balance(asset='USDT')['free'])
            message1 = await ws1.recv()
            message2 = await ws2.recv()
            message3 = await ws3.recv()
            json_message1 = json.loads(message1)
            BTC=float(json_message1['c'])
            json_message2 = json.loads(message2)
            ETH_BTC = float(json_message2['c'])
            json_message3 = json.loads(message3)
            ETH = float(json_message3['c'])
            #print('{:.8f}'.format(ETH_BTC))
            #print(BTC)
            ##USDT-->BTC-->ETH-->USDT
            BTCpos1=mul*AccountSize/BTC
            ETH_BTC_pos1=mul*BTCpos1*ETH_BTC
            ETHpos1=mul*ETH_BTC_pos1*ETH

            ##USDT-->ETH-->BTC-->USDT
            ETHpos2 = mul * AccountSize/ETH
            ETH_BTC_pos2 = mul * ETHpos2/ETH_BTC
            BTCpos2 = mul * ETH_BTC_pos2 * BTC

            #info = client.get_symbol_info('DOGEBTC')
            #print(info)


            #print(BTCpos,ETH_BTC_pos,ETHpos)
            try:
                if ETHpos1-AccountSize>0:
                    print("USDT-->DOGE-->BTC-->USDT")

                    if trading:
                        #print("quantity:",round((float(client.get_asset_balance(asset='USDT')['free'])*.9/BTC)-.5))
                        Order(round((float(client.get_asset_balance(asset='USDT')['free'])*.9/BTC)-.5),1,"DOGEUSDT",BTC) ##Buy 30 dollars of Doge
                        Order(float(client.get_asset_balance(asset='DOGE')['free']),0,"DOGEBTC",'{:.8f}'.format(ETH_BTC)) ##Sell DOGE for BTC
                        Order(round(float(client.get_asset_balance(asset='BTC')['free'])-.0000005,6),0,"BTCUSDT",ETH) ##Sell BTC for usdt

                    AccountSize+=ETHpos1-AccountSize

                elif BTCpos2-AccountSize>0:
                    print("USDT-->BTC-->DOGE-->USDT")

                    if trading:
                        #print("quantity:",'{:.6f}'.format(float(client.get_asset_balance(asset='USDT')['free'])*.9 / ETH))
                        Order('{:.6f}'.format(float(client.get_asset_balance(asset='USDT')['free'])*.9 / ETH), 1, "BTCUSDT",ETH)  ##Buy 30 dollars of BTC
                        Order(round((float(client.get_asset_balance(asset='BTC')['free'])/ETH_BTC)-.5), 1, "DOGEBTC",'{:.8f}'.format(ETH_BTC))  ##Buy DOGE with BTC
                        Order(float(client.get_asset_balance(asset='DOGE')['free']), 0, "DOGEUSDT",BTC)  ##Sell DOGE for usdt

                    AccountSize+=BTCpos2-AccountSize
            except BinanceAPIException as e:  # BinanceAPIException
                print(e)
                print(e.status_code)
                print(e.message)
            if AccountSize!=old_AccountSize and not trading:
                print("Balance:",AccountSize)
            elif AccountSize!=old_AccountSize:
                print("Balance:", client.get_asset_balance(asset='USDT')['free'])
            old_AccountSize=copy(AccountSize)



def Order(q, side1, s,p):
    if side1: ##Buy
        ##Place the Buy
        order1 = client.create_order(
            symbol=s,
            side=SIDE_BUY,
            type=ORDER_TYPE_LIMIT,
            price=p,
            timeInForce=TIME_IN_FORCE_IOC,
            quantity=q)
    else: ##Sell
        ##Place the Sell
        order1 = client.create_order(
            symbol=s,
            side=SIDE_SELL,
            type=ORDER_TYPE_LIMIT,
            price=p,
            timeInForce=TIME_IN_FORCE_IOC,
            quantity=q)

def run():
    try:
        asyncio.get_event_loop().run_until_complete(runWS())
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print("Error in websocket, retrying")
        time.sleep(1)
        run()


run()

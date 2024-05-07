#from upbit_websocket.collect import upbit_websocket
import pyupbit
import ccxt
from binance_websocket_collect.collect import binance_websocket

if __name__ == '__main__':
    # coins =  pyupbit.get_tickers(fiat="KRW")
    # balance = {'KRW': 1260000}
    # mode = 'ticker'
    # collector = upbit_websocket(coins, balance, mode, 'trade')
    # collector.run()
    coins = ['storjusdt']
    collector = binance_websocket(coins)
    
    collector.run()

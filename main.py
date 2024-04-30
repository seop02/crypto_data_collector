from websocket_data.collect import upbit_websocket
import pyupbit

if __name__ == '__main__':
    coins =  pyupbit.get_tickers(fiat="KRW")
    balance = {'KRW': 1260000}
    mode = 'ticker'
    collector = upbit_websocket(coins, balance, mode, False)
    collector.run()
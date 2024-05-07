import json
import time
import logging
import threading 
import websocket
import websockets
import multiprocessing as mp
import pyupbit
import math
import pandas as pd
import os
import numpy as np
import asyncio
import multiprocessing
import concurrent.futures
from datetime import timezone, datetime
import pymongo
from upbit_websocket_collect import data_path
from upbit_websocket_collect.trading import dev_trader
from upbit_websocket_collect.order import market_interaction


logging.basicConfig(level=logging.WARNING)
logging.getLogger().setLevel(logging.INFO)
LOG = logging.getLogger(__name__)


class upbit_websocket:
    initial_krw = 10000
    def __init__(self, coins, balance, mode, trade):
        self.coins = coins
        self.balance = balance
        self.mode = mode
        self.transaction = 0.9995**2
        self.trade = trade
        self.cache_vol = {
            coin : 0 for coin in coins
        }
        self.dev_cut = {
        'KRW-BTC': 1.5e-10, 'KRW-GLM': 5.42e-05
        }
        self.trading_coins = list(self.dev_cut.keys())
        self.profit_cut = {
            'KRW-BTC': 1.03, 'KRW-GLM': 1.2
        }
        self.trade = ['trade', 'no_trade']
        self.trial = 0
        if mode == 'ticker':
            self.data = {
                'coin': [],
                'acc_trade_vol': [],
                'traded_time': [],
                'traded_price': [],
                'ask_bid': [],  
                'high': [],
                'dev': [0],
                '24h_vol': []
            }
        elif mode == 'orderbook':
            self.data = {
                'coin': [],
                'timestamp': [],
                'ask_price1': [],
                'ask_vol1': [],
                'ask_price2': [],
                'ask_vol2': [],
                'ask_price3': [],
                'ask_vol3': [],
                'bid_price1': [],
                'bid_vol1': [],
                'bid_price2': [],
                'bid_vol2': [],
                'bid_price3': [],
                'bid_vol3': []
            } 
    
    async def collect_ticker(self):
        url = "wss://api.upbit.com/websocket/v1"
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        
        #create folder to store data
        if not os.path.exists(f'{data_path}/ticker/{date}'):
            os.mkdir(f'{data_path}/ticker/{date}')
            
        trade_dev = dev_trader(self.trading_coins, self.initial_krw)
        # if trading_status == True:
        #     file_name = self.trade[0]
        # else:
        #     file_name = self.trade[1]
        
        while True:
            try:
                async with websockets.connect(url) as ws:
                    payload = [
                        {"ticket": "your-ticket"}, 
                        {"type": self.mode, "codes": self.coins}]  
                    await ws.send(json.dumps(payload))
                    while True:
                        try:
                            response = await ws.recv()
                            raw = json.loads(response)
                        except Exception as e:
                            LOG.info('Error while analyzing data')
                            LOG.error(f'Error: {e}')
                            await asyncio.sleep(1)
                            break
                        coin = raw['code']
                        tot_vol = raw['acc_trade_price_24h']
                        self.data['coin'].append(raw['code'])
                        self.data['traded_price'].append(raw['trade_price'])
                        self.data['acc_trade_vol'].append(raw['acc_trade_volume'])
                        self.data['high'].append(raw['high_price'])
                        self.data['ask_bid'].append(raw['ask_bid'])
                        self.data['traded_time'].append(time.time())
                        self.data['24h_vol'].append(tot_vol)
                        
                        if self.cache_vol[coin] == 0:
                            self.cache_vol[coin] = raw['acc_trade_volume']
                        dev = 0
                        #calculate the change in volume
                        if len(self.data['traded_time']) >= 2:
                            vol_diff = self.data['acc_trade_vol'][-1] - self.cache_vol[coin]
                            if self.data['ask_bid'][-1] == "ASK":
                                sign = -1
                            elif self.data['ask_bid'][-1] == "BID":
                                sign = 1
                            dev = (sign*vol_diff)/(tot_vol)
                            if vol_diff < 0: 
                                #means that the accumulate volume has been reset to zero
                                LOG.info('day has passed updating max_vol and start_price')
                                dev = sign*self.data['acc_trade_vol'][-1]/tot_vol
                            self.data['dev'].append(dev)
                            self.cache_vol[coin] = self.data['acc_trade_vol'][-1]
                        #run trader!!
                        if coin in self.trading_coins:
                            trade_dev.run_trader(
                                coin, raw['trade_price'], self.dev_cut, dev, self.profit_cut
                                )
                        #save file
                        file_path = f'{data_path}/ticker/{date}/upbit_volume_{self.trial}.csv'
                        df1 = pd.DataFrame(self.data)
                        df1.to_csv(file_path)
                        #if current size is over 2000 flush current data
                        if len(self.data['coin']) >= 1500:
                            # root_path = f'{data_path}/ticker/{date}/{file_name}_upbit_volume.csv'
                            # if self.trial == 0:
                            #     df = pd.DataFrame(self.data)
                            #     df.to_csv(root_path)
                            # else:
                            #     df = pd.read_csv(root_path, index_col=0)
                            #     df = pd.concat([df, df1], ignore_index=True)
                            #     df.to_csv(root_path)
                            # os.remove(file_path)
                            self.data['coin'] = self.data['coin'][-1:]
                            self.data['traded_price'] = self.data['traded_price'][-1:]
                            self.data['acc_trade_vol'] = self.data['acc_trade_vol'][-1:]
                            self.data['high'] = self.data['high'][-1:]
                            self.data['ask_bid'] =  self.data['ask_bid'][-1:]
                            self.data['traded_time'] = self.data['traded_time'][-1:]
                            self.data['24h_vol'] = self.data['24h_vol'][-1:]
                            self.data['dev'] = self.data['dev'][-1:]
                            self.trial += 1
            except Exception as e:
                LOG.info('Error while receving data')
                LOG.error(f'Error: {e}')
                await asyncio.sleep(1)
                LOG.info('return to the loop')
        
    async def main(self, trading_coin, collecting_coin):
        await asyncio.gather(
            self.collect_ticker(False, collecting_coin),
            self.collect_ticker(True, trading_coin)
        )
                        
    def run(self):
        asyncio.run(self.collect_ticker())
                        
                        
                        
        
        
        
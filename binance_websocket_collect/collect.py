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


logging.basicConfig(level=logging.WARNING)
logging.getLogger().setLevel(logging.INFO)
LOG = logging.getLogger(__name__)


class binance_websocket:
    initial_krw = 10000
    def __init__(self, coins):
        self.symbols = coins
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
        url = "wss://stream.binance.com:9443/ws"
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        
        #create folder to store data
        # if not os.path.exists(f'{data_path}/binance_ticker/{date}'):
        #     os.mkdir(f'{data_path}/binance_ticker/{date}')
        
        while True:
            try:
                async with websockets.connect(url) as ws:
                    payload = {
                        "method": "SUBSCRIBE",
                        "params": [f"{symbol}@depth3" for symbol in self.symbols],
                        "id": 1
                    }
                        
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
                        if len(raw) == 2:
                            pass
                        else:
                            coin = raw['s']
                            bids = raw['b']
                            asks = raw['a']
                            print(f'{coin} bid: {bids} ask: {asks}')
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
                        
                        
                        
        
        
        
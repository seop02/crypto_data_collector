import asyncio
import ccxt
import logging
import numpy as np
import pprint
import time
import pyupbit
import math
import time

logging.basicConfig(level=logging.WARNING)
logging.getLogger().setLevel(logging.INFO)
LOG = logging.getLogger(__name__)

class market_interaction:
    with open("api.txt") as f:
        lines = f.readlines()
        key_b = lines[0].strip() 
        secret_b = lines[1].strip()

    with open("api_upbit.txt") as f:
        lines = f.readlines()
        key_u = lines[0].strip() 
        secret_u = lines[1].strip()
        
    def __init__(self, coins:list, initial_krw:float):
        self.coins = coins
        self.order_instance = {coin: [0, 0] for coin in coins}
        self.status = {coin: 'sold' for coin in coins}
        self.orders = {coin: 
            {'order': [], 'order_time': 0, 'oder_id': 0, 'state': 0}
            for coin in coins}
        self.balance = {'KRW': initial_krw}
        self.profit = {coin: 1 for coin in coins}
        self.transaction = 0.9995**2
        
    def round_sigfigs(self, num, sig_figs):
        if num != 0:
            return round(num, -int(math.floor(math.log10(abs(num)))) + (sig_figs - 1))
        else:
            return 0.0
    
    def current_balance(self, coin) -> float:
        upbit = pyupbit.Upbit(self.key_u, self.secret_u)
        amount = upbit.get_balance(coin)
        return float(amount)

    def update_balance(self, coin, amount, action):
        upbit = pyupbit.Upbit(self.key_u, self.secret_u)
        if action == 'buy':
            self.balance['KRW'] = 0
            self.balance[coin] = float(amount)
        elif action  == 'sell':
            self.balance[coin] = 0
            self.balance['KRW'] += amount
        elif action == 'sold' or action == 'bought':
            upbit_balance = upbit.get_balance(coin)
            krw_balance = upbit.get_balance('KRW')
            self.balance['KRW'] = 10000
            self.balance[coin] = upbit_balance
            
    
    def update_status(self, coin, order, action, price):
        self.orders[coin]['order'] = order
        self.orders[coin]['order_time'] = time.time()
        self.orders[coin]['order_id'] = order['uuid']
        self.orders[coin]['state'] = order['state']
        self.order_instance[coin] = [price, time.time()]
        self.status[coin] = action
        
    def insert_order(self, coin, action, current_price, amount):
        upbit = pyupbit.Upbit(self.key_u, self.secret_u)
        if action == 'buy':
            price = current_price
            LOG.info(f'buying with current price: {price} currency: {coin} amount: {amount}')
            order = upbit.buy_limit_order(coin, price, amount)
            LOG.info('order submitted')
            LOG.info(order)
            pprint.pprint(order)
            self.update_status(coin, order, action)
            self.update_balance(coin, amount, action)
            return order
        
        elif action == 'sell':
            price = current_price
            LOG.info(f'selling with current price: {price} currency: {coin} amount: {amount}')
            order = upbit.sell_limit_order(coin, price, amount)
            LOG.info('order submitted')
            LOG.info(order)
            self.update_status(coin, order, action)
            self.update_balance(coin, amount, action)
            return order
        
    def market_buy(self, coin, amount):
        upbit = pyupbit.Upbit(self.key_u, self.secret_u)
        order = upbit.buy_market_order(coin, amount)
        LOG.info(order)
        self.update_status(coin, order, 'buy')
        return order
        
    def market_sell(self, coin, amount):
        upbit = pyupbit.Upbit(self.key_u, self.secret_u)
        order = upbit.sell_market_order(coin, amount)
        LOG.info(order)
        self.update_status(coin, order, 'sell')
        return order
        
    def cancel_order(self, orderID):
        upbit = pyupbit.Upbit(self.key_u, self.secret_u)

        resp = upbit.cancel_order(
            uuid=orderID
        )
        return resp 
    
    def get_order(self, orderID, coin):
        upbit = pyupbit.Upbit(self.key_u, self.secret_u)

        resp = upbit.get_order(
            orderID
        )
        self.orders[coin]['order_id'] = resp['uuid']
        self.orders[coin]['state'] = resp['state']
        #LOG.info(f'remaining order: {resp}')
        
    
    
    
    def cancel_protocol(self, coin):
        now = time.time()
        if (now-self.orders[coin]['order_time'] >20 and 
              self.status[coin] == 'buy' and 
              self.orders[coin]['state'] == 'wait'):
            
            LOG.info(f'cancelling buying orders for {coin}')
            LOG.info(f'balance before: {self.balance}')
            self.cancel_order(self.orders[coin]['order_id'])
            self.status[coin] = 'sold'
            self.update_balance(coin, 0, self.status[coin])
            LOG.info(f'current {coin} balance: {self.balance} status: {self.status[coin]}')
   
        elif (now-self.order_instance[coin][1]>40000 and 
              self.status[coin] == 'buy' and 
              self.orders[coin]['state'] == 'wait'):
            
            LOG.info(f'cancelling the orders for {coin}')
            LOG.info(f'balance before: {self.balance}')
            self.cancel_order(self.orders[coin]['uuid'])
            LOG.info('cancelled sell order')
            self.status[coin] = 'bought'
            self.update_balance(coin, 0, self.status[coin])
            LOG.info(f'balance after: {self.balance}')
            

            
            
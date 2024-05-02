from websocket_data.order import market_interaction
import logging
import time
import ccxt
import pyupbit
import math
from sklearn.tree import DecisionTreeClassifier
from catboost import CatBoostClassifier
import numpy as np

logging.basicConfig(level=logging.WARNING)
logging.getLogger().setLevel(logging.INFO)
LOG = logging.getLogger(__name__)


class dev_trader(market_interaction):
    def update_order(self, coin, profit_cut):
        if self.status[coin] == 'buy' or self.status[coin] == 'sell':
            self.get_order(self.orders[coin]['order_id'], coin)
            if self.orders[coin]['state'] != 'wait':
                if self.status[coin] == 'buy':
                    target_price = (profit_cut[coin]*self.order_instance[coin][0])/self.transaction
                    if coin == 'KRW-BTC':
                        target_price= self.round_sigfigs(target_price, 5)
                    else:
                        target_price = self.round_sigfigs(target_price, 4)
                    amount = self.balance[coin]
                    self.insert_order(coin, 'sell', target_price, amount)
                elif self.status[coin] == 'sell':
                    self.status[coin] = 'sold'
                    self.update_balance(coin, 0,'sold')
                    LOG.info(f'order filled for {coin} status: {self.status[coin]} balance: {self.balance}')
                    self.profit[coin] = 1
    
    def update_profit(self, coin, price):
        if self.status[coin] != 'sold':
            self.profit[coin] = (self.transaction*price)/self.order_instance[coin][0]
    
    def sell_protocol(self, coin, price, profit_cut):
        now = time.time()
        if self.profit[coin] <= -0.05 and (self.status[coin] == 'bought' or self.status[coin] == 'sell'):
            if self.status[coin] == 'SELL':
                LOG.info(f'cancelling the orders for {coin}')
                LOG.info(f'balance before: {self.balance}')
                self.cancel_order(self.orders[coin]['order_id'])
                LOG.info('cancelled sell order')
                self.update_balance(coin, 0, self.status[coin])
                LOG.info(f'balance after: {self.balance}')
                self.status[coin] = 'bought'
                time.sleep(1)
            if self.status[coin] == 'bought':
                a = self.balance[coin]
                LOG.info(f'kind of bad selling {coin} at price {price} balance:{self.balance} profit: {self.profit[coin]}')
                self.insert_order(coin, 'sell', price, a)
                self.status[coin] = 'sell'
                self.update_balance(coin, a, 'sell')
                LOG.info(f'kind of bad sold {coin} at price {price} balance: {self.balance} profit: {self.profit[coin]}')
                time.sleep(5)
    
        if now-self.order_instance[coin][1]> 400000 and self.status[coin] == 'bought':
            a = self.balance[coin]
            LOG.info(f'late selling {coin} at price {price} balance: {self.balance[coin]} profit: {self.profit[coin]}')
            self.insert_order(coin, 'sell', price, a)
            
        if self.status[coin] == 'buy' or self.status[coin] == 'sell':
            self.update_order(coin, profit_cut)
        self.cancel_protocol(coin)
    
    def scalp(self, coin, price, dev_cut, dev):
        if (dev > dev_cut[coin] and self.status[coin] == 'sold'
            and self.balance['KRW'] > 5100 ):
            LOG.info(f'buying signal generated for {coin} at price {price}')
            amount = (self.balance['KRW']/price)*0.9995
            self.insert_order(coin, 'buy', price, amount)
            LOG.info(f'buying {coin} at price {price} balance: {self.balance} orders: {self.order_instance[coin]}')
            
        elif self.status[coin] == 'sold' and self.balance['KRW'] < 5100 and dev > dev_cut[coin]:
            LOG.info(f'buying signal generated for {coin} for price: {price} but could not buy')
            
    def run_trader(self, coin, price, dev_cut, dev, profit_cut):
        self.scalp(coin, price, dev_cut, dev)
        self.update_profit(coin, price)
        self.sell_protocol(coin, price, profit_cut)
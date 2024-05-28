from upbit_websocket_collect.order import market_interaction
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
                    self.update_balance(coin, 0,'sold')
                    amount = self.balance[coin]
                    time.sleep(0.5)
                    self.insert_order(coin, 'sell', target_price, amount)
                elif self.status[coin] == 'sell':
                    self.status[coin] = 'sold'
                    self.update_balance(coin, 0,'sold')
                    if self.balance[coin] != 0:
                        self.status[coin] = 'bought'
                    else:
                        self.status[coin] == 'sold'
                    LOG.info(f'order filled for {coin} status: {self.status[coin]} balance: {self.balance}')
                    self.profit[coin] = 1
    
    def update_profit(self, coin, price):
        if self.status[coin] != 'sold' and self.bought_instance[coin][0] != 0:
            self.profit[coin] = (self.transaction*price)/self.bought_instance[coin][0]
    
    def sell_protocol(self, coin, price, profit_cut):
        now = time.time()
        if self.profit[coin] <= 0.98 and (self.status[coin] == 'bought' or self.status[coin] == 'sell'):
            if self.status[coin] == 'sell':
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
            
        self.update_sell_order(coin, price, profit_cut)
        self.cancel_protocol(coin)
    
    def scalp(self, coin, price, dev_cut, dev, high):
        # if price <= 0.99*high and self.status[coin] == 'sold' and self.balance['KRW'] >= 5100:
        #     LOG.info(f'coin: {coin} price: {price} high: {high}')
        if (dev >= dev_cut[coin] and self.status[coin] == 'sold'
            and self.balance['KRW'] >= 5100 and price <= 0.99*high):
            LOG.info(f'buying signal generated for {coin} at price {price} dev: {dev} dev_cut: {dev_cut[coin]}')
            amount = (self.balance['KRW']/price)*0.9995
            self.insert_order(coin, 'buy', price, amount)
            LOG.info(f'buying {coin} at price {price} balance: {self.balance} orders: {self.order_instance[coin]}')
            
        elif self.status[coin] == 'sold' and self.balance['KRW'] < 5100 and dev > dev_cut[coin]:
            LOG.info(f'buying signal generated for {coin} for price: {price} but could not buy')
            self.order_instance[coin] = [price, time.time()]
            
    def update_sell_order(self, coin, price, profit_cut):
        if self.status[coin] == 'sell' or self.status[coin] == 'bought' and self.profit[coin] >= 0.99:
            upbit = pyupbit.Upbit(self.key_u, self.secret_u)
            time_diff = time.time() - self.bought_instance[coin][1]
            new_profit = 1.001/0.9995+0.099*np.exp(-time_diff/10000)
            new_target_price = self.bought_instance[coin][0]*new_profit
            if coin == 'KRW-BTC':
                new_target_price= self.round_sigfigs(new_target_price, 5)
            else:
                new_target_price = self.round_sigfigs(new_target_price, 4)
            
            if self.order_instance[coin][0] != new_target_price:
                #LOG.info(f'{coin} cancel existing sell ORDER!!!')
                old_price = self.order_instance[coin][0]
                order_id = self.orders[coin]['order_id']
                #LOG.info(f'new: {new_target_price} old: {old_price} ID: {order_id}')
                self.cancel_order(self.orders[coin]['order_id'])
                time.sleep(0.5)
                amount = upbit.get_balance(coin)
                self.insert_order(coin, 'sell', new_target_price, amount)
                self.status[coin] = 'sell'
            
            
    def run_trader(self, coin, price, dev_cut, dev, profit_cut, high):
        if self.i == 1:
            self.update_balance('KRW-BTC', 0, 'sold')
            # LOG.info(f'starting balance: {self.balance}')
            # self.bought_instance['KRW-STORJ'] = [134.4, time.time()-10000]
            # self.insert_order('KRW-ATOM', 'sell', 12000, self.balance['KRW-ATOM'])
            # self.status['KRW-ATOM'] = 'sell'
            #LOG.info(f'status: {self.status[coin]}')
            self.i += 1
        self.scalp(coin, price, dev_cut, dev, high)
        self.update_profit(coin, price)
        self.sell_protocol(coin, price, profit_cut)
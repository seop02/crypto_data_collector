from order import market_interaction
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


class accumulated_trade(market_interaction):
    transaction = 0.9995**2
            
    def sell_protocol(self, balance:dict, profit:float, status:dict, coin:str, 
                      order:dict, order_time:dict, price:float, sold_price:dict,
                      order_id:dict, bought_time:dict, bought_price:dict, initial_krw:float,
                      profit_cut:float, max_profit:dict, time_diffs:dict):
        now = time.time()
        # if high_count[coin] > 100000 and status[coin] == 'BOUGHT':
        #     a = balance[coin]
        #     LOG.info(f'selling {coin} at price {price} balance: {balance} profit: {profit} high_count: {high_count}')
        #     order[coin] = self.insert_order(coin, 'sell', price, a)
        #     order_time[coin] = time.time()
        #     sold_price[coin] = price
        #     order_id[coin] = self.get_order(order[coin]['uuid'])
        #     status[coin] = 'SELL'
        #     balance[coin] = 0
        #     #balance['KRW'] +=  10000
        #     LOG.info(f'selling {coin} at price {price} balance: {balance} profit: {profit}')
        
        if profit <= -0.01 and (status[coin] == 'BOUGHT' or status[coin] == 'SELL'):
            if status[coin] == 'SELL':
                LOG.info(f'cancelling the orders for {coin}')
                LOG.info(f'balance before: {balance}')
                order_id[coin] = self.get_order(order[coin]['uuid'])
                upbit = pyupbit.Upbit(self.key_u, self.secret_u)
                self.cancel_order(order_id[coin]['uuid'])
                LOG.info('cancelled sell order')
                upbit_balance = upbit.get_balance(coin)
                krw_balance = upbit.get_balance('KRW')
                #balance['KRW'] -= 1220000
                LOG.info(upbit_balance)
                cry_balance = float(upbit_balance)
                balance[coin] = cry_balance
                LOG.info(f'balance after: {balance}')
                status[coin] = 'BOUGHT'
                time.sleep(1)
            if status[coin] == 'BOUGHT':
                a = balance[coin]
                LOG.info(f'kind of bad selling {coin} at price {price} balance: {balance} profit: {profit}')
                order[coin] = self.insert_order(coin, 'sell', price, a)
                order_time[coin] = time.time()
                sold_price[coin] = price
                order_id[coin] = self.get_order(order[coin]['uuid'])
                status[coin] = 'SELL'
                balance[coin] = 0
                #balance['KRW'] +=  50000
                LOG.info(f'kind of bad sold {coin} at price {price} balance: {balance} profit: {profit}')
                time.sleep(5)

        if max_profit[coin] >= 0.005 and profit <= max_profit[coin]/2 and (status[coin] == 'BOUGHT' or status[coin] == 'SELL'):
            if status[coin] == 'SELL':
                LOG.info(f'cancelling the orders for {coin}')
                LOG.info(f'balance before: {balance}')
                order_id[coin] = self.get_order(order[coin]['uuid'])
                upbit = pyupbit.Upbit(self.key_u, self.secret_u)
                self.cancel_order(order_id[coin]['uuid'])
                LOG.info('cancelled sell order')
                upbit_balance = upbit.get_balance(coin)
                krw_balance = upbit.get_balance('KRW')
                #balance['KRW'] -= 1220000
                LOG.info(upbit_balance)
                cry_balance = float(upbit_balance)
                balance[coin] = cry_balance
                LOG.info(f'balance after: {balance}')
                status[coin] = 'BOUGHT'
                order[coin] = self.market_sell(coin, cry_balance)
                order_id[coin] = self.get_order(order[coin]['uuid'])
                status[coin] = 'SELL'
                time.sleep(1)
            if status[coin] == 'BOUGHT':
                a = balance[coin]
                LOG.info(f'kind of good selling {coin} at price {price} balance: {balance} profit: {profit}')
                order[coin] = self.insert_order(coin, 'sell', price, a)
                order_time[coin] = time.time()
                sold_price[coin] = price
                order_id[coin] = self.get_order(order[coin]['uuid'])
                status[coin] = 'SELL'
                balance[coin] = 0
                #balance['KRW'] +=  50000
                LOG.info(f'kind of bad sold {coin} at price {price} balance: {balance} profit: {profit}')
        #         time.sleep(5)
    
        if now-order_time[coin]> 400000 and status[coin] == 'BOUGHT':
            a = balance[coin]
            LOG.info(f'late selling {coin} at price {price} balance: {balance} profit: {profit}')
            order[coin] = self.insert_order(coin, 'sell', price, a)
            order_time[coin] = time.time()
            sold_price[coin] = price
            order_id[coin] = self.get_order(order[coin]['uuid'])
            status[coin] = 'SELL'
            LOG.info(f'late bad sold {coin} at price {price} balance: {balance} profit: {profit}')
            
        if status[coin] == 'BUY' or status[coin] == 'SELL':
            #LOG.info(f'updating {coin} orderID current profit: {profit}')
            order_id[coin] = self.get_order(order[coin]['uuid'])
            if order_id[coin]['state'] != 'wait':
                if status[coin] == 'BUY':
                    balance, bought_price, order, order_time, order_id, status = self.upper_sell(coin, bought_price, balance, 
                                                                                                 status, order, order_id, order_time)
                    #status[coin] = 'BOUGHT1'
                    #balance[coin] = float(order_id[coin]['volume'])
                    order_time[coin] = time.time()
                    LOG.info(f'order filled for {coin} status: {status[coin]} balance: {balance}')
                elif status[coin] == 'SELL':
                    status[coin] = 'SOLD1'
                    max_profit[coin] = 0
                    #high_count[coin] = 0
                    balance['KRW'] += 1260000
                    balance[coin] = 0
                    LOG.info(f'order filled for {coin} status: {status[coin]} balance: {balance}')
                    max_profit[coin] = 0
        order_id, status, balance, order = self.cancel_protocol(now, coin, balance, order_time, 
                                                                order_id, order, status, initial_krw,
                                                                bought_price, bought_time)
            
        return balance, status, bought_time, order, order_id, sold_price, max_profit, time_diffs
            
            
    
    def scalp(self, coin: str, current_volume:dict,price: float,
            order_time: dict, balance: dict, status: dict, 
            order: dict, dev:float, time_delta:float, max_price:dict,
            order_id:dict,  bought_price:dict, initial_krw:float,
            bought_time:dict, step:dict, start_time:float, high_p:float, 
            dev_cut:dict):
        
        
        if dev > dev_cut[coin] and status[coin] == 'SOLD' and balance['KRW'] > 5100 and coin != 'KRW-MED' and coin != 'KRW-STRAX' and coin != 'KRW-GLM' and coin != 'KRW-HPO':
        #if status[coin] == 'SOLD' and balance['KRW'] > 5100 and 50 > time_delta > 15:
        #if balance["KRW"] > 5000:
            # sublist = np.array(current_volume['dev'][-100:-2])
            # std = np.std(sublist/np.linalg.norm(sublist))
            # sub_min = np.min(sublist)
            # sub_max = np.max(sublist)
            # normalized_diff = (sub_max-sub_min)/(sub_max)
            LOG.info(f'buying signal generated for {coin} at price {price}')
            high_diff = (high_p-price)/price
            LOG.info(f'coin: {coin} time_delta: {time_delta} high_diff: {high_diff}')
            condition_2 = coin == 'KRW-BTC' or coin == 'KRW-ETC' or coin =='KRW-ETH' or coin =='KRW-XRP'      
            if True:
                balance, bought_price, order, order_time, order_id, status = self.buy(
                                                                                        coin, balance, price, step, 
                                                                                        bought_price, order, order_time, 
                                                                                        order_id, status
                                                                                        )
                bought_price[coin] = price-0*step[coin]
                bought_time[coin] = float(time.time())
                status[coin] = 'BUY'
                #std = 1
                LOG.info(f'buying {coin} at price {bought_price[coin]} balance: {balance} order_id: {order_id[coin]} time_delta: {time_delta} bought_time: {bought_time[coin]} status: {status[coin]} high_diff: {(high_p-price)/price}')
            
        elif coin != 'KRW-BTC' and status[coin] == 'SOLD' and balance['KRW'] < 5100 and dev > dev_cut[coin] and status[coin] == 'SOLD':
            LOG.info(f'buying signal generated for {coin} for price: {price} but could not buy')
            
        return balance, status, bought_time, bought_price, order, order_id
    
    def lower_buy(self, coin: str, current_volume:dict,price: float,
            order_time: dict, balance: dict, status: dict, 
            order: dict, dev:float, max_dev:dict, max_price:dict,
            order_id:dict,  bought_price:dict, initial_krw:float,
            bought_time:dict, step:dict, start_time:float):
        
        
        if status[coin] == 'BUYING' and balance['KRW'] > 5100 and coin != 'KRW-PLA':
            balance, bought_price, order, order_time, order_id, status = self.buy(
                                                                                    coin, balance, price, step, 
                                                                                    bought_price, order, order_time, 
                                                                                    order_id, status
                                                                                    )
            #bought_price[coin] = price-60*step[coin]
            status[coin] = 'BUY'
            LOG.info(f'buying {coin} at price {bought_price[coin]} balance: {balance} order_id: {order_id[coin]}')
    
        elif status[coin] == 'BUYING' and balance['KRW'] < 5100:
            LOG.info(f'buying signal generated for {coin} for price: {price} but could not buy')
            
        return balance, status, bought_time, bought_price, order, order_id
            
            
        

class max_trade(trade_fast):
            
    def run(self, coin, step, current_price, 
            current_vol, balance, currency, 
            order_time, order, order_id, cutoff):
        asset = balance[0] + (current_price-step)*balance[1]

        if current_vol >= cutoff and balance[1] != 0 and current_price != ordered_price and order_time[1] == 'BOUGHT':
        #if asset > 1.01*initial_asset and balance[1] != 0:
            LOG.info(f'selling {coin} at price {current_price} with {current_momentum} {max_mo}')
            #order = self.market_sell(coin, balance[1])
            order = self.insert_order(coin, 'sell', current_price, balance[1], step)
            #a = (balance[1]*(current_price-step))*0.9995
            #balance = [a, 0]
            ordered_price = current_price
            asset = balance[0] + (current_price-step)*balance[1]
            LOG.info(f'current asset for {coin}: {asset}')
            max_mo = current_momentum
            order_time = [time.time(), 'SELL']
            LOG.info(f'selling order: {order}')
            order_id = self.get_order(order['uuid'])
        
        elif cutoff[3]*min_mo <= current_momentum and current_momentum<= cutoff[4]*min_mo and ordered_price != current_price and (order_time[1] == 'SOLD' or order_time[1] =='null'):
            a = (balance[0]/(current_price+step))*0.9995
            LOG.info(balance)
            LOG.info(order_time)
            LOG.info(f'buying {coin} at price {current_price} amount: {a} momentum: {current_momentum} {min_mo}')
            order = self.insert_order(coin, 'buy', current_price, a, step)
            balance = [0, a]
            LOG.info(f'balance after buying: {balance}')
            ordered_price = current_price
            min_mo = current_momentum
            order_time = [time.time(), 'BUY']
            LOG.info(f'buying order: {order}')
            LOG.info(f'buying time: {order_time}')
            order_id = self.get_order(order['uuid'])
        
        if order_time[1] == 'BUY' or order_time[1] == 'SELL':
            LOG.info('updating orderID')
            order_id = self.get_order(order['uuid'])
        now = time.time()
        if now-order_time[0]>3 and order_id['state'] == 'wait':
            LOG.info(f'cancelling the orders for {coin}')
            LOG.info(f'balance before: {balance}')
            order_id = self.get_order(order['uuid'])
            upbit = pyupbit.Upbit(self.key_u, self.secret_u)
            self.cancel_order(order_id['uuid'])
            if order_time[1] == 'BUY':
                LOG.info('cancelled buy order')
                upbit_balance = upbit.get_balance(coin)
                krw_balance = krw_balance = 0.9995*(current_price-step)*balance[1]
                LOG.info(upbit_balance)
                cry_balance = 0
                balance =[krw_balance, cry_balance]
                LOG.info(f'balance after: {balance}')
                order_time = [time.time(), 'SOLD']
            elif order_time[1] == 'SELL':
                LOG.info('cancelled sell order')
                # a = balance[0]/((current_price+step)*0.9995)
                # balance = [0, a]
                upbit_balance = upbit.get_balance(coin)
                krw_balance = 0
                LOG.info(upbit_balance)
                cry_balance = float(upbit_balance)
                balance =[krw_balance, cry_balance]
                LOG.info(f'balance after: {balance}')
                order_time = [time.time(), 'BOUGHT']
            LOG.info(f'order_time after cancellation: {order_time}')

        elif order_id['state'] == 'done' and order_time[1] != 'BOUGHT' and order_time[1] != 'SOLD':
            LOG.info(f'order filled for {coin}')
            upbit = pyupbit.Upbit(self.key_u, self.secret_u)
            if order_time[1] == 'BUY':
                order_time = [time.time(), 'BOUGHT']
                upbit_balance = upbit.get_balance(coin)
                krw_balance = 0
                LOG.info(upbit_balance)
                cry_balance = float(upbit_balance)
                balance =[krw_balance, cry_balance]
                LOG.info(f'balance after buying: {balance}')
            elif order_time[1] == 'SELL':
                order_time = [time.time(), 'SOLD']
                upbit_balance = upbit.get_balance(coin)
                krw_balance = 0.9995*(current_price-step)*balance[1]
                LOG.info(upbit_balance)
                cry_balance = float(upbit_balance)
                balance =[krw_balance, cry_balance]
                LOG.info(f'balance after selling: {balance}')
                
            LOG.info(f'{coin} {order_time} {balance}')
        #LOG.info('moving on')
        #LOG.info(f'current order)time: {order_time}')
        
        return balance, asset, ordered_price, order, order_time
    
    def sell_everything(self, coin, current_price, step):
        upbit = pyupbit.Upbit(self.key_u, self.secret_u)
        upbit_balance = upbit.get_balance(coin)
        cry_balance = float(upbit_balance)
        order = self.market_sell(coin, cry_balance)
        

#!/usr/bin/python
# -*- coding: utf-8 -*-

from stocks import Util, Stocks, Stock
from account import Account

 
NO_CROSS = 0
INIT_GOLD_CROSS = 1   # 初始化时, 金叉排列
INIT_DEAD_CROSS = 2   # 初始化时, 死叉排列
GOLD_CROSS = 3
DEAD_CROSS = 4

class AvgLine(object):
    def __init__(self, m, n):
        self.min_n = min(m, n)
        self.max_n = max(m, n)
        self.min_avg = 0
        self.max_avg = 0
        self.data_len = 0
        self.cross_len = 0
        self.cross = NO_CROSS

    def calc_avg(self, data, n, avg):
        if self.data_len > n:
            return (data + n * avg) / float(n + 1)
        else:
            return (data + (self.data_len - 1) * avg) / float(self.data_len)

    def update(self, data):
        self.data_len += 1
        self.min_avg = self.calc_avg(data, self.min_n, self.min_avg)
        self.max_avg = self.calc_avg(data, self.max_n, self.max_avg)
        if self.data_len > self.max_n:
            if self.min_avg > self.max_avg:
                if self.cross in [GOLD_CROSS, INIT_GOLD_CROSS]:
                    self.cross_len += 1
                elif self.cross in [DEAD_CROSS, INIT_DEAD_CROSS]:
                    self.cross = GOLD_CROSS
                    self.cross_len = 0
                else:
                    self.cross = INIT_GOLD_CROSS
            elif self.min_avg < self.max_avg:
                if self.cross in [DEAD_CROSS, INIT_DEAD_CROSS]:
                    self.cross_len += 1
                elif self.cross in [GOLD_CROSS, INIT_GOLD_CROSS]:
                    self.cross = DEAD_CROSS
                    self.cross_len = 0
                else:
                    self.cross = INIT_DEAD_CROSS
            else:
                self.cross_len += 1
        return (self.cross, self.cross_len)


# 策略1：每只股票单独跟踪，买入信号时买入，平均控制仓位，板块控制总量，可以用指数进行过滤
class Stra(object):
    def __init__(self, m, n):
        self.avg_m_n = (m, n)
        self.internal_stat = {}  # {stock_id: AvgLine}

    # 跟踪每只股票，生成买卖信号，不考虑持有情况
    def first_oper(self, tick):
        stock_oper = []  # [(stock_id, 'buy/sell/NoAct', price), ...]
        # tick: (time, [(stock_id, (open, close, high, low, volume)), (stock_id, ()), ...])
        time_, tick_data = tick
        for stock_id, tick_info in tick_data:
            stock_oper.append((stock_id, 'NoAct'))
            if tick_info:
                close_ = tick_info[1]
                # 5, 15日均线金叉买入，死叉卖出，错过交叉点3日内可以买卖
                if not stock_id in self.internal_stat: self.internal_stat[stock_id] = AvgLine(*self.avg_m_n)
                cross, cross_len = self.internal_stat[stock_id].update(close_)
                if cross_len < 3:
                    if cross == GOLD_CROSS:
                        stock_oper[-1] = (stock_id, 'buy', close_)
                    elif cross == DEAD_CROSS:
                        stock_oper[-1] = (stock_id, 'sell', close_)
        return (time_, stock_oper)

    # 筛选股票，需要卖的保留，需要买的需要根据条件挑选，只保留几只股票
    def second_oper(self, account, time_, stock_oper_1):
        stock_oper = []   # [(stock_id, 'buy/sell'， price, number)]
        # 先处理卖的，再处理买的
        # 过滤，保留买的，和可以卖的
        for stock_id, oper, price in stock_oper_1:
            if oper == 'buy':
                stock_oper.append((stock_id, oper, price, 0))
            elif oper == 'sell':
                number = account.can_sell_num(stock_id, time_):
                if number > 0: stock_oper.append((stock_id, oper, price, number))
        return stock_oper

    # 根据资金管理，生成买股票的数量
    def third_oper(self, account, time_, stock_oper_2):
        # 资金管理
        stock_oper = []   # [(stock_id, 'buy/sell', price, number)]
        return stock_oper_2


class Test(object):
    def __init__(self):
        self.account = Account(10000)
        self.stocks = Stocks()
        self.stocks.load_from_file('stock_data.dat')

    def test_stra(self, stra):
        self.account.reset()
        for tick in self.stocks.iter_ticks():
            time_, oper = stra.first_oper(tick)
            oper = stra.second_oper(tick, self.account, time_, oper)
            oper = stra.third_oper(tick, self.account, time_, oper)
        return result


if __name__ == '__main__':
    stra = Stra(5, 15)
    test = Test()
    result = test.test_stra(stra)
    print result
    result1 = test.test_stra(Stra(3, 30))
    print result1

    


    
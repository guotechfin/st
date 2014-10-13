#!/usr/bin/python
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
from stocks import Util, Stocks


class Account(object):
    def __init__(self, money):
        self.init_money = money
        self.fee = 0.006   # trade fee, 6/1000
        self.reset()

    def __str__(self):
        s = 'history:\n'
        for h in self.history:
            s += '    %s\n' % str(h)
        s += '\nprofit:\n'
        for p in self.profit:
            s += '    %s\n' % str(p)
        return s

    def reset(self):
        self.money = self.init_money
        self.stocks = []  # stock_id, buy_time, buy_price(元/手), number(手), used_money
        self.hold_stocks = {}   # stock_id: number
        self.market_time = []
        self.market_value = []
        self.history = []  # time, buy or sell, stock_id, price, number
        self.profit = []   # sell_time, stock_id, profit
        self.all_profit = []  # profit
        self.hold_days = []  # stock hold days of one trade
        self.latest_price = {}  # stock_id: latest stock price

    def update(self, tick):
        # tick: (time, [(stock_id, (open, close, high, low, volume)), (stock_id, ()), ...])
        stocks_value = 0
        time_, stocks_price = tick
        for stock_id, price in stocks_price:
            if price:
                self.latest_price[stock_id] = price[1]
        for stock_id, c in self.latest_price.items():
            if stock_id in self.hold_stocks:
                stocks_value += c * self.hold_stocks[stock_id]
        self.market_time.append(time_)
        self.market_value.append(stocks_value + self.money)

    def can_sell_num(self, stock_id, time_ = None):
        stock_num = 0
        for sid, buy_time, buy_price, number, used_money in self.stocks:
            if sid == stock_id and Util.time_to_digit(buy_time) < Util.time_to_digit(time_):
                stock_num += number
        return stock_num

    def hold_stock_num(self):
        return len(self.hold_stocks)

    # def buy_sell_stocks(self, oper, today = None):
    #     # oper: [(stock_id, 'buy/sell', price, number), ...]
    #     for stock_id, buy_sell, price, number in oper:
    #         if buy_sell == 'buy' and number > 0:
    #             self.buy_stock(stock_id, price, number, today)
    #         elif buy_sell == 'sell' and number > 0:
    #             self.sell_stock(stock_id, price, number, today)

    # money: 元, price: 元/手(100股), number: 手(100股)
    def buy_stock(self, stock_id, price, money = 0, today = None):
        money = min(money, self.money) or self.money
        net_money = money / (1 + self.fee)
        number = int(net_money / float(price))  # 手(100股)
        if number:
            money = price * number * (1 + self.fee)
            self.money -= money
            self.stocks.append((stock_id, today, price, number, money))
            self.history.append((today, 'buy', stock_id, price, number))
            if stock_id not in self.hold_stocks: self.hold_stocks[stock_id] = 0
            self.hold_stocks[stock_id] += number

    # # money: 元, price: 元/股, number: 股
    # def buy_stock_1(self, stock_id, price, number = 0, today = None):
    #     max_number = int(self.money / float(price * 100))  # 手(100股)
    #     number = min(max_number, int(number /100) or max_number)
    #     if number:
    #         money = price * number * 100
    #         self.money -= money
    #         self.stocks.append((stock_id, today, price, number, money))
    #         self.history.append((today, 'buy', stock_id, price, number))

    # always sell all at once
    def sell_stock(self, stock_id, price, today = None, hold_stock_days = None):
        total_sell_n = 0
        hold_trade_num = len(self.stocks)
        stock_cost = 0
        for i, (sid, buy_time, buy_price, n, used_money) in enumerate(self.stocks[::-1]):
            if sid == stock_id:
                if today and Util.time_to_digit(buy_time) >= Util.time_to_digit(today):
                    raise Exception('Error: stock_id: %s, buy_time: %s, sell_time: %s' % (sid, buy_time, today))
                total_sell_n += n
                stock_cost += used_money
                del self.stocks[hold_trade_num - i - 1]
        if total_sell_n:
            self.history.append((today, 'sell', stock_id, price, total_sell_n))
            money = total_sell_n * price
            self.money += money
            profit = (float(money) / stock_cost - 1) * 100
            self.profit.append((today, stock_id, profit))
            self.all_profit.append(profit)
            del self.hold_stocks[stock_id]
            if hold_stock_days: self.hold_days.append(hold_stock_days)

    # def sell_stock_1(self, stock_id, price, number = 0, today = None, hold_stock_days = None):
    #     total_sell_n = 0
    #     remain_number = number
    #     for i, (sid, buy_time, buy_price, n) in enumerate(self.stocks):
    #         if sid == stock_id and (not today or Util.time_to_digit(buy_time) < Util.time_to_digit(today)):
    #             if number and n >= remain_number:
    #                 total_sell_n += remain_number
    #                 if n == remain_number:
    #                     self.stocks[i] = None
    #                 else:
    #                     self.stocks[i] = (sid, buy_time, buy_price, n - remain_number)
    #                 break
    #             else:
    #                 total_sell_n += n
    #                 self.stocks[i] = None
    #                 if number: remain_number -= n
    #     for i in range(self.stocks.count(None)):
    #         self.stocks.remove(None)
    #     if total_sell_n:
    #         self.history.append((today, 'sell', stock_id, price, total_sell_n))
    #         self.money += total_sell_n * price * 100

    def summarize(self, test_period = None, trade_stocks = None):
        # 平均收益, 胜率, 盈亏比, 盈亏股票比, 频率, 最大回撤, 盈利直方图
        total_profit = 0
        win_num = lose_num = 0
        win_profit = lose_profit = 0
        max_win_profit = max_lose_profit = 0
        stock_profit = {}
        for time_, stock_id, profit in self.profit:
            max_win_profit = max(max_win_profit, profit)
            max_lose_profit = min(max_lose_profit, profit)
            total_profit += profit
            if not stock_id in stock_profit: stock_profit[stock_id] = 0
            stock_profit[stock_id] += profit
            if profit > 0:
                win_num += 1
                win_profit += profit
            elif profit < 0:
                lose_num += 1
                lose_profit += profit
        win_stock = lose_stock = 0
        for stock_id, profit in stock_profit.items():
            if profit > 0:
                win_stock += 1
            elif profit < 0:
                lose_stock += 1
        win_profit, lose_profit = float(win_profit) / win_num, float(lose_profit) / lose_num
        win_lose_profit_ratio = -float(win_profit) / lose_profit
        win_lose_ratio = float(win_num) / (win_num + lose_num) * 100
        win_lose_stock_ratio = float(win_stock) / (win_stock + lose_stock) * 100
        mean_profit = total_profit / len(self.profit)

        s = '\ntotal_profit: %.1f%%, mean_profit: %.1f%%\n' % (total_profit, mean_profit)
        s += 'mean_win_profit: %.1f%%, mean_lose_profit: %.1f%%\n' % (win_profit, lose_profit)
        s += 'win_lose_ratio: %.1f%%\n' % win_lose_ratio
        s += 'win_lose_profit_ratio: %.1f\n' % win_lose_profit_ratio
        s += 'win_lose_stock_ratio: %.1f%%\n' % win_lose_stock_ratio
        s += 'max_win: %.1f%%, max_lose: %.1f%%\n' % (max_win_profit, max_lose_profit)
        s += 'trade_num: %d, avg_hold_days: %.1f' % (len(self.profit), np.mean(self.hold_days))
        if test_period and trade_stocks:
            days, day_start, day_end = test_period
            s += '\ntrade_freq: %.2f%%, total_days: %d, total_stocks: %d\n' % (len(self.profit)*100/float(days)/trade_stocks, days, trade_stocks)
            s += 'test from %s to %s' % (day_start, day_end)
        return s

    def show_profit_pdf(self):
        plt.hist(self.all_profit, 100)
        plt.grid(True)
        plt.show()

    def show_summarize(self, test_period = None, trade_stocks = None):
        s = self.summarize(test_period, trade_stocks)
        print s

class VirtualAccount(object):
    def __init__(self):
        self.stocks = {}   # stock_id: buy_price(元)
        self.history = []  # time, buy or sell, stock_id, price
        self.profit = []   # time, stock_id, profit
        self.all_profit = []  # profit
        self.hold_days = []  # stock hold days of one trade

    def buy_stock(self, stock_id, price, today):
        self.stocks[stock_id] = price
        self.history.append((today, 'buy', stock_id, price))

    def sell_stock(self, stock_id, price, today, hold_stock_days = None):
        if stock_id in self.stocks:
            profit = (float(price) / self.stocks[stock_id] - 1) * 100
            self.profit.append((today, stock_id, profit))
            self.all_profit.append(profit)
            self.history.append((today, 'sell', stock_id, price))
            if hold_stock_days: self.hold_days.append(hold_stock_days)
            del self.stocks[stock_id]

    def summarize(self, test_period = None, trade_stocks = None):
        # 平均收益, 胜率, 盈亏比, 盈亏股票比, 频率, 最大回撤, 盈利直方图
        total_profit = 0
        win_num = lose_num = 0
        win_profit = lose_profit = 0
        max_win_profit = max_lose_profit = 0
        stock_profit = {}
        for time_, stock_id, profit in self.profit:
            max_win_profit = max(max_win_profit, profit)
            max_lose_profit = min(max_lose_profit, profit)
            total_profit += profit
            if not stock_id in stock_profit: stock_profit[stock_id] = 0
            stock_profit[stock_id] += profit
            if profit > 0:
                win_num += 1
                win_profit += profit
            elif profit < 0:
                lose_num += 1
                lose_profit += profit
        win_stock = lose_stock = 0
        for stock_id, profit in stock_profit.items():
            if profit > 0:
                win_stock += 1
            elif profit < 0:
                lose_stock += 1
        win_profit, lose_profit = float(win_profit) / win_num, float(lose_profit) / lose_num
        win_lose_profit_ratio = -float(win_profit) / lose_profit
        win_lose_ratio = float(win_num) / (win_num + lose_num) * 100
        win_lose_stock_ratio = float(win_stock) / (win_stock + lose_stock) * 100
        mean_profit = total_profit / len(self.profit)

        s = '\ntotal_profit: %.1f%%, mean_profit: %.1f%%\n' % (total_profit, mean_profit)
        s += 'mean_win_profit: %.1f%%, mean_lose_profit: %.1f%%\n' % (win_profit, lose_profit)
        s += 'win_lose_ratio: %.1f%%\n' % win_lose_ratio
        s += 'win_lose_profit_ratio: %.1f\n' % win_lose_profit_ratio
        s += 'win_lose_stock_ratio: %.1f%%\n' % win_lose_stock_ratio
        s += 'max_win: %.1f%%, max_lose: %.1f%%\n' % (max_win_profit, max_lose_profit)
        s += 'trade_num: %d, avg_hold_days: %.1f' % (len(self.profit), np.mean(self.hold_days))
        if test_period and trade_stocks:
            days, day_start, day_end = test_period
            s += '\ntrade_freq: %.2f%%, total_days: %d, total_stocks: %d\n' % (len(self.profit)*100/float(days)/trade_stocks, days, trade_stocks)
            s += 'test from %s to %s' % (day_start, day_end)
        return s

    def show_profit_pdf(self):
        plt.hist(self.all_profit, 100)
        plt.grid(True)
        plt.show()

    def show_summarize(self, test_period = None, trade_stocks = None):
        s = self.summarize(test_period, trade_stocks)
        print s

    def __str__(self):
        s = 'history:\n'
        for h in self.history:
            s += '    %s\n' % str(h)
        s += '\nprofit:\n'
        for p in self.profit:
            s += '    %s\n' % str(p)
        return s

if __name__ == '__main__':
    account = Account(3000)
    account.buy_stock('000001', 2, 200, 20121008)
    account.buy_stock('000002', 3, 400, 20121009)
    account.buy_stock('000001', 2.5, 300, 20121010)
    print account
    account.sell_stock('000001', 1.8, 300, 20121011)
    print account


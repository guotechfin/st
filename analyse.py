#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import random
import copy

from stocks import Util, Stocks, Stock
from stra import *
from account import VirtualAccount, Account


class Analyse(object):
    def __init__(self):
        self.in_market_analyse_days = 60   # 大约3个月
        self.stocks = Stocks()
        self.stocks.load_data(100)   # 100 stocks
        self.trade_stock_num = len(self.stocks.stock_list) - len(Stock.SPECIAL_LIST)

    def analyse_in_market(self, in_market_stra, selected_stock_id = None):
        result_time = []
        result_time_stock = {}
        result_price_change = []
        for stock_id, stock in self.stocks.stock_list.items():
            #print stock_id
            if selected_stock_id == stock_id or not selected_stock_id:
                in_market_stra.reset()
                # 选定满足策略的入市时间
                for time_, price in stock.iter_tick():
                    if in_market_stra.update(price):
                        result_time.append(time_)
                        if stock_id not in result_time_stock: result_time_stock[stock_id] = []
                        result_time_stock[stock_id].append(time_)
                        # 根据每个入市时间，统计入市后的每日涨幅(相比入市点)
                        timeslice_price = stock.get_timeslice_close_price(time_, self.in_market_analyse_days)
                        start_price = timeslice_price[0]
                        result_price_change.append([100*(price/float(start_price)-1) if price else None for price in timeslice_price])
        price_len = len(result_price_change)
        result = []
        for price in zip(*result_price_change):
            assert len(price) == price_len, 'price error'
            price_set = set(price)
            if None in price_set: price_set.remove(None)
            price_array = np.array(tuple(price_set))
            # 求平均值和方差
            result.append((round(np.mean(price_array), 2), round(np.std(price_array), 2)))
        for stock_id, time_list in result_time_stock.items():
            print stock_id
            print time_list
        return result, result_time

    def analyse_strategy(self):
        in_stra_list = [ ATRTunnelStra(20, 20, 3, False),
                         #MacdDeviationStra(),
                         #BreakOutStra(20),
                         #AvgLineCrossStra(20),
                         #TwoAvgLineCrossStra(10, 60),
                         #RandomStra(0.3),
                        ]

        out_stra_list = [ ATRTunnelStra(20, 20, 3),
                          #MacdDeviationStra(gold_cross_report = False),
                          #BreakOutStra(10, False),
                          #AvgLineCrossStra(20, False),
                          #TwoAvgLineCrossStra(5, 20, False),
                          ATRStopLossStra(20, 2, False),
                          ConstPeriodStra(5), ConstPeriodStra(20), ConstPeriodStra(60),
                        ]

        self.market_index = {}
        for stock_id in Stock.SPECIAL_LIST:
            stock = self.stocks.stock_list[stock_id]
            self.market_index[stock_id] = (stock.processed_price[0][1], stock.processed_price[-1][1])  # close

        stra_index = 1
        for in_stra in in_stra_list:
            for out_stra in out_stra_list:
                print 'Stra %d' % stra_index, '#' * 20, '\n'
                stra_index += 1
                analyse.analyse_trade(in_stra, out_stra)

    def analyse_real_strategy(self, start_time = None, end_time = None):
        in_stra_list = [ #(ATRTunnelStra, (20, 20, 3, False)),
                         #(MacdDeviationStra, ()),
                         #(BreakOutStra, (20,)),
                         (BreakOutBackOffStra, (20, 5)),
                         #(AvgLineCrossStra, (20,)),
                         #(TwoAvgLineCrossStra, (10, 60)),
                         #(RandomStra, (0.3,), (100,)),
                         #(RandomStra, (0.3,)),
                        ]

        out_stra_list = [ #(ATRTunnelStra, (20, 20, 3)),
                          #(MacdDeviationStra, (False,)),
                          #(BreakOutStra, (10, False)),
                          #(AvgLineCrossStra, (20, False)),
                          #(TwoAvgLineCrossStra, (5, 20, False)),
                          (ATRStopLossStra, (20, 2, False)),
                          #(ConstPeriodStra, (1,)),
                          #(ConstPeriodStra, (5,), (20,), (60,)),
                          #(ConstPeriodStra, (30,), (60,), (90,)),
                          #(MultiStra, ([(MacdDeviationStra, (False,)), (ATRStopLossStra, (20, 2, False))],)),
                          #(MultiStra, ([(ATRStopLossStra, (20, 2, False))],)),
                        ]

        buy_stra_list = [ (BuyMultiStra, (3, 'random')),
                        ]

        start_index, end_index = self.stocks.set_test_period(start_time, end_time)
        self.market_index = {}
        for stock_id in Stock.SPECIAL_LIST:
            stock = self.stocks.stock_list[stock_id]
            self.market_index[stock_id] = (stock.processed_price[start_index][1], stock.processed_price[end_index][1])  # close

        result = []
        stra_index = 1
        for in_stra_class in in_stra_list:
            in_stra = [(in_stra_class[0], param) for param in in_stra_class[1:]]

            for in_market_stra in in_stra:
                for out_stra_class in out_stra_list:
                    out_stra = [(out_stra_class[0], param) for param in out_stra_class[1:]]

                    for out_market_stra in out_stra:
                        for buy_stra_class in buy_stra_list:
                            buy_stra = [(buy_stra_class[0], param) for param in buy_stra_class[1:]]

                            for buy_stock_stra in buy_stra:
                                print 'Stra %d' % stra_index, '#' * 20, '\n'
                                self._show_stra_info(in_market_stra, out_market_stra, buy_stock_stra)
                                p = analyse.analyse_real_trade(in_market_stra, out_market_stra, buy_stock_stra)
                                result.append((stra_index, in_market_stra, out_market_stra, buy_stock_stra, p))
                                stra_index += 1
        # print result
        for r in result:
            s = 'Stra %d, In(%s) Out(%s) Buy(%s): ' % (r[0], self._class_abbreviation(r[1]), self._class_abbreviation(r[2]), self._class_abbreviation(r[3]))
            s += '(total_profit: %.1f%%, no_fee_profit: %.1f%%, max_backoff: %.1f%%' % r[4]
            print s
        print ''

    def _class_instance(self, class_param_tuple):
        class_, param = class_param_tuple
        return class_(*param)

    def _class_name(self, class_param_tuple):
        return self._class_instance(class_param_tuple).name

    def _class_abbreviation(self, class_param_tuple):
        return self._class_instance(class_param_tuple).abbreviation

    def analyse_real_trade(self, in_market_stra_class, out_market_stra_class, buy_stock_stra_class):
        market_trigger = {}
        market_status_in_market = {}
        hold_stock_days = {}

        buy_stra = self._class_instance(buy_stock_stra_class)
        account = Account(50000)  # initial money
        for stock_id in self.stocks.stock_list:
            if stock_id not in Stock.SPECIAL_LIST:
                market_trigger[stock_id] = StraTrigger(self._class_instance(in_market_stra_class), self._class_instance(out_market_stra_class))
                market_status_in_market[stock_id] = False
                hold_stock_days[stock_id] = 0

        # tick: (time, [(stock_id, (open, close, high, low, volume)), (stock_id, ()), ...])
        for tick in self.stocks.iter_ticks():
            time_, stocks_price = tick
            in_trigger_stocks = []
            for stock_id, price in stocks_price:
                if stock_id not in Stock.SPECIAL_LIST:
                    in_market_trigger, out_market_trigger = market_trigger[stock_id].update(price)
                    if in_market_trigger:
                        in_trigger_stocks.append(stock_id)
                    # deal with sell first
                    if market_status_in_market[stock_id]:   # have the stock
                        if price: hold_stock_days[stock_id] += 1
                        if out_market_trigger:
                            account.sell_stock(stock_id, price[1], today = time_, hold_stock_days = hold_stock_days[stock_id])
                            market_status_in_market[stock_id] = False
            # deal with buy
            buy_stocks = buy_stra.buy_stock(in_trigger_stocks, tick, account)
            for stock_id in buy_stocks:
                market_status_in_market[stock_id] = True
                hold_stock_days[stock_id] = 0
                market_trigger[stock_id].enter_market()
            account.update(tick)
        account.summarize()
        total_profit = account.report['account_total_profit']
        no_fee_profit = account.report['no_fee_total_profit']
        max_backoff = account.report['max_backoff']
        self._show_account_info(account)
        self._show_stock_trade(account)
        return (total_profit, no_fee_profit, max_backoff)

    def _show_stra_info(self, in_market_stra_class = None, out_market_stra_class = None, buy_stock_stra_class = None):
        if in_market_stra_class: print 'In Market: ', self._class_name(in_market_stra_class)
        if out_market_stra_class: print 'Out Market: ', self._class_name(out_market_stra_class)
        if buy_stock_stra_class: print 'Select Stock: ', self._class_name(buy_stock_stra_class)
        print ''

    def analyse_trade(self, in_market_stra, out_market_stra, selected_stock_id = None):
        account = VirtualAccount()
        self.trade_stocks = 0
        for stock_id, stock in self.stocks.stock_list.items():
            #print stock_id
            if (selected_stock_id == stock_id or not selected_stock_id) and stock_id not in Stock.SPECIAL_LIST:
                in_market_stra.reset()
                out_market_stra.reset()
                market_status_in_market = False
                hold_stock_days = 0
                self.trade_stocks += 1
                # 选定满足策略的入市时间
                for time_, price in stock.iter_tick():
                    in_market_trigger = in_market_stra.update(price)
                    out_market_trigger = out_market_stra.update(price)
                    if not market_status_in_market:  # 不在市场内, 寻找入市机会
                        if in_market_trigger:
                            account.buy_stock(stock_id, price[1], today = time_)  # close价格作为买入, 卖出价
                            market_status_in_market = True
                            if 'start_monitor' in dir(out_market_stra):
                                out_market_stra.start_monitor()
                            hold_stock_days = 0
                    else:
                        if price: hold_stock_days += 1
                        if out_market_trigger:
                            account.sell_stock(stock_id, price[1], today = time_, hold_stock_days = hold_stock_days)
                            market_status_in_market = False
                            if 'start_monitor' in dir(in_market_stra):
                                in_market_stra.start_monitor()
        self._show_stra_info(in_market_stra, out_market_stra)
        self._show_account_info(account)

    def _show_account_info(self, account):
        account.show_trade_history()
        print account
        account.show_report(self.stocks.get_test_period(), self.trade_stock_num)
        s = 'MarketIndex:'
        for stock_id, (start_index, end_index) in self.market_index.items():
            s += ' %s: %.1f%%(%.1f~%.1f),' % (stock_id, (float(end_index) / start_index - 1)*100, start_index, end_index)
        print s + '\n'
        #account.show_profit_pdf()
        #account.show_market_value()

    def _show_stock_trade(self, account, stock_id = None):
        days, day_start, day_stop = self.stocks.get_test_period()
        stocks_trade_history = account.get_stocks_trade_history()
        print stocks_trade_history
        stock_id = stock_id or list(stocks_trade_history.keys())[0]
        print stock_id
        stock = self.stocks.stock_list[stock_id]
        stock.plot(day_start, day_stop, trade_history = stocks_trade_history[stock_id])


if __name__ == '__main__':
    test = 4
    if test == 1:
        analyse = Analyse()
        #stra = RaiseBigStra(9)  # 8% raise
        #stra = RaiseBigStra(-8, False)  # 8% drop
        #stra = AvgLineCrossStra(120)
        stra = MacdDeviationStra()
        #stra = AvgLineCrossStra(120, False)
        #result,result_time = analyse.analyse_in_market(stra, selected_stock_id = '999999')
        result,result_time = analyse.analyse_in_market(stra)
        result_time_1 = list(set(result_time))
        result_time_1.sort()
        result = zip(*result)
        print result
        print len(result_time), len(result_time_1)
        print result_time_1
        if False:
            from matplotlib import pyplot
            pyplot.figure()
            pyplot.plot(result[0], '*-')
            pyplot.plot(result[1], 'r*-')
            pyplot.grid(True)
            pyplot.show()
    elif test == 2:
        analyse = Analyse()
        #in_stra = ATRTunnelStra(20, 20, 3)
        in_stra = MacdDeviationStra()
        #in_stra = ATRStopLossStra(20, 3)
        #in_stra = BreakOutStra(20)
        #in_stra = AvgLineCrossStra(20, up_cross_report = True)
        #in_stra = TwoAvgLineCrossStra(10, 60)
        #out_stra = TwoAvgLineCrossStra(5, 20, up_cross_report = False)
        #out_stra = AvgLineCrossStra(20, up_cross_report = False)
        #out_stra = BreakOutStra(10, break_up = False)
        #out_stra = ATRTunnelStra(20, 20, 3, tunnel_up = False)
        out_stra = ATRStopLossStra(20, 2, direction_up = False)
        analyse.analyse_trade(in_stra, out_stra)
    elif test == 3:
        analyse = Analyse()
        analyse.analyse_strategy()
    elif test == 4:
        analyse = Analyse()
        #analyse.analyse_real_strategy(end_time = 20100710)
        #analyse.analyse_real_strategy(20120101, 20121231)
        #analyse.analyse_real_strategy(20130101)
        analyse.analyse_real_strategy()






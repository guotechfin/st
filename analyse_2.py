#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import random
import copy

from stocks import Util, Stocks, Stock
from stra import *
from index import AMI
from account import VirtualAccount, Account


class Analyse(object):
    def __init__(self):
        self.in_market_analyse_days = 60   # 大约3个月
        self.stocks = Stocks()
        self.stocks.load_data(100)   # 100 stocks
        self.trade_stock_num = len(self.stocks.stock_list) - len(Stock.SPECIAL_LIST)
        self.ami = AMI()

    def analyse_trade_time_strategy(self, start_time = None, end_time = None):
        in_stra_list = [ #(ATRTunnelStra, (20, 20, 3, False)),
                         #(MacdDeviationStra, ()),
                         #(BreakOutStra, (20,)),
                         #(BreakOutBackOffStra, (20, 3)),
                         #(AvgLineCrossStra, (20,)),
                         (TwoAvgLineCrossStra, (10, 60)),
                         #(RandomStra, (0.3,), (100,)),
                         #(RandomStra, (0.3,)),
                        ]

        out_stra_list = [ #(ATRTunnelStra, (20, 20, 3)),
                          #(MacdDeviationStra, (False,)),
                          #(BreakOutStra, (10, False)),
                          #(AvgLineCrossStra, (20, False)),
                          #(TwoAvgLineCrossStra, (12, 26, False)),
                          (ATRStopLossStra, (20, 2, False)),
                          #(ConstPeriodStra, (10,)),
                          #(ConstPeriodStra, (5,), (20,), (60,)),
                          #(ConstPeriodStra, (30,), (60,), (90,)),
                          #(MultiStra, ([(MacdDeviationStra, (False,)), (ATRStopLossStra, (20, 2, False))],)),
                          #(MultiStra, ([(TwoAvgLineCrossStra, (10, 60, False)), (ATRStopLossStra, (20, 2, False))],)),
                        ]

        buy_stra_list = [ #(BuyMultiStra, (1, 'first')),
                          (BuyMultiStra, (1, 'random')),
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
                                p = analyse.analyse_real_trade(in_market_stra, out_market_stra, buy_stock_stra, selected_stock_id)
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

    def trade_strategy(self, in_market_stra_class, out_market_stra_class, buy_stock_stra_class):
        # tick: (time, [(stock_id, (open, close, high, low, volume)), (stock_id, ()), ...])
        for tick in self.stocks.iter_ticks():
            ami = self.ami.update(tick)
            time_, stocks_price = tick
            # here???

    def analyse_trade(self, in_market_stra_class, out_market_stra_class, buy_stock_stra_class):
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
                if stock_id not in Stock.SPECIAL_LIST and (not selected_stock_id or stock_id in selected_stock_id):
                    in_market_trigger, out_market_trigger = market_trigger[stock_id].update(price)
                    if in_market_trigger:
                        in_trigger_stocks.append(stock_id)
                    # deal with sell first
                    if market_status_in_market[stock_id]:   # have the stock
                        if price: hold_stock_days[stock_id] += 1
                        if out_market_trigger:
                            account.sell_stock(stock_id, price[1], today = time_, hold_stock_days = hold_stock_days[stock_id])
                            market_status_in_market[stock_id] = False
                            market_trigger[stock_id].quit_market()
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
        #self._show_stock_trade(account)
        return (total_profit, no_fee_profit, max_backoff)

    def _show_stra_info(self, in_market_stra_class = None, out_market_stra_class = None, buy_stock_stra_class = None):
        if in_market_stra_class: print 'In Market: ', self._class_name(in_market_stra_class)
        if out_market_stra_class: print 'Out Market: ', self._class_name(out_market_stra_class)
        if buy_stock_stra_class: print 'Select Stock: ', self._class_name(buy_stock_stra_class)
        print ''

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
        #print stocks_trade_history
        #stock_id = account.history[0][2]
        stock_id = stock_id or list(stocks_trade_history.keys())[0]
        #print stock_id
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
        #analyse.analyse_real_strategy(20140101, selected_stock_id = None)
        analyse.analyse_real_strategy(20130101)






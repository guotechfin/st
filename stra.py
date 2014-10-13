#!/usr/bin/python
# -*- coding: utf-8 -*-

import random
from index import MACD, EMA, EMA2, Cross, LastMaxMin, ATR


class BuyOneStra(object):
    def __init__(self, select = 'random', max_hold_stocks = 0):
        self.name = 'Buy One At a Time, %s' % select
        if max_hold_stocks: self.name += ', Max Hold %d Stocks in Account' % max_hold_stocks
        self.select = select  # 'random', 'min', 'max', 'first', 'last'
        self.max_hold_stocks = max_hold_stocks   # 0: unlimited

    def buy_stock(self, in_trigger_stocks, tick, account):
        # tick: (time, [(stock_id, (open, close, high, low, volume)), (stock_id, ()), ...])
        time_, stocks_price = tick
        buy_stocks = []
        in_trigger_num = len(in_trigger_stocks)
        hold_stock_num = account.hold_stock_num()
        if in_trigger_num and (not self.max_hold_stocks or hold_stock_num < self.max_hold_stocks):
            if self.select == 'random':
                index = random.randint(0, in_trigger_num - 1)
            elif self.select == 'first':
                index = 0
            elif self.select == 'last':
                index = -1
            else:
                index = None

            if index is None:
                stock_id = in_trigger_stocks[0]
                # for 
            else:
                stock_id = in_trigger_stocks[index]

            for sid, price in stocks_price:
                if sid == stock_id:
                    account.buy_stock(stock_id, price[1], today = time_)   # close as buy price
                    break
            buy_stocks.append(stock_id)
        return buy_stocks


class StraTrigger(object):
    def __init__(self, in_stra, out_stra):
        self.in_stra = in_stra
        self.out_stra = out_stra
        self.in_market = False

    def update(self, price):
        in_trigger = out_trigger = False
        if price:
            in_stra_trigger = self.in_stra.update(price)
            out_stra_trigger = self.out_stra.update(price)
            if not self.in_market:
                if in_stra_trigger:
                    in_trigger = True
                    self.in_market = True
            else:
                if out_stra_trigger:
                    out_trigger = True
                    self.in_market = False
        return (in_trigger, out_trigger)

    def enter_market(self):
       if 'start_monitor' in dir(self.out_stra):
            self.out_stra.start_monitor()


class RandomStra(object):
    def __init__(self, probability, direction_up = True):
        self.name = 'Random %s, probability %.1f%%' % ('Up' if direction_up else 'Down', probability)
        self.probability = probability * 100   # x/10000
        self.direction_up = direction_up
        self.reset()

    def reset(self):
        pass

    def update(self, price):
        in_market_trigger = False
        if price:
            if random.randint(0, 9999) < self.probability:
                in_market_trigger = True
        return in_market_trigger


class ConstPeriodStra(object):
    def __init__(self, period, direction_up = False):
        self.name = 'Const Period %d days, %s' % (period, 'Up' if direction_up else 'Down')
        self.period = period
        self.reset()

    def reset(self):
        self.days = 0

    def start_monitor(self):
        self.days = 0

    def update(self, price):
        in_market_trigger = False
        if price:
            self.days += 1
            if self.days >= self.period:
                in_market_trigger = True
        return in_market_trigger


# 某日单日涨幅 或跌幅
class RaiseBigStra(object):
    def __init__(self, raise_value, raise_report = True):
        self.name = '%s %s : %f%%' % ('Raise' if raise_report else 'Drop', 'In One Day', raise_value)
        self.raise_report = raise_report  # True: 上涨, False: 下跌
        self.raise_value = raise_value  # 幅度百分比
        self.reset()

    def reset(self):
        self.old_price = None

    def update(self, price):  # [open, close, high, low]
        in_market_trigger = False
        if price:
            o, c, h, l = price
            if self.old_price:
                price_raise = 100*(c / float(self.old_price) - 1)
                if (self.raise_report and price_raise > self.raise_value) or (not self.raise_report and price_raise < self.raise_value):
                    in_market_trigger = True
            self.old_price = c
        return in_market_trigger


class ATRTunnelStra(object):
    def __init__(self, ema_avg_days, atr_avg_days, multiple, tunnel_up = True):
        self.name = 'EMA %d days, %s%.1fx ATR %d days Tunnel, %s' % (ema_avg_days, '+' if tunnel_up else '-', multiple, atr_avg_days, 'Up' if tunnel_up else 'Down')
        self.tunnel_up = tunnel_up
        self.ema_avg_days = ema_avg_days
        self.atr_avg_days = atr_avg_days
        self.multiple = float(multiple)
        self.reset()

    def reset(self):
        self.ema = EMA(self.ema_avg_days)
        self.atr = ATR(self.atr_avg_days)

    def update(self, price):  # [open, close, high, low]
        in_market_trigger = False
        if price:
            o, c, h, l = price
            atr = self.atr.update(price)
            ema = self.ema.update(c)
            if atr and ema and ((self.tunnel_up and c > (ema + self.multiple*atr)) or (not self.tunnel_up and c < (ema - self.multiple*atr))):
                in_market_trigger = True
        return in_market_trigger


class ATRStopLossStra(object):
    def __init__(self, atr_avg_days, multiple, direction_up = True):
        self.name = 'Stop Loss %s%.1fx ATR %d days, %s' % ('+' if direction_up else '-', multiple, atr_avg_days, 'Up' if direction_up else 'Down')
        self.direction_up = direction_up
        self.atr_avg_days = atr_avg_days
        self.multiple = float(multiple)
        self.reset()

    def reset(self):
        self.atr = ATR(self.atr_avg_days)
        self.start_monitor()

    def start_monitor(self):
        self.threshold = None

    def update(self, price):  # [open, close, high, low]
        in_market_trigger = False
        if price:
            o, c, h, l = price
            atr = self.atr.update(price)
            if atr:
                if self.direction_up:
                    threshold = c + self.multiple * atr
                    if self.threshold is None: self.threshold = threshold
                    self.threshold = min(self.threshold, threshold)
                else:
                    threshold = c - self.multiple * atr
                    if self.threshold is None: self.threshold = threshold
                    self.threshold = max(self.threshold, threshold)
            if self.threshold and ((self.direction_up and c > self.threshold) or (not self.direction_up and c < self.threshold)):
                in_market_trigger = True
        return in_market_trigger


# 突破
class BreakOutStra(object):
    def __init__(self, break_days, break_up = True):
        self.name = 'BreakOut %d days, %s' % (break_days, 'Up' if break_up else 'Down')
        self.break_days = break_days
        self.break_up = break_up     # True: 向上突破, False: 向下突破
        self.reset()

    def reset(self):
        self.last_max_min = LastMaxMin(self.break_days, self.break_up)

    def update(self, price):  # [open, close, high, low]
        in_market_trigger = False
        if price:
            o, c, h, l = price
            value = self.last_max_min.update(c)
            if value and ((c > value and self.break_up) or (c < value and not self.break_up)):
                in_market_trigger = True
        return in_market_trigger


# 上穿, 下穿某日均线
class AvgLineCrossStra(object):
    def __init__(self, avg_days, up_cross_report = True):
        self.name = 'Average Line %d days, %s Cross' % (avg_days, 'Up' if up_cross_report else 'Down')
        self.avg_days = avg_days
        self.up_cross_report = up_cross_report  # True: 上穿, False: 下穿
        self.reset()

    def reset(self):
        self.ema = EMA(self.avg_days)
        self.cross = Cross()
        self.direction = 0  # 0: invalid, 1: top 2: bottom

    def update(self, price):  # [open, close, high, low]
        in_market_trigger = False
        if price:
            o, c, h, l = price
            avg_value = self.ema.update(c)
            cross = self.cross.update(c, avg_value)
            if (cross == 'gold' and self.up_cross_report) or (cross == 'dead' and not self.up_cross_report):
                in_market_trigger = True
        return in_market_trigger


class TwoAvgLineCrossStra(object):
    def __init__(self, short_days, long_days, up_cross_report = True):
        self.name = 'Average Lines %d days and %d days, %s Cross' % (short_days, long_days, 'Gold' if up_cross_report else 'Dead')
        self.ema2_param = (short_days, long_days)
        self.up_cross_report = up_cross_report
        self.reset()

    def reset(self):
        self.ema2 = EMA2(*self.ema2_param)
        self.direction = 0  # 0: invalid, 1: top 2: bottom

    def update(self, price):  # [open, close, high, low]
        in_market_trigger = False
        if price:
            o, c, h, l = price
            avg_value, cross = self.ema2.update(c)
            if (cross == 'gold' and self.up_cross_report) or (cross == 'dead' and not self.up_cross_report):
                in_market_trigger = True
        return in_market_trigger


# MACD背离
class MacdDeviationStra(object):
    def __init__(self, gold_cross_report = True, short_days = 12, long_days = 26, dif_days = 9, price_dev = (-0.1, 0), dif_dev = 0.5, last_dif = 3):
        self.name = 'MACD (%d, %d, %d) %s Deviation: price range %d%%~%d%%, dif range %d%%, search last %d cross' % (short_days, long_days, dif_days,
                    'Bottom' if gold_cross_report else 'Top', price_dev[0]*100, price_dev[1]*100, dif_dev*100, last_dif)
        self.macd_para = (short_days, long_days, dif_days)
        self.gold_cross_report = gold_cross_report
        self.price_dev = price_dev
        self.dif_dev = dif_dev
        self.last_dif = last_dif
        self.reset()

    def reset(self):
        self.macd = MACD(*self.macd_para)
        self.low_prices = []
        self.high_prices = []
        self.last_gold_cross_dif = []
        self.last_dead_cross_dif = []
        self.last_cross = None

    # price: [open, close, high, low]
    def update(self, price):
        macd_deviation = None
        if price:
            o, c, h, l = price
            macd_price, macd_dif, macd_cross = self.macd.update(c)
            if macd_cross == 'gold':
                if macd_dif < 0 and self.low_prices:
                    lowest_price = min(self.low_prices)
                    min_dif = -1  # maximum value
                    for p, dif in self.last_gold_cross_dif[::-1]:
                        #print float(lowest_price - p)/p, float(macd_dif)
                        if self.price_dev[0] < float(lowest_price - p) / p < self.price_dev[1] and float(macd_dif) / dif < self.dif_dev and dif < min_dif:
                            #print price, self.last_gold_cross_dif, lowest_price, p, dif, macd_dif
                            macd_deviation = 'gold'
                            break
                        min_dif = min(min_dif, dif)
                    self.last_gold_cross_dif.append((lowest_price, macd_dif))
                    if len(self.last_gold_cross_dif) > self.last_dif:
                        self.last_gold_cross_dif.pop(0)
                self.last_cross = macd_cross
                self.high_prices = []
            elif macd_cross == 'dead':
                if macd_dif > 0 and self.high_prices:
                    highest_price = max(self.high_prices)
                    max_dif = 1   # minimum value
                    for p, dif in self.last_dead_cross_dif[::-1]:
                        if self.price_dev[0] < float(highest_price - p) / p < self.price_dev[1] and float(macd_dif) / dif < self.dif_dev and dif > max_dif:
                            macd_deviation = 'dead'
                            break
                        max_dif = max(max_dif, dif)
                    self.last_dead_cross_dif.append((highest_price, macd_dif))
                    if len(self.last_dead_cross_dif) > self.last_dif:
                        self.last_dead_cross_dif.pop(0)
                self.last_cross = macd_cross
                self.low_prices = []

            if self.last_cross == 'gold':
                self.high_prices.append(h)
            elif self.last_cross == 'dead':
                self.low_prices.append(l)
        return macd_deviation == 'gold' if self.gold_cross_report else macd_deviation == 'dead'


if __name__ == '__main__':
    test = 3
    if test == 1:
        pass


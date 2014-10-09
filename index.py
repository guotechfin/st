#!/usr/bin/python
# -*- coding: utf-8 -*-


class TR(object):
    def __init__(self):
        self.close = None

    # price: [open, close, high, low]
    def update(self, price):
        tr_price = None
        if not price is None:
            o, c, h, l = price
            if not self.close is None:
                tr_price = max(abs(h - l), abs(h - self.close), abs(self.close - l))
            self.close = c
        return tr_price


class ATR(object):
    def __init__(self, avg_days):
        self.avg_days = avg_days
        self.tr = TR()
        self.ema = EMA(avg_days)

    # price: [open, close, high, low]
    def update(self, price):
        tr_price = self.tr.update(price)
        atr_price = self.ema.update(tr_price)
        return atr_price


class EMA(object):
    def __init__(self, avg_days):
        self.avg_days = avg_days
        self.days = self.ema_price = 0

    def update(self, price):
        ema_price = None
        if not price is None:
            self.days += 1
            if self.days > self.avg_days:
                self.ema_price = float(2 * price + (self.avg_days - 1) * self.ema_price) / (self.avg_days + 1)
                ema_price = self.ema_price
            else:
                self.ema_price = float(price + (self.days - 1) * self.ema_price) / self.days
        return ema_price


class EMA2(object):
    def __init__(self, short_days, long_days):
        self.ema1 = EMA(short_days)
        self.ema2 = EMA(long_days)
        self.cross = Cross()

    def update(self, price):
        ema2_price = cross = None
        ema1 = self.ema1.update(price)
        ema2 = self.ema2.update(price)
        if ema1 and ema2:
            ema2_price = ema1 - ema2
            cross = self.cross.update(ema1, ema2)
        return ema2_price, cross

class Cross(object):
    def __init__(self):
        self.cross = None  # 'gold', 'dead'

    def update(self, short_price, long_price):
        cross = None
        if None not in [short_price, long_price]:
            if self.cross == 'good':
                if short_price < long_price:
                    cross = self.cross = 'dead'
            elif self.cross == 'dead':
                if short_price > long_price:
                    cross = self.cross = 'gold'
            else:
                if short_price < long_price:
                    self.cross = 'dead'
                elif short_price > long_price:
                    self.cross = 'good'
        return cross


class MACD(object):
    def __init__(self, short_days = 12, long_days = 26, dif_days = 9):
        self.ema1 = EMA(short_days)
        self.ema2 = EMA(long_days)
        self.ema_dif = EMA(dif_days)
        self.cross = Cross()

    def update(self, price):
        macd_price = cross = dif = None
        #dif = None
        ema1 = self.ema1.update(price)
        ema2 = self.ema2.update(price)
        if ema1 and ema2:
            #dif = ema1 - ema2
            dif = (ema1 - ema2) / float(ema2) * 100
            dea = self.ema_dif.update(dif)
            cross = self.cross.update(dif, dea)
            if dea:
                macd_price = dif - dea
        #print (ema1, ema2, dif, dea, macd_price)
        return macd_price, dif, cross


class ADX(object):
    def __init__(self, dmi_avg_days = 14, adx_avg_days = 6):
        self.dmi_avg_days = dmi_avg_days
        self.adx_avg_days = adx_avg_days
        self.atr = ATR(dmi_avg_days)
        self.dm_plus = EMA(dmi_avg_days)
        self.dm_minus = EMA(dmi_avg_days)
        self.adx = EMA(adx_avg_days)
        self.adxr = EMA(adx_avg_days)
        self.high = self.low = None

    # price: [open, close, high, low]
    def update(self, price):
        adx_price = None
        if not price is None:
            atr_price = self.atr.update(price)
            o, c, h, l = price
            if not None in [self.high, self.low]:
                hd = h - self.high
                ld = self.low - l
                dm_plus_price = self.dm_plus.update(hd if hd > max(ld, 0) else 0)
                dm_minus_price = self.dm_minus.update(ld if ld > max(hd, 0) else 0)
                if not None in [dm_plus_price, dm_minus_price, atr_price]:
                    plus_di = dm_plus_price * 100 / float(atr_price)
                    minus_di = dm_minus_price * 100 / float(atr_price)
                    denominator = plus_di + minus_di
                    adx_price = self.adx.update(abs(plus_di - minus_di) * 100 / float(denominator) if denominator else 0)
                    adxr_price = self.adxr.update(adx_price)
            self.high = h
            self.low = l
        return adx_price


class HighLowPoint(object):
    def __init__(self, interval_days):
        self.interval_days = interval_days
        self.low_points = []
        self.high_points = []
        self.search = None   # 'low', 'high'
        self.days = 0

    def update(self, price, time_):
        if not price is None:
            self.days += 1
            if self.search == 'high':
                if price > self.candidate[0]:
                    self.candidate = (price, self.days)
                elif (self.days - self.candidate[1]) >= self.interval_days:
                    self.high_points.append(self.candidate)
                    pass
            elif self.days > 1:
                if price > self.close:
                    self.search = 'high'
                elif price < self.close:
                    self.search = 'low'
                self.candidate = (price, self.days)
            self.close = price


if __name__ == '__main__':
    test = 5
    #stocks = Stocks()
    #stocks.load_from_file('stock_data.dat')
    #s = stocks.stock_list['000006']
    if test == 1:
        macd_prices = []
        macd = MACD(3, 5, 5)
        for p in range(50):
            price = macd.update(p)
            macd_prices.append(price)
        print macd_prices
    elif test == 2:
        prices = zip(range(10), range(2, 12), range(3, 13), range(10))
        atr_prices = []
        atr = ATR(5)
        for p in prices:
            atr_prices.append(atr.update(p))
        print prices
        print atr_prices
    elif test == 3:
        ema2 = EMA2(5, 10)
        ema_2_prices = []
        for p in range(1,20):
            price = ema2.update(p)
            #print p, price, stat
            ema_2_prices.append(price)
        print ema_2_prices
    elif test == 4:
        prices = zip(range(40), range(2, 42), range(3, 43), range(40))
        adx = ADX(2, 2)
        adx_prices = []
        for p in prices:
            adx_prices.append(adx.update(p))
        print adx_prices
    elif test == 5:
        prices = zip(range(40), range(2, 42), range(3, 43), range(40))
        macd_dev = MACDDev()
        macd_dev_prices = []
        for p in prices:
            macd_dev_prices.append(macd_dev.update(p))
        print macd_dev_prices




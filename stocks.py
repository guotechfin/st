#!/usr/bin/python
# -*- coding: utf-8 -*-

import gevent, gevent.monkey; gevent.monkey.patch_all()
import re, struct, urllib2, os, copy, time
import cPickle as pickle
import matplotlib.pyplot as plt


class Util(object):
    @staticmethod
    def time_to_digit(time_):
        # time_: 20140628
        year, month, day = time_/10000, (time_ % 10000) / 100, time_ % 100
        return year * 12*31 + (month-1) * 31 + (day-1)

    @staticmethod
    def digit_to_time(digit):
        year, month, day = digit / (12*31), (digit % (12*31)) / 31 + 1, (digit % 31) + 1
        return year * 10000 + month * 100 + day

class Stock(object):
    NAME_URL = r'http://quote.eastmoney.com/stocklist.html'
    SHAREBONUS_URL = r'http://vip.stock.finance.sina.com.cn/corp/go.php/vISSUE_ShareBonus/stockid/%s.phtml'
    PATH_DATA = r'vipdoc'
    PATH_SZ = os.path.join(PATH_DATA, 'sz', 'lday')
    PATH_SH = os.path.join(PATH_DATA, 'sh', 'lday')
    SPECIAL_LIST = {'999999': ('上证综指', 'sh'), '399001': ('深证成指', 'sz')}
    stock_name_page = None
    price_time_index = {}  # 'time1': index1 in list
    price_time_list = []

    def __init__(self, stock_id):
        self.id = stock_id
        self.name, self.pos_attr = self.get_stock_name(stock_id)
        self.in_collection = []
        if not Stock.price_time_list:
            Stock.price_time_list, Stock.price_time_index = self.load_history_time()
        self.history_price, self.history_volume = self.load_history_price()  # price : 单位 分
        try:
            self.processed_price = self.ex_bonus(self.history_price)   # [open, close, high, low]
            #self.processed_price = self.history_price
            self.init_success = True
        except:
            self.init_success = False

    def __str__(self):
        latest_price = self.history_price
        string = 'stock: %s (%s) - %s\n  belongs to: %s\n  time: %s\n  history price: %s\n  processed price: %s\n' % (
            self.id, self.name, self.pos_attr, self.in_collection, self.price_time_list, self.history_price, self.processed_price)
        return string

    def print_(self, msg):
        print msg

    def _get_file_path(self, stock_id = '', pos_attr = ''):
        if not stock_id: stock_id = self.id
        if not pos_attr: pos_attr = self.pos_attr
        return os.path.join(Stock.PATH_SH if pos_attr == 'sh' else Stock.PATH_SZ, '%s%s.day' % (pos_attr, stock_id))

    def get_tick(self, time_):
        # tick: (stock_id, (open, close, high, low, volume))
        if time_ not in Stock.price_time_index: return (self.id, ())
        index = Stock.price_time_index[time_]
        # return (self.id, tuple(self.processed_price[index]) + tuple(self.history_volume[index]))
        return (self.id, tuple(self.processed_price[index]))

    def iter_tick(self):
        for time_, processed_price in zip(Stock.price_time_list, self.processed_price):
            yield (time_, processed_price)

    def get_timeslice_close_price(self, time_start, time_points):
        index = Stock.price_time_index[time_start]
        total_len = len(Stock.price_time_list)
        remain_len = total_len - index
        if remain_len >= time_points:
            price_slice = self.processed_price[index:index+time_points]
        else:
            price_slice = self.processed_price[index:] + [None] * (time_points - remain_len)
        return [price[1] if price else None for price in price_slice]

    def get_interval_price(self, time_start = None, time_stop = None):
        start_index = Stock.price_time_index[Stock.get_exact_time(time_start, 1)]
        stop_index = Stock.price_time_index[Stock.get_exact_time(time_stop, -1)]

        interval_time, interval_history_price, interval_processed_price = [], [], []
        for index in range(start_index, stop_index+1):
            if self.processed_price[index]:
                interval_time.append(Stock.price_time_list[index])
                interval_history_price.append(self.history_price[index])
                interval_processed_price.append(self.processed_price[index])
        return (interval_time, interval_history_price, interval_processed_price)

    @staticmethod
    def _get_html_page(url, timeout = 3, try_times = 5):
        page = None
        for times in range(try_times):
            try:
                response = urllib2.urlopen(url, timeout = timeout)
                page = response.read()
                break
            except Exception as e:
                print '   [temp %d]: %s, url: %s' % (times, str(e), url)
                continue
        if times == try_times: raise Exception('cannot get page: %s' % url)
        return page

    @staticmethod
    def get_stock_name_page():
        page = Stock._get_html_page(Stock.NAME_URL)
        pos = page.find(r'<a name="sz"/>')
        if pos < 0: raise Exception('stock name page fail, cannot find "sz"')
        Stock.stock_name_page = (page[:pos], page[pos:])

    @staticmethod
    def get_exact_time(time_ = None, add_next = 1):
        if time_ is None:
            t = Stock.price_time_list[0] if add_next == 1 else Stock.price_time_list[-1]
        else:
            digit = Util.time_to_digit(time_)
            min_d, max_d = [Util.time_to_digit(Stock.price_time_list[i]) for i in [0, -1]]
            while True:
                if not min_d <= digit <= max_d: raise Exception('can not find exact time %s, min %s, max %s' % (time_, Stock.price_time_list[0], Stock.price_time_list[-1]))
                t = Util.digit_to_time(digit)
                if t in Stock.price_time_index: break
                digit += add_next
        return t

    def get_stock_name(self, stock_id):
        ''' return (stock_name, stock_pos_attr) '''
        if stock_id in Stock.SPECIAL_LIST:
            return Stock.SPECIAL_LIST[stock_id]
        if not Stock.stock_name_page:
            Stock.get_stock_name_page()
        stock_name_pattern = r'(?<=">)(.*)(?=\(%s\))' % stock_id
        r = re.search(stock_name_pattern, Stock.stock_name_page[0])
        if r:
            stock_name, stock_pos_attr = r.group(1), 'sh'
        else:
            r = re.search(stock_name_pattern, Stock.stock_name_page[1])
            if r:
                stock_name, stock_pos_attr = r.group(1), 'sz'
            else:
                raise Exception('cannot find stock %s' % stock_id)
        return (stock_name, stock_pos_attr)

    def _load_history_price_file(self, stock_file = ''):
        if not stock_file: stock_file = self._get_file_path()
        raw_data = open(stock_file, 'rb').read()
        # 通达信格式, 日期，开盘， 最高， 最低， 收盘， xx， 成交量， xx， 各32bit
        data = struct.unpack('i'*(len(raw_data)/4), raw_data)
        time_data = []
        price_dict = {}
        for i in xrange(len(data)/8):
            time_, open_, high_, low_, close_, not_use, volume_, not_use2 = data[i*8:i*8+8]
            price = [open_, close_, high_, low_, volume_]  # price: 单位 分
            time_data.append(time_)
            price_dict[time_] = price
        return (time_data, price_dict)

    def load_history_price(self):
        not_use, price_dict = self._load_history_price_file()
        history_price, history_volume = [], []
        for time_ in Stock.price_time_list:
            if time_ in price_dict:
                history_price.append(price_dict[time_][:4])
                history_volume.append(price_dict[time_][4])
            else:
                history_price.append(())
                history_volume.append(())
        return (history_price, history_volume)

    def load_history_time(self):
        time_data, not_use = self._load_history_price_file(self._get_file_path('999999', 'sh'))
        time_index = {}
        for index, time_ in enumerate(time_data):
            time_index[time_] = index
        return (time_data, time_index)

    def get_bonus_history(self):
        page = Stock._get_html_page(Stock.SHAREBONUS_URL % self.id, timeout = 3, try_times = 1)
        pos = page.find('sharebonus_2')
        if pos < 0: raise Exception('stock %s page error, cannot find sharebonus_2' % self.id)
        # 分红
        raw_bonus = re.findall(r'(?<=<td>)[\d\.-]+(?=</td>)', page[:pos])
        bonus_history = []
        for i in xrange(len(raw_bonus)/7):
            # 公告日期  送股(股)(每10股)	转增(股)	派息(税前)(元)  除权除息日	股权登记日	红股上市日
            bonus = raw_bonus[i*7:i*7+7]
            if bonus[4] != '--':
                # 除权除息日  送股+转增(股)(每10股)  派息(税前)(元)(每10股)
                bonus_history.append((int(bonus[4].replace('-', '')), float(bonus[1])+float(bonus[2]), float(bonus[3])))
        bonus_history = bonus_history[::-1]
        # 配股
        raw_share_placement = re.findall(r'(?<=<td>)[\d\.-]+(?=</td>)', page[pos:])
        share_placement_history = []
        for i in xrange(len(raw_share_placement)/8):
            # 公告日期	配股方案(每10股配股股数)	配股价格(元)	基准股本(万股)	除权日	股权登记日	缴款起始日	缴款终止日	配股上市日
            placement = raw_share_placement[i*8:i*8+8]
            if placement[4] != '--':
                # 除权日  配股方案(每10股配股股数)  配股价格(元)
                share_placement_history.append((int(placement[4].replace('-', '')), float(placement[1]), float(placement[2])))
        share_placement_history = share_placement_history[::-1]
        # 分红, 配股
        return (bonus_history, share_placement_history)

    def ex_bonus(self, history_price):
        processed_price = copy.deepcopy(history_price)
        bonus_history, share_placement_history = self.get_bonus_history()
        #除权(息)报价＝[(前收盘价-现金红利)＋配(新)股价格×流通股份变动比例]÷(1＋流通股份变动比例)
        for time_, share, bonus in bonus_history:
            if not time_ in Stock.price_time_index:
                #print time_
                continue
            index = Stock.price_time_index[time_]
            for i in xrange(index):
                for p, price in enumerate(processed_price[i]):
                    processed_price[i][p] = round(float(10 * price - bonus*100) / ( 10 + share), 2)
        for time_, share, place_price in share_placement_history:
            if not time_ in Stock.price_time_index:
                #print time_
                continue
            index = Stock.price_time_index[time_]
            for i in xrange(index):
                for p, price in enumerate(processed_price[i]):
                    processed_price[i][p] = round(float(10* price + place_price * share) / ( 10 + share), 2)
        return processed_price

    def plot(self, time_start = None, time_stop = None, trade_history = None):
        interval_time, interval_history_price, interval_processed_price = self.get_interval_price(time_start, time_stop)
        #print interval_processed_price
        close_ = [price[1] for price in interval_processed_price]
        plt.figure()
        if trade_history:
            # trade_history: [(time_buy, time_sell), (time_buy, time_sell), ...]
            trade_time = reduce(lambda x,y:x+list(y), trade_history, [])
            trade_index = [i for i, time_ in enumerate(interval_time) if time_ in trade_time]
            # trade_index: [(index_buy, index_sell), (index_buy, index_sell), ...]
            even_trade_index = [index for i, index in enumerate(trade_index) if i % 2 == 0]
            odd_trade_index = [index for i, index in enumerate(trade_index) if i % 2 == 1]
            trade_index = zip(even_trade_index, odd_trade_index)
            assert len(trade_history) == len(trade_index), 'trade_history: %d, trade_index: %d' % (len(trade_history), len(trade_index))
            # non_trade_index: [(0, index_buy), (index_sell, index_buy), ..., (index_sell, end)]
            non_trade_index = zip([0] + odd_trade_index, even_trade_index + [len(interval_time)-1])
            for start, stop in non_trade_index:
                if stop > start:
                    plt.plot(range(start, stop+1), [close_[i] for i in range(start, stop+1)], 'b*-')
            for start, stop in trade_index:
                if stop > start:
                    plt.plot(range(start, stop+1), [close_[i] for i in range(start, stop+1)], 'r*-')
        else:
            plt.plot(close_, '*-')
        plt.grid(True)
        plt.show()


class Stocks(object):
    def __init__(self):
        self.start_time = time.time()
        self.stock_list = {}  # stock_id: Stock()
        self.price_time_index = {}  # 'time1': index1 in list
        self.price_time_list = []

    def __str__(self):
        string = ''
        for stock_id, stock in self.stock_list.items():
            string += stock.__str__() + '\n'
        return string

    def set_test_period(self, time_start = None, time_stop = None):
        self.test_index_start = Stock.price_time_index[Stock.get_exact_time(time_start, 1)]
        self.test_index_stop = Stock.price_time_index[Stock.get_exact_time(time_stop, -1)]
        return (self.test_index_start, self.test_index_stop)

    def get_test_period(self):
        start, stop = self.test_index_start, self.test_index_stop
        return (len(Stock.price_time_list[start:stop+1]), Stock.price_time_list[start], Stock.price_time_list[stop])

    def iter_ticks(self):
        start, stop = self.test_index_start, self.test_index_stop
        for time_ in Stock.price_time_list[start:stop+1]:
            tick_data = []
            for stock_id, stock in self.stock_list.items():
                tick_data.append(stock.get_tick(time_))
            yield (time_, tick_data)

    def get_stock_list(self, list_num = None):
        # sh, 600000~ 603993, 999999
        sh_special_list = ['999999']
        sh_list = sh_special_list + [os.path.splitext(f)[0][2:] for f in os.listdir(Stock.PATH_SH) if f.startswith('sh60')]
        # sz, 000000~002729, 300001~300397, 399001
        sz_special_list = ['399001']
        sz_list = sz_special_list + [os.path.splitext(f)[0][2:] for f in os.listdir(Stock.PATH_SZ) if f.startswith('sz00') or f.startswith('sz300')]
        if list_num:
            sh_list = sh_list[:list_num/2]
            sz_list = sz_list[:list_num/2]

        stock_list = {}
        Stock.get_stock_name_page()
        #for stock_id in sh_list + sz_list:
        def do_stock(stock_id, stock_list, unprocessed_stock_list):
            s = Stock(stock_id)
            if s.init_success:
                stock_list[stock_id] = s
                print 'process stock %s , total %d, time elapse %ds' % (stock_id, len(stock_list), time.time()-self.start_time)
            else:
                unprocessed_stock_list.append(stock_id)
        remain_list = sh_list + sz_list
        process_list_num_once = 100
        process_list_num = 0
        while remain_list:
            if len(remain_list) > process_list_num_once:
                process_list, remain_list = remain_list[:process_list_num_once], remain_list[process_list_num_once:]
            else:
                process_list, remain_list = remain_list, []
            unprocessed_stock_list = []
            gevent.joinall([gevent.spawn(do_stock, stock_id, stock_list, unprocessed_stock_list) for stock_id in process_list])
            process_list_num += 1
            remain_list += unprocessed_stock_list
            print 'process list %d done, unprocessed %d, time elapse %ds' % (process_list_num, len(unprocessed_stock_list), time.time()-self.start_time)
        self.stock_list = stock_list
        self.price_time_index = Stock.price_time_index
        self.price_time_list = Stock.price_time_list
        return stock_list

    def save_to_file(self, filename):
        pickle.dump(self, open(filename, 'wb'))

    def load_from_file(self, filename):
        stocks = pickle.load(open(filename, 'rb'))
        self.stock_list = stocks.stock_list
        Stock.price_time_index = stocks.price_time_index
        Stock.price_time_list = stocks.price_time_list

    def load_data(self, gen_stock_num = None):
        stock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_data.dat')
        if os.path.isfile(stock_file):
            self.load_from_file(stock_file)
        else:
            print 'no file found, start to generate list...'
            self.get_stock_list(gen_stock_num)
            self.save_to_file(stock_file)
            print 'done, save to file'


if __name__ == '__main__':
    test = 2
    if test == 0:
        dividend = Dividend()
        for stock_id in ['%06d' % i for i in range(20)]:
            bonus_data, stock_data = dividend.get_dividend_data(stock_id)
            print stock_id
            print bonus_data
            print stock_data
    elif test == 1:
        stock = Stock('000001')
        #print stock
        stock.plot()
        #for i in stock.get_interval_price((20121129, 20121202)):
        #    print i
        #s = pickle.dumps(stock)
        #t = pickle.loads(s)
        #print t
    elif test == 2:
        stocks = Stocks()
        stock_list = stocks.get_stock_list(100)
        stocks.save_to_file('stock_data.dat')
        print 'saved to stock_data.dat'
        print stocks
        #s = pickle.dumps(stocks)
        #t = pickle.loads(s)
        #print t
    elif test == 3:
        stocks = Stocks()
        stocks.load_from_file('stock_data.dat')
        print stocks
        print Stock.price_time_list
        #for stock_id, stock in stock_list.items():
        #    print stock
    elif test == 4:
        stocks = Stocks()
        stocks.load_from_file('stock_data.dat')
        for i, tick in enumerate(stocks.iter_ticks()):
            if i < 10:
                print tick
    elif test == 5:
        stocks = Stocks()
        stocks.load_from_file('stock_data.dat')
        stock = stocks.stock_list['000006']
        print stock.price_time_list[-10:]
        print stock.get_timeslice_close_price(20140815, 10)



#!/usr/bin/python
# -*- coding: utf-8 -*-

import struct


def load_data(file):
    data = open(file, 'rb').read()
    # 通达信格式, 日期，开盘， 最高， 最低， 收盘， xx， 成交量， xx， 各32bit
    data1 = struct.unpack('i'*(len(data)/4), data)
    stock_data = {}
    for i in xrange(len(data1)/8):
        #print data1[i*8:i*8+8]
        time_, open_, high_, low_, close_, not_use, volume_, not_use2 = data1[i*8:i*8+8]
        stock_data[time_] = [open_, close_, high_, low_, volume_]
    return stock_data

if __name__ == '__main__':
    data = load_data(r'D:\Program Files\sws2010\vipdoc\sz\lday\sz000001.day')
    for t in range(20140609, 20140617):
        if t in data:
            print t, data[t]
# test branchs

import random
import numpy as np

class Test:
    def __init__(self, initial, unit = 1):
        self.initial = initial
        self.N = 10000
        
    def test_sts(self, exp, rate, num, sts):
        for data in self.gen_data(exp, rate, num):
            for st in sts:
                result[st.name].add(st.deal(data, self.initial))
        self.show_result(result)

    def gen_data(self, exp, rate, num):
        R = (exp + 1) / rate -1
        #exp = rate *(R+1) - 1
        n1 = R
        n2 = -1
        choice = [n1] * int(rate*100) + [n2] * int(100-rate*100)

        for i in xrange(self.N):
            random.seed()
            data = [random.choice(choice) for i in xrange(num)]
            yield data
    
class St:
    def __init__(self, name, st_func):
        self.name = name
        self.st_func = st_func
        
    def deal(self, data, initial):
        return self.st_func(data, initial)

    def fix_initial_st(data, initial, ratio):
        unit = round(initial * ratio)
        final = initial
        max_backoff = 0
        max_value = final
        #test_final = []
        for v in data:
            if unit <= final:
                final += v * unit
            else:
                final += v * final
            #test_final.append(final)
            if final > max_value:
                max_value = final
            else:
                backoff = float(final) / max_value - 1
                max_backoff = min(max_backoff, backoff)
            if final <= 0:
                final = 0
                max_backoff = -1
                break
        #print r
        #print test_final
        return final, max_backoff
    
def fix_total_st(r, initial, ratio):
    final = initial
    max_backoff = 0
    max_value = final
    #test_final = []
    for v in r:
        unit = round(final * ratio)
        if unit == 0: unit = final
        final += v * unit
        if final > max_value:
            max_value = final
        else:
            backoff = float(final) / max_value - 1
            max_backoff = min(max_backoff, backoff)
        #test_final.append(final)
        if final <= 0:
            final = 0
            max_backoff = -1
            break
    #print r
    #print test_final
    return final, max_backoff

def float_total_st(r, initial, ratio):
    final, max_final = initial, initial
    #test_final = []
    for v in r:
        unit = round(max_final * ratio)
        if unit <= final:
            final += v * unit
        else:
            final += v * final
        max_final = max(final, max_final)
        #test_final.append(final)
        if final <= 0:
            final = 0
            break
    #print r
    #print test_final
    return final, 0

def gen_ratio_st(func, ratio):
    def _st(r, initial):
        return func(r, initial, ratio)
    _st.__name__ = '%s_%.3f' % (func.__name__, ratio)
    return _st

def calc_b(name, rslt, initial):
    n = len(rslt)
    rslt_final = [r[0] for r in rslt]
    rslt_max_backoff = [r[1] for r in rslt]
    bkrp_rate = float(rslt_final.count(0)) / n
    b = np.array(rslt_final) / initial - 1
    avg_b = np.average(b)
    var_b = np.std(b)
    #print b
    lose_rate = float((b < 0).sum()) / n
    max_lose = b.min()
    max_backoff = min(rslt_max_backoff)
    #return (bkrp_rate, avg_b, var_b)
    print '%s: %.2f%%, %d%%, %.2f, %.1f%%, %.1f%%, %.1f%%.' % (name, bkrp_rate*100, avg_b*100, var_b, lose_rate*100, max_lose*100, max_backoff*100)

# test
sts = []
#ratios = [0.005, 0.01, 0.02, 0.05, 0.1]
#ratios = [0.005, 0.01, 0.02]
ratios = [0.01]
for ratio in ratios:
    sts.append(gen_ratio_st(fix_initial_st, ratio))
for ratio in ratios:
    sts.append(gen_ratio_st(fix_total_st, ratio))
# # for ratio in ratios:
    # # sts.append(gen_ratio_st(float_total_st, ratio))

# 2R, 40%, 0.4*(2R+1)-1 = 0.2
exp = 0.6
#R = 3
#rate = 0.6
for rate in [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]:
    R = (exp + 1) / rate -1

    #exp = rate *(R+1) - 1

    n1 = R
    n2 = -1
    choice = [n1] * int(rate*100) + [n2] * int(100-rate*100)

    n = 100
    initial = 1000

    rslt = {}
    for st in sts:
        rslt[st.__name__] = []

    for times in xrange(10000):
        random.seed()
        r = [random.choice(choice) for i in xrange(n)]
        for st in sts:
            final = st(r, initial)
            rslt[st.__name__].append(final)

    print 'R %.1f, rate %.1f. exp: %.1f' % (R, rate, exp)
    for st in sts:
        calc_b(st.__name__, rslt[st.__name__], initial)
        #print rslt[st.__name__]

#!/usr/bin/python
# -*- coding: utf-8 -*-

from singleton import ArgsSingleton


class Calc(ArgsSingleton):
    _SUBS_ITEMS = {}  # {instance: (user, variable)}

    def subscribe(self, user, variable):
        if not self in Calc._SUBS_ITEMS:
            Calc._SUBS_ITEMS[self] = set()
        if not (user, variable) in Calc._SUBS_ITEMS[self]:
            Calc._SUBS_ITEMS[self].add((user, variable))
            
    def unsubscribe(self, user):
        if self in Calc._SUBS_ITEMS:
            user_variable = []
            for u, v in Calc._SUBS_ITEMS[self]:
                if u == user:
                    user_variable.append((u, v))
            for uv in user_variable:
                Calc._SUBS_ITEMS[self].remove(uv)

    def update(self, data):
        users = set()
        for item in Calc._SUBS_ITEMS:
            item_data = item.update(data)
            for user, variable in Calc._SUBS_ITEMS[item]:
                #user.update(item_data)
                setattr(user, variable, item_data)
                users.add(user)
        for user in users:
            user.update()

class Avg(Calc):
    def __init__(self, n):
        #print 'Avg(%d) init' % n
        self.n = n
        self.avg_data = None

    def update(self, data):
        #print 'Avg(%d) update: %f' % (self.n, data)
        if not self.avg_data:
            self.avg_data = data
        else:
            self.avg_data = (float)(data + (self.n-1) * self.avg_data ) /self.n
        return self.avg_data

class Sum(Calc):
    def __init__(self):
        #print 'Sum init'
        self.data_sum = 0
        
    def update(self, data):
        #print 'Sum update: %d' % data
        self.data_sum += data
        return self.data_sum

class User:
    def __init__(self):
        self.avg_2 = 0
        self.avg_10 = 0
        self.sum = 0

    def test(self):
        Avg(2).subscribe(self, 'avg_2')
        Avg(10).subscribe(self, 'avg_10')
        Sum().subscribe(self, 'sum')
        
    def update(self):
        print 'User Update: %f, %f, %d' % (self.avg_2, self.avg_10, self.sum)

class User2:
    def __init__(self):
        self.avg_2 = 0
        self.avg_5 = 0
        self.sum = 0

    def test(self):
        Avg(2).subscribe(self, 'avg_2')
        Avg(5).subscribe(self, 'avg_5')
        Sum().subscribe(self, 'sum')
        
    def test2(self):
        Avg(2).unsubscribe(self)
        Avg(5).unsubscribe(self)
        
    def update(self):
        print 'User2 Update: %f, %f, %d' % (self.avg_2, self.avg_5, self.sum)

u = User()
u.test()
u2 = User2()
u2.test()

c = Calc()
c.update(10)
c.update(20)
c.update(30)

u2.test2()

c.update(40)
c.update(50)

    

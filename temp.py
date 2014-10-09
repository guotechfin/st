#!/usr/bin/python
# -*- coding: utf-8 -*-

class ArgsSingleton(object):
  _instance = None
  def __new__(class_, *args, **kwargs):
    if not isinstance(class_._instance, class_):
        class_._args_instance = {}   # {args: instance}
    if args not in class_._args_instance:
        class_._instance = object.__new__(class_)
        class_._args_instance[args] = class_._instance
    return class_._args_instance[args]

class A(ArgsSingleton):
    #t1 = [1,2,3]
    t1 = 1
    def __init__(self, n):
        print 'A: %d' % 1
        pass
        
class D(ArgsSingleton):
    #t1 = [1,2,3]
    t1 = 1
    def __init__(self, n):
        print 'D: %d' % 1
        pass
    
class B(A):
    def test(self):
        print A.t1
        print B.t1
        
    def test2(self):
        #A.t1.append(5)
        A.t1 = 2
        print A.t1
        print B.t1
        
    def test3(self):
        #B.t1.append(6)
        B.t1 = 3
        print A.t1
        print B.t1
        
class C(A):
    def test3(self):
        print A.t1
        print C.t1

class Test(object):
    def __init__(self):
        self.value = range(5)

    def iterat(self):
        for i in self.value:
            print i
            yield i

test = 1
if test == 0:
    a = A(1)
    b = A(2)
    c = A(1)
    d = D(1)
    e = D(2)
    f = D(1)
    print a ==b, a==c, a == d
    print a is b, a is c, a is d
    print d ==e, d==f
    print d is e, d is f
elif test == 1:
    t = Test()
    for x in t.iterat():
        if x == 2: break
        print '1x: %d' % x
    for x in t.iterat():
        print '2x: %d' % x


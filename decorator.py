#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading


def thread(func):
    def _func(self, *args, **kwargs):
        threading.Thread(target = func, args = args, kwargs = kwargs).start()
    return _func

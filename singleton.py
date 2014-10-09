#!/usr/bin/python
# -*- coding: utf-8 -*-

class Singleton(object):
  _instance = None
  def __new__(class_, *args, **kwargs):
    if not isinstance(class_._instance, class_):
        class_._instance = object.__new__(class_)
    return class_._instance


class ArgsSingleton(object):
  _instance = None
  def __new__(class_, *args, **kwargs):
    if not isinstance(class_._instance, class_):
        class_._args_instance = {}   # {args: instance}
    if args not in class_._args_instance:
        class_._instance = object.__new__(class_)
        class_._args_instance[args] = class_._instance
    return class_._args_instance[args]


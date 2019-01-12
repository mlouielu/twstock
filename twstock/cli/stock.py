# -*- coding: utf-8 -*-

import twstock


def run(argv, initial_fetch: bool=True, proxies_list: list=[]):
    for sid in argv:
        s = twstock.Stock(sid, initial_fetch=initial_fetch, proxies_list=proxies_list)
        print('-------------- %s ---------------- ' % sid)
        print('high : {:>5} {:>5} {:>5} {:>5} {:>5}'.format(*s.high[-5:]))
        print('low  : {:>5} {:>5} {:>5} {:>5} {:>5}'.format(*s.low[-5:]))
        print('price: {:>5} {:>5} {:>5} {:>5} {:>5}'.format(*s.price[-5:]))

# -*- coding: utf-8 -*-

import unittest
from twstock import cli


class CLIFunctionTest(unittest.TestCase):
    def setUp(self):
        self.stocks = ['2330', '6223']
        self.proxies_list = [
            'http://128.199.165.29:8888',
            'http://128.199.195.200:8080',
            'socks5://207.180.233.152:50775',
        ]

    def test_best_four_point(self):
        cli.best_four_point.run(self.stocks)

    def test_stock(self):
        cli.stock.run(self.stocks)

    # def test_stock_with_proxy(self):
    #     cli.stock.run(self.stocks, proxies_list=self.proxies_list)

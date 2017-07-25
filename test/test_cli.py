# -*- coding: utf-8 -*-

import unittest
from twstock import cli


class CLIFunctionTest(unittest.TestCase):
    def setUp(self):
        self.stocks = ['2330', '6223']

    def test_best_four_point(self):
        cli.best_four_point.run(self.stocks)

    def test_stock(self):
        cli.stock.run(self.stocks)

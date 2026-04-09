# -*- coding: utf-8 -*-

import unittest
import vcr
from twstock import cli

MY_VCR = vcr.VCR(cassette_library_dir="test/cassettes", record_mode="none")


class CLIFunctionTest(unittest.TestCase):
    def setUp(self):
        self.stocks = ["2330", "6223"]

    @MY_VCR.use_cassette("cli_2330_6223.yaml")
    def test_best_four_point(self):
        cli.best_four_point.run(self.stocks)

    @MY_VCR.use_cassette("cli_2330_6223.yaml")
    def test_stock(self):
        cli.stock.run(self.stocks)

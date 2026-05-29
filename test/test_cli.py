# -*- coding: utf-8 -*-

import datetime
import unittest
from unittest.mock import patch
import vcr
from twstock import cli

MY_VCR = vcr.VCR(cassette_library_dir="test/cassettes", record_mode="none")


class MockDatetime(datetime.datetime):
    @classmethod
    def today(cls):
        return datetime.datetime(2026, 5, 15)

    @classmethod
    def now(cls, tz=None):
        return datetime.datetime(2026, 5, 15, tzinfo=tz)


class CLIFunctionTest(unittest.TestCase):
    def setUp(self):
        self.stocks = ["2330", "6223"]
        from twstock import stock
        self.original_datetime = stock.datetime.datetime
        stock.datetime.datetime = MockDatetime

    def tearDown(self):
        from twstock import stock
        stock.datetime.datetime = self.original_datetime

    @MY_VCR.use_cassette("cli_2330_6223.yaml")
    def test_best_four_point(self):
        cli.best_four_point.run(self.stocks)

    @MY_VCR.use_cassette("cli_2330_6223.yaml")
    def test_stock(self):
        cli.stock.run(self.stocks)

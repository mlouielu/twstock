import datetime
import unittest
from twstock import stock


class TWSEFetcherTest(unittest.TestCase):
    def setUp(self):
        self.fetcher = stock.TWSEFetcher()

    def test_convert_date(self):
        date = '106/05/01'
        cv_date = self.fetcher._convert_date(date)
        self.assertEqual(cv_date, '2017/05/01')

    def test_make_datatuple(self):
        data = ['106/05/02', '45,851,963', '9,053,856,108', '198.50',
                '199.00', '195.50', '196.50', '+2.00', '15,718']
        dt = self.fetcher._make_datatuple(data)
        self.assertEqual(dt.date, datetime.datetime(2017, 5, 2))
        self.assertEqual(dt.capacity, 45851963)
        self.assertEqual(dt.turnover, 9053856108)
        self.assertEqual(dt.open, 198.5)
        self.assertEqual(dt.high, 199.0)
        self.assertEqual(dt.low, 195.5)
        self.assertEqual(dt.close, 196.5)
        self.assertEqual(dt.ratio, 2.0)
        self.assertEqual(dt.transaction, 15718)


class StockTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stk = stock.Stock('2330')
        cls.stk.fetch(2015, 5)

    def test_price(self):
        self.assertIsInstance(self.stk.price, list)
        self.assertEqual(len(self.stk.price), len(self.stk.data))
        self.assertEqual(self.stk.price, [d.close for d in self.stk.data])
        self.assertEqual(self.stk.price,
                         [147.5, 147.0, 147.5, 146.5, 146.5, 148.5, 147.5,
                          148.0, 146.0, 146.5, 146.5, 146.5, 146.5, 145.5,
                          145.5, 147.5, 146.5, 145.0, 147.0, 146.0])

    def test_high(self):
        self.assertIsInstance(self.stk.high, list)
        self.assertEqual(len(self.stk.high), len(self.stk.data))
        self.assertEqual(self.stk.high, [d.high for d in self.stk.data])

    def test_low(self):
        self.assertIsInstance(self.stk.low, list)
        self.assertEqual(len(self.stk.low), len(self.stk.data))
        self.assertEqual(self.stk.low, [d.low for d in self.stk.data])

    def test_capacity(self):
        self.assertIsInstance(self.stk.capacity, list)
        self.assertEqual(len(self.stk.capacity), len(self.stk.data))
        self.assertEqual(self.stk.capacity, [d.capacity for d in self.stk.data])
        self.assertEqual(self.stk.capacity,
                         [30868640, 27789400, 18824208, 21908150, 20035646,
                          20402529, 24956498, 19437537, 39888654, 24831890,
                          26212375, 26321396, 26984912, 41286686, 22103852,
                          16323218, 16069726, 24257941, 36704395, 61983862])

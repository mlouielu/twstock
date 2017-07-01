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

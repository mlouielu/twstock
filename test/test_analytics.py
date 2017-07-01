import unittest
from twstock import stock


class AnalyticsTest(unittest.TestCase):
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

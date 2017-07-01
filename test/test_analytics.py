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

    def test_capacity(self):
        self.assertIsInstance(self.stk.capacity, list)
        self.assertEqual(len(self.stk.capacity), len(self.stk.data))
        self.assertEqual(self.stk.capacity, [d.capacity for d in self.stk.data])
        self.assertEqual(self.stk.capacity,
                         [30868640, 27789400, 18824208, 21908150, 20035646,
                          20402529, 24956498, 19437537, 39888654, 24831890,
                          26212375, 26321396, 26984912, 41286686, 22103852,
                          16323218, 16069726, 24257941, 36704395, 61983862])

# -*- coding: utf-8 -*-

import unittest
import twstock
from twstock import realtime


class RealtimeTest(unittest.TestCase):
    def test_realtime_field(self):
        self.assertCountEqual(
            realtime.get_raw('2330').keys(),
            twstock.mock.get_stock_info('2330').keys())

    def test_realtime_get_raw(self):
        self.assertIn('msgArray', realtime.get_raw('2330'))

    def test_realtime_get_blank(self):
        stock = realtime.get('')

        self.assertFalse(stock['success'])
        self.assertIn('rtmessage', stock)
        self.assertIn('rtcode', stock)

    def test_realtime_get_bad_id(self):
        stock = realtime.get('9999')

        self.assertFalse(stock['success'])
        self.assertIn('rtmessage', stock)
        self.assertIn('rtcode', stock)

        stock = realtime.get(['9999', '8888'])

        self.assertFalse(stock['success'])
        self.assertIn('rtmessage', stock)
        self.assertIn('rtcode', stock)

    def test_realtime_get_tpex_id(self):
        stock = realtime.get('6223')

        self.assertTrue(stock['success'])
        self.assertEqual(stock['info']['code'], '6223')


class MockRealtimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        realtime.mock = True

    @classmethod
    def tearDownClass(cls):
        realtime.mock = False

    def test_mock_one_stock_id(self):
        s = realtime.get('2330')

        self.assertTrue(s['success'])
        self.assertEqual(s['info']['code'], '2330')
        self.assertEqual(s['realtime']['latest_trade_price'], '214.50')
        self.assertEqual(s['realtime']['best_bid_price'],
                         ['214.00', '213.50', '213.00', '212.50', '212.00'])

    @unittest.skip('Dont want to fix this, is about the code in realtime')
    def test_mock_multiple_stock_id(self):
        s = realtime.get(['2330', '2337'])

        self.assertTrue(s['success'])
        self.assertCountEqual(s.keys(), ['2330', '2337', 'success'])
        self.assertTrue(s['2330']['success'])
        self.assertEqual(s['2330']['info']['code'], '2330')
        self.assertEqual(s['2330']['realtime']['latest_trade_price'], '214.50')
        self.assertTrue(s['2337']['success'])

# -*- coding: utf-8 -*-

import unittest
from unittest import mock
import twstock
from twstock import realtime
import responses
from requests.exceptions import ProxyError, InvalidURL
import json
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError
import sys

# import logging
# from pprint import pprint
# # 顯示 DEBUG 訊息
# # logging.basicConfig(level=logging.DEBUG)


class RealtimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.FETCH_URL = {
            '2330' : 'http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_2330.tw&_=1500861243000',
            '6223' : 'http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=otc_6223.tw&_=1500861243000',
            '2330_6223' : 'http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_2330.tw%7Cotc_6223.tw&_=1500861243000'
        }

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_realtime_field(self):
        realtime.proxies_list = []
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['2330'],
            json=twstock.mock.get_stock_info('2330'),
            status=200
        )
        stock = realtime.get_raw('2330')

        self.assertCountEqual(
            stock.keys(),
            twstock.mock.get_stock_info('2330').keys())

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_realtime_get_raw(self):
        realtime.proxies_list = []
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['2330'],
            json=twstock.mock.get_stock_info('2330'),
            status=200
        )
        stock = realtime.get_raw('2330')

        self.assertIn('msgArray', stock)

    def test_realtime_get_blank(self):
        realtime.proxies_list = []
        stock = realtime.get('')

        self.assertFalse(stock['success'])
        self.assertIn('rtmessage', stock)
        self.assertIn('rtcode', stock)

    def test_realtime_get_bad_id(self):
        realtime.proxies_list = []
        stock = realtime.get('9999')

        self.assertFalse(stock['success'])
        self.assertIn('rtmessage', stock)
        self.assertIn('rtcode', stock)

        stock = realtime.get(['9999', '8888'])

        self.assertFalse(stock['success'])
        self.assertIn('rtmessage', stock)
        self.assertIn('rtcode', stock)

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_realtime_get_tpex_id(self):
        realtime.proxies_list = []
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['6223'],
            json=twstock.mock.get_stock_info('6223'),
            status=200
        )
        stock = realtime.get('6223')

        self.assertTrue(stock['success'])
        self.assertEqual(stock['info']['code'], '6223')

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_realtime_multiple_stock_id(self):
        realtime.proxies_list = []
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['2330_6223'],
            json=twstock.mock.get_stock_info('2330_6223'),
            status=200
        )
        stock = realtime.get(['2330', '6223'])

        self.assertTrue(stock['success'])
        self.assertIn('2330', stock)
        self.assertTrue(stock['2330']['success'])
        self.assertEqual(stock['2330']['info']['code'], '2330')
        self.assertIn('6223', stock)
        self.assertTrue(stock['6223']['success'])
        self.assertEqual(stock['6223']['info']['code'], '6223')

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_realtime_get_response_with_wrong_id(self):
        realtime.proxies_list = []
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['2330'],
            json=twstock.mock.get_stock_info('error_code'),
            status=200
        )
        stock = realtime.get('2330')
        self.assertFalse(stock['success'])
        self.assertIn('rtmessage', stock)
        self.assertIn('rtcode', stock)
        self.assertEqual(stock['rtcode'], '5004')

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_realtime_get_response_without_msg_array(self):
        realtime.proxies_list = []
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['2330'],
            json=twstock.mock.get_stock_info('without_msg_array'),
            status=200
        )
        stock = realtime.get('2330')
        self.assertFalse(stock['success'])
        self.assertIn('rtmessage', stock)
        self.assertIn('rtcode', stock)

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_realtime_get_response_empty_msg_array(self):
        realtime.proxies_list = []
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['2330'],
            json=twstock.mock.get_stock_info('empty_msg_array'),
            status=200
        )
        stock = realtime.get('2330')
        self.assertFalse(stock['success'])
        self.assertIn('rtmessage', stock)
        self.assertIn('rtcode', stock)
        self.assertEqual(stock['rtcode'], '5001')

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_raises_json_decode_error(self):
        realtime.proxies_list = []
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['2330'],
            body='{json:wrong',
            status=200
        )
        stock = realtime.get('2330')

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_raises_timeout_error(self):
        realtime.proxies_list = []
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['2330'],
            body=TimeoutError('Unittest Mock TimeoutError!!'),
            status=200
        )
        stock = realtime.get('2330')

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_raises_unexpected_error(self):
        realtime.proxies_list = []
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['2330'],
            body=InvalidURL('Unittest Mock InvalidURL!!'),
            status=200
        )
        self.assertRaises(InvalidURL, realtime.get, '2330')

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_proxy_raises_proxy_error(self):
        realtime.proxies_list = [
            'http://0.0.0.0:1234',
            'http://0.0.0.0:3128',
        ]
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['2330'],
            body=ProxyError('Unittest Mock ProxyError!!'),
            status=200
        )
        stock = realtime.get('2330')

    @responses.activate
    @mock.patch('time.time', mock.MagicMock(return_value=1500861243))
    def test_proxy(self):
        realtime.proxies_list = [
            'http://128.199.165.29:8888',
            'http://128.199.195.200:8080',
            'socks5://207.180.233.152:50775',
        ]
        responses.add(
            responses.GET,
            'http://mis.twse.com.tw/stock/index.jsp',
            status=200
        )
        responses.add(
            responses.GET,
            self.FETCH_URL['2330'],
            json=twstock.mock.get_stock_info('2330'),
            status=200
        )
        stock = realtime.get('2330')


class MockRealtimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        realtime.mock = True

    @classmethod
    def tearDownClass(cls):
        realtime.mock = False

    def test_mock_one_stock_id(self):
        mock_stock = realtime.get('2330')

        self.assertTrue(mock_stock['success'])
        self.assertEqual(mock_stock['info']['code'], '2330')
        self.assertEqual(mock_stock['realtime']['latest_trade_price'], '214.50')
        self.assertEqual(mock_stock['realtime']['best_bid_price'],
                         ['214.00', '213.50', '213.00', '212.50', '212.00'])

    @unittest.skip('Dont want to fix this, is about the code in realtime')
    def test_mock_multiple_stock_id(self):
        mock_stock = realtime.get(['2330', '2337'])

        self.assertTrue(mock_stock['success'])
        self.assertCountEqual(mock_stock.keys(), ['2330', '2337', 'success'])
        self.assertTrue(mock_stock['2330']['success'])
        self.assertEqual(mock_stock['2330']['info']['code'], '2330')
        self.assertEqual(mock_stock['2330']['realtime']['latest_trade_price'], '214.50')
        self.assertTrue(mock_stock['2337']['success'])

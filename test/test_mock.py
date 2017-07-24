import unittest
from twstock import mock


class MockTest(unittest.TestCase):
    def test_mock_get_stock_info_will_work(self):
        self.assertIn('msgArray', mock.get_stock_info('2330'))

    def test_mock_get_stock_info_raw_data(self):
        self.assertCountEqual(
            mock.get_stock_info('2330').keys(),
            ['msgArray', 'userDelay', 'rtmessage', 'referer', 'queryTime', 'rtcode'])

    def test_mock_get_stock_info_msgarray(self):
        self.assertEqual(mock.get_stock_info('2330')['msgArray'][0]['c'], '2330')

    def test_mock_get_stock_info_will_change_in_different_index(self):
        self.assertNotEqual(
            mock.get_stock_info('2330', 0), mock.get_stock_info('2330', 1))
        self.assertNotEqual(
            mock.get_stock_info('2330', 1), mock.get_stock_info('2330', 2))
        self.assertNotEqual(
            mock.get_stock_info('2330', 0), mock.get_stock_info('2330', 2))

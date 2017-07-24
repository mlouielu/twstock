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

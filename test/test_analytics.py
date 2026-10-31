import unittest
import vcr
from twstock import stock
from twstock import analytics
from twstock import legacy

MY_VCR = vcr.VCR(cassette_library_dir="test/cassettes", record_mode="none")


class AnalyticsTest(unittest.TestCase):
    def setUp(self):
        self.legacy = legacy.LegacyAnalytics()
        self.ng = analytics.Analytics()

    def test_continuous(self):
        data = [1, 2, 3, 4, 5, 6, 7]
        legacy_result = self.legacy.cal_continue(data)
        ng_result = self.ng.continuous(data)
        self.assertEqual(ng_result, legacy_result)
        self.assertEqual(ng_result, 6)

        data = [1, 2, 3, 4, 1, 2]
        legacy_result = self.legacy.cal_continue(data)
        ng_result = self.ng.continuous(data)
        self.assertEqual(ng_result, legacy_result)
        self.assertEqual(ng_result, 1)

        data = [1, 2, 3, 4, 1, 2, 3, 4, 5]
        legacy_result = self.legacy.cal_continue(data)
        ng_result = self.ng.continuous(data)
        self.assertEqual(ng_result, legacy_result)
        self.assertEqual(ng_result, 4)

        data = [5, 4, 3, 2, 1]
        legacy_result = self.legacy.cal_continue(data)
        ng_result = self.ng.continuous(data)
        self.assertEqual(ng_result, legacy_result)
        self.assertEqual(ng_result, -4)

        data = [5, 4, 3, 2, 1, 5, 4, 3]
        legacy_result = self.legacy.cal_continue(data)
        ng_result = self.ng.continuous(data)
        self.assertEqual(ng_result, legacy_result)
        self.assertEqual(ng_result, -2)

    def test_moving_average(self):
        data = [50, 60, 70, 75]

        # Legacy moving_average will affect data argument's data
        ng_result = self.ng.moving_average(data, 2)
        legacy_result = self.legacy.moving_average(data, 2)
        self.assertEqual(ng_result, legacy_result)
        self.assertEqual(ng_result, [55.0, 65.0, 72.5])

    def test_moving_average_with_none(self):
        # stock.py converts the exchange's "--" (no trade) into None, so a real
        # series can contain None. A window holding a missing day has no
        # meaningful average, so that point is None instead of raising.
        data = [50, 60, 70, None, 80, 90]

        ng_result = self.ng.moving_average(data, 2)
        legacy_result = self.legacy.moving_average(data, 2)
        self.assertEqual(ng_result, legacy_result)
        self.assertEqual(ng_result, [55.0, 65.0, None, None, 85.0])

    def test_continuous_with_none(self):
        # The run is interrupted by the gap: only 70 -> 60 -> 50 counts.
        data = [50, 60, 70, None, 80, 90]
        ng_result = self.ng.continuous(data)
        self.assertEqual(ng_result, self.legacy.cal_continue(data))
        self.assertEqual(ng_result, 1)

    def test_ma_bias_ratio_with_none(self):
        data = [50, 60, 70, None, 80, 90]
        self.ng.price = data
        ng_result = self.ng.ma_bias_ratio(2, 3)
        legacy_result = self.legacy.ma_bias_ratio(2, 3, data)
        self.assertEqual(ng_result, legacy_result)
        self.assertEqual(ng_result, [5.0, None, None, None])

    def test_all_none_does_not_raise(self):
        # A fully missing series (delisted or no trades in range) must return
        # empty/all-None results rather than raising.
        for series in ([None, None, None], [None], []):
            self.assertEqual(self.ng.moving_average(series, 2),
                             self.legacy.moving_average(series, 2))
            self.assertEqual(self.ng.continuous(series),
                             self.legacy.cal_continue(series))

    def test_ma_bias_ratio(self):
        data = [50, 60, 70, 75, 80, 88, 102, 105, 106]
        self.ng.price = data
        ng_result = self.ng.ma_bias_ratio(3, 6)
        legacy_result = self.legacy.ma_bias_ratio(3, 6, data)
        self.assertEqual(ng_result, legacy_result)

        data = [75, 72, 77, 85, 100, 65, 60, 55, 52, 45]
        self.ng.price = data
        ng_result = self.ng.ma_bias_ratio(3, 6)
        legacy_result = self.legacy.ma_bias_ratio(3, 6, data)
        self.assertEqual(ng_result, legacy_result)

    def test_ma_bias_ratio_pivot(self):
        data = [50, 60, 70, 75, 80, 88, 102, 105, 106]
        legacy_result = self.legacy.ma_bias_ratio_point(data, 5, False)
        ng_result = self.ng.ma_bias_ratio_pivot(data, 5, False)
        self.assertEqual(legacy_result, ng_result)

        legacy_result = self.legacy.ma_bias_ratio_point(data, 5, True)
        ng_result = self.ng.ma_bias_ratio_pivot(data, 5, True)
        self.assertEqual(legacy_result, ng_result)

        data = [75, 72, 77, 85, 100, 65, 60, 55, 52, 45]
        legacy_result = self.legacy.ma_bias_ratio_point(data, 5, False)
        ng_result = self.ng.ma_bias_ratio_pivot(data, 5, False)
        self.assertEqual(legacy_result, ng_result)

        legacy_result = self.legacy.ma_bias_ratio_point(data, 5, True)
        ng_result = self.ng.ma_bias_ratio_pivot(data, 5, True)
        self.assertEqual(legacy_result, ng_result)


class BestFourPointTest(unittest.TestCase):
    @classmethod
    @MY_VCR.use_cassette("twse_2330_recent.yaml")
    def setUpClass(self):
        self.stock = stock.Stock("2330")
        self.legacy = legacy.LegacyBestFourPoint(self.stock)
        self.ng = analytics.BestFourPoint(self.stock)

    def test_bias_ratio(self):
        self.assertEqual(self.ng.bias_ratio(), self.legacy.bias_ratio())
        self.assertEqual(self.ng.bias_ratio(True), self.legacy.bias_ratio(True))

    def test_best_buy_1(self):
        self.assertEqual(self.ng.best_buy_1(), self.legacy.best_buy_1())

    def test_best_buy_2(self):
        self.assertEqual(self.ng.best_buy_2(), self.legacy.best_buy_2())

    def test_best_buy_3(self):
        self.assertEqual(self.ng.best_buy_3(), self.legacy.best_buy_3())

    def test_best_buy_4(self):
        self.assertEqual(self.ng.best_buy_4(), self.legacy.best_buy_4())

    def test_best_sell_1(self):
        self.assertEqual(self.ng.best_sell_1(), self.legacy.best_sell_1())

    def test_best_sell_2(self):
        self.assertEqual(self.ng.best_sell_2(), self.legacy.best_sell_2())

    def test_best_sell_3(self):
        self.assertEqual(self.ng.best_sell_3(), self.legacy.best_sell_3())

    def test_best_sell_4(self):
        self.assertEqual(self.ng.best_sell_4(), self.legacy.best_sell_4())

    def test_best_four_point_to_buy(self):
        self.assertEqual(
            self.ng.best_four_point_to_buy(), self.legacy.best_four_point_to_buy()
        )

    def test_best_four_point_to_sell(self):
        self.assertEqual(
            self.ng.best_four_point_to_sell(), self.legacy.best_four_point_to_sell()
        )

    @MY_VCR.use_cassette("twse_2330_historical.yaml")
    def test_best_four_point(self):
        self.stock.fetch(2014, 5)
        self.assertEqual(self.ng.best_four_point(), self.legacy.best_four_point())

        self.stock.fetch(2015, 5)
        self.assertEqual(self.ng.best_four_point(), self.legacy.best_four_point())

        self.stock.fetch(2016, 5)
        self.assertEqual(self.ng.best_four_point(), self.legacy.best_four_point())

        self.stock.fetch(2017, 5)
        self.assertEqual(self.ng.best_four_point(), self.legacy.best_four_point())

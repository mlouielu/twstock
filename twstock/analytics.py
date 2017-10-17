# -*- coding: utf-8 -*-

from collections import namedtuple
from datetime import datetime

class Analytics(object):

    def continuous(self, data):
        diff = [1 if data[-i] > data[-i - 1] else -1 for i in range(1, len(data))]
        cont = 0
        for v in diff:
            if v == diff[0]:
                cont += 1
            else:
                break
        return cont * diff[0]

    def moving_average(self, data, days):
        result = []
        data = data[:]
        for _ in range(len(data) - days + 1):
            result.append(round(sum(data[-days:]) / days, 2))
            data.pop()
        return result[::-1]

    def ma_bias_ratio(self, day1, day2):
        """Calculate moving average bias ratio"""
        data1 = self.moving_average(self.price, day1)
        data2 = self.moving_average(self.price, day2)
        result = [data1[-i] - data2[-i] for i in range(1, min(len(data1), len(data2)) + 1)]

        return result[::-1]

    def ma_bias_ratio_pivot(self, data, sample_size=5, position=False):
        """Calculate pivot point"""
        sample = data[-sample_size:]

        if position is True:
            check_value = max(sample)
            pre_check_value = max(sample) > 0
        elif position is False:
            check_value = min(sample)
            pre_check_value = max(sample) < 0

        return ((sample_size - sample.index(check_value) < 4 and
                 sample.index(check_value) != sample_size - 1 and pre_check_value),
                sample_size - sample.index(check_value) - 1,
                check_value)


class BestFourPoint(object):
    BEST_BUY_WHY = ['量大收紅', '量縮價不跌', '三日均價由下往上', '三日均價大於六日均價']
    BEST_SELL_WHY = ['量大收黑', '量縮價跌', '三日均價由上往下', '三日均價小於六日均價']

    def __init__(self, stock):
        self.stock = stock

    def bias_ratio(self, position=False):
        return self.stock.ma_bias_ratio_pivot(
            self.stock.ma_bias_ratio(3, 6),
            position=position)

    def plus_bias_ratio(self):
        return self.bias_ratio(True)

    def mins_bias_ratio(self):
        return self.bias_ratio(False)

    def best_buy_1(self):
        return (self.stock.capacity[-1] > self.stock.capacity[-2] and
                self.stock.price[-1] > self.stock.open[-1])

    def best_buy_2(self):
        return (self.stock.capacity[-1] < self.stock.capacity[-2] and
                self.stock.price[-1] > self.stock.open[-2])

    def best_buy_3(self):
        return self.stock.continuous(self.stock.moving_average(self.stock.price, 3)) == 1

    def best_buy_4(self):
        return (self.stock.moving_average(self.stock.price, 3)[-1] >
                self.stock.moving_average(self.stock.price, 6)[-1])

    def best_sell_1(self):
        return (self.stock.capacity[-1] > self.stock.capacity[-2] and
                self.stock.price[-1] < self.stock.open[-1])

    def best_sell_2(self):
        return (self.stock.capacity[-1] < self.stock.capacity[-2] and
                self.stock.price[-1] < self.stock.open[-2])

    def best_sell_3(self):
        return self.stock.continuous(self.stock.moving_average(self.stock.price, 3)) == -1

    def best_sell_4(self):
        return (self.stock.moving_average(self.stock.price, 3)[-1] <
                self.stock.moving_average(self.stock.price, 6)[-1])

    def best_four_point_to_buy(self):
        result = []
        check = [self.best_buy_1(), self.best_buy_2(),
                 self.best_buy_3(), self.best_buy_4()]
        if self.mins_bias_ratio() and any(check):
            for index, v in enumerate(check):
                if v:
                    result.append(self.BEST_BUY_WHY[index])
        else:
            return False
        return ', '.join(result)

    def best_four_point_to_sell(self):
        result = []
        check = [self.best_sell_1(), self.best_sell_2(),
                 self.best_sell_3(), self.best_sell_4()]
        if self.plus_bias_ratio() and any(check):
            for index, v in enumerate(check):
                if v:
                    result.append(self.BEST_SELL_WHY[index])
        else:
            return False
        return ', '.join(result)

    def best_four_point(self):
        buy = self.best_four_point_to_buy()
        sell = self.best_four_point_to_sell()
        if buy:
            return (True, buy)
        elif sell:
            return (False, sell)

        return None


class StochastiOscillator(object): # 隨機震盪指標
    """A Stochasti Oscillator(KD) object"""

    def __init__(self, stock, periods=9, smoothing_versus=3, period='day', high=80, low=20, realtime_data=None):
        """Initialize Stochasti Oscillator

        Args:
            stock: twstock.Stock.
            periods: How many units of time.
            smoothing_versus: Use how many units of time to calculate Simple Moving Average(SMA).
            period: How long is a unit time.
            high: Edge of Overbought Zone.
            low: Edge of Oversold Zone.
            realtime_data: Realtime stock infomation.
        """

        self._stock = stock  # 假如是預設丟31筆資料
        self._periods = periods  # 取樣範圍 需要periods單位period以上的資料才可以開始算kd值 9 41 198 594 2376
        self._smoothing_versus = smoothing_versus # 平滑因子 simple moving average of rsv/%k
        self._period = period # period: day, week, month, season, year
        self._high = high # 自定義超買區(Overbought Zone)界線
        self._low = low # 自定義超賣區(Oversold Zone)界線
        self._realtime_data = realtime_data # 補上當日資料
        self._realtime = False # 是否使用即時資料
        self.data = []
        self.calc()

    def calc(self, start=0):
        """Calculate Stochasti Oscillator

        Args:
            start: which row start calculating.
        """

        def get_period_data():
            """Transfer daily data to specified period data."""

            self.raw_data = [{'date': None, 'price': None, 'high': None, 'low': None}]
            index = 0
            def append_newline(index : int, with_data = True):
                self.raw_data.append({
                    'date': (datetime.strptime(self._realtime_data['info']['time'], '%Y-%m-%d %H:%M:%S') if index == len(self._stock.price) else self._stock.date[index]) if with_data else None,
                    'price': (float(self._realtime_data['realtime']['latest_trade_price']) if index == len(self._stock.price) else self._stock.price[index]) if with_data else None,
                    'high': (float(self._realtime_data['realtime']['high']) if index == len(self._stock.price) else self._stock.high[index]) if with_data else None,
                    'low': (float(self._realtime_data['realtime']['low']) if index == len(self._stock.price) else self._stock.low[index]) if with_data else None})
            def update_lastline(index : int, override = False):
                self.raw_data[-1]['date'] = (datetime.strptime(self._realtime_data['info']['time'], '%Y-%m-%d %H:%M:%S') if index == len(self._stock.price) else self._stock.date[index])
                self.raw_data[-1]['price'] = (float(self._realtime_data['realtime']['latest_trade_price']) if index == len(self._stock.price) else self._stock.price[index])
                high = float(self._realtime_data['realtime']['high']) if index == len(self._stock.price) else self._stock.high[index]
                low = float(self._realtime_data['realtime']['low']) if index == len(self._stock.price) else self._stock.low[index]
                self.raw_data[-1]['high'] = high if override else max(high, self.raw_data[-1]['high'])
                self.raw_data[-1]['low'] = low if override else min(low, self.raw_data[-1]['low'])
            for index in range(len(self._stock.price) + 1):
                if index == len(self._stock.price):
                    if self._realtime_data is None or self._realtime_data['info']['time'][:10] == self.raw_data[-1]['date'].isoformat()[:10]:  # 沒有即時資料或已經有當天資料了
                        break
                    else:
                        self._realtime = True
                date = datetime.strptime(self._realtime_data['info']['time'], '%Y-%m-%d %H:%M:%S') if index == len(self._stock.price) else self._stock.date[index]
                if self.raw_data[-1]['date'] is None:
                    update_lastline(index, True)
                    continue
                else:
                    if self.period == 'day':
                        append_newline(index)
                        continue
                    elif self.period == 'week':
                        if self.raw_data[-1]['date'].isocalendar()[:2] == date.isocalendar()[:2]: # 同一周
                            update_lastline(index)
                            continue
                    elif self.raw_data[-1]['date'].year == date.year: # 同一年
                        if self.period == 'month':
                            if self.raw_data[-1]['date'].month == date.month: # 同一月
                                update_lastline(index)
                                continue
                        elif self.period == 'season':
                            if (self.raw_data[-1]['date'].month - 1) // 3  == (date.month - 1) // 3: # 同一季
                                update_lastline(index)
                                continue
                        elif self.period == 'year':
                            update_lastline(index)
                            continue
                    append_newline(index)
        get_period_data()
        KDJContainer = namedtuple('KDJ', ['date', 'rsv', 'k', 'd', 'j', 'j2', 'price'])
        self.data = []
        for index in range(start, len(self.raw_data) - self._periods + 1):
            low = min([self.raw_data[index2]['low'] for index2 in range(index, index + self._periods)]) # n單位週期的最低最低價
            high = max([self.raw_data[index2]['high'] for index2 in range(index, index + self._periods)]) # n單位週期的最高最高價
            # 開始計算 KD 值初始日，無前一日 KD 的數值，可以代入 50
            raw_stochastic_value = (self.raw_data[index + self._periods - 1]['price'] - low) * 100 / (high - low) # 未成熟隨機值(Raw Stochastic Value)
            k_value = ((self._smoothing_versus - 1) * (50 if len(self.data) == 0 else self.data[-1].k) + raw_stochastic_value) / self._smoothing_versus # 快速移動平均值: RSV 值的smoothing_versus單位period指數平滑移動平均
            d_value = ((self._smoothing_versus - 1) * (50 if len(self.data) == 0 else self.data[-1].d) + k_value) / self._smoothing_versus # 慢速移動平均值: K 值的smoothing_versus單位period指數平滑移動平均
            j_value = 3 * d_value - 2 * k_value # 正乖離程度
            j2_value = 3 * k_value - 2 * d_value # 負乖離程度
            self.data.append(KDJContainer(self.raw_data[index + self._periods - 1]['date'], raw_stochastic_value, k_value, d_value, j_value, j2_value, self.raw_data[index + self._periods - 1]['price']))

    def kd_high_passivation(self):
        """高檔鈍化 K值在高檔(K值>80)連續3天 未來再漲的機率高

        Returns:
            Does high passivation happen?
        """

        if len(self.data) < 3:
            return None
        return self.data[-1].k >= self._high and self.data[-2].k >= self._high and self.data[-3].k >= self._high

    def kd_low_passivation(self):
        """低檔鈍化 K值在低檔(K值<20)區連續3天 未來繼續跌的機率高"""
        if len(self.data) < 3:
            return None
        return self.data[-1].k <= self._low and self.data[-2].k <= self._low and self.data[-3].k <= self._low

    def k_high(self):
        """K高檔(建議賣出)"""
        if len(self.data) == 0:
            return None
        return self.data[-1].k >= self._high

    def k_low(self):
        """K低檔(建議買進)"""
        if len(self.data) == 0:
            return None
        return self.data[-1].k <= self._low

    def golden_intersection(self):
        """黃金交叉(建議買進)"""
        if len(self.data) < 2:
            return None
        return self.data[-1].d <= 30 and self.data[-1].k >= self.data[-1].d and self.data[-2].k < self.data[-2].d

    def dead_intersection(self):
        """死亡交叉(建議賣出)"""
        if len(self.data) < 2:
            return None
        return self.data[-1].d >= 70 and self.data[-1].k <= self.data[-1].d and self.data[-2].k > self.data[-2].d

    # 低檔鈍化後反彈

    # 高檔鈍化後反彈

    def top_divergence(self):
        """頂背離(建議賣出) 股價創新高，KD沒有創新高 或 股價沒有創新高，KD創新高"""
        if len(self.data) < 2:
            return None
        return (self.data[-1].price > self.data[-2].price and self.data[-1].k <= self.data[-2].k and self.data[-1].d <= self.data[-2].d) or (self.data[-1].k > self.data[-2].k and self.data[-1].d > self.data[-2].d and self.data[-1].price <= self.data[-2].price)

    def button_divergence(self):
        """底背離(建議買進) 股價創新低，KD沒有創新低 或 股價沒有創新低，KD創新低"""
        if len(self.data) < 2:
            return None
        return (self.data[-1].price < self.data[-2].price and self.data[-1].k >= self.data[-2].k and self.data[-1].d >= self.data[-2].d) or (self.data[-1].k < self.data[-2].k and self.data[-1].d < self.data[-2].d and self.data[-1].price >= self.data[-2].price)

    # 多頭高生命力股
    #   季線：向上+金叉
    #   月線：向上+金叉+高檔鈍化+高檔鈍化後反彈
    #   週線：向上+金叉+高檔鈍化+突破高布林+高檔鈍化後反彈
    #   日線：向上+金叉+高檔鈍化+突破高布林+高檔鈍化後反彈

    # 空頭高生命力股
    #   季線：向下+死叉
    #   月線：向下+死叉+低檔鈍化+低檔鈍化後反彈
    #   週線：向下+死叉+低檔鈍化+跌破低布林+低檔鈍化後反彈
    #   日線：向下+死叉+低檔鈍化+跌破低布林+低檔鈍化後反彈

    def __len__(self):
        return len(self.data)

    @property
    def stock(self):
        return self._stock

    @stock.setter
    def stock(self, value):
        self._stock = value
        self.calc()

    @property
    def periods(self):
        return self._periods

    @periods.setter
    def periods(self, value : int):
        self._periods = value
        self.calc()

    @property
    def smoothing_versus(self):
        return self._smoothing_versus

    @smoothing_versus.setter
    def smoothing_versus(self, value : int):
        self._smoothing_versus = value
        self.calc()

    @property
    def period(self):
        return self._period

    @period.setter
    def period(self, value : str):
        self._period = value
        self.calc()

    @property
    def realtime_data(self):
        return self._realtime_data

    @realtime_data.setter
    def realtime_data(self, value : dict):
        self._realtime_data = value
        self._realtime = False
        self.calc()

    @property
    def realtime(self):
        return self._realtime

    @property
    def date(self):
        return [d.date for d in self.data]

    @property
    def rsv(self):
        return [d.rsv for d in self.data]

    @property
    def k(self):
        return [d.k for d in self.data]

    @property
    def d(self):
        return [d.d for d in self.data]

    @property
    def j(self):
        return [d.j for d in self.data]

    @property
    def j2(self):
        return [d.j2 for d in self.data]

    @property
    def price(self):
        return [d.price for d in self.data]

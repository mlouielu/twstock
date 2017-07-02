# -*- coding: utf-8 -*-


class LegacyAnalytics(object):
    """Legacy analytics from toomore/grs"""

    def cal_continue(self, list_data):
        """ 計算持續天數

            :rtype: int
            :returns: 向量數值：正數向上、負數向下。
        """
        diff_data = []
        for i in range(1, len(list_data)):
            if list_data[-i] > list_data[-i - 1]:
                diff_data.append(1)
            else:
                diff_data.append(-1)
        cont = 0
        for value in diff_data:
            if value == diff_data[0]:
                cont += 1
            else:
                break
        return cont * diff_data[0]

    def moving_average(self, days, data):
        """ 計算移動平均數

            :rtype: 序列 舊→新
        """
        result = []
        for dummy in range(len(data) - int(days) + 1):
            result.append(round(sum(data[-days:]) / days, 2))
            data.pop()
        result.reverse()
        return result

    def ma_bias_ratio(self, date1, date2, data):
        """ 計算乖離率（均價）
            date1 - date2

            :param int data1: n 日
            :param int data2: m 日
            :rtype: 序列 舊→新
        """
        data1 = self.moving_average(date1, data)
        data2 = self.moving_average(date2, data)
        cal_list = []
        for i in range(1, min(len(data1), len(data2)) + 1):
            cal_list.append(data1[-i] - data2[-i])
        cal_list.reverse()
        return cal_list

    def ma_bias_ratio_point(cls, data, sample=5,
                            positive_or_negative=False):
        """判斷轉折點位置

           :param list data: 計算資料
           :param int sample: 計算的區間樣本數量
           :param bool positive_or_negative: 正乖離 為 True，負乖離 為 False
           :rtype: tuple
           :returns: (True or False, 第幾個轉折日, 轉折點值)
        """
        sample_data = data[-sample:]
        if positive_or_negative:  # 正
            ckvalue = max(sample_data)  # 尋找最大值
            preckvalue = max(sample_data) > 0  # 區間最大值必須為正
        else:
            ckvalue = min(sample_data)  # 尋找最小值
            preckvalue = max(sample_data) < 0  # 區間最大值必須為負
        return (sample - sample_data.index(ckvalue) < 4 and \
                sample_data.index(ckvalue) != sample - 1 and preckvalue,
                sample - sample_data.index(ckvalue) - 1,
                ckvalue)


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

    def moving_average(self, days, data):
        result = []
        data = data[:]
        for _ in range(len(data) - days + 1):
            result.append(round(sum(data[-days:]) / days, 2))
            data.pop()
        return result[::-1]

    def ma_bias_ratio(self, day1, day2):
        """Calculate moving average bias ratio"""
        data1 = self.moving_average(day1, self.price)
        data2 = self.moving_average(day2, self.price)
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
        return self.stock.continuous(self.stock.moving_average(3, self.stock.price)) == 1

    def best_buy_4(self):
        return (self.stock.moving_average(3, self.stock.price)[-1] >
                self.stock.moving_average(6, self.stock.price)[-1])

    def best_sell_1(self):
        return (self.stock.capacity[-1] > self.stock.capacity[-2] and
                self.stock.price[-1] < self.stock.open[-1])

    def best_sell_2(self):
        return (self.stock.capacity[-1] < self.stock.capacity[-2] and
                self.stock.price[-1] < self.stock.open[-2])

    def best_sell_3(self):
        return self.stock.continuous(self.stock.moving_average(3, self.stock.price)) == -1

    def best_sell_4(self):
        return (self.stock.moving_average(3, self.stock.price)[-1] <
                self.stock.moving_average(6, self.stock.price)[-1])

    def best_four_to_buy(self):
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

    def best_four_to_sell(self):
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
        buy = self.best_four_to_buy()
        sell = self.best_four_to_sell()
        if buy:
            return (True, buy)
        elif sell:
            return (False, sell)

        return None

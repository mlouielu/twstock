# -*- coding: utf-8 -*-


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

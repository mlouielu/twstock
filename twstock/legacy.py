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

    def moving_average(self, data, days):
        """ 計算移動平均數

            :rtype: 序列 舊→新
        """
        result = []
        data = data[:]
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
        data1 = self.moving_average(data, date1)
        data2 = self.moving_average(data, date2)
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


class LegacyBestFourPoint(object):
    """ 四大買點組合

        :param grs.Stock data: 個股資料
    """
    def __init__(self, data):
        self.data = data

    def bias_ratio(self, position=False):
        """ 判斷乖離

            :param bool positive_or_negative: 正乖離 為 True，負乖離 為 False
        """
        return self.data.ma_bias_ratio_pivot(
                   self.data.ma_bias_ratio(3, 6),
                   position=position)

    def check_plus_bias_ratio(self):
        """ 正乖離扣至最大 """
        return self.bias_ratio(True)

    def check_mins_bias_ratio(self):
        """ 負乖離扣至最大 """
        return self.bias_ratio()

    ##### 四大買點 #####
    def best_buy_1(self):
        """量大收紅
        """
        result = self.data.capacity[-1] > self.data.capacity[-2] and \
                 self.data.price[-1] > self.data.open[-1]
        return result

    def best_buy_2(self):
        """量縮價不跌
        """
        result = self.data.capacity[-1] < self.data.capacity[-2] and \
                 self.data.price[-1] > self.data.price[-2]
        return result

    def best_buy_3(self):
        """三日均價由下往上
        """
        return self.data.continuous(self.data.moving_average(self.data.price, 3)) == 1

    def best_buy_4(self):
        """三日均價大於六日均價
        """
        return self.data.moving_average(self.data.price, 3)[-1] > \
               self.data.moving_average(self.data.price, 6)[-1]

    ##### 四大賣點 #####
    def best_sell_1(self):
        """量大收黑
        """
        result = self.data.capacity[-1] > self.data.capacity[-2] and \
                 self.data.price[-1] < self.data.open[-1]
        return result

    def best_sell_2(self):
        """量縮價跌
        """
        result = self.data.capacity[-1] < self.data.capacity[-2] and \
                 self.data.price[-1] < self.data.price[-2]
        return result

    def best_sell_3(self):
        """三日均價由上往下
        """
        return self.data.continuous(self.data.moving_average(self.data.price, 3)) == -1

    def best_sell_4(self):
        """三日均價小於六日均價
        """
        return self.data.moving_average(self.data.price, 3)[-1] < \
               self.data.moving_average(self.data.price, 6)[-1]

    def best_four_point_to_buy(self):
        """ 判斷是否為四大買點

            :rtype: str or False
        """
        result = []
        if self.check_mins_bias_ratio() and \
            (self.best_buy_1() or self.best_buy_2() or self.best_buy_3() or \
             self.best_buy_4()):
            if self.best_buy_1():
                result.append(self.best_buy_1.__doc__.strip())
            if self.best_buy_2():
                result.append(self.best_buy_2.__doc__.strip())
            if self.best_buy_3():
                result.append(self.best_buy_3.__doc__.strip())
            if self.best_buy_4():
                result.append(self.best_buy_4.__doc__.strip())
            result = ', '.join(result)
        else:
            result = False
        return result

    def best_four_point_to_sell(self):
        """ 判斷是否為四大賣點

            :rtype: str or False
        """
        result = []
        if self.check_plus_bias_ratio() and \
            (self.best_sell_1() or self.best_sell_2() or self.best_sell_3() or \
             self.best_sell_4()):
            if self.best_sell_1():
                result.append(self.best_sell_1.__doc__.strip())
            if self.best_sell_2():
                result.append(self.best_sell_2.__doc__.strip())
            if self.best_sell_3():
                result.append(self.best_sell_3.__doc__.strip())
            if self.best_sell_4():
                result.append(self.best_sell_4.__doc__.strip())
            result = ', '.join(result)
        else:
            result = False
        return result

    def best_four_point(self):
        """ 判斷買點或賣點

            :rtype: tuple
            :returns: (bool, str)
        """
        buy = self.best_four_point_to_buy()
        sell = self.best_four_point_to_sell()

        if buy:
            return True, buy
        elif sell:
            return False, sell

        return None

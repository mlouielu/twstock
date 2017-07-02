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


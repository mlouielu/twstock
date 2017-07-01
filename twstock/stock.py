# -*- coding: utf-8 -*-

import datetime
import urllib.parse
from collections import namedtuple
import requests


TWSE_BASE_URL = 'http://www.twse.com.tw/'
DATATUPLE = namedtuple('Data', ['date', 'capacity', 'turnover', 'open',
                                'high', 'low', 'close', 'ratio', 'transaction'])


class TWSEFetcher(object):
    REPORT_URL = urllib.parse.urljoin(TWSE_BASE_URL, 'exchangeReport/STOCK_DAY')

    def __init__(self):
        pass

    def fetch(self, year: int, month: int, sid: str):
        params = {'date': '%d%02d01' % (year, month), 'stockNo': sid}
        r = requests.get(self.REPORT_URL, params=params)
        data = r.json()

        if data['stat'] == '很抱歉，沒有符合條件的資料!':
            data['data'] = {}
        elif data['stat'] == 'OK':
            data['data'] = self.purify(data)
        return data

    def _convert_date(self, date):
        """Convert '106/05/01' to '2017/05/01'"""
        return '/'.join([str(int(date.split('/')[0]) + 1911)] + date.split('/')[1:])

    def _make_datatuple(self, data):
        data[0] = datetime.datetime.strptime(self._convert_date(data[0]), '%Y/%m/%d')
        data[1] = int(data[1].replace(',', ''))
        data[2] = int(data[2].replace(',', ''))
        data[3] = float(data[3])
        data[4] = float(data[4])
        data[5] = float(data[5])
        data[6] = float(data[6])
        data[7] = float(0.0 if data[7] == 'X0.00' else data[7])  # +/-/X表示漲/跌/不比價
        data[8] = int(data[8].replace(',', ''))
        return DATATUPLE(*data)

    def purify(self, original_data):
        return [self._make_datatuple(d) for d in original_data['data']]


class Stock(object):

    def __init__(self, sid: str):
        self.sid = sid
        self.fetcher = TWSEFetcher()
        self.raw_data = []
        self.data = []

    def _month_year_iter(self, start_month, start_year, end_month, end_year):
        ym_start = 12 * start_year + start_month - 1
        ym_end = 12 * end_year + end_month - 1
        for ym in range(ym_start, ym_end):
            y, m = divmod(ym, 12)
            yield y, m + 1

    def fetch(self, year: int, month: int):
        """Fetch year month data"""
        self.raw_data = [self.fetcher.fetch(year, month, self.sid)]
        self.data = self.raw_data['data']
        return self.data

    def fetch_from(self, year: int, month: int):
        """Fetch data from year, month to current year month data"""
        self.raw_data = []
        self.data = []
        today = datetime.datetime.today()
        for year, month in self._month_year_iter(month, year, today.month, today.year):
            self.raw_data.append(self.fetcher.fetch(year, month, self.sid))
            self.data.extend(self.raw_data[-1]['data'])
        return self.data


if __name__ == '__main__':
    f = Stock('2330')
    print(f.fetch_from(2017, 5))

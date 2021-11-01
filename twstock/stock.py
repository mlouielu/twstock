# -*- coding: utf-8 -*-

import datetime
import urllib.parse
from collections import namedtuple

from operator import attrgetter
from time import sleep
from twstock.proxy import get_proxies
import os
import json

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

import requests

try:
    from . import analytics
    from .codes import codes
except ImportError as e:
    if e.name == 'lxml':
        # Fix #69
        raise e
    import analytics
    from codes import codes


TWSE_BASE_URL = 'http://www.twse.com.tw/'
TPEX_BASE_URL = 'http://www.tpex.org.tw/'
DATATUPLE = namedtuple('Data', ['date', 'capacity', 'turnover', 'open',
                                'high', 'low', 'close', 'change', 'transaction'])


class BaseFetcher(object):
    def fetch(self, year, month, sid, retry, retry_interval):
        pass

    def _convert_date(self, date):
        """Convert '106/05/01' to '2017/05/01'"""
        return '/'.join([str(int(date.split('/')[0]) + 1911)] + date.split('/')[1:])

    def _make_datatuple(self, data):
        pass

    def purify(self, original_data):
        pass


class TWSEFetcher(BaseFetcher):
    REPORT_URL = urllib.parse.urljoin(
        TWSE_BASE_URL, 'exchangeReport/STOCK_DAY')

    def __init__(self):
        pass

    def fetch(self, year: int, month: int, sid: str, retry: int=5, retry_interval: int=5):
        params = {'date': '%d%02d01' % (year, month), 'stockNo': sid}
        for retry_i in range(retry):
            r = requests.get(self.REPORT_URL, params=params,
                             proxies=get_proxies())
            sleep(retry_interval)
            try:
                data = r.json()
            except JSONDecodeError:
                continue
            else:
                break
        else:
            # Fail in all retries
            data = {'stat': '', 'data': []}

        if data['stat'] == 'OK':
            data['data'] = self.purify(data)
        else:
            data['data'] = []
        return data

    def _make_datatuple(self, data):
        data[0] = datetime.datetime.strptime(
            self._convert_date(data[0]), '%Y/%m/%d')
        data[1] = int(data[1].replace(',', ''))
        data[2] = int(data[2].replace(',', ''))
        data[3] = None if data[3] == '--' else float(data[3].replace(',', ''))
        data[4] = None if data[4] == '--' else float(data[4].replace(',', ''))
        data[5] = None if data[5] == '--' else float(data[5].replace(',', ''))
        data[6] = None if data[6] == '--' else float(data[6].replace(',', ''))
        # +/-/X表示漲/跌/不比價
        data[7] = float(0.0 if data[7].replace(',', '') ==
                        'X0.00' else data[7].replace(',', ''))
        data[8] = int(data[8].replace(',', ''))
        return DATATUPLE(*data)

    def purify(self, original_data):
        return [self._make_datatuple(d) for d in original_data['data']]


class TPEXFetcher(BaseFetcher):
    REPORT_URL = urllib.parse.urljoin(TPEX_BASE_URL,
                                      'web/stock/aftertrading/daily_trading_info/st43_result.php')

    def __init__(self):
        pass

    def fetch(self, year: int, month: int, sid: str, retry: int=5, retry_interval: int=5):
        params = {'d': '%d/%d' % (year - 1911, month), 'stkno': sid}
        for retry_i in range(retry):
            r = requests.get(self.REPORT_URL, params=params,
                             proxies=get_proxies())
            sleep(retry_interval)
            try:
                data = r.json()
            except JSONDecodeError:
                continue
            else:
                break
        else:
            # Fail in all retries
            data = {'aaData': []}

        data['data'] = []
        if data['aaData']:
            data['data'] = self.purify(data)
        return data

    def _convert_date(self, date):
        """Convert '106/05/01' to '2017/05/01'"""
        return '/'.join([str(int(date.split('/')[0]) + 1911)] + date.split('/')[1:])

    def _make_datatuple(self, data):
        data[0] = datetime.datetime.strptime(self._convert_date(data[0].replace('＊', '')),
                                             '%Y/%m/%d')
        data[1] = int(data[1].replace(',', '')) * 1000
        data[2] = int(data[2].replace(',', '')) * 1000
        data[3] = None if data[3] == '--' else float(data[3].replace(',', ''))
        data[4] = None if data[4] == '--' else float(data[4].replace(',', ''))
        data[5] = None if data[5] == '--' else float(data[5].replace(',', ''))
        data[6] = None if data[6] == '--' else float(data[6].replace(',', ''))
        data[7] = float(data[7].replace(',', ''))
        data[8] = int(data[8].replace(',', ''))
        return DATATUPLE(*data)

    def purify(self, original_data):
        return [self._make_datatuple(d) for d in original_data['aaData']]


class Stock(analytics.Analytics):

    def __init__(self, sid: str, initial_fetch: bool=True, skip_fetch_31: bool=False):
        self.sid = sid
        self.fetcher = TWSEFetcher(
        ) if codes[sid].market == '上市' else TPEXFetcher()
        self.raw_data = []
        # Handle json cache
        self.dump_file = 'twstock_' + sid + '.json'
        self.data_cache = []
        self.data_cache_ptr = 0
        self.data = []
        if os.path.exists(self.dump_file):
            # Load json cache if exists
            self.load()

        # Init data
        if initial_fetch and not skip_fetch_31:
            self.fetch_31()

    def search_data_cache(self, y, m):
        # search data cache for _month_year_iter()
        # if y and m find matched entry, copy data from self.data_cache to self.data 
        # return value
        #    1. True : find matched entry. Copy the data to self.data_cache.
        #              And self.data_cache_ptr stores the index of self.data_cache.
        #    2. False : Not found, need to send request to TWSE or TPEX.

        if len(self.data_cache) == 0:
            return False

        find_match_entry = False

        for data_cache_i in range(self.data_cache_ptr, len(self.data_cache)):
            if self.data_cache[data_cache_i].date.year == y and \
                    self.data_cache[data_cache_i].date.month == m :
                # Hit in data cache, start loop until next miss. To move a month data to data cache.
                # ex. If find 11/1 , then loop to add 11/1 ~ 11/30
                self.data.append(self.data_cache[data_cache_i])       
                find_match_entry = True
            elif find_match_entry == True:
                # First miss after hit, break
                # Finish moving a month data.
                self.data_cache_ptr = data_cache_i
                break
            elif self.data_cache[data_cache_i].date.year < y or \
                ( self.data_cache[data_cache_i].date.year == y and \
                    self.data_cache[data_cache_i].date.month < m ) :
                # find datetime before first date of target month, continue search
                self.data_cache_ptr = data_cache_i
                continue
            else:
                # find datetime after last date of target month, break
                self.data_cache_ptr = data_cache_i
                break
        return find_match_entry

    def _month_year_iter(self, start_month, start_year, end_month, end_year):
        ym_start = 12 * start_year + start_month - 1
        ym_end = 12 * end_year + end_month
        for ym in range(ym_start, ym_end):
            y, m = divmod(ym, 12)
            if self.search_data_cache(y,m + 1):
                # if match in data cache, skip it
                continue
            yield y, m + 1

    def fetch(self, year: int, month: int):
        """Fetch year month data"""
        self.raw_data = [self.fetcher.fetch(year, month, self.sid)]
        self.data = self.raw_data[0]['data']
        return self.data

    def fetch_period(self, from_year: int, from_month: int, from_day: int=0, to_year: int=0, to_month: int=0, to_day: int=0, retry: int=5, retry_interval: int=5):
        self.raw_data = []
        self.data = []
        self.data_cache_ptr = 0
        global REQ_COUNTER
        REQ_COUNTER = 0

        if to_year == 0 or to_month == 0:
            today = datetime.datetime.today()
            to_year = today.year
            to_month = today.month

        if from_year > to_year or ( from_year == to_year and from_month > to_month) or \
                ( from_year == to_year and from_month == to_month and from_day > to_day and from_day != 0):
            # check if invalid period
            return

        for year, month in self._month_year_iter(from_month, from_year, to_month, to_year):
            self.raw_data.append(self.fetcher.fetch(year, month, self.sid, retry, retry_interval))
            self.data.extend(self.raw_data[-1]['data'])
            # Copy fetched data to cache
            if self.data_cache_ptr + 1 >= len(self.data_cache):
                self.data_cache = self.data_cache + self.raw_data[-1]['data']
            else:
                self.data_cache = self.data_cache[:self.data_cache_ptr] +  self.raw_data[-1]['data'] + self.data_cache[self.data_cache_ptr:]
            if month == 12:
                # To decrease save data_cache frequency
                self.save()

        if from_day != 0:
            start_index = 0
            for dd_i in range(len(self.data)):
                if self.data[dd_i].date.day < from_day and \
                    self.data[dd_i].date.year == from_year and \
                    self.data[dd_i].date.month == from_month :
                    start_index += 1
                else:
                    break
            self.data = self.data[start_index:]

        if to_day != 0:
            end_index = len(self.data)
            for dd_ii in range(len(self.data),0,-1):
                dd_i = dd_ii - 1
                if self.data[dd_i].date.day > to_day and \
                    self.data[dd_i].date.year == to_year and \
                    self.data[dd_i].date.month == to_month :
                    end_index -= 1
                else:
                    break
            self.data = self.data[:end_index]

        self.check_data_valid()
        self.save()
        return self.data

    def fetch_from(self, from_year: int, from_month: int):
        """Fetch data from year, month to current year month data"""
        self.fetch_period(from_year=from_year, from_month=from_month)
        return self.data

    def fetch_31(self, current_year: int=0, current_month: int=0, current_day: int=0):
        """Fetch 31 days data"""
        if current_year == 0 or current_month == 0:
            start_date = datetime.datetime.today()
        else:
            start_date = datetime.datetime( current_year, current_month, current_day)
        before = start_date - datetime.timedelta(days=60)
        self.fetch_from(before.year, before.month)
        self.data = self.data[-31:]
        self.check_data_valid()
        return self.data

    def save(self):
        data_cache_save = self.data_cache
        today = datetime.datetime.today()

        # To avoid saving incomplete month data. ex. if today is 2020/11/12, then all data with 2020/11 will be ignore.
        for dc_c in range(len(data_cache_save),0,-1):
            dc_i = dc_c - 1 # from len(data_cache_save)-1 ~ 0
            if data_cache_save[dc_i].date.month == today.month and data_cache_save[dc_i].date.month == today.month:
                continue
            else:
                data_cache_save = data_cache_save[:dc_c]
                break

        with open(self.dump_file, 'w') as f:
            json.dump(data_cache_save, f, indent=4, sort_keys=True, default=str)

    def load(self):
        self.data_cache = []
        data_cache_tmp = []
        with open(self.dump_file, 'r') as f:
            data_cache_tmp = json.load(f)

        for data_i in range(len(data_cache_tmp)) :
            # To package to namedtuple "Data"
            entry_i = data_cache_tmp[data_i]
            datetime_d = entry_i[0]
            entry_i[0] = datetime.datetime.strptime(entry_i[0], '%Y-%m-%d %H:%M:%S')
            self.data_cache.append(DATATUPLE(*entry_i))

        self.check_data_valid()

    def organize_data_cache(self):
        self.data_cache = list(set(self.data_cache))
        self.data_cache = sorted(self.data_cache,key=attrgetter('date'), reverse=False)

    def check_data_valid(self):
        data_tmp = sorted(self.data,key=attrgetter('date'), reverse=False)
        detect_potential_issue = False
        if data_tmp != self.data:
            print("Potential self.data order issue")
            detect_potential_issue = True
        if len(set(data_tmp)) != len(self.data):
            print("Potential self.data duplicate issue")
            detect_potential_issue = True

        data_tmp = sorted(self.data_cache,key=attrgetter('date'), reverse=False)
        if data_tmp != self.data_cache:
            print("Potential self.data_cache order issue")
            detect_potential_issue = True
        if len(set(data_tmp)) != len(self.data_cache):
            print("Potential self.data_cache duplicate issue")               
            detect_potential_issue = True 
        if detect_potential_issue == False :
            print("Check data pass")

    @property
    def date(self):
        return [d.date for d in self.data]

    @property
    def capacity(self):
        return [d.capacity for d in self.data]

    @property
    def turnover(self):
        return [d.turnover for d in self.data]

    @property
    def price(self):
        return [d.close for d in self.data]

    @property
    def high(self):
        return [d.high for d in self.data]

    @property
    def low(self):
        return [d.low for d in self.data]

    @property
    def open(self):
        return [d.open for d in self.data]

    @property
    def close(self):
        return [d.close for d in self.data]

    @property
    def change(self):
        return [d.change for d in self.data]

    @property
    def transaction(self):
        return [d.transaction for d in self.data]

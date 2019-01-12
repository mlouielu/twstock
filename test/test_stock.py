import datetime
import unittest
from twstock import stock
import responses
import json
from requests.exceptions import ProxyError, InvalidURL
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

TWSE_2330_TW_201505_RESPONSE = '{"stat":"OK","date":"20150501","title":"104年05月 2330 台積電           各日成交資訊","fields":["日期","成交股數","成交金額","開盤價","最高價","最低價","收盤價","漲跌價差","成交筆數"],"data":[["104/05/04","30,868,640","4,548,281,580","148.50","148.50","146.00","147.50","+0.50","8,598"],["104/05/05","27,789,400","4,083,589,300","147.50","148.00","146.00","147.00","-0.50","6,502"],["104/05/06","18,824,208","2,765,471,076","145.50","148.00","145.50","147.50","+0.50","6,477"],["104/05/07","21,908,150","3,209,664,442","146.00","147.50","146.00","146.50","-1.00","5,816"],["104/05/08","20,035,646","2,938,305,595","146.00","147.50","146.00","146.50"," 0.00","7,730"],["104/05/11","20,402,529","3,020,441,292","149.00","149.00","147.00","148.50","+2.00","6,385"],["104/05/12","24,956,498","3,687,151,073","147.00","148.50","147.00","147.50","-1.00","6,593"],["104/05/13","19,437,537","2,880,697,082","147.50","149.00","147.00","148.00","+0.50","5,694"],["104/05/14","39,888,654","5,860,602,872","148.00","148.50","146.00","146.00","-2.00","12,300"],["104/05/15","24,831,890","3,627,515,848","147.00","147.00","145.00","146.50","+0.50","8,186"],["104/05/18","26,212,375","3,823,751,806","147.00","147.00","145.00","146.50"," 0.00","7,178"],["104/05/19","26,321,396","3,852,118,475","145.50","147.50","145.00","146.50"," 0.00","9,418"],["104/05/20","26,984,912","3,949,956,564","146.50","147.00","146.00","146.50"," 0.00","10,516"],["104/05/21","41,286,686","5,995,895,156","146.00","146.50","144.50","145.50","-1.00","12,871"],["104/05/22","22,103,852","3,229,666,392","146.00","147.00","145.00","145.50"," 0.00","6,813"],["104/05/25","16,323,218","2,396,692,046","146.50","147.50","145.50","147.50","+2.00","5,998"],["104/05/26","16,069,726","2,368,218,823","148.50","148.50","146.50","146.50","-1.00","6,148"],["104/05/27","24,257,941","3,536,266,849","145.50","147.00","145.00","145.00","-1.50","6,869"],["104/05/28","36,704,395","5,388,568,653","147.00","147.50","146.00","147.00","+2.00","10,259"],["104/05/29","61,983,862","9,053,910,953","147.00","147.50","145.50","146.00","-1.00","8,252"]],"notes":["符號說明:+/-/X表示漲/跌/不比價","當日統計資訊含一般、零股、盤後定價、鉅額交易，不含拍賣、標購。"]}'
TPEX_6223_TW_201505_RESPONSE = '{"stkNo":"6223","stkName":"\u65fa\u77fd","showListPriceNote":false,"showListPriceLink":false,"reportDate":"104\/5","iTotalRecords":20,"aaData":[["104\/05\/04","374","34,462","93.00","93.00","91.30","91.40","-0.60","323"],["104\/05\/05","474","43,721","91.50","93.20","91.20","91.80","0.40","368"],["104\/05\/06","468","42,967","91.50","93.20","90.40","91.80","0.00","401"],["104\/05\/07","1,257","117,125","91.80","94.10","91.80","93.50","1.70","820"],["104\/05\/08","1,079","99,439","93.50","93.90","90.30","91.00","-2.50","804"],["104\/05\/11","3,400","294,740","92.40","92.80","84.70","84.70","-6.30","2,031"],["104\/05\/12","3,424","280,856","83.70","84.80","78.80","84.00","-0.70","2,484"],["104\/05\/13","1,078","91,625","84.00","86.40","82.50","85.80","1.80","808"],["104\/05\/14","1,433","125,392","88.70","88.70","86.50","87.10","1.30","1,065"],["104\/05\/15","891","76,478","86.50","86.60","85.00","86.10","-1.00","632"],["104\/05\/18","1,202","100,938","86.10","86.10","83.00","83.90","-2.20","913"],["104\/05\/19","1,008","85,342","83.50","85.50","83.40","84.50","0.60","850"],["104\/05\/20","999","86,379","85.30","87.10","84.70","86.70","2.20","731"],["104\/05\/21","488","42,151","86.40","86.90","85.60","86.30","-0.40","335"],["104\/05\/22","706","60,965","86.20","87.40","85.70","86.00","-0.30","496"],["104\/05\/25","231","19,948","85.90","86.90","85.70","86.20","0.20","179"],["104\/05\/26","1,890","169,432","87.00","91.90","86.30","91.10","4.90","1,406"],["104\/05\/27","782","70,881","90.70","91.60","89.50","90.90","-0.20","585"],["104\/05\/28","1,214","112,992","91.20","94.40","91.20","91.70","0.80","870"],["104\/05\/29","583","53,033","92.00","92.60","90.40","90.40","-1.30","415"]]}'

class BaseFetcherTest(unittest.TestCase,):
    fetcher = stock.BaseFetcher()

    def test_fetch(self):
        dt = self.fetcher.fetch(1970, 1, 'Test1', 0)

    def test_make_datatuple(self):
        data = []
        dt = self.fetcher._make_datatuple(data)

    def test_purify(self):
        data = []
        dt = self.fetcher.purify(data)

class FetcherTest(object):
    def test_convert_date(self):
        date = '106/05/01'
        cv_date = self.fetcher._convert_date(date)
        self.assertEqual(cv_date, '2017/05/01')

    def test_make_datatuple(self):
        data = ['106/05/02', '45,851,963', '9,053,856,108', '198.50', '199.00',
                '195.50', '196.50', '+2.00', '15,718']
        dt = self.fetcher._make_datatuple(data)
        self.assertEqual(dt.date, datetime.datetime(2017, 5, 2))
        self.assertEqual(dt.capacity, 45851963)
        self.assertEqual(dt.turnover, 9053856108)
        self.assertEqual(dt.open, 198.5)
        self.assertEqual(dt.high, 199.0)
        self.assertEqual(dt.low, 195.5)
        self.assertEqual(dt.close, 196.5)
        self.assertEqual(dt.change, 2.0)
        self.assertEqual(dt.transaction, 15718)

    def test_make_datatuple_without_prices(self):
        data = ['106/05/02', '45,851,963', '9,053,856,108', '--', '--', '--',
                '--', ' 0.00', '15,718']
        dt = self.fetcher._make_datatuple(data)
        self.assertEqual(dt.date, datetime.datetime(2017, 5, 2))
        self.assertEqual(dt.capacity, 45851963)
        self.assertEqual(dt.turnover, 9053856108)
        self.assertEqual(dt.open, None)
        self.assertEqual(dt.high, None)
        self.assertEqual(dt.low, None)
        self.assertEqual(dt.close, None)
        self.assertEqual(dt.change, 0.0)
        self.assertEqual(dt.transaction, 15718)


class TWSEFetcerTest(unittest.TestCase, FetcherTest):
    fetcher = stock.TWSEFetcher()


class TPEXFetcherTest(unittest.TestCase, FetcherTest):
    fetcher = stock.TPEXFetcher()

    def test_make_datatuple(self):
        data = ['106/05/02', '45,851', '9,053,856', '198.50',
                '199.00', '195.50', '196.50', '2.00', '15,718']
        dt = self.fetcher._make_datatuple(data)
        self.assertEqual(dt.date, datetime.datetime(2017, 5, 2))
        self.assertEqual(dt.capacity, 45851000)
        self.assertEqual(dt.turnover, 9053856000)
        self.assertEqual(dt.open, 198.5)
        self.assertEqual(dt.high, 199.0)
        self.assertEqual(dt.low, 195.5)
        self.assertEqual(dt.close, 196.5)
        self.assertEqual(dt.change, 2.0)
        self.assertEqual(dt.transaction, 15718)

    def test_make_datatuple_without_prices(self):
        data = ['106/05/02', '45,851', '9,053,856', '--',
                '--', '--', '--', '0.00', '15,718']
        dt = self.fetcher._make_datatuple(data)
        self.assertEqual(dt.date, datetime.datetime(2017, 5, 2))
        self.assertEqual(dt.capacity, 45851000)
        self.assertEqual(dt.turnover, 9053856000)
        self.assertEqual(dt.open, None)
        self.assertEqual(dt.high, None)
        self.assertEqual(dt.low, None)
        self.assertEqual(dt.close, None)
        self.assertEqual(dt.change, 0.0)
        self.assertEqual(dt.transaction, 15718)

    def test_make_datatuple_with_asterisk(self):
        data = ['106/05/02＊', '45,851', '9,053,856', '198.50',
                '199.00', '195.50', '196.50', '2.00', '15,718']
        dt = self.fetcher._make_datatuple(data)
        self.assertEqual(dt.date, datetime.datetime(2017, 5, 2))
        self.assertEqual(dt.capacity, 45851000)
        self.assertEqual(dt.turnover, 9053856000)
        self.assertEqual(dt.open, 198.5)
        self.assertEqual(dt.high, 199.0)
        self.assertEqual(dt.low, 195.5)
        self.assertEqual(dt.close, 196.5)
        self.assertEqual(dt.change, 2.0)
        self.assertEqual(dt.transaction, 15718)

class StockTest(object):
    def test_fetch_31(self):
        self.stk.fetch_31()
        self.assertEqual(len(self.stk.data), 31)
        self.assertEqual(len(self.stk.price), 31)

    def test_date(self):
        self.assertIsInstance(self.stk.date, list)
        self.assertEqual(len(self.stk.date), len(self.stk.data))
        self.assertEqual(self.stk.date, [d.date for d in self.stk.data])

    def test_capacity(self):
        self.assertIsInstance(self.stk.capacity, list)
        self.assertEqual(len(self.stk.capacity), len(self.stk.data))
        self.assertEqual(self.stk.capacity, [d.capacity for d in self.stk.data])

    def test_turnover(self):
        self.assertIsInstance(self.stk.turnover, list)
        self.assertEqual(len(self.stk.turnover), len(self.stk.data))
        self.assertEqual(self.stk.turnover, [d.turnover for d in self.stk.data])

    def test_price(self):
        self.assertIsInstance(self.stk.price, list)
        self.assertEqual(len(self.stk.price), len(self.stk.data))
        self.assertEqual(self.stk.price, [d.close for d in self.stk.data])

    def test_high(self):
        self.assertIsInstance(self.stk.high, list)
        self.assertEqual(len(self.stk.high), len(self.stk.data))
        self.assertEqual(self.stk.high, [d.high for d in self.stk.data])

    def test_low(self):
        self.assertIsInstance(self.stk.low, list)
        self.assertEqual(len(self.stk.low), len(self.stk.data))
        self.assertEqual(self.stk.low, [d.low for d in self.stk.data])

    def test_open(self):
        self.assertIsInstance(self.stk.open, list)
        self.assertEqual(len(self.stk.open), len(self.stk.data))
        self.assertEqual(self.stk.open, [d.open for d in self.stk.data])

    def test_close(self):
        self.assertIsInstance(self.stk.close, list)
        self.assertEqual(len(self.stk.close), len(self.stk.data))
        self.assertEqual(self.stk.close, [d.close for d in self.stk.data])

    def test_change(self):
        self.assertIsInstance(self.stk.change, list)
        self.assertEqual(len(self.stk.change), len(self.stk.data))
        self.assertEqual(self.stk.change, [d.change for d in self.stk.data])

    def test_transaction(self):
        self.assertIsInstance(self.stk.transaction, list)
        self.assertEqual(len(self.stk.transaction), len(self.stk.data))
        self.assertEqual(self.stk.transaction, [d.transaction for d in self.stk.data])


class TWSEStockTest(unittest.TestCase, StockTest):
    @classmethod
    def setUpClass(cls):
        cls.FETCH_URL = 'http://www.twse.com.tw/exchangeReport/STOCK_DAY?date=20150501&stockNo=2330'
        cls.stk = stock.Stock('2330', initial_fetch=False)

    def test_initial_fetch(self):
        self.stk = stock.Stock('2330', initial_fetch=True)
        self.assertNotEqual(self.stk.data, [])
        for data in self.stk.raw_data:
            self.assertEqual(data['stat'], 'OK')
        self.assertEqual(self.stk.sid, '2330')

    def test_price(self):
        self.stk.fetch(2015, 5)
        self.assertIsInstance(self.stk.price, list)
        self.assertEqual(len(self.stk.price), len(self.stk.data))
        self.assertEqual(self.stk.price, [d.close for d in self.stk.data])
        self.assertEqual(self.stk.price,
                         [147.5, 147.0, 147.5, 146.5, 146.5, 148.5, 147.5,
                          148.0, 146.0, 146.5, 146.5, 146.5, 146.5, 145.5,
                          145.5, 147.5, 146.5, 145.0, 147.0, 146.0])

    def test_capacity(self):
        self.stk.fetch(2015, 5)
        self.assertIsInstance(self.stk.capacity, list)
        self.assertEqual(len(self.stk.capacity), len(self.stk.data))
        self.assertEqual(self.stk.capacity, [d.capacity for d in self.stk.data])
        self.assertEqual(self.stk.capacity,
                         [30868640, 27789400, 18824208, 21908150, 20035646,
                          20402529, 24956498, 19437537, 39888654, 24831890,
                          26212375, 26321396, 26984912, 41286686, 22103852,
                          16323218, 16069726, 24257941, 36704395, 61983862])

    @responses.activate
    def test_raises_json_decode_error(self):
        responses.add(
            responses.GET,
            self.FETCH_URL,
            body='{json:wrong',
            status=200
        )
        self.stk.fetch(2015, 5)
        self.assertEqual(self.stk.data, [])
        for data in self.stk.raw_data:
            self.assertEqual(data, {'data': [], 'stat': ''})
        self.assertEqual(self.stk.sid, '2330')

    @responses.activate
    def test_raises_timeout_error(self):
        responses.add(
            responses.GET,
            self.FETCH_URL,
            body=TimeoutError('Unittest Mock TimeoutError!!'),
            status=200
        )
        self.stk.fetch(2015, 5)
        self.assertEqual(self.stk.data, [])
        for data in self.stk.raw_data:
            self.assertEqual(data, {'data': [], 'stat': ''})
        self.assertEqual(self.stk.sid, '2330')

    @responses.activate
    def test_raises_unexpected_error(self):
        responses.add(
            responses.GET,
            self.FETCH_URL,
            body=InvalidURL('Unittest Mock InvalidURL!!'),
            status=200
        )
        self.assertRaises(InvalidURL, self.stk.fetch, 2015, 5)

    @responses.activate
    def test_proxy_raises_proxy_error(self):
        proxies_list = [
            'http://0.0.0.0:1234',
            'http://0.0.0.0:3128',
        ]
        self.stk = stock.Stock('2330', initial_fetch=False, proxies_list=proxies_list)
        responses.add(
            responses.GET,
            self.FETCH_URL,
            body=ProxyError('Unittest Mock ProxyError!!'),
            status=200
        )
        self.stk.fetch(2015, 5)
        self.assertEqual(self.stk.data, [])
        self.assertEqual(self.stk.fetcher.PROXIES_LIST, proxies_list)
        self.assertLess(self.stk.fetcher.proxy_counter, len(proxies_list))
        self.assertGreaterEqual(self.stk.fetcher.proxy_counter, 0)
        for data in self.stk.raw_data:
            self.assertEqual(data, {'data': [], 'stat': ''})
        self.assertEqual(self.stk.sid, '2330')

    @responses.activate
    def test_proxy(self):
        proxies_list = [
            'http://128.199.165.29:8888',
            'http://128.199.195.200:8080',
            'socks5://207.180.233.152:50775',
        ]
        self.stk = stock.Stock('2330', initial_fetch=False, proxies_list=proxies_list)
        responses.add(
            responses.GET,
            self.FETCH_URL,
            json=json.loads(TWSE_2330_TW_201505_RESPONSE),
            status=200
        )
        self.stk.fetch(2015, 5)
        self.assertNotEqual(self.stk.data, [])
        self.assertEqual(self.stk.fetcher.PROXIES_LIST, proxies_list)
        self.assertLess(self.stk.fetcher.proxy_counter, len(proxies_list))
        self.assertGreaterEqual(self.stk.fetcher.proxy_counter, 0)
        for data in self.stk.raw_data:
            self.assertEqual(data['stat'], 'OK')
        self.assertEqual(self.stk.sid, '2330')


class TPEXStockTest(unittest.TestCase, StockTest):
    @classmethod
    def setUpClass(cls):
        cls.stk = stock.Stock('6223', initial_fetch=False)
        cls.FETCH_URL = 'http://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_result.php?d=104/5&stkno=6223'

    def test_price(self):
        self.stk.fetch(2015, 5)
        self.assertIsInstance(self.stk.price, list)
        self.assertEqual(len(self.stk.price), len(self.stk.data))
        self.assertEqual(self.stk.price, [d.close for d in self.stk.data])
        self.assertEqual(self.stk.price,
                         [91.4, 91.8, 91.8, 93.5, 91.0, 84.7, 84.0, 85.8, 87.1,
                          86.1, 83.9, 84.5, 86.7, 86.3, 86.0, 86.2, 91.1, 90.9,
                          91.7, 90.4])

    def test_capacity(self):
        self.stk.fetch(2015, 5)
        self.assertIsInstance(self.stk.capacity, list)
        self.assertEqual(len(self.stk.capacity), len(self.stk.data))
        self.assertEqual(self.stk.capacity, [d.capacity for d in self.stk.data])
        self.assertEqual(self.stk.capacity,
                         [374000, 474000, 468000, 1257000, 1079000, 3400000,
                          3424000, 1078000, 1433000, 891000, 1202000, 1008000,
                          999000, 488000, 706000, 231000, 1890000, 782000,
                          1214000, 583000])

    @responses.activate
    def test_raises_json_decode_error(self):
        responses.add(
            responses.GET,
            self.FETCH_URL,
            body='{json:wrong',
            status=200
        )
        self.stk.fetch(2015, 5)
        self.assertEqual(self.stk.data, [])
        for data in self.stk.raw_data:
            self.assertEqual(data, {'aaData': [], 'data': []})
        self.assertEqual(self.stk.sid, '6223')

    @responses.activate
    def test_raises_timeout_error(self):
        responses.add(
            responses.GET,
            self.FETCH_URL,
            body=TimeoutError('Unittest Mock TimeoutError!!'),
            status=200
        )
        self.stk.fetch(2015, 5)
        self.assertEqual(self.stk.data, [])
        for data in self.stk.raw_data:
            self.assertEqual(data, {'aaData': [], 'data': []})
        self.assertEqual(self.stk.sid, '6223')

    @responses.activate
    def test_raises_unexpected_error(self):
        responses.add(
            responses.GET,
            self.FETCH_URL,
            body=InvalidURL('Unittest Mock InvalidURL!!'),
            status=200
        )
        self.assertRaises(InvalidURL, self.stk.fetch, 2015, 5)

    @responses.activate
    def test_proxy_raises_proxy_error(self):
        proxies_list = [
            'http://0.0.0.0:1234',
            'http://0.0.0.0:3128',
        ]
        self.stk = stock.Stock('6223', initial_fetch=False, proxies_list=proxies_list)
        responses.add(
            responses.GET,
            self.FETCH_URL,
            body=ProxyError('Unittest Mock ProxyError!!'),
            status=200
        )
        self.stk.fetch(2015, 5)
        self.assertEqual(self.stk.data, [])
        self.assertEqual(self.stk.fetcher.PROXIES_LIST, proxies_list)
        self.assertLess(self.stk.fetcher.proxy_counter, len(proxies_list))
        self.assertGreaterEqual(self.stk.fetcher.proxy_counter, 0)
        for data in self.stk.raw_data:
            self.assertEqual(data, {'aaData': [], 'data': []})
        self.assertEqual(self.stk.sid, '6223')

    @responses.activate
    def test_proxy(self):
        proxies_list = [
            'http://128.199.165.29:8888',
            'http://128.199.195.200:8080',
            'socks5://207.180.233.152:50775',
        ]
        self.stk = stock.Stock('6223', initial_fetch=False, proxies_list=proxies_list)
        responses.add(
            responses.GET,
            self.FETCH_URL,
            json=json.loads(TPEX_6223_TW_201505_RESPONSE),
            status=200
        )
        self.stk.fetch(2015, 5)
        self.assertNotEqual(self.stk.data, [])
        self.assertEqual(self.stk.fetcher.PROXIES_LIST, proxies_list)
        self.assertLess(self.stk.fetcher.proxy_counter, len(proxies_list))
        self.assertGreaterEqual(self.stk.fetcher.proxy_counter, 0)
        self.assertEqual(self.stk.sid, '6223')

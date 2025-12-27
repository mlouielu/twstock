# -*- coding: utf-8 -*-

import datetime
import urllib.parse
from collections import namedtuple
import logging

from twstock.proxy import get_proxies

# Setup logging for debugging
# Set to WARNING to only show warnings and errors
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

import requests

try:
    from . import analytics
    from .codes import codes
except ImportError as e:
    if e.name == "lxml":
        # Fix #69
        raise e
    import analytics
    from codes import codes


TWSE_BASE_URL = "http://www.twse.com.tw/"
TPEX_BASE_URL = "http://www.tpex.org.tw/"
DATATUPLE = namedtuple(
    "Data",
    [
        "date",
        "capacity",
        "turnover",
        "open",
        "high",
        "low",
        "close",
        "change",
        "transaction",
        "note",
    ],
)


class BaseFetcher(object):
    def fetch(self, year, month, sid, retry):
        pass

    def _convert_date(self, date):
        """Convert '106/05/01' to '2017/05/01'"""
        return "/".join([str(int(date.split("/")[0]) + 1911)] + date.split("/")[1:])

    def _make_datatuple(self, data):
        pass

    def purify(self, original_data):
        pass


class TWSEFetcher(BaseFetcher):
    REPORT_URL = urllib.parse.urljoin(TWSE_BASE_URL, "exchangeReport/STOCK_DAY")

    def __init__(self):
        pass

    def fetch(self, year: int, month: int, sid: str, retry: int = 5):
        params = {"date": "%d%02d01" % (year, month), "stockNo": sid, "response": "json"}
        logger.debug(f"[TWSE] Fetching sid={sid}, year={year}, month={month}, params={params}")

        for retry_i in range(retry):
            logger.debug(f"[TWSE] Retry {retry_i + 1}/{retry}, URL={self.REPORT_URL}")
            try:
                r = requests.get(self.REPORT_URL, params=params, proxies=get_proxies())
                logger.debug(f"[TWSE] Response status: {r.status_code}")
                logger.debug(f"[TWSE] Response content preview: {r.text[:200]}")
                logger.debug(f"[TWSE] Actual request URL: {r.url}")
                data = r.json()
                logger.debug(f"[TWSE] JSON parsed successfully, stat={data.get('stat', 'N/A')}")
            except JSONDecodeError as e:
                logger.warning(f"[TWSE] JSONDecodeError on retry {retry_i + 1}: {e} | Request: sid={sid}, year={year}, month={month}, URL={self.REPORT_URL}")
                continue
            except Exception as e:
                logger.error(f"[TWSE] Unexpected error on retry {retry_i + 1}: {e} | Request: sid={sid}, year={year}, month={month}, URL={self.REPORT_URL}")
                continue
            else:
                break
        else:
            # Fail in all retries
            logger.error(f"[TWSE] All {retry} retries failed | Request: sid={sid}, year={year}, month={month}, URL={self.REPORT_URL}")
            data = {"stat": "", "data": []}

        if data["stat"] == "OK":
            logger.debug(f"[TWSE] Data fetched successfully, {len(data.get('data', []))} records")
            data["data"] = self.purify(data)
        else:
            logger.warning(f"[TWSE] Data stat is not OK: {data.get('stat', 'N/A')} | Request: sid={sid}, year={year}, month={month}, date_param={params.get('date', 'N/A')}")
            data["data"] = []
        return data

    def _make_datatuple(self, data):
        try:
            logger.debug(f"[TWSE] Converting data: {data}")
            data[0] = datetime.datetime.strptime(self._convert_date(data[0]), "%Y/%m/%d")
            data[1] = int(data[1].replace(",", ""))
            data[2] = int(data[2].replace(",", ""))
            data[3] = None if data[3] == "--" else float(data[3].replace(",", ""))
            data[4] = None if data[4] == "--" else float(data[4].replace(",", ""))
            data[5] = None if data[5] == "--" else float(data[5].replace(",", ""))
            data[6] = None if data[6] == "--" else float(data[6].replace(",", ""))
            # +/-/X表示漲/跌/不比價
            data[7] = float(
                0.0 if data[7].replace(",", "") == "X0.00" else data[7].replace(",", "")
            )
            data[8] = int(data[8].replace(",", ""))
            # data[9] is the note field (註記), keep as is (usually empty string)
            # If data only has 9 fields, add empty note
            if len(data) == 9:
                data.append("")
            result = DATATUPLE(*data)
            logger.debug(f"[TWSE] Converted successfully: {result}")
            return result
        except Exception as e:
            logger.error(f"[TWSE] Error converting data: {data}, error: {e}")
            raise

    def purify(self, original_data):
        return [self._make_datatuple(d) for d in original_data["data"]]


class TPEXFetcher(BaseFetcher):
    REPORT_URL = urllib.parse.urljoin(
        TPEX_BASE_URL, "www/zh-tw/afterTrading/tradingStock"
    )

    def __init__(self):
        pass

    def fetch(self, year: int, month: int, sid: str, retry: int = 5):
        params = {"code": sid, "date": "%d/%02d/01" % (year, month)}
        logger.debug(f"[TPEX] Fetching sid={sid}, year={year}, month={month}, params={params}")

        for retry_i in range(retry):
            logger.debug(f"[TPEX] Retry {retry_i + 1}/{retry}, URL={self.REPORT_URL}")
            try:
                r = requests.get(self.REPORT_URL, params=params, proxies=get_proxies())
                logger.debug(f"[TPEX] Response status: {r.status_code}")
                logger.debug(f"[TPEX] Response content preview: {r.text[:200]}")
                data = r.json()
                logger.debug(f"[TPEX] JSON parsed successfully, aaData count={len(data.get('aaData', []))}")
            except JSONDecodeError as e:
                logger.warning(f"[TPEX] JSONDecodeError on retry {retry_i + 1}: {e} | Request: sid={sid}, year={year}, month={month}, URL={self.REPORT_URL}")
                continue
            except Exception as e:
                logger.error(f"[TPEX] Unexpected error on retry {retry_i + 1}: {e} | Request: sid={sid}, year={year}, month={month}, URL={self.REPORT_URL}")
                continue
            else:
                break
        else:
            # Fail in all retries
            logger.error(f"[TPEX] All {retry} retries failed | Request: sid={sid}, year={year}, month={month}, URL={self.REPORT_URL}")
            data = {"aaData": []}

        data["data"] = []
        # Support both old (aaData) and new API response formats
        if "aaData" in data and data["aaData"]:
            logger.debug(f"[TPEX] Data fetched successfully (old format: aaData), {len(data['aaData'])} records")
            data["data"] = self.purify(data)
        elif "tables" in data and data["tables"] and data.get("stat") == "ok":
            logger.debug(f"[TPEX] Data fetched successfully (new format: tables)")
            # New API format - extract data from tables
            try:
                table_data = data["tables"][0]["data"]
                logger.debug(f"[TPEX] Found {len(table_data)} records in new format")
                # Convert new format to old format structure
                data["aaData"] = table_data
                data["data"] = self.purify(data)
            except (KeyError, IndexError) as e:
                logger.error(f"[TPEX] Error parsing new format: {e}")
                logger.debug(f"[TPEX] Response structure: {list(data.keys())}")
        else:
            logger.warning(f"[TPEX] No data found. stat={data.get('stat', 'N/A')}, Response keys: {list(data.keys())} | Request: sid={sid}, year={year}, month={month}")
        return data

    def _convert_date(self, date):
        """Convert '106/05/01' to '2017/05/01'"""
        return "/".join([str(int(date.split("/")[0]) + 1911)] + date.split("/")[1:])

    def _make_datatuple(self, data):
        try:
            logger.debug(f"[TPEX] Converting data: {data}")

            # Handle both old format (10 fields) and new format (9 fields)
            # New format fields: 日期, 成交張數, 成交仟元, 開盤, 最高, 最低, 收盤, 漲跌, 筆數
            data[0] = datetime.datetime.strptime(
                self._convert_date(data[0].replace("＊", "")), "%Y/%m/%d"
            )
            data[1] = int(data[1].replace(",", "")) * 1000  # 成交張數 (convert to shares)
            data[2] = int(data[2].replace(",", "")) * 1000  # 成交仟元 (convert to dollars)
            data[3] = None if data[3] == "--" else float(data[3].replace(",", ""))
            data[4] = None if data[4] == "--" else float(data[4].replace(",", ""))
            data[5] = None if data[5] == "--" else float(data[5].replace(",", ""))
            data[6] = None if data[6] == "--" else float(data[6].replace(",", ""))
            data[7] = float(data[7].replace(",", ""))
            data[8] = int(data[8].replace(",", ""))

            # Add empty note field if not present (for compatibility with 10-field DATATUPLE)
            if len(data) == 9:
                data.append("")

            result = DATATUPLE(*data)
            logger.debug(f"[TPEX] Converted successfully: {result}")
            return result
        except Exception as e:
            logger.error(f"[TPEX] Error converting data: {data}, error: {e}")
            raise

    def purify(self, original_data):
        return [self._make_datatuple(d) for d in original_data["aaData"]]


class Stock(analytics.Analytics):
    def __init__(self, sid: str, initial_fetch: bool = True):
        self.sid = sid
        logger.info(f"[Stock] Initializing stock sid={sid}")
        market = codes[sid].market
        logger.info(f"[Stock] Market type: {market}")
        self.fetcher = TWSEFetcher() if market == "上市" else TPEXFetcher()
        self.raw_data = []
        self.data = []

        # Init data
        if initial_fetch:
            logger.info(f"[Stock] Fetching initial data (31 days)")
            self.fetch_31()

    def _month_year_iter(self, start_month, start_year, end_month, end_year):
        ym_start = 12 * start_year + start_month - 1
        ym_end = 12 * end_year + end_month
        for ym in range(ym_start, ym_end):
            y, m = divmod(ym, 12)
            yield y, m + 1

    def fetch(self, year: int, month: int):
        """Fetch year month data"""
        logger.info(f"[Stock] Fetching data for {year}/{month}")
        self.raw_data = [self.fetcher.fetch(year, month, self.sid)]
        self.data = self.raw_data[0]["data"]
        logger.info(f"[Stock] Fetched {len(self.data)} records")
        return self.data

    def fetch_from(self, year: int, month: int):
        """Fetch data from year, month to current year month data"""
        logger.info(f"[Stock] Fetching data from {year}/{month} to current")
        self.raw_data = []
        self.data = []
        today = datetime.datetime.today()
        logger.info(f"[Stock] Today is {today.year}/{today.month}/{today.day}")
        for year, month in self._month_year_iter(month, year, today.month, today.year):
            logger.info(f"[Stock] Fetching {year}/{month}")
            self.raw_data.append(self.fetcher.fetch(year, month, self.sid))
            self.data.extend(self.raw_data[-1]["data"])
        logger.info(f"[Stock] Total fetched {len(self.data)} records")
        return self.data

    def fetch_31(self):
        """Fetch 31 days data"""
        logger.info(f"[Stock] Fetching 31 days data")
        today = datetime.datetime.today()
        before = today - datetime.timedelta(days=60)
        logger.info(f"[Stock] Fetching from {before.year}/{before.month} (60 days before)")
        self.fetch_from(before.year, before.month)
        logger.info(f"[Stock] Trimming to last 31 records from {len(self.data)} total")
        self.data = self.data[-31:]
        logger.info(f"[Stock] Final data count: {len(self.data)}")
        return self.data

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

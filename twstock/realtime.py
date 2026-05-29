# -*- coding: utf-8 -*-

import datetime
import json
import time
import requests
import twstock
import sys
import xml.etree.ElementTree as ET
from twstock.proxy import get_proxies, get_session


SESSION_URL = "http://mis.twse.com.tw/stock/index.jsp"
STOCKINFO_URL = (
    "http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={stock_id}&_={time}"
)

# Mock data
mock = False


def _format_stock_info(data) -> dict:
    result = {"timestamp": 0.0, "info": {}, "realtime": {}}

    # Timestamp
    result["timestamp"] = int(data["tlong"]) / 1000

    # Information
    result["info"]["code"] = data["c"]
    result["info"]["channel"] = data["ch"]
    result["info"]["name"] = data["n"]
    result["info"]["fullname"] = data["nf"]
    result["info"]["time"] = datetime.datetime.fromtimestamp(
        int(data["tlong"]) / 1000
    ).strftime("%Y-%m-%d %H:%M:%S")

    # Process best result
    def _split_best(d):
        if d:
            return d.strip("_").split("_")
        return d

    # Realtime information
    result["realtime"]["latest_trade_price"] = data.get("z", None)
    result["realtime"]["trade_volume"] = data.get("tv", None)
    result["realtime"]["accumulate_trade_volume"] = data.get("v", None)
    result["realtime"]["best_bid_price"] = _split_best(data.get("b", None))
    result["realtime"]["best_bid_volume"] = _split_best(data.get("g", None))
    result["realtime"]["best_ask_price"] = _split_best(data.get("a", None))
    result["realtime"]["best_ask_volume"] = _split_best(data.get("f", None))
    result["realtime"]["open"] = data.get("o", None)
    result["realtime"]["high"] = data.get("h", None)
    result["realtime"]["low"] = data.get("l", None)

    # Success fetching
    result["success"] = True

    return result


def _join_stock_id(stocks) -> str:
    if isinstance(stocks, list):
        return "|".join(
            [
                "{}_{}.tw".format("tse" if s in twstock.twse else "otc", s)
                for s in stocks
            ]
        )
    return "{}_{stock_id}.tw".format(
        "tse" if stocks in twstock.twse else "otc", stock_id=stocks
    )


def get_raw(stocks) -> dict:
    req = get_session()
    req.get(SESSION_URL, proxies=get_proxies())

    r = req.get(
        STOCKINFO_URL.format(
            stock_id=_join_stock_id(stocks), time=int(time.time()) * 1000
        )
    )

    if sys.version_info < (3, 5):
        try:
            return r.json()
        except ValueError:
            return {"rtmessage": "json decode error", "rtcode": "5000"}
    else:
        try:
            return r.json()
        except json.decoder.JSONDecodeError:
            return {"rtmessage": "json decode error", "rtcode": "5000"}


def _get_esb(stock_id: str) -> dict:
    if mock:
        return {
            "timestamp": 1780044900.0,
            "info": {
                "code": stock_id,
                "channel": f"{stock_id}.tw",
                "name": twstock.codes.get(stock_id).name if stock_id in twstock.codes else "模擬股",
                "fullname": twstock.esb_fullname.get(stock_id, "模擬股份有限公司"),
                "time": "2026/05/29 16:55"
            },
            "realtime": {
                "latest_trade_price": "100.00",
                "trade_volume": "1000",
                "accumulate_trade_volume": "50000",
                "open": "101.00",
                "high": "105.00",
                "low": "99.00",
                "best_bid_price": ["99.50", "99.00", "98.50", "98.00", "97.50"],
                "best_bid_volume": ["10", "20", "30", "40", "50"],
                "best_ask_price": ["100.50", "101.00", "101.50", "102.00", "102.50"],
                "best_ask_volume": ["10", "20", "30", "40", "50"]
            },
            "success": True
        }

    url = "https://mis.tpex.org.tw/Quote.asmx/GETQ20"
    session = get_session()
    try:
        r = session.post(url, data={"SymbolID": stock_id}, timeout=5, proxies=get_proxies())
        if r.status_code != 200:
            return {"rtmessage": "HTTP Error", "rtcode": str(r.status_code), "success": False}

        root = ET.fromstring(r.text)
        ns = "{http://otcq.daiphy.com/}"

        def get_val(tag, default=""):
            node = root.find(ns + tag)
            return node.text if node is not None else default

        symbol_id = get_val("SymbolID")
        if not symbol_id:
            return {"rtmessage": "Invalid Stock ID.", "rtcode": "5002", "success": False}

        symbol_name = get_val("SymbolName")
        trade_day = get_val("TradeDay")  # YYYY/MM/DD
        trade_time = get_val("TradeStatisticTime")  # HH:MM

        # Parse date and time to create timestamp
        try:
            dt_str = f"{trade_day} {trade_time}"
            dt = datetime.datetime.strptime(dt_str, "%Y/%m/%d %H:%M")
            timestamp = dt.timestamp()
        except Exception:
            timestamp = time.time()
            dt_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

        # Documented constraints:
        # 1. open: Set to TradeStatisticAverage (weighted average price).
        # 2. fullname: Look up in esb_fullname database. If not found, use SymbolName as a fallback.
        # 3. best_bid_price/volume & best_ask_price/volume (Scheme B):
        #    Parse all broker quotes in <quotesDetail>, sort, and take the top 5.
        fullname = twstock.esb_fullname.get(symbol_id, symbol_name)
        result = {
            "timestamp": timestamp,
            "info": {
                "code": symbol_id,
                "channel": f"{symbol_id}.tw",
                "name": symbol_name,
                "fullname": fullname,
                "time": dt_str
            },
            "realtime": {}
        }

        def to_float(val):
            if val and val != "--":
                try:
                    return float(val.replace(",", ""))
                except ValueError:
                    pass
            return None

        result["realtime"]["latest_trade_price"] = get_val("TradePrice")
        result["realtime"]["trade_volume"] = get_val("TradeVol")
        result["realtime"]["accumulate_trade_volume"] = get_val("TradeStatisticTtlVol")
        result["realtime"]["open"] = get_val("TradeStatisticAverage")  # Open is replaced by TradeStatisticAverage
        result["realtime"]["high"] = get_val("TradeStatisticHigh")
        result["realtime"]["low"] = get_val("TradeStatisticLow")

        # Parse quotesDetail for Scheme B (Issue 3)
        quotes_detail = root.find(ns + "quotesDetail")
        bids = []
        asks = []

        if quotes_detail is not None:
            for q in quotes_detail.findall(ns + "Q20QuotesDetail"):
                b_price_node = q.find(ns + "BuyPrice")
                b_vol_node = q.find(ns + "BuyVol")
                s_price_node = q.find(ns + "SellPrice")
                s_vol_node = q.find(ns + "SellVol")

                buy_price = to_float(b_price_node.text if b_price_node is not None else "")
                buy_vol = to_float(b_vol_node.text if b_vol_node is not None else "")
                sell_price = to_float(s_price_node.text if s_price_node is not None else "")
                sell_vol = to_float(s_vol_node.text if s_vol_node is not None else "")

                if buy_price and buy_price > 0 and buy_vol and buy_vol > 0:
                    bids.append((buy_price, int(buy_vol)))
                if sell_price and sell_price > 0 and sell_vol and sell_vol > 0:
                    asks.append((sell_price, int(sell_vol)))

        # Sort bids descending (highest first)
        bids.sort(key=lambda x: x[0], reverse=True)
        # Sort asks ascending (lowest first)
        asks.sort(key=lambda x: x[0])

        # Take top 5
        bids = bids[:5]
        asks = asks[:5]

        # Format price strings to 4 decimal places matching TWSE format
        result["realtime"]["best_bid_price"] = [f"{b[0]:.4f}" for b in bids]
        result["realtime"]["best_bid_volume"] = [str(b[1]) for b in bids]
        result["realtime"]["best_ask_price"] = [f"{a[0]:.4f}" for a in asks]
        result["realtime"]["best_ask_volume"] = [str(a[1]) for a in asks]

        result["success"] = True
        return result
    except Exception as e:
        return {"rtmessage": f"Error: {str(e)}", "rtcode": "5000", "success": False}


def get(stocks, retry=3):
    # Check if we are fetching a single ESB stock
    if isinstance(stocks, str) and stocks in twstock.esb:
        return _get_esb(stocks)

    # Check if we are fetching a list of stocks
    if isinstance(stocks, list):
        esb_stocks = [s for s in stocks if s in twstock.esb]
        non_esb_stocks = [s for s in stocks if s not in twstock.esb]

        result = {}
        # Fetch non-ESB stocks
        if non_esb_stocks:
            non_esb_data = get_raw(non_esb_stocks) if not mock else twstock.mock.get(non_esb_stocks)
            if non_esb_data.get("rtcode") == "5000" and retry:
                return get(stocks, retry - 1)
            if "msgArray" in non_esb_data and len(non_esb_data["msgArray"]):
                for item in non_esb_data["msgArray"]:
                    if "tlong" in item:
                        formatted = _format_stock_info(item)
                        result[formatted["info"]["code"]] = formatted

        # Fetch ESB stocks
        for s in esb_stocks:
            formatted = _get_esb(s)
            if formatted.get("success"):
                result[s] = formatted

        if not result:
            if non_esb_stocks and 'non_esb_data' in locals():
                non_esb_data["success"] = False
                if "rtmessage" not in non_esb_data:
                    non_esb_data["rtmessage"] = "Empty Query."
                    non_esb_data["rtcode"] = "5001"
                return non_esb_data
            return {"success": False, "rtmessage": "Empty Query.", "rtcode": "5001"}

        result["success"] = True
        return result

    # Prepare data
    data = get_raw(stocks) if not mock else twstock.mock.get(stocks)

    # Set success
    data["success"] = False

    # JSONdecode error, could be too fast, retry
    if data["rtcode"] == "5000":
        # XXX: Stupit retry, you will dead here
        if retry:
            return get(stocks, retry - 1)
        return data

    # No msgArray, dead
    if "msgArray" not in data:
        return data

    # Check have data
    if not len(data["msgArray"]):
        data["rtmessage"] = "Empty Query."
        data["rtcode"] = "5001"
        return data

    # Check if the response contains valid stock data
    if "tlong" not in data["msgArray"][0]:
        data["rtmessage"] = "Invalid Stock ID."
        data["rtcode"] = "5002"
        return data

    return _format_stock_info(data["msgArray"][0])

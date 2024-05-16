# -*- coding: utf-8 -*-

import json


TSE_2330_TW = [
    """{"msgArray": [{"tv": "-", "ps": "-", "pz": "-", "bp": "0", "a": "849.0000_850.0000_851.0000_852.0000_853.0000_", "b": "848.0000_847.0000_846.0000_845.0000_844.0000_", "c": "2330", "d": "20240516", "ch": "2330.tw", "tlong": "1715827494000", "f": "170_372_260_647_514_", "ip": "0", "g": "6_50_126_107_255_", "mt": "692836", "h": "856.0000", "i": "24", "it": "12", "l": "844.0000", "n": "\\u53f0\\u7a4d\\u96fb", "o": "852.0000", "p": "0", "ex": "tse", "s": "-", "t": "10:44:54", "u": "922.0000", "v": "23350", "w": "756.0000", "nf": "\\u53f0\\u7063\\u7a4d\\u9ad4\\u96fb\\u8def\\u88fd\\u9020\\u80a1\\u4efd\\u6709\\u9650\\u516c\\u53f8", "y": "839.0000", "z": "-", "ts": "0"}], "referer": "", "userDelay": 5000, "rtcode": "0000", "queryTime": {"sysDate": "20240516", "stockInfoItem": 2300, "stockInfo": 1107969, "sessionStr": "UserSession", "sysTime": "10:45:02", "showChart": false, "sessionFromTime": 1715827477731, "sessionLatestTime": 1715827477731}, "rtmessage": "OK", "exKey": "if_tse_2330.tw_zh-tw.null", "cachedAlive": 41360}""",
    """{"msgArray": [{"tv": "-", "ps": "-", "pz": "-", "bp": "0", "a": "848.0000_849.0000_850.0000_851.0000_852.0000_", "b": "847.0000_846.0000_845.0000_844.0000_843.0000_", "c": "2330", "d": "20240516", "ch": "2330.tw", "tlong": "1715827560000", "f": "53_157_370_261_945_", "ip": "0", "g": "42_124_116_271_187_", "mt": "826330", "h": "856.0000", "i": "24", "it": "12", "l": "844.0000", "n": "\\u53f0\\u7a4d\\u96fb", "o": "852.0000", "p": "0", "ex": "tse", "s": "-", "t": "10:46:00", "u": "922.0000", "v": "23384", "w": "756.0000", "nf": "\\u53f0\\u7063\\u7a4d\\u9ad4\\u96fb\\u8def\\u88fd\\u9020\\u80a1\\u4efd\\u6709\\u9650\\u516c\\u53f8", "y": "839.0000", "z": "-", "ts": "0"}], "referer": "", "userDelay": 5000, "rtcode": "0000", "queryTime": {"sysDate": "20240516", "stockInfoItem": 762, "stockInfo": 270448, "sessionStr": "UserSession", "sysTime": "10:46:02", "showChart": false, "sessionFromTime": 1715827446503, "sessionLatestTime": 1715827446503}, "rtmessage": "OK", "exKey": "if_tse_2330.tw_zh-tw.null", "cachedAlive": 17846}""",
    """{"msgArray": [{"tv": "-", "ps": "-", "pz": "-", "bp": "0", "a": "848.0000_849.0000_850.0000_851.0000_852.0000_", "b": "847.0000_846.0000_845.0000_844.0000_843.0000_", "c": "2330", "d": "20240516", "ch": "2330.tw", "tlong": "1715827579000", "f": "64_157_371_261_947_", "ip": "0", "g": "40_124_118_270_185_", "mt": "655374", "h": "856.0000", "i": "24", "it": "12", "l": "844.0000", "n": "\\u53f0\\u7a4d\\u96fb", "o": "852.0000", "p": "0", "ex": "tse", "s": "-", "t": "10:46:19", "u": "922.0000", "v": "23388", "w": "756.0000", "nf": "\\u53f0\\u7063\\u7a4d\\u9ad4\\u96fb\\u8def\\u88fd\\u9020\\u80a1\\u4efd\\u6709\\u9650\\u516c\\u53f8", "y": "839.0000", "z": "-", "ts": "0"}], "referer": "", "userDelay": 5000, "rtcode": "0000", "queryTime": {"sysDate": "20240516", "stockInfoItem": 2216, "stockInfo": 506844, "sessionStr": "UserSession", "sysTime": "10:46:25", "showChart": false, "sessionFromTime": -1, "sessionLatestTime": -1}, "rtmessage": "OK", "exKey": "if_tse_2330.tw_zh-tw.null", "cachedAlive": 21231}""",
]


stock_list = {
    "2330": TSE_2330_TW,
}


def get_stock_info(stock_id, index=0):
    return json.loads(stock_list[stock_id][index])


def get_stocks_info(stocks):
    data = json.loads(stock_list["2330"][0])
    for _ in range(len(stocks)):
        data["msgArray"].append(data["msgArray"][0])
    return data


def get(stocks):
    if isinstance(stocks, list):
        return get_stocks_info(stocks)
    return get_stock_info(stocks)

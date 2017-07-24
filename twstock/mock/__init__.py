# -*- coding: utf-8 -*-

import json


TSE_2330_TW = ["""
{"msgArray": [{"ts": "0", "tk0": "2330.tw_tse_20170724_B_9999778918", "tk1":
"2330.tw_tse_20170724_B_9999777950", "tlong": "1500860849000", "f":
"853_1193_972_1209_817_", "ex": "tse", "g": "1221_1530_817_1038_1193_", "d":
"20170724", "it": "12", "b": "214.00_213.50_213.00_212.50_212.00_", "c":
"2330", "mt": "264564", "a": "214.50_215.00_215.50_216.00_216.50_", "n":
"\u53f0\u7a4d\u96fb", "o": "213.50", "l": "213.00", "h": "214.50", "ip": "0",
"i": "24", "w": "193.00", "v": "5094", "u": "235.00", "t": "09:47:29", "s":
"1", "pz": "213.50", "tv": "1", "p": "0", "nf":
"\u53f0\u7063\u7a4d\u9ad4\u96fb\u8def\u88fd\u9020\u80a1\u4efd\u6709\u9650\u516c\u53f8",
"ch": "2330.tw",
"z": "214.50", "y": "214.00", "ps": "1323"}], "userDelay": 5000, "rtmessage":
"OK", "referer": "", "queryTime": {"sysTime": "09:47:30", "sessionLatestTime":
-1, "sysDate": "20170724", "sessionKey": "tse_2330.tw_20170724|",
"sessionFromTime": -1, "stockInfoItem": 2065, "showChart": false,
"sessionStr": "UserSession", "stockInfo": 204322}, "rtcode": "0000"}
""", """
{"msgArray": [{"ts": "0", "tk0": "2330.tw_tse_20170724_B_9999766224", "tk1":
"2330.tw_tse_20170724_B_9999765954", "tlong": "1500861105000", "f":
"1059_1079_1014_1229_907_", "ex": "tse", "g": "1455_1598_797_1019_1134_", "d":
"20170724", "it": "12", "b": "214.00_213.50_213.00_212.50_212.00_", "c":
"2330", "mt": "778472", "a": "214.50_215.00_215.50_216.00_216.50_", "n":
"\u53f0\u7a4d\u96fb", "o": "213.50", "l": "213.00", "h": "214.50", "ip": "0",
"i": "24", "w": "193.00", "v": "5217", "u": "235.00", "t": "09:51:45", "s":
"0", "pz": "213.50", "tv": "1", "p": "0", "nf":
"\u53f0\u7063\u7a4d\u9ad4\u96fb\u8def\u88fd\u9020\u80a1\u4efd\u6709\u9650\u516c\u53f8",
"ch": "2330.tw",
"z": "214.50", "y": "214.00", "ps": "1323"}], "userDelay": 5000, "rtmessage":
"OK", "referer": "", "queryTime": {"sysTime": "09:51:48", "sessionLatestTime":
-1, "sysDate": "20170724", "sessionKey": "tse_2330.tw_20170724|",
"sessionFromTime": -1, "stockInfoItem": 2055, "showChart": false,
"sessionStr": "UserSession", "stockInfo": 130895}, "rtcode": "0000"}
""", """
{"msgArray": [{"ts": "0", "tk0": "2330.tw_tse_20170724_B_9999760446", "tk1":
"2330.tw_tse_20170724_B_9999759382", "tlong": "1500861243000", "f":
"1034_1028_1009_1253_933_", "ex": "tse", "g": "1466_1625_798_987_1117_", "d":
"20170724", "it": "12", "b": "214.00_213.50_213.00_212.50_212.00_", "c":
"2330", "mt": "962863", "a": "214.50_215.00_215.50_216.00_216.50_", "n":
"\u53f0\u7a4d\u96fb", "o": "213.50", "l": "213.00", "h": "214.50", "ip": "0",
"i": "24", "w": "193.00", "v": "5268", "u": "235.00", "t": "09:54:03", "s":
"0", "pz": "213.50", "tv": "3", "p": "0", "nf":
"\u53f0\u7063\u7a4d\u9ad4\u96fb\u8def\u88fd\u9020\u80a1\u4efd\u6709\u9650\u516c\u53f8",
"ch": "2330.tw",
"z": "214.00", "y": "214.00", "ps": "1323"}], "userDelay": 5000, "rtmessage":
"OK", "referer": "", "queryTime": {"sysTime": "09:54:10", "sessionLatestTime":
-1, "sysDate": "20170724", "sessionKey": "tse_2330.tw_20170724|",
"sessionFromTime": -1, "stockInfoItem": 1602, "showChart": false,
"sessionStr": "UserSession", "stockInfo": 119518}, "rtcode": "0000"}
"""]


stock_list = {
    '2330': TSE_2330_TW,
}


def get_stock_info(stock_id, index=0):
    return json.loads(stock_list[stock_id][index])


def get_stocks_info(stocks):
    data = json.loads(stock_list['2330'][0])
    for _ in range(len(stocks)):
        data['msgArray'].append(data['msgArray'][0])
    return data

def get(stocks):
    if isinstance(stocks, list):
        return get_stocks_info(stocks)
    return get_stock_info(stocks)


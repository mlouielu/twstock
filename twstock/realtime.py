# -*- coding: utf-8 -*-

import datetime
import random
import json
import time
import requests


SESSION_URL = 'http://mis.twse.com.tw/stock/index.jsp'
STOCKINFO_URL = 'http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={stock_id}&_={time}'


def _format_stock_info(data):
    result = {
        'timestamp': 0.0,
        'info': {},
        'realtime': {}
    }

    # Timestamp
    result['timestamp'] = int(data['tlong']) / 1000

    # Information
    result['info']['code'] = data['c']
    result['info']['channel'] = data['ch']
    result['info']['name'] = data['n']
    result['info']['fullname'] = data['nf']
    result['info']['time'] = datetime.datetime.fromtimestamp(
        int(data['tlong']) / 1000).strftime('%Y-%m-%d %H:%M:%S')

    # Realtime information
    result['realtime']['latest_trade_price'] = data['z']
    result['realtime']['trade_volume'] = data['tv']
    result['realtime']['accumulate_trade_volume'] = data['v']
    result['realtime']['best_bid_price'] = data['b'].strip('_').split('_')
    result['realtime']['best_bid_volume'] = data['g'].strip('_').split('_')
    result['realtime']['best_ask_price'] = data['a'].strip('_').split('_')
    result['realtime']['best_ask_volume'] = data['f'].strip('_').split('_')
    result['realtime']['open'] = data['o']
    result['realtime']['high'] = data['h']
    result['realtime']['low'] = data['l']

    # Success fetching
    result['success'] = True

    return result


def _join_stock_id(stocks):
    if isinstance(stocks, list):
        return '|'.join(['tse_{}.tw'.format(s) for s in stocks])
    return 'tse_{stock_id}.tw'.format(stock_id=stocks)


def get_raw(stocks):
    req = requests.Session()
    req.get(SESSION_URL)

    r = req.get(
        STOCKINFO_URL.format(
            stock_id=_join_stock_id(stocks),
            time=int(time.time()) * 1000))
    try:
        return r.json()
    except json.decoder.JSONDecodeError:
        return {'rtmessage': 'json decode error', 'rtcode': '0001'}


def get(stocks, retry=3):
    data = get_raw(stocks)

    # Add success
    data['success'] = False

    if (data['rtcode'] == '0001' or
            data['rtcode'] != '0000' or
            'msgArray' not in data):
        # XXX: Stupit retry, you will dead here
        if retry:
            return get(stocks, retry - 1)
        return data

    # Return multiple stock data
    if isinstance(stocks, list):
        return list(map(_format_stock_info, data['msgArray']))

    return _format_stock_info(data['msgArray'][0])

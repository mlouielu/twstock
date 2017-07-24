# -*- coding: utf-8 -*-

import datetime
import json
import time
import requests
import twstock


SESSION_URL = 'http://mis.twse.com.tw/stock/index.jsp'
STOCKINFO_URL = 'http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={stock_id}&_={time}'

# Mock data
mock = False


def _format_stock_info(data) -> dict:
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


def _join_stock_id(stocks) -> str:
    if isinstance(stocks, list):
        return '|'.join(['{}_{}.tw'.format(
            'tse' if s in twstock.twse else 'otc', s) for s in stocks])
    return '{}_{stock_id}.tw'.format(
        'tse' if stocks in twstock.twse else 'otc', stock_id=stocks)


def get_raw(stocks) -> dict:
    req = requests.Session()
    req.get(SESSION_URL)

    r = req.get(
        STOCKINFO_URL.format(
            stock_id=_join_stock_id(stocks),
            time=int(time.time()) * 1000))

    try:
        return r.json()
    except json.decoder.JSONDecodeError:
        return {'rtmessage': 'json decode error', 'rtcode': '5000'}


def get(stocks, retry=3):
    if mock:
        if isinstance(stocks, list):
            data = twstock.mock.get_stocks_info(stocks)
        else:
            data = twstock.mock.get_stock_info(stocks)
    else:
        data = get_raw(stocks)

    # Set success
    data['success'] = False

    # JSONdecode error, could be too fast, retry
    if data['rtcode'] == '5000':
        # XXX: Stupit retry, you will dead here
        if retry:
            return get(stocks, retry - 1)
        return data

    # No msgArray, dead
    if 'msgArray' not in data:
        return data

    # Check have data
    if not len(data['msgArray']):
        data['rtmessage'] = 'Empty Query.'
        data['rtcode'] = '5001'
        return data

    # Return multiple stock data
    if isinstance(stocks, list):
        result = {
            stock_id: data for stock_id, data in zip(
                stocks, map(_format_stock_info, data['msgArray']))
        }
        result['success'] = True
        return result

    return _format_stock_info(data['msgArray'][0])

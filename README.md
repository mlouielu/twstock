[![Travis Build
Status](https://travis-ci.org/mlouielu/twstock.svg?branch=master)](https://travis-ci.org/mlouielu/twstock)
[![Appveyor Build Status](https://ci.appveyor.com/api/projects/status/d03c5laj01ap7qrt?svg=true)](https://ci.appveyor.com/project/mlouielu/twstock)
[![Coverage Status](https://coveralls.io/repos/github/mlouielu/twstock/badge.svg?branch=master)](https://coveralls.io/github/mlouielu/twstock?branch=master)
[![PyPI version](https://badge.fury.io/py/twstock.svg)](https://badge.fury.io/py/twstock)
[![Documentation Status](https://readthedocs.org/projects/twstock/badge/?version=latest)](http://twstock.readthedocs.io/zh_TW/latest/?badge=latest)


有任何問題歡迎透過 [Gitter.im](https://gitter.im/twstock/Lobby) 詢問。

twstock 台灣股市股票價格擷取
----------------------------

擷取台灣證券交易所之股價資料
重新製作 toomore/grs 之功能

資料來源:

* [證券交易所 (TWSE)](http://www.twse.com.tw)
* [證券櫃台買賣中心 (TPEX)](http://www.tpex.org.tw)

(請注意，TWSE 有 request limit, 每 5 秒鐘 3 個 request，超過的話會被 ban 掉，請自行注意)

## Documentation

* [twstock documentation (正體中文)](http://twstock.readthedocs.io/zh_TW/latest)

## Requirements

* requests
* Python 3

## Install

from pip (recommand):

```
$ pip install --user twstock

or

$ sudo pip install twstock
```

from GitHub:

```
$ git clone https://github.com/mlouielu/twstock
$ cd twstock
$ pip install flit  # If you didn't install flit before
$ flit install
```

## CLI Tools

```
$ twstock -b 2330 6223
四大買賣點判斷 Best Four Point
------------------------------
2330: Buy   量大收紅
6223: Sell  量縮價跌, 三日均價小於六日均價
```

```
$ twstock -s 2330 6223
-------------- 2330 ----------------
high : 215.0 214.0 210.0 210.5 208.5
low  : 212.0 211.0 208.0 208.5 206.5
price: 215.0 211.5 208.5 210.0 208.5
-------------- 2337 ----------------
high :  16.2  16.8  16.4 16.75 16.75
low  :  15.8  16.1 15.15  16.3 16.25
price: 15.95 16.25 16.25  16.6  16.7
```

## Update Codes

當你第一次使用 twstock 時，你可以更新 TPEX 跟 TWSE 的列表，可以使用兩種方式更新：

* By CLI

```
$ twstock -U
Start to update codes
Done!
```

* By Python

```
>>> import twstock
>>> twstock.__update_codes()
```

## Quick Start

分析計算

```python
from twstock import Stock

stock = Stock('2330')                             # 擷取台積電股價
ma_p = stock.moving_average(stock.price, 5)       # 計算五日均價
ma_c = stock.moving_average(stock.capacity, 5)    # 計算五日均量
ma_p_cont = stock.continuous(ma_p)                # 計算五日均價持續天數
ma_br = stock.ma_bias_ratio(5, 10)                # 計算五日、十日乖離值
```

擷取自 2015 年 1 月至今之資料

```python
stock = Stock('2330')
stock.fetch_from(2015, 1)
```

基本資料之使用

```python
>>> stock = Stock('2330')
>>> stock.price
[203.5, 203.0, 205.0, 205.0, 205.5, 207.0, 207.0, 203.0, 207.0, 209.0, 209.0, 212.0, 210.5, 211.5, 213.0, 212.0, 207.5, 208.0, 207.0, 208.0, 211.5, 213.0, 216.5, 215.5, 218.0, 217.0, 215.0, 211.5, 208.5, 210.0, 208.5]
>>> stock.capacity
[22490217, 17163108, 17419705, 23028298, 18307715, 26088748, 32976727, 67935145, 29623649, 23265323, 1535230, 22545164, 15382025, 34729326, 21654488, 35190159, 63111746, 49983303, 39083899, 19486457, 32856536, 17489571, 28784100, 45384482, 26094649, 39686091, 60140797, 44504785, 52273921, 27049234, 31709978]
>>> stock.data[0]
Data(date=datetime.datetime(2017, 5, 18, 0, 0), capacity=22490217, turnover=4559780051, open=202.5, high=204.0, low=201.5, close=203.5, change=-0.5, transaction=6983)
```


台股證券編碼

```python
>>> import twstock
>>> print(twstock.codes)                # 列印台股全部證券編碼資料
>>> print(twstock.codes['2330'])        # 列印 2330 證券編碼資料
StockCodeInfo(type='股票', code='2330', name='台積電', ISIN='TW0002330008', start='1994/09/05', market='上市', group='半導體業', CFI='ESVUFR')
>>> print(twstock.codes['2330'].name)   # 列印 2330 證券名稱
'台積電'
>>> print(twstock.codes['2330'].start)  # 列印 2330 證券上市日期
'1994/09/05'
```

使用 Proxy (基於 [requests proxies](https://2.python-requests.org/en/master/user/advanced/#proxies))

```python
# 單一 Proxy
>>> from twstock.proxy import SingleProxyProvider
>>> spr = SingleProxyProvider({'http': 'http://localhost:8080'})
>>> twstock.proxy.configure_proxy_provider(spr)

# 多個 Proxy
>>> from twstock.proxy import RoundRobinProxiesProvider
>>> proxies = [{'http': 'http://localhost:5000'}, {'http': 'http://localhost:5001'}]
>>> rrpr = RoundRobinProxiesProvider(proxies)
>>> twstock.proxy.configure_proxy_provider(rrpr)

# 變更 Proxy 表
>>> another_proxies = [{'http': 'http://localhost:8000'}, {'https': 'https://localhost:8001'}]
>>> rrpr.proxies = another_proxies
```


## 四大買賣點分析

```python
from twstock import Stock
from twstock import BestFourPoint

stock = Stock('2330')
bfp = BestFourPoint(stock)

bfp.best_four_point_to_buy()    # 判斷是否為四大買點
bfp.best_four_point_to_sell()   # 判斷是否為四大賣點
bfp.best_four_point()           # 綜合判斷
```

## 即時股票資訊查詢

```python
import twstock

twstock.realtime.get('2330')    # 擷取當前台積電股票資訊
twstock.realtime.get(['2330', '2337', '2409'])  # 擷取當前三檔資訊
```


## 使用範例

* [tw-stocker](https://github.com/mlouielu/stocker)

## Contributing

twstock was created by Louie Lu `<git@louie.lu>`.

Contributing were welcome, please use GitHub issue and Pull Request to contribute!

歡迎協作，請使用 GitHub issue 以及 Pull Request 功能來協作。

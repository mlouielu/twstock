[![Build 
Status](https://travis-ci.org/mlouielu/twstock.svg?branch=master)](https://travis-ci.org/mlouielu/twstock)
[![Coverage Status](https://coveralls.io/repos/github/mlouielu/twstock/badge.png?branch=master)](https://coveralls.io/github/mlouielu/twstock?branch=master)

twstock 台灣股市股票價格擷取
----------------------------

擷取台灣證券交易所之股價資料
重新製作 toomore/grs 之功能

資料來源:

* [證券交易所 (TWSE)](http://www.twse.com.tw)


## Requirements

* requests
* lxml

## Install

from GitHub:

```
$ git clone https://github.com/mlouielu/twstock
$ cd twstock
$ python setup.py install
```

## Quick Start

分析計算

```
from twstock import Stock

stock = Stock('2330')                             # 擷取台積電股價
ma_p = stock.moving_average(5, stock.price)       # 計算五日均價
ma_c = stock.moving_average(5, stock.capacity)    # 計算五日均量
ma_p_cont = stock.continuous(ma_p)                # 計算五日均價持續天數
ma_br = stock.ma_bias_ratio(5, 10)                # 計算五日、十日乖離值
```

擷取自 2015 年 1 月至今之資料

```
stock = Stock('2330')
stock.fetch_from(2015, 1)
```

基本資料之使用

```
>>> stock = Stock('2330')
>>> stock.price
[203.5, 203.0, 205.0, 205.0, 205.5, 207.0, 207.0, 203.0, 207.0, 209.0, 209.0, 212.0, 210.5, 211.5, 213.0, 212.0, 207.5, 208.0, 207.0, 208.0, 211.5, 213.0, 216.5, 215.5, 218.0, 217.0, 215.0, 211.5, 208.5, 210.0, 208.5]
>>> stock.capacity
[22490217, 17163108, 17419705, 23028298, 18307715, 26088748, 32976727, 67935145, 29623649, 23265323, 1535230, 22545164, 15382025, 34729326, 21654488, 35190159, 63111746, 49983303, 39083899, 19486457, 32856536, 17489571, 28784100, 45384482, 26094649, 39686091, 60140797, 44504785, 52273921, 27049234, 31709978]
>>> stock.data[0]
Data(date=datetime.datetime(2017, 5, 18, 0, 0), capacity=22490217, turnover=4559780051, open=202.5, high=204.0, low=201.5, close=203.5, ratio=-0.5, transaction=6983)
```

Data tuple 命名

```
date        = 日期
capacity    = 總成交股數
turnover    = 總成交金額
open        = 開盤價
high        = 最高價
low         = 最低價
close       = 收盤價
ratio       = 漲跌價差
transaction = 成交筆數
```

## 四大買賣點分析

```
from twstock import Stock
from twstock import BestFourPoint

stock = Stock('2330')
bfp = BestFourPoint(stock)

bfp.best_four_point_to_buy()    # 判斷是否為四大買點
bfp.best_four_point_to_sell()   # 判斷是否為四大賣點
bfp.best_four_point()           # 綜合判斷
```

## 使用範例

* [tw-stocker](https://github.com/mlouielu/stocker)

## Contributing

twstock was created by Louie Lu `<git@louie.lu>`.

Contributing were welcome, please use GitHub issue and Pull Request to contribute!

歡迎協作，請使用 GitHub issue 以及 Pull Request 功能來協作。

[![Build 
Status](https://travis-ci.org/mlouielu/twstock.svg?branch=master)](https://travis-ci.org/mlouielu/twstock)
[![Coverage Status](https://coveralls.io/repos/github/mlouielu/twstock/badge.svg?branch=master)](https://coveralls.io/github/mlouielu/twstock?branch=master)

twstock 台灣股市股票價格擷取
----------------------------

擷取台灣證券交易所之股價資料

資料來源:

* [證券交易所 (TWSE)](http://www.twse.com.tw)


## Requirements

* requests
* lxml

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

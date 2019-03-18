.. _quickstart:

*********
 快速上手
*********

下面將透過 Python REPL 來學習如何使用 ``twstock``。

更新 TPEX / TWSE Codes
======================

如果你是第一次使用 twstock，你可能會需要更新 TPEX/TWSE Codes。

你可以透過下面兩種方式更新:

以 CLI 更新::

  $ twstock -U

以 Python 更新::

  >>> import twstock
  >>> twstock.__update_codes()


認識 Stock
===========

在 twstock 之中，我們可以使用 :class:`.Stock` 來取得歷史股票資訊。

歷史資料
---------

舉例而言::

   >>> import twstock
   >>> stock = twstock.Stock('2330')
   >>> stock.sid  # 回傳股票代號
   '2330'
   >>> stock.price  # 回傳各日之收盤價
   [207.5, 208.0, 207.0, 208.0, 211.5, 213.0, 216.5, 215.5, 218.0,
    217.0, 215.0, 211.5, 208.5, 210.0, 208.5, 209.0, 207.0, 208.5,
    207.5, 206.0, 206.0, 212.0, 210.5, 214.5, 213.0, 213.0, 214.0,
    214.5, 215.5, 214.0, 214.5]
   >>> stock.high  # 回傳各日之最高價
   [210.0, 208.5, 209.5, 208.0, 212.0, 213.0, 218.0, 217.0, 218.0,
    218.5, 215.0, 214.0, 210.0, 210.5, 208.5, 209.0, 208.5, 208.5,
    208.5, 207.5, 207.0, 212.0, 212.5, 216.0, 214.5, 215.5, 214.0,
    215.0, 215.5, 215.0, 214.5]

在 :class:`.Stock` 之中的資料，愈前面之資料越舊，愈後面之資料愈新，可以透過
:attr:`date` 取得各個資料集之中相對應的日期::


   >>> stock.date  # 回傳資料之對應日期
   [datetime.datetime(2017, 6, 12, 0, 0),
    datetime.datetime(2017, 6, 13, 0, 0),
    datetime.datetime(2017, 6, 14, 0, 0),
    datetime.datetime(2017, 6, 15, 0, 0),
    ...,
    datetime.datetime(2017, 7, 21, 0, 0),
    datetime.datetime(2017, 7, 24, 0, 0)]

獲取其他日期之資料
-------------------

同時，:class:`.Stock` 預設建立時會取得近 31 日開盤之資料，如果需要其他日期之資料，可透過
不同之 fetch 功能獲得::

   >>> stock.fetch(2015, 7)  # 獲取 2015 年 7 月之股票資料
   >>> stock.fetch(2010, 5)  # 獲取 2010 年 5 月之股票資料
   >>> stock.fetch_31()      # 獲取近 31 日開盤之股票資料
   >>> stock.fetch_from(2000, 10)  # 獲取 2000 年 10 月至今日之股票資料


基本股票資訊分析
-----------------

:class:`.Stock` 內建基本股票分析功能，可以透過這些 method 來使用::

   >>> stock.moving_average(stock.price, 5)  # 計算五日平均價格
   [208.4, 209.5, 211.2, 212.9, 214.9, 216.0, 216.4, 215.4,
    214.0, 212.4, 210.7, 209.5, 208.6, 208.6, 208.1, 207.6,
    207.0, 208.0, 208.4, 209.8, 211.2, 212.6, 213.0, 213.8,
    214.0, 214.2, 214.5]
   >>> stock.moving_average(stock.capacity, 5)  # 計算五日平均交易量
   [40904388.2, 31779953.2, 27540112.6, 28800229.2, 30121867.6,
    31487778.6, 40018023.8, 43162160.8, 44540048.6, 44730965.6,
    43135743.0, 35320904.6, 30738402.0, 24976223.8, 22618522.2,
    20590067.6, 19042051.8, 21642392.4, 22327332.0, 29302556.6,
    29461849.0, 31076569.0, 27909064.6, 26663795.2, 20795579.4,
    19407173.2, 19127688.4]
   >>> stock.ma_bias_ratio(5, 10)  # 計算五日、十日乖離值
   [3.8000000000000114, 3.450000000000017, 2.0999999999999943,
    0.5500000000000114, -1.25, -2.6500000000000057,
    -3.4499999999999886, -3.4000000000000057, -2.700000000000017,
    -2.1500000000000057, -1.5500000000000114, -1.25,
    -0.30000000000001137, -0.09999999999999432,
    0.8500000000000227, 1.799999999999983, 2.799999999999983, 2.5,
    2.700000000000017, 2.0999999999999943, 1.5, 0.9499999999999886]


認識 BestFourPoint
==================

:class:`.BestFourPoint` 四大買賣點判斷來自 toomore/grs 之中的一個功能，
透過四大買賣點來判斷是否要買賣股票。四個買賣點分別為：

   * 量大收紅 / 量大收黑
   * 量縮價不跌 / 量縮價跌
   * 三日均價由下往上 / 三日均價由上往下
   * 三日均價大於六日均價 / 三日均價小於六日均價

使用範例如下::

   >>> stock = twstock.Stock('2330')
   >>> bfp = twstock.BestFourPoint(stock)
   >>> bfp.best_four_point_to_buy()   # 判斷是否為四大買點
   '量大收紅, 三日均價大於六日均價'
   >>> bfp.best_four_point_to_sell()  # 判斷是否為四大賣點
   False
   >>> bfp.best_four_point()          # 綜合判斷
   (True, '量大收紅, 三日均價大於六日均價')

.. note::

   ``BestFourPoint`` 是 ``Stock`` 的一層 wrapper，如果更動
   ``Stock`` 之資料，將會直接影響 ``BestFourPoint`` 之結果，請特別注意。


認識 realtime
===============

:mod:`realtime` 可以取得當前股票市場之即時資訊，可查詢上市以及上櫃之資料。
同時可以透過 :attr:`.realtime.mock` 來設定是否使用假資料。


取得單一股票之即時資料
----------------------

使用 :mod:`realtime` 取得台積電 (2330) 之即時股票資料::

   >>> import twstock
   >>> stock = twstock.realtime.get('2330')  # 查詢上市股票之即時資料
   {
      "timestamp": 1500877800.0,
      "info": {
         "code": "2330",
         "channel": "2330.tw",
         "name": "台積電",
         "fullname": "台灣積體電路製造股份有限公司",
         "time": "2017-07-24 14:30:00"
      },
      "realtime": {
         "latest_trade_price": "214.50",
         "trade_volume": "4437",
         "accumulate_trade_volume": "19955",
         "best_bid_price": [
               "214.00",
               "213.50",
               "213.00",
               "212.50",
               "212.00"
         ],
         "best_bid_volume": [
               "29",
               "1621",
               "2056",
               "1337",
               "1673"
         ],
         "best_ask_price": [
               "214.50",
               "215.00",
               "215.50",
               "216.00",
               "216.50"
         ],
         "best_ask_volume": [
               "736",
               "3116",
               "995",
               "1065",
               "684"
         ],
         "open": "213.50",
         "high": "214.50",
         "low": "213.00"
      },
      "success": true
   }
   >>> stock = twstock.realtime.get('6223')  # 查詢上櫃股票之即時資料
   >>> stock
   {'timestamp': 1500877800.0, 'info': {'code': '6223', 'channel': '6223.tw',
    'name': '旺矽', 'fullname': '旺矽科技股份有限公司', 'time': '2017-07-24 14:30:00'},
    'realtime': ..., 'success': True}


透過 `success` 確認資料之正確性
-------------------------------

使用 :mod:`realtime` 之資料時，需先確認 ``success`` 是否為 ``True``，
如果為 ``False`` 代表取得之資料有誤或是有錯誤產生，請再度參照 ``rtmessage``
取得錯誤訊息、``rtcode`` 取得錯誤代碼::

   >>> stock = twstock.realtime.get('2330')
   >>> stock['success']
   True
   >>> stock = twstock.realtime.get('')
   >>> stock['success']
   False
   >>> stock
   {'rtmessage': 'Information Data Not Found.', 'rtcode': '9999',
    'success': False}
   >>> stock = twstock.realtime.get('9999')
   >>> stock['success']
   False
   >>> stock
   {'msgArray': [], 'userDelay': 0, 'rtmessage': 'Empty Query.',
    'referer': '', 'queryTime': {'sysTime': '17:27:02',
   'sessionLatestTime': -1, 'sysDate': '20170724', 'sessionKey':
   'tse_9999.tw_20170724|', 'sessionFromTime': -1, 'stockInfoItem': 1719,
   'showChart': False, 'sessionStr': 'UserSession', 'stockInfo': 277019},
   'rtcode': '5001', 'success': False}

多股票即時資料查詢
------------------

:mod:`realtime` 支援多個股票同時查詢::

   >>> stocks = twstock.realtime.get(['2330', '2337', '2409'])
   >>> stocks['success']
   >>> stocks
   {'2330': {'timestamp': 1500877800.0, ..., 'success': True},
    '2337': {'timestamp': 1500877800.0, ..., 'success': True},
    '2409': {'timestamp': 1500877800.0, ..., 'success': True},
    'success': True}
   >>> stocks['2330']['success']
   True


使用 ``mock``
--------------

    >>> twstock.realtime.mock = True
    >>> twstock.realtime.get('2337')


認識 Codes
===========

:mod:`codes` 提供了台灣股票代號之查詢，分別為 :data:`codes.tpex`、:data:`codes.twse`、:data:`codes.codes`。


查詢代號是否為上市股票::

   >>> import twstock
   >>> '2330' in twstock.twse
   True
   >>> '6223' in twstock.twse
   False

查詢代號是否為上櫃股票::

   >>> '2330' in twstock.tpex
   False
   >>> '6223' in twstock.tpex
   True

查詢代號是否為台灣股票代號::

   >>> '2330' in twstock.codes
   True
   >>> '6223' in twstock.codes
   True


認識 Legacy
============

:mod:`Legacy` 用於初期自 ``toomore/grs`` 銜接驗證使用，包含兩組 grs 重要功能之驗證，
分別為 :class:`.LegacyAnalytics` 以及 :class:`.LegacyBestFourPoint`。


認識 CLI tools
================

``twstock`` 內建兩組 command line tools 可以使用，分別為查詢股票資訊以及四大買賣判斷之功能::

   $ twstock -s 2330 6223
   -------------- 2330 ----------------
   high : 215.0 214.0 210.0 210.5 208.5
   low  : 212.0 211.0 208.0 208.5 206.5
   price: 215.0 211.5 208.5 210.0 208.5
   -------------- 2337 ----------------
   high :  16.2  16.8  16.4 16.75 16.75
   low  :  15.8  16.1 15.15  16.3 16.25
   price: 15.95 16.25 16.25  16.6  16.7

   $ twstock -b 2330
   四大買賣點判斷 Best Four Point
   ------------------------------
   2330: Buy   量大收紅
   6223: Sell  量縮價跌, 三日均價小於六日均價

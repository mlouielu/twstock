.. _realtime:

:mod:`realtime` --- 即時股票資訊
===================================

.. module:: realtime

:mod:`realtime` 封裝了 `基本市況報導網站 <http://mis.twse.com.tw>`_ 的
即時股票資訊 API，透過 :meth:`get` 來取得相關股票即時資訊。

Attributes:

.. attribute:: mock

   透過 :attr:`mock` 來設定是否使用假資料::
   
      >>> twstock.realtime.mock = True   # 使用假資料
      >>> twstock.realtime.mock = False  # 使用正常資料

Methods:

.. method:: get(stocks)

   提供包裝後之股票即時資料。

   :param stocks:

      欲查詢之股票代號，多重搜尋請放入 ``list`` 之中::

         >>> realtime.get('2330')            # 單一查詢
         >>> realtime.get(['2330', '6223'])  # 多重查詢

   :type stocks:

      ``str`` or ``list[str]``

   :returns:  dict -- 回傳資料之格式如下

   單一代碼::

      >>> realtime.get('2330')
      {
         'timestamp': 1500877800.0,
         'info': {
            'code': '2330',
            'channel': '2330.tw'
            'name': '台積電',
            'fullname': '台灣積體電路製造股份有限公司',
            'time': '2017-07-24 14:30:00'
         },
         'realtime': {
            'latest_trade_price': '214.50',
            'trade_volume': '4437',
            'accumulate_trade_volume':'19955',
            'best_bid_price': ['214.00', '213.50', '213.00', '212.50', '212.00'],
            'best_bid_volume': ['29', '1621', '2056', '1337', '1673'],
            'best_ask_price': ['214.50', '215.00', '215.50', '216.00', '216.50'],
            'best_ask_volume': ['736', '3116', '995', '1065', '684'],
            'open': '213.50',
            'high': '214.50',
            'low': '213.00'
         },
         'success': True
      }

   多重代碼::

      >>> realtime.get(['2330', '2337'])
      {
         '2330': ...,
         '2337': ...,
         'success': True
      }

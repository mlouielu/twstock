:class:`Stock` --- 股票歷史資訊
=================================

.. class:: DATATUPLE(date, capacity, turnover, open, high, low, close, change, transaction)

   歷史資料之 `nametuple`。

   Attributes:

   .. attribute:: date

      ``datetime.datetime`` 格式之時間，例如 ``datetime.datetime(2017, 6, 12, 0, 0)``。

   .. attribute:: capacity

      總成交股數 (單位: 股)。

   .. attribute:: turnover

      總成交金額 (單位: 新台幣/元)。

   .. attribute:: open

      開盤價。

   .. attribute:: high
   
      盤中最高價

   .. attribute:: low

      盤中最低價。

   .. attribute:: close

      收盤價。
   
   .. attribute:: change

      漲跌價差。

   .. attribute:: transaction

      成交筆數。


.. class:: twstock.Stock(stock_id: str)

   有關股票歷史資訊 (開/收盤價，交易量，日期...etc) 以及簡易股票分析。
   建立 :class:`Stock` 實例時，會自動呼叫 :meth:`fetch_31` 抓取近 31 日
   之歷史股票資料。


   Class attributes are:

   .. attribute:: sid

      股票代號。

   .. attribute:: fetcher

      抓取方式之 instance，程式會自動判斷上櫃或上市，使用相對應之 fetcher。

   .. attribute:: raw_data

      經由 :class:`TWSEFetcher` 或是 :class:`TPEXFetcher` 抓取之原始資料。

   .. attribute:: data

      將 :attr:`raw_data` 透過 :class:`DATATUPLE` 處理之歷史股票資料。

   Fetcher method:

   .. method:: fetch(self, year: int, month: int)

      擷取該年、月份之歷史股票資料

   .. method:: fetch_from(self, year: int, month: int)

      擷取自該年、月至今日之歷史股票資料

   .. method:: fetch_31(self)

      擷取近 31 日開盤之歷史股票資料

   分析 method:

   .. method:: continuous(self, data)

      ``data`` 之持續上升天數

   .. method:: moving_average(self, days: int, data)

      ``data`` 之 ``days`` 日均數值

   .. method:: ma_bias_ratio(self, day1, day2)

      計算 ``day1`` 日以及 ``day2`` 之乖離值

   .. method:: ma_bias_ratio_pivot(self, data, sample_size=5, position=False)

      判斷正負乖離

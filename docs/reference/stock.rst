:class:`Stock` --- 股票歷史資訊
=================================

.. class:: twstock.Stock(stock_id: str)

   有關股票歷史資訊 (開/收盤價，交易量，日期...etc) 以及簡易股票分析。

   Attributes:

   .. attribute:: sid

      股票代號

   .. attribute:: fetcher

      抓取方式

   .. attribute:: raw_data

      原始資料

   .. attribute:: data

      data tuple list
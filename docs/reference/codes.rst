.. _codes:

:mod:`codes` -- 台灣股票代碼
==============================

.. module:: codes

:mod:`codes` 提供了台灣股票代碼的查詢功能，一般使用者並不會直接面對這個模組，
僅會透過 :attr:`twstock.codes`、:attr:`twstock.tpex`、:attr:`twstock.twse`
接觸已解析完成之代號。


.. class:: StockCodeInfo(type, code, name, ISIN, start, market, group, CFI)

    各股票代號之資訊

.. data:: codes

    台灣上市上櫃股票代號

.. data:: tpex

    台灣上櫃股票代號

.. data:: twse

    台灣上市股票代號

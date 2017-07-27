.. _prepare:

*********
 準備工作
*********

工欲善其事，必先利其器。在開始旅程之前，先讓我們準備好工作環境。
以下的步驟會將所需的環境準備好，請照著使用，謝謝。

.. note::

    twstock 要求需要 ``Python 3`` 以上之版本！

    強烈建議使用 Python 3，別管 Python 2 了。


快速安裝 twstock (透過 pip)
==============================

如果你想要快速安裝 `twstock`，可以透過 `pip` 來安裝::

    $ pip install --user twstock

如果想要安裝到所有使用者身上，請加上 `sudo`::

    $ sudo pip install twstock


取得 twstock 原始碼
=======================

``twstock`` 之原始碼存放於 `github <https://github.com/mlouielu/twstock>`_，你可以透過
``git clone`` 獲得原始碼，或是自上方 github 網頁下載。以下將示範如何透過 ``git clone`` 取得原始碼::

   $ git clone https://github.com/mlouielu/twstock
   $ cd twstock
   $ ls
   docs  flit.ini  LICENSE  MANIFEST.in  README.md  requirements.txt
   setup.py  test  twstock


手動安裝 twstock (透過原始碼)
===============================

取得原始碼後並且進入 `twstock` 之資料夾後，如果沒有安裝過 ``flit``，
請先透過 ``pip`` 安裝::

    $ pip install flit

接著透過 ``flit`` 即可安裝 `twstock`::

    $ flit install

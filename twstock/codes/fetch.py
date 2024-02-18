# -*- coding: utf-8 -*-
#
# Usage: Download all stock code info from TWSE
#
# TWSE equities = 上市證券
# TPEx equities = 上櫃證券
#

import os
import csv
from collections import namedtuple

from lxml import etree

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

TWSE_EQUITIES_URL = 'http://isin.twse.com.tw/isin/C_public.jsp?strMode=2'
TPEX_EQUITIES_URL = 'http://isin.twse.com.tw/isin/C_public.jsp?strMode=4'
ROW = namedtuple('Row', ['type', 'code', 'name', 'ISIN', 'start',
                         'market', 'group', 'CFI'])


def make_row_tuple(typ, row):
    code, name = row[1].split('\u3000')
    return ROW(typ, code, name, *row[2: -1])


def fetch_data(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 啟用無頭模式

    # 初始化Selenium WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 使用WebDriver先訪問主頁面，再訪問指定的URL
    main_page_url = "https://isin.twse.com.tw"
    driver.get(main_page_url)
    time.sleep(5)  # 等待JavaScript渲染完成
    driver.get(url)
    time.sleep(5)  # 等待JavaScript渲染完成

    # 獲取網頁的源代碼
    page_source = driver.page_source
    driver.quit()  # 關閉瀏覽器

    root = etree.HTML(page_source)
    trs = root.xpath('//tr')[1:]

    result = []
    typ = ''
    for tr in trs:
        tr = list(map(lambda x: x.text, tr.iter()))
        if len(tr) == 4:
            # This is type
            typ = tr[2].strip(' ')
        else:
            # This is the row data
            result.append(make_row_tuple(typ, tr))
    return result


def to_csv(url, path):
    data = fetch_data(url)
    with open(path, 'w', newline='', encoding='utf_8') as csvfile:
        writer = csv.writer(csvfile,
                            delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(data[0]._fields)
        for d in data:
            writer.writerow([_ for _ in d])


def __update_codes():
    def get_directory():
        return os.path.dirname(os.path.abspath(__file__))
    to_csv(TWSE_EQUITIES_URL, os.path.join(get_directory(), 'twse_equities.csv'))
    to_csv(TPEX_EQUITIES_URL, os.path.join(get_directory(), 'tpex_equities.csv'))


if __name__ == '__main__':
    to_csv(TWSE_EQUITIES_URL, 'twse_equities.csv')
    to_csv(TPEX_EQUITIES_URL, 'tpex_equities.csv')

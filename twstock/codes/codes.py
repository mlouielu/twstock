# -*- coding: utf-8 -*-
#
# Usage: Load all Taiwan stock code info from csv file
#
# TWSE equities = 上市證券
# TPEx equities = 上櫃證券
#

import csv
import os
from collections import namedtuple


ROW = namedtuple(
    "StockCodeInfo",
    ["type", "code", "name", "ISIN", "start", "market", "group", "CFI", "data_source"],
)
PACKAGE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
TPEX_EQUITIES_CSV_PATH = os.path.join(PACKAGE_DIRECTORY, "tpex_equities.csv")
TWSE_EQUITIES_CSV_PATH = os.path.join(PACKAGE_DIRECTORY, "twse_equities.csv")
ESB_EQUITIES_CSV_PATH = os.path.join(PACKAGE_DIRECTORY, "esb_equities.csv")
ESB_FULLNAME_JSON_PATH = os.path.join(PACKAGE_DIRECTORY, "esb_fullname.json")

codes = {}
tpex = {}
twse = {}
esb = {}
esb_fullname = {}

if os.path.exists(ESB_FULLNAME_JSON_PATH):
    import json
    try:
        with open(ESB_FULLNAME_JSON_PATH, encoding="utf-8") as f:
            esb_fullname = json.load(f)
    except Exception:
        pass


def read_csv(path, types):
    global codes, twse, tpex, esb
    with open(path, newline="", encoding="utf_8") as csvfile:
        reader = csv.reader(csvfile)
        csvfile.readline()
        for row in reader:
            row = ROW(*(item.strip() for item in row), data_source=types)
            codes[row.code] = row
            if types == "tpex":
                tpex[row.code] = row
            elif types == "esb":
                esb[row.code] = row
            else:
                twse[row.code] = row


read_csv(TPEX_EQUITIES_CSV_PATH, "tpex")
read_csv(TWSE_EQUITIES_CSV_PATH, "twse")
read_csv(ESB_EQUITIES_CSV_PATH, "esb")

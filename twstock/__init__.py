"""Taiwan Stock Opendata with realtime - twstock"""

import importlib.metadata

from twstock import stock
from twstock import analytics
from twstock import cli
from twstock import mock
from twstock import realtime

from twstock.analytics import BestFourPoint
from twstock.codes import __update_codes, twse, tpex, codes
from twstock.stock import Stock

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "1.4.0"

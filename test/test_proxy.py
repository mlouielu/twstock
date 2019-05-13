import unittest

from twstock.proxy import get_proxies, configure_proxy_provider, reset_proxy_provider
from twstock.proxy import SingleProxyProvider


class ProxyProviderTest(unittest.TestCase):

    def setUp(self):
        reset_proxy_provider()

    def tearDown(self):
        reset_proxy_provider()

    def test_configure(self):
        # default values are empty
        self.assertDictEqual({}, get_proxies())

        # configure fake proxy
        configure_proxy_provider(SingleProxyProvider(dict(http="http-proxy", https="https-proxy")))
        self.assertEqual("http-proxy", get_proxies()['http'])
        self.assertEqual("https-proxy", get_proxies()['https'])

        # reset proxy
        reset_proxy_provider()
        self.assertDictEqual({}, get_proxies())

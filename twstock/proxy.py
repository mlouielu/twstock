import abc
import ssl
from itertools import cycle

import requests


class _LegacyCertAdapter(requests.adapters.HTTPAdapter):
    """Adapter for TWSE/TPEX servers whose certificates are missing the
    Subject Key Identifier extension, rejected by Python 3.13+ VERIFY_X509_STRICT."""

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        if hasattr(ssl, "VERIFY_X509_STRICT"):
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


class ProxyProvider(abc.ABC):
    @abc.abstractmethod
    def get_proxy(self):
        return NotImplemented


class NoProxyProvier(ProxyProvider):
    def get_proxy(self):
        return {}


class SingleProxyProvider(ProxyProvider):
    def __init__(self, proxy=None):
        self._proxy = proxy

    def get_proxy(self):
        return self._proxy


class RoundRobinProxiesProvider(ProxyProvider):
    def __init__(self, proxies: list):
        self._proxies = proxies
        self._proxies_cycle = cycle(proxies)

    @property
    def proxies(self):
        return self._proxies

    @proxies.setter
    def proxies(self, proxies: list):
        if not isinstance(proxies, list):
            raise ValueError("Proxies only accept list")

        self._proxies = proxies
        self._proxies_cycle = cycle(proxies)

    def get_proxy(self):
        return next(self._proxies_cycle)


_provider_instance = NoProxyProvier()


def reset_proxy_provider():
    configure_proxy_provider(NoProxyProvier())


def configure_proxy_provider(provider_instance):
    global _provider_instance
    if not isinstance(provider_instance, ProxyProvider):
        raise BaseException("proxy provider should be a ProxyProvider object")
    _provider_instance = provider_instance


def get_proxies():
    return _provider_instance.get_proxy()


def get_session() -> requests.Session:
    session = requests.Session()
    session.mount("https://", _LegacyCertAdapter())
    session.mount("http://", _LegacyCertAdapter())
    return session

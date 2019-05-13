import abc


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

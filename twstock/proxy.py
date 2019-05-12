def _no_proxy_configurer():
    return {}


_provider = _no_proxy_configurer


def reset_proxy_provider():
    configure_proxy_provider(_no_proxy_configurer)


def configure_proxy_provider(provider_callback):
    global _provider
    if not callable(provider_callback):
        raise BaseException("proxy provider should be a callable type")
    _provider = provider_callback


def get_proxies():
    return _provider()

# -*- coding: utf-8 -*-
import ssl
import urllib.request

from mnemos import config


def ssl_context_for_https():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def github_urlopen(url, *, timeout, accept="application/octet-stream"):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"{config.APP_NAME}-Updater/1.0",
            "Accept": accept,
        },
    )
    return urllib.request.urlopen(
        req, timeout=timeout, context=ssl_context_for_https(),
    )

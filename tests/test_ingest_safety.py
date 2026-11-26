import socket

import pytest

from codemind.knowledge.ingest import _NoRedirectHandler, _validate_public_url


def test_only_https_is_accepted():
    with pytest.raises(ValueError, match="HTTPS"):
        _validate_public_url("http://docs.python.org/")


def test_localhost_is_rejected():
    with pytest.raises(ValueError, match="Local"):
        _validate_public_url("https://localhost/")


def test_private_dns_resolution_is_rejected(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.10", 443))],
    )
    with pytest.raises(ValueError, match="non-public"):
        _validate_public_url("https://example.test/")


def test_redirect_handler_does_not_follow_redirects():
    handler = _NoRedirectHandler()
    result = handler.redirect_request(None, None, 302, "Found", {}, "https://127.0.0.1/")
    assert result is None

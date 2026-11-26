"""Basic web-page ingestion for the prototype.

This is intentionally conservative. It rejects local/private destinations and only
accepts HTML-like responses. Production ingestion needs a hardened fetch service.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .library import KnowledgeItem, KnowledgeLibrary


class _NoRedirectHandler(HTTPRedirectHandler):
    """Do not follow redirects during prototype URL ingestion."""

    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._skip += 1
        elif tag.lower() in {"p", "div", "article", "section", "h1", "h2", "h3", "li", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            value = re.sub(r"\s+", " ", data).strip()
            if value:
                self.parts.append(value)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "\n".join(self.parts)).strip()


def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Only HTTPS URLs are accepted.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing embedded credentials are not allowed.")
    try:
        if parsed.port not in (None, 443):
            raise ValueError("Only the standard HTTPS port is allowed.")
    except ValueError as exc:
        raise ValueError("Invalid URL port.") from exc
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("Local destinations are not allowed.")
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve host: {host}") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("Private, loopback and non-public destinations are not allowed.")


def add_url(library: KnowledgeLibrary, url: str, *, tags: tuple[str, ...] = ()) -> KnowledgeItem:
    _validate_public_url(url)
    request = Request(url, headers={"User-Agent": "NKK-CodeMind/0.1 (+documentation research)"})
    opener = build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=12) as response:
            final_url = response.geturl()
            _validate_public_url(final_url)
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "text/plain" not in content_type:
                raise ValueError(f"Unsupported content type: {content_type or 'unknown'}")
            raw = response.read(2_000_001)
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError(f"Unable to retrieve URL: {exc}") from exc

    if len(raw) > 2_000_000:
        raise ValueError("Web page exceeds the 2 MB prototype limit.")
    decoded = raw.decode("utf-8", errors="replace")
    if "text/html" in content_type:
        parser = _TextExtractor()
        parser.feed(decoded)
        text = parser.text()
    else:
        text = decoded
    title_match = re.search(r"<title[^>]*>(.*?)</title>", decoded, re.I | re.S)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else url
    if not text:
        raise ValueError("No readable text was found at this URL.")
    return library.add_text(title, final_url, text, source_type="url", tags=tags)
import ipaddress
import socket
from datetime import UTC, datetime
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from app.core.errors import ExternalProviderError
from app.providers.base import RetrievedPage

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {None, 80, 443}
BLOCKED_HOST_SUFFIXES = (".internal", ".local", ".localhost")


class SafeHttpPageFetcher:
    def __init__(self, timeout_seconds: float, maximum_bytes: int) -> None:
        self._timeout = httpx.Timeout(timeout_seconds)
        self._maximum_bytes = maximum_bytes

    def fetch(self, url: str) -> RetrievedPage:
        current_url = url
        with httpx.Client(
            timeout=self._timeout,
            follow_redirects=False,
            headers={
                "User-Agent": "CompassIntelligenceBot/1.0 (+source research)",
                "Accept": "text/html,text/plain;q=0.9",
            },
        ) as client:
            for _redirect in range(4):
                validate_public_url(current_url)
                try:
                    with client.stream("GET", current_url) as response:
                        if response.status_code in {301, 302, 303, 307, 308}:
                            location = response.headers.get("location")
                            if not location:
                                raise ExternalProviderError(
                                    "Source redirect did not include a location"
                                )
                            current_url = urljoin(current_url, location)
                            continue
                        response.raise_for_status()
                        content_type = response.headers.get("content-type", "").split(";", 1)[0]
                        if content_type not in {"text/html", "text/plain", "application/xhtml+xml"}:
                            raise ExternalProviderError("Source content type is not supported")
                        declared_length = response.headers.get("content-length")
                        if declared_length and int(declared_length) > self._maximum_bytes:
                            raise ExternalProviderError(
                                "Source content exceeds the configured size limit"
                            )
                        body = bytearray()
                        for chunk in response.iter_bytes():
                            body.extend(chunk)
                            if len(body) > self._maximum_bytes:
                                raise ExternalProviderError(
                                    "Source content exceeds the configured size limit"
                                )
                        encoding = response.encoding or "utf-8"
                except (httpx.HTTPError, UnicodeError, ValueError) as error:
                    raise ExternalProviderError("Source page retrieval failed") from error
                return clean_retrieved_page(current_url, bytes(body), encoding, content_type)
        raise ExternalProviderError("Source redirected too many times")


def validate_public_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ExternalProviderError("Only HTTP and HTTPS source URLs are allowed")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ExternalProviderError("Source URL host is invalid")
    if parsed.port not in ALLOWED_PORTS:
        raise ExternalProviderError("Source URL port is not allowed")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(BLOCKED_HOST_SUFFIXES):
        raise ExternalProviderError("Private or internal source URLs are blocked")
    try:
        addresses = socket.getaddrinfo(hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise ExternalProviderError("Source host could not be resolved") from error
    if not addresses:
        raise ExternalProviderError("Source host did not resolve to an address")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ExternalProviderError("Private or internal source URLs are blocked")


def clean_retrieved_page(
    url: str,
    body: bytes,
    encoding: str,
    content_type: str,
) -> RetrievedPage:
    text = body.decode(encoding, errors="replace")
    parsed = urlsplit(url)
    if content_type == "text/plain":
        title = parsed.path.rsplit("/", 1)[-1] or parsed.hostname or "Source"
        content = " ".join(text.split())
    else:
        soup = BeautifulSoup(text, "html.parser")
        for element in soup(["script", "style", "noscript", "svg", "nav", "footer", "form"]):
            element.decompose()
        title = soup.title.get_text(" ", strip=True) if soup.title else parsed.hostname or "Source"
        container = soup.find("main") or soup.find("article") or soup.body or soup
        content = "\n".join(
            line
            for line in (part.strip() for part in container.get_text("\n").splitlines())
            if line
        )
    return RetrievedPage(
        url=url,
        title=title[:1000],
        content=content[:250_000],
        retrieved_at=datetime.now(UTC),
        publisher=parsed.hostname or "unknown",
        content_type=content_type,
    )

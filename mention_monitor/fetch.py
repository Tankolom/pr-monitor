from __future__ import annotations

import gzip
import html
import json
import re
import urllib.parse
import urllib.error
import urllib.request
from html.parser import HTMLParser


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text:
                self.parts.append(text)


def fetch_url(url: str, user_agent: str, timeout: int = 12) -> tuple[str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            encoding = response.headers.get_content_charset() or "utf-8"
            if response.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        encoding = exc.headers.get_content_charset() or "utf-8"
        if exc.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        detail = raw.decode(encoding, errors="replace")[:1200]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    return raw.decode(encoding, errors="replace"), content_type


def post_json(url: str, payload: dict, user_agent: str, headers: dict | None = None, timeout: int = 20) -> tuple[str, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request_headers = {
        "User-Agent": user_agent,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip",
    }
    request_headers.update(headers or {})
    request = urllib.request.Request(url, data=body, headers=request_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            encoding = response.headers.get_content_charset() or "utf-8"
            if response.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        encoding = exc.headers.get_content_charset() or "utf-8"
        if exc.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        detail = raw.decode(encoding, errors="replace")[:1200]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    return raw.decode(encoding, errors="replace"), content_type


def strip_html(markup: str) -> str:
    parser = TextExtractor()
    parser.feed(markup or "")
    text = html.unescape(" ".join(parser.parts))
    return re.sub(r"\s+", " ", text).strip()


def clean_html_fragment(fragment: str) -> str:
    return strip_html(fragment or "")


def extract_title(markup: str, fallback_url: str = "") -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", markup or "", flags=re.I | re.S)
    if match:
        return clean_html_fragment(match.group(1))
    parsed = urllib.parse.urlparse(fallback_url)
    return parsed.netloc or fallback_url


def extract_description(markup: str) -> str:
    patterns = [
        r'<meta[^>]+name=["\\\']description["\\\'][^>]+content=["\\\'](.*?)["\\\']',
        r'<meta[^>]+property=["\\\']og:description["\\\'][^>]+content=["\\\'](.*?)["\\\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, markup or "", flags=re.I | re.S)
        if match:
            return clean_html_fragment(match.group(1))
    return ""

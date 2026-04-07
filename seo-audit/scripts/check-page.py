#!/usr/bin/env python3
"""
Page-level SEO checks: H1, title tag, meta description, and canonical.
Uses Python stdlib html.parser — no BeautifulSoup required.
Outputs structured JSON to stdout for direct agent consumption.

Usage:
    python check-page.py https://example.com
    python check-page.py https://example.com --timeout 20

Output example (JSON):
    {
      "url": "https://example.com/",
      "final_url": "https://example.com/",
      "http_status": 200,
      "redirect_chain": [],
      "h1": {
        "status": "pass",
        "count": 1,
        "values": ["Best Running Shoes 2025"],
        "detail": "Single H1 found."
      },
      "title": {
        "status": "pass",
        "value": "Best Running Shoes 2025 | Free Shipping",
        "length": 42,
        "detail": "Title is 42 characters — within recommended range (50-60)."
      },
      "meta_description": {
        "status": "pass",
        "value": "Shop the best running shoes...",
        "length": 138,
        "detail": "Meta description is 138 characters — within recommended range (120-160)."
      },
      "canonical": {
        "status": "pass",
        "value": "https://example.com/",
        "matches_final_url": true,
        "detail": "Self-referencing canonical present."
      }
    }

Dependencies:
    pip install requests
    (HTML parsing uses Python stdlib html.parser — no extra packages needed)
"""

import argparse
import ipaddress
import json
import socket
import sys
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


# ── HTTP fetch ────────────────────────────────────────────────────────────────

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 ClaudeSEO/1.2"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}


def _fetch(url: str, timeout: int) -> tuple[Optional[int], Optional[str], str, list[dict], Optional[str]]:
    """
    Fetch a page with SSRF protection.
    Returns (status_code, content, final_url, redirect_chain, error).
    """
    parsed = urlparse(url)

    # SSRF protection: block private, loopback, and reserved IPs
    try:
        hostname = parsed.hostname or ""
        resolved_ip = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(resolved_ip)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            return None, None, url, [], f"Blocked: resolves to private IP ({resolved_ip})"
    except (socket.gaierror, ValueError):
        pass

    try:
        session = requests.Session()
        session.max_redirects = 5
        resp = session.get(url, headers=_DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
        redirect_chain = [
            {"url": r.url, "status_code": r.status_code} for r in resp.history
        ]
        return resp.status_code, resp.text, resp.url, redirect_chain, None
    except requests.exceptions.Timeout:
        return None, None, url, [], f"Timed out after {timeout}s"
    except requests.exceptions.TooManyRedirects:
        return None, None, url, [], "Too many redirects (max 5)"
    except requests.exceptions.SSLError as e:
        return None, None, url, [], f"SSL error: {e}"
    except requests.exceptions.ConnectionError as e:
        return None, None, url, [], f"Connection error: {e}"
    except requests.exceptions.RequestException as e:
        return None, None, url, [], f"Request failed: {e}"


# ── HTML parser (stdlib, no external dependencies) ────────────────────────────

class _SEOParser(HTMLParser):
    """
    Lightweight SEO element extractor.
    Extracts <title>, <h1>, <meta name="description">, and <link rel="canonical">.
    Does not build a full DOM tree — single-pass scan only.
    """

    def __init__(self) -> None:
        super().__init__()
        # title state
        self.title: Optional[str] = None
        self._in_title = False
        self._title_buf = ""
        # h1 state
        self.h1_values: list[str] = []
        self._in_h1 = False
        self._h1_depth = 0  # tracks nesting depth to handle inline tags inside <h1>
        self._h1_buf = ""
        # meta description
        self.meta_description: Optional[str] = None
        # canonical
        self.canonical: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}

        if tag == "title" and self.title is None:
            self._in_title = True
            self._title_buf = ""

        elif tag == "h1":
            self._in_h1 = True
            self._h1_depth += 1
            self._h1_buf = ""

        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            if name == "description" and self.meta_description is None:
                self.meta_description = attrs_dict.get("content", "")

        elif tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            if "canonical" in rel and self.canonical is None:
                self.canonical = attrs_dict.get("href", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = self._title_buf.strip() or None

        elif tag == "h1" and self._in_h1:
            self._h1_depth -= 1
            if self._h1_depth <= 0:
                self._in_h1 = False
                self._h1_depth = 0
                text = self._h1_buf.strip()
                if text:
                    self.h1_values.append(text)

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_buf += data
        if self._in_h1:
            self._h1_buf += data


# ── Check functions ───────────────────────────────────────────────────────────

def _check_h1(h1_values: list[str]) -> dict:
    """H1 uniqueness check: exactly one H1 required, must be non-empty."""
    count = len(h1_values)
    if count == 0:
        return {
            "status": "fail",
            "count": 0,
            "values": [],
            "detail": "No H1 tag found. Every page should have exactly one H1.",
        }
    if count == 1:
        return {
            "status": "pass",
            "count": 1,
            "values": h1_values,
            "detail": f'Single H1 found: "{h1_values[0]}".',
        }
    # Multiple H1s
    return {
        "status": "fail",
        "count": count,
        "values": h1_values,
        "detail": (
            f"{count} H1 tags found. Multiple H1s dilute heading hierarchy "
            f"and make it harder for crawlers to identify the primary topic."
        ),
    }


def _check_title(title: Optional[str]) -> dict:
    """Title tag check: presence and length (recommended 50-60 characters)."""
    if not title:
        return {
            "status": "fail",
            "value": None,
            "length": 0,
            "detail": "No <title> tag found. Title is a critical on-page SEO element.",
        }

    length = len(title)
    # Length thresholds: <10 = likely placeholder, >60 = truncation risk, <50 = underutilized
    if length < 10:
        status = "warn"
        note = f"Title is only {length} characters — likely a placeholder or too short."
    elif length > 60:
        status = "warn"
        note = f"Title is {length} characters — may be truncated in SERPs (recommended <= 60)."
    elif length < 50:
        status = "warn"
        note = f"Title is {length} characters — slightly short (recommended 50-60)."
    else:
        status = "pass"
        note = f"Title is {length} characters — within recommended range (50-60)."

    return {
        "status": status,
        "value": title,
        "length": length,
        "detail": note,
    }


def _check_meta_description(meta_desc: Optional[str]) -> dict:
    """Meta description check: presence and length (recommended 120-160 characters)."""
    if meta_desc is None:
        return {
            "status": "fail",
            "value": None,
            "length": 0,
            "detail": "No <meta name='description'> found. Missing meta descriptions reduce SERP snippet quality.",
        }

    # Tag present but content is empty
    if not meta_desc.strip():
        return {
            "status": "warn",
            "value": "",
            "length": 0,
            "detail": "Meta description tag present but content is empty.",
        }

    length = len(meta_desc)
    if length < 70:
        status = "warn"
        note = f"Meta description is {length} characters — too short (recommended 120-160)."
    elif length > 160:
        status = "warn"
        note = f"Meta description is {length} characters — may be truncated in SERPs (recommended <= 160)."
    elif length < 120:
        status = "warn"
        note = f"Meta description is {length} characters — slightly short (recommended 120-160)."
    else:
        status = "pass"
        note = f"Meta description is {length} characters — within recommended range (120-160)."

    return {
        "status": status,
        "value": meta_desc,
        "length": length,
        "detail": note,
    }


def _check_canonical(canonical: Optional[str], final_url: str) -> dict:
    """Canonical tag check: presence and whether it points to the correct URL."""
    if not canonical:
        return {
            "status": "warn",
            "value": None,
            "matches_final_url": False,
            "detail": (
                "No <link rel='canonical'> found. "
                "Without a canonical tag, duplicate content issues may arise."
            ),
        }

    # Normalize comparison by stripping trailing slashes
    canonical_norm = canonical.rstrip("/")
    final_norm = final_url.rstrip("/")
    matches = canonical_norm == final_norm

    if matches:
        return {
            "status": "pass",
            "value": canonical,
            "matches_final_url": True,
            "detail": "Self-referencing canonical present.",
        }

    # Canonical points to a different URL — may be cross-domain canonical or misconfiguration
    return {
        "status": "warn",
        "value": canonical,
        "matches_final_url": False,
        "detail": (
            f"Canonical points to a different URL: {canonical}. "
            f"Final page URL is: {final_url}. "
            "Verify this is intentional (cross-domain canonical) and not a misconfiguration."
        ),
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run page-level SEO checks (H1, title, meta description, canonical) and output JSON."
    )
    parser.add_argument("url", help="Target page URL")
    parser.add_argument("--timeout", "-t", type=int, default=20, help="Request timeout in seconds")
    args = parser.parse_args()

    url = args.url
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    status_code, content, final_url, redirect_chain, error = _fetch(url, args.timeout)

    base_result: dict = {
        "url": url,
        "final_url": final_url,
        "http_status": status_code,
        "redirect_chain": redirect_chain,
    }

    if error:
        base_result["error"] = error
        print(json.dumps(base_result, indent=2, ensure_ascii=False))
        sys.exit(1)

    if status_code != 200:
        base_result["error"] = f"Page returned HTTP {status_code} — cannot perform on-page checks."
        print(json.dumps(base_result, indent=2, ensure_ascii=False))
        sys.exit(1)

    if not content:
        base_result["error"] = "Page returned empty body."
        print(json.dumps(base_result, indent=2, ensure_ascii=False))
        sys.exit(1)

    # Parse HTML and run all checks
    seo_parser = _SEOParser()
    seo_parser.feed(content)

    output = {
        **base_result,
        "h1": _check_h1(seo_parser.h1_values),
        "title": _check_title(seo_parser.title),
        "meta_description": _check_meta_description(seo_parser.meta_description),
        "canonical": _check_canonical(seo_parser.canonical, final_url),
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))

    # Exit with code 1 if any check is fail
    has_failure = any(
        output[key]["status"] == "fail"
        for key in ("h1", "title", "meta_description", "canonical")
    )
    sys.exit(1 if has_failure else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Site-level SEO checks: robots.txt and sitemap.xml.
Outputs structured JSON to stdout so the agent can consume results directly
without needing to interpret raw HTTP responses or parse formats manually.

Usage:
    python check-site.py https://example.com
    python check-site.py https://example.com --timeout 15

Output example (JSON):
    {
      "origin": "https://example.com",
      "robots": {
        "status": "pass",
        "http_status": 200,
        "disallow_all": false,
        "googlebot_blocked": false,
        "sitemap_directive": "https://example.com/sitemap.xml",
        "detail": "robots.txt found. No critical blocking rules detected."
      },
      "sitemap": {
        "status": "pass",
        "http_status": 200,
        "url_count": 42,
        "is_index": false,
        "detail": "sitemap.xml found with 42 URLs."
      }
    }

Dependencies:
    pip install requests
"""

import argparse
import ipaddress
import json
import re
import socket
import sys
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


# Same UA as fetch-page.py for consistent request fingerprinting
_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 ClaudeSEO/1.2"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}


def _safe_fetch(url: str, timeout: int) -> tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Internal helper: fetch a URL safely with SSRF protection.
    Returns (status_code, content, error_message).
    """
    parsed = urlparse(url)

    # SSRF protection: block private, loopback, and reserved IPs
    try:
        hostname = parsed.hostname or ""
        resolved_ip = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(resolved_ip)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            return None, None, f"Blocked: resolves to private IP ({resolved_ip})"
    except (socket.gaierror, ValueError):
        pass

    try:
        resp = requests.get(url, headers=_DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
        return resp.status_code, resp.text, None
    except requests.exceptions.Timeout:
        return None, None, f"Timed out after {timeout}s"
    except requests.exceptions.SSLError as e:
        return None, None, f"SSL error: {e}"
    except requests.exceptions.ConnectionError as e:
        return None, None, f"Connection error: {e}"
    except requests.exceptions.RequestException as e:
        return None, None, f"Request failed: {e}"


def check_robots(origin: str, timeout: int) -> dict:
    """
    Check robots.txt for:
    - Accessibility (HTTP 200)
    - Disallow: / or Disallow: /* (full-site blocking)
    - Googlebot-specific blocking
    - Sitemap: directive presence
    """
    url = f"{origin}/robots.txt"
    status_code, content, error = _safe_fetch(url, timeout)

    result: dict = {
        "status": "error",
        "http_status": status_code,
        "disallow_all": False,
        "googlebot_blocked": False,
        "sitemap_directive": None,
        "detail": "",
    }

    if error:
        result["detail"] = f"Fetch error: {error}"
        return result

    if status_code != 200:
        result["status"] = "fail"
        result["detail"] = f"robots.txt returned HTTP {status_code}. File may not exist or is inaccessible."
        return result

    if not content:
        result["status"] = "warn"
        result["detail"] = "robots.txt returned HTTP 200 but body is empty."
        return result

    # Parse robots.txt directives line by line
    current_agents: list[str] = []
    disallow_all_agents: list[str] = []
    googlebot_blocked = False
    sitemap_directive: Optional[str] = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            continue

        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()

        if key == "user-agent":
            current_agents = [a.strip().lower() for a in value.split(",")]
        elif key == "disallow":
            # Disallow: / or Disallow: /* means the entire site is blocked
            if value in ("/", "/*"):
                disallow_all_agents.extend(current_agents)
        elif key == "sitemap":
            sitemap_directive = value

    # Determine if all crawlers or specifically Googlebot is blocked
    if "*" in disallow_all_agents or "googlebot" in disallow_all_agents:
        result["disallow_all"] = True
    if "googlebot" in disallow_all_agents:
        googlebot_blocked = True

    result["googlebot_blocked"] = googlebot_blocked
    result["sitemap_directive"] = sitemap_directive

    # Collect issues and set final status
    issues: list[str] = []
    if result["disallow_all"]:
        issues.append("Disallow: / detected — entire site may be blocked from crawling.")
    if googlebot_blocked:
        issues.append("Googlebot is explicitly blocked.")
    if not sitemap_directive:
        issues.append("No Sitemap: directive found in robots.txt.")

    if googlebot_blocked or result["disallow_all"]:
        result["status"] = "fail"
    elif issues:
        result["status"] = "warn"
    else:
        result["status"] = "pass"

    if issues:
        result["detail"] = " ".join(issues)
    else:
        sitemap_note = f" Sitemap directive: {sitemap_directive}." if sitemap_directive else ""
        result["detail"] = f"robots.txt found. No critical blocking rules detected.{sitemap_note}"

    return result


def check_sitemap(origin: str, timeout: int) -> dict:
    """
    Check sitemap.xml for:
    - Accessibility (HTTP 200)
    - Valid XML structure
    - Whether it is a sitemap index or a regular urlset
    - Number of <url> or <sitemap> entries
    """
    url = f"{origin}/sitemap.xml"
    status_code, content, error = _safe_fetch(url, timeout)

    result: dict = {
        "status": "error",
        "http_status": status_code,
        "url_count": 0,
        "is_index": False,
        "detail": "",
    }

    if error:
        result["detail"] = f"Fetch error: {error}"
        return result

    if status_code == 404:
        result["status"] = "fail"
        result["detail"] = (
            "sitemap.xml not found at /sitemap.xml (HTTP 404). "
            "Check robots.txt Sitemap: directive for alternate paths."
        )
        return result

    if status_code != 200:
        result["status"] = "warn"
        result["detail"] = f"sitemap.xml returned HTTP {status_code}."
        return result

    if not content:
        result["status"] = "fail"
        result["detail"] = "sitemap.xml returned HTTP 200 but body is empty."
        return result

    # Attempt XML parse
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        result["status"] = "fail"
        result["detail"] = f"sitemap.xml is not valid XML: {e}"
        return result

    # Strip XML namespace prefix for tag matching
    tag = re.sub(r"\{.*?\}", "", root.tag).lower()

    if tag == "sitemapindex":
        # This is a sitemap index file — count child <sitemap> entries
        result["is_index"] = True
        child_count = sum(
            1 for child in root
            if re.sub(r"\{.*?\}", "", child.tag).lower() == "sitemap"
        )
        result["url_count"] = child_count
        result["status"] = "pass" if child_count > 0 else "warn"
        result["detail"] = (
            f"Sitemap index found with {child_count} child sitemap(s)."
            if child_count > 0
            else "Sitemap index found but contains no child sitemaps."
        )
    elif tag == "urlset":
        # Standard sitemap — count <url> entries
        url_count = sum(
            1 for child in root
            if re.sub(r"\{.*?\}", "", child.tag).lower() == "url"
        )
        result["url_count"] = url_count
        result["status"] = "pass" if url_count > 0 else "warn"
        result["detail"] = (
            f"sitemap.xml found with {url_count} URL(s)."
            if url_count > 0
            else "sitemap.xml found but contains no <url> entries."
        )
    else:
        # Unexpected root element — possibly a custom format
        result["status"] = "warn"
        result["detail"] = f"sitemap.xml has unexpected root element: <{tag}>."

    return result


def normalize_origin(url: str) -> str:
    """Extract the origin (scheme + host) from a URL for constructing robots.txt and sitemap paths."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run site-level SEO checks (robots.txt + sitemap.xml) and output JSON."
    )
    parser.add_argument("url", help="Target URL or domain (e.g. https://example.com)")
    parser.add_argument("--timeout", "-t", type=int, default=15, help="Request timeout in seconds")
    args = parser.parse_args()

    origin = normalize_origin(args.url)

    robots_result = check_robots(origin, args.timeout)
    sitemap_result = check_sitemap(origin, args.timeout)

    output = {
        "origin": origin,
        "robots": robots_result,
        "sitemap": sitemap_result,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))

    # Exit with code 1 if any check is fail or error — useful for CI integration
    has_failure = any(
        r["status"] in ("fail", "error") for r in [robots_result, sitemap_result]
    )
    sys.exit(1 if has_failure else 0)


if __name__ == "__main__":
    main()

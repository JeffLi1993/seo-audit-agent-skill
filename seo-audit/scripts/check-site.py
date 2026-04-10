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


def _parse_robots_groups(content: str) -> tuple[list[dict], list[str]]:
    """
    Parse robots.txt into directive groups per RFC 9309.
    Consecutive User-Agent lines merge into one group.
    Returns (groups, sitemap_directives).
    """
    groups: list[dict] = []
    current_group: Optional[dict] = None
    prev_key = ""
    sitemap_directives: list[str] = []

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
            if prev_key == "user-agent" and current_group is not None:
                current_group["agents"].append(value.lower())
            else:
                current_group = {
                    "agents": [value.lower()],
                    "allow": [],
                    "disallow": [],
                }
                groups.append(current_group)
            prev_key = "user-agent"
        elif key in ("allow", "disallow") and current_group is not None:
            if value:
                current_group[key].append(value)
            prev_key = key
        elif key == "sitemap":
            if value:
                sitemap_directives.append(value)
            prev_key = key
        else:
            prev_key = key

    return groups, sitemap_directives


def _group_blocks_all(group: dict) -> bool:
    """
    Check if a group fully blocks the site.
    Disallow: / alone blocks everything, but Allow: sub-paths means partial access.
    Per RFC 9309, the most specific (longest) matching rule wins.
    """
    has_root_block = any(rule in ("/", "/*") for rule in group.get("disallow", []))
    if not has_root_block:
        return False
    # Allow rules for sub-paths override the root block → not a full block
    has_allow = any(r and r != "/" for r in group.get("allow", []))
    return not has_allow


def _find_group_for_agent(groups: list[dict], agent: str) -> Optional[dict]:
    """Find the group matching a specific user agent name."""
    agent_lower = agent.lower()
    for group in groups:
        if agent_lower in group["agents"]:
            return group
    return None


def check_robots(origin: str, timeout: int) -> dict:
    """
    Check robots.txt with RFC 9309-compliant group parsing.
    Handles Allow overrides, multi-agent groups, and multiple Sitemap directives.
    """
    url = f"{origin}/robots.txt"
    status_code, content, error = _safe_fetch(url, timeout)

    result: dict = {
        "status": "error",
        "http_status": status_code,
        "disallow_all": False,
        "googlebot_blocked": False,
        "sitemap_directives": [],
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

    groups, sitemap_directives = _parse_robots_groups(content)
    result["sitemap_directives"] = sitemap_directives
    result["sitemap_directive"] = sitemap_directives[0] if sitemap_directives else None

    # Evaluate blocking: Googlebot uses its own group if present, else inherits *
    wildcard_group = _find_group_for_agent(groups, "*")
    wildcard_blocked = _group_blocks_all(wildcard_group) if wildcard_group else False

    googlebot_group = _find_group_for_agent(groups, "googlebot")
    if googlebot_group:
        googlebot_blocked = _group_blocks_all(googlebot_group)
    else:
        googlebot_blocked = wildcard_blocked

    result["disallow_all"] = wildcard_blocked or googlebot_blocked
    result["googlebot_blocked"] = googlebot_blocked

    issues: list[str] = []
    if googlebot_blocked and wildcard_blocked:
        issues.append("Disallow: / blocks all crawlers including Googlebot.")
    elif googlebot_blocked:
        issues.append("Googlebot is explicitly blocked by its own Disallow: / rule.")
    elif wildcard_blocked:
        issues.append(
            "Disallow: / for User-Agent: * blocks most crawlers "
            "(Googlebot not specifically overridden)."
        )
    elif wildcard_group and any(d in ("/", "/*") for d in wildcard_group.get("disallow", [])):
        # Disallow: / exists but Allow rules partially override it
        allow_paths = [r for r in wildcard_group.get("allow", []) if r and r != "/"]
        if allow_paths:
            paths_str = ", ".join(allow_paths[:5])
            issues.append(
                f"Disallow: / present but partially overridden by Allow: {paths_str}. "
                "Site is not fully blocked."
            )

    if not sitemap_directives:
        issues.append("No Sitemap: directive found in robots.txt.")

    if googlebot_blocked:
        result["status"] = "fail"
    elif issues:
        result["status"] = "warn"
    else:
        result["status"] = "pass"

    if issues:
        result["detail"] = " ".join(issues)
    else:
        sitemap_note = (
            f" Sitemap: {', '.join(sitemap_directives)}."
            if sitemap_directives else ""
        )
        result["detail"] = f"robots.txt found. No critical blocking rules detected.{sitemap_note}"

    return result


def _parse_sitemap_xml(content: str, source_url: str) -> dict:
    """Parse and validate a single sitemap XML document."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        return {"status": "fail", "detail": f"Sitemap at {source_url} is not valid XML: {e}"}

    tag = re.sub(r"\{.*?\}", "", root.tag).lower()

    if tag == "sitemapindex":
        child_count = sum(
            1 for child in root
            if re.sub(r"\{.*?\}", "", child.tag).lower() == "sitemap"
        )
        return {
            "status": "pass" if child_count > 0 else "warn",
            "is_index": True,
            "url_count": child_count,
            "detail": (
                f"Sitemap index at {source_url} with {child_count} child sitemap(s)."
                if child_count > 0
                else f"Sitemap index at {source_url} contains no child sitemaps."
            ),
        }

    if tag == "urlset":
        url_count = sum(
            1 for child in root
            if re.sub(r"\{.*?\}", "", child.tag).lower() == "url"
        )
        return {
            "status": "pass" if url_count > 0 else "warn",
            "is_index": False,
            "url_count": url_count,
            "detail": (
                f"Sitemap at {source_url} with {url_count} URL(s)."
                if url_count > 0
                else f"Sitemap at {source_url} contains no <url> entries."
            ),
        }

    return {"status": "warn", "detail": f"Sitemap at {source_url} has unexpected root element: <{tag}>."}


def check_sitemap(
    origin: str, timeout: int, sitemap_urls: Optional[list[str]] = None
) -> dict:
    """
    Check sitemap for accessibility and valid XML structure.
    Tries URLs declared in robots.txt first, then falls back to {origin}/sitemap.xml.
    """
    candidates: list[str] = list(sitemap_urls) if sitemap_urls else []
    default_url = f"{origin}/sitemap.xml"
    if default_url not in candidates:
        candidates.append(default_url)

    result: dict = {
        "status": "error",
        "http_status": None,
        "url_count": 0,
        "is_index": False,
        "checked_url": None,
        "detail": "",
    }

    for candidate in candidates:
        status_code, content, error = _safe_fetch(candidate, timeout)
        result["checked_url"] = candidate
        result["http_status"] = status_code

        if error or status_code == 404 or status_code is None:
            continue

        if status_code != 200:
            result["status"] = "warn"
            result["detail"] = f"Sitemap at {candidate} returned HTTP {status_code}."
            return result

        if not content:
            continue

        parsed = _parse_sitemap_xml(content, candidate)
        result["status"] = parsed["status"]
        result["is_index"] = parsed.get("is_index", False)
        result["url_count"] = parsed.get("url_count", 0)
        result["detail"] = parsed["detail"]
        return result

    # None of the candidates were accessible
    checked = ", ".join(candidates)
    result["status"] = "fail"
    result["detail"] = (
        f"No accessible sitemap found. Checked: {checked}. "
        "Ensure a valid XML sitemap exists and is referenced in robots.txt."
    )
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
    sitemap_urls = robots_result.get("sitemap_directives", [])
    sitemap_result = check_sitemap(origin, args.timeout, sitemap_urls=sitemap_urls)

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

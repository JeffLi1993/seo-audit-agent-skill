#!/usr/bin/env python3
"""
OG Tags + Twitter Card 社交标签验证脚本。

从 HTML 中提取 Open Graph 和 Twitter Card meta 标签，
验证关键字段的存在性、长度、一致性。

Usage:
    python scripts/check-social.py https://example.com
    python scripts/check-social.py --file page.html

Output: JSON — og / twitter_card 两组检查结果 + 整体 status。

Dependencies:
    pip install requests
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
    print(
        "Error: requests library required. Install with: pip install requests",
        file=sys.stderr,
    )
    sys.exit(1)


_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 ClaudeSEO/1.2"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

# OG 字段长度阈值
_OG_TITLE_MAX = 95
_OG_DESC_MAX = 200

# Twitter 字段长度阈值
_TW_TITLE_MAX = 70
_TW_DESC_MAX = 200

# 合法的 twitter:card 类型
_VALID_CARD_TYPES = frozenset({
    "summary", "summary_large_image", "app", "player",
})


# ── HTTP fetch ────────────────────────────────────────────────────────────────


def _safe_fetch(
    url: str, timeout: int
) -> tuple[Optional[int], Optional[str], Optional[str]]:
    """带 SSRF 防护的 HTTP 请求，返回 (status, content, error)。"""
    parsed = urlparse(url)
    try:
        hostname = parsed.hostname or ""
        resolved_ip = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(resolved_ip)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            return None, None, f"Blocked: resolves to private IP ({resolved_ip})"
    except (socket.gaierror, ValueError):
        pass

    try:
        resp = requests.get(
            url, headers=_DEFAULT_HEADERS, timeout=timeout, allow_redirects=True
        )
        return resp.status_code, resp.text, None
    except requests.exceptions.RequestException as exc:
        return None, None, str(exc)


# ── HTML parser ───────────────────────────────────────────────────────────────


class _MetaExtractor(HTMLParser):
    """单次遍历提取 <meta> 标签中的 OG / Twitter / canonical 信息。"""

    def __init__(self) -> None:
        super().__init__()
        self.og: dict[str, str] = {}
        self.twitter: dict[str, str] = {}
        self.canonical: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag == "meta":
            attrs_dict = {k.lower(): (v or "") for k, v in attrs}
            prop = attrs_dict.get("property", "").lower()
            name = attrs_dict.get("name", "").lower()
            content = attrs_dict.get("content", "")

            # OG 标签: <meta property="og:xxx" content="...">
            if prop.startswith("og:"):
                key = prop[3:]  # 去掉 "og:" 前缀
                if key and content:
                    self.og[key] = content

            # Twitter 标签: <meta name="twitter:xxx" content="...">
            if name.startswith("twitter:"):
                key = name[8:]  # 去掉 "twitter:" 前缀
                if key and content:
                    self.twitter[key] = content

        # Canonical: <link rel="canonical" href="...">
        if tag == "link":
            attrs_dict = {k.lower(): (v or "") for k, v in attrs}
            if attrs_dict.get("rel", "").lower() == "canonical":
                href = attrs_dict.get("href", "").strip()
                if href:
                    self.canonical = href


# ── OG 验证 ───────────────────────────────────────────────────────────────────


def _check_og(og: dict[str, str], canonical: Optional[str]) -> dict:
    """验证 Open Graph 标签完整性和质量。"""
    issues: list[str] = []
    warnings: list[str] = []
    fields: dict[str, dict] = {}

    # og:title — 必须存在
    title = og.get("title", "")
    if not title:
        issues.append("og:title missing.")
        fields["title"] = {"present": False, "status": "fail"}
    else:
        f: dict = {"present": True, "value": title, "length": len(title), "status": "pass"}
        if len(title) > _OG_TITLE_MAX:
            f["status"] = "warn"
            warnings.append(f"og:title is {len(title)} chars (max {_OG_TITLE_MAX}).")
        fields["title"] = f

    # og:description — 推荐存在
    desc = og.get("description", "")
    if not desc:
        warnings.append("og:description missing.")
        fields["description"] = {"present": False, "status": "warn"}
    else:
        f = {"present": True, "value": desc, "length": len(desc), "status": "pass"}
        if len(desc) > _OG_DESC_MAX:
            f["status"] = "warn"
            warnings.append(f"og:description is {len(desc)} chars (max {_OG_DESC_MAX}).")
        fields["description"] = f

    # og:image — 必须存在且为有效 URL
    image = og.get("image", "")
    if not image:
        issues.append("og:image missing — social shares will lack a preview image.")
        fields["image"] = {"present": False, "status": "fail"}
    else:
        f = {"present": True, "value": image, "status": "pass"}
        if not image.startswith(("http://", "https://")):
            f["status"] = "warn"
            warnings.append("og:image is not an absolute URL.")
        fields["image"] = f

    # og:type — 推荐存在
    og_type = og.get("type", "")
    if not og_type:
        warnings.append("og:type missing (defaults to 'website').")
        fields["type"] = {"present": False, "status": "warn"}
    else:
        fields["type"] = {"present": True, "value": og_type, "status": "pass"}

    # og:url — 推荐存在，且应与 canonical 一致
    og_url = og.get("url", "")
    if not og_url:
        warnings.append("og:url missing.")
        fields["url"] = {"present": False, "status": "warn"}
    else:
        f = {"present": True, "value": og_url, "status": "pass"}
        if canonical and og_url.rstrip("/") != canonical.rstrip("/"):
            f["status"] = "warn"
            f["canonical_mismatch"] = True
            warnings.append(
                f"og:url ({og_url}) differs from canonical ({canonical})."
            )
        fields["url"] = f

    # 综合状态
    if issues:
        status = "fail"
    elif warnings:
        status = "warn"
    else:
        status = "pass"

    detail_parts = []
    if issues:
        detail_parts.extend(issues)
    if warnings:
        detail_parts.extend(warnings)
    if not detail_parts:
        detail_parts.append("All OG tags present and valid.")

    return {
        "status": status,
        "fields": fields,
        "issues": issues,
        "warnings": warnings,
        "detail": " ".join(detail_parts),
    }


# ── Twitter Card 验证 ─────────────────────────────────────────────────────────


def _check_twitter(
    twitter: dict[str, str], og: dict[str, str]
) -> dict:
    """验证 Twitter Card 标签，考虑 OG fallback 机制。"""
    issues: list[str] = []
    warnings: list[str] = []
    fields: dict[str, dict] = {}

    # twitter:card — 必须存在
    card = twitter.get("card", "")
    if not card:
        issues.append("twitter:card missing — no Twitter Card will render.")
        fields["card"] = {"present": False, "status": "fail"}
    else:
        f: dict = {"present": True, "value": card, "status": "pass"}
        if card not in _VALID_CARD_TYPES:
            f["status"] = "warn"
            warnings.append(f"twitter:card value '{card}' is non-standard.")
        fields["card"] = f

    # twitter:title — 可 fallback 到 og:title
    tw_title = twitter.get("title", "")
    og_title = og.get("title", "")
    if tw_title:
        f = {"present": True, "value": tw_title, "length": len(tw_title), "status": "pass"}
        if len(tw_title) > _TW_TITLE_MAX:
            f["status"] = "warn"
            warnings.append(f"twitter:title is {len(tw_title)} chars (max {_TW_TITLE_MAX}).")
        fields["title"] = f
    elif og_title:
        fields["title"] = {
            "present": False, "fallback": "og:title",
            "fallback_value": og_title, "status": "pass",
        }
    else:
        warnings.append("twitter:title missing and no og:title fallback.")
        fields["title"] = {"present": False, "status": "warn"}

    # twitter:description — 可 fallback 到 og:description
    tw_desc = twitter.get("description", "")
    og_desc = og.get("description", "")
    if tw_desc:
        f = {"present": True, "value": tw_desc, "length": len(tw_desc), "status": "pass"}
        if len(tw_desc) > _TW_DESC_MAX:
            f["status"] = "warn"
            warnings.append(
                f"twitter:description is {len(tw_desc)} chars (max {_TW_DESC_MAX})."
            )
        fields["description"] = f
    elif og_desc:
        fields["description"] = {
            "present": False, "fallback": "og:description",
            "fallback_value": og_desc, "status": "pass",
        }
    else:
        warnings.append("twitter:description missing and no og:description fallback.")
        fields["description"] = {"present": False, "status": "warn"}

    # twitter:image — 可 fallback 到 og:image
    tw_image = twitter.get("image", "")
    og_image = og.get("image", "")
    if tw_image:
        fields["image"] = {"present": True, "value": tw_image, "status": "pass"}
    elif og_image:
        fields["image"] = {
            "present": False, "fallback": "og:image",
            "fallback_value": og_image, "status": "pass",
        }
    else:
        warnings.append("twitter:image missing and no og:image fallback.")
        fields["image"] = {"present": False, "status": "warn"}

    # 综合状态
    if issues:
        status = "fail"
    elif warnings:
        status = "warn"
    else:
        status = "pass"

    detail_parts = []
    if issues:
        detail_parts.extend(issues)
    if warnings:
        detail_parts.extend(warnings)
    if not detail_parts:
        detail_parts.append("Twitter Card valid with all fields present or fallback available.")

    return {
        "status": status,
        "fields": fields,
        "issues": issues,
        "warnings": warnings,
        "detail": " ".join(detail_parts),
    }


# ── Main check ────────────────────────────────────────────────────────────────


def check_social(html: str, url: str = "") -> dict:
    """提取并验证 OG + Twitter Card 社交标签。"""
    extractor = _MetaExtractor()
    try:
        extractor.feed(html)
    except Exception:
        return {
            "url": url,
            "status": "error",
            "og": {},
            "twitter_card": {},
            "detail": "Failed to parse HTML for meta tag extraction.",
        }

    og_result = _check_og(extractor.og, extractor.canonical)
    tw_result = _check_twitter(extractor.twitter, extractor.og)

    # 综合两组检查的最终状态
    statuses = [og_result["status"], tw_result["status"]]
    if "fail" in statuses:
        overall = "fail"
    elif "warn" in statuses:
        overall = "warn"
    else:
        overall = "pass"

    return {
        "url": url,
        "status": overall,
        "og": og_result,
        "twitter_card": tw_result,
        "detail": f"OG: {og_result['status']}. Twitter Card: {tw_result['status']}.",
    }


# ── CLI entry point ──────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate OG Tags + Twitter Card on a page and output JSON."
    )
    parser.add_argument("url", nargs="?", help="Target page URL")
    parser.add_argument(
        "--file", "-f", help="Local HTML file path (skip HTTP fetch)"
    )
    parser.add_argument(
        "--timeout", "-t", type=int, default=20, help="Request timeout in seconds"
    )
    args = parser.parse_args()

    if not args.url and not args.file:
        parser.error("Provide a URL or --file <path>")

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                html = f.read()
        except OSError as exc:
            print(json.dumps({"error": str(exc)}, indent=2))
            sys.exit(1)
        url = args.url or args.file
    else:
        url = args.url or ""
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        status_code, html, error = _safe_fetch(url, args.timeout)
        if error or not html:
            err_msg = error or f"HTTP {status_code}"
            print(json.dumps({"url": url, "status": "error", "error": err_msg}, indent=2))
            sys.exit(1)

    result = check_social(html, url=url)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(1 if result["status"] == "fail" else 0)


if __name__ == "__main__":
    main()

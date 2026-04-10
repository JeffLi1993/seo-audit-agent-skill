"""
check-pagespeed.py — PageSpeed Insights score checker

Calls the Google PageSpeed Insights API (free, no API key required for basic usage)
and outputs Performance / Accessibility / Best Practices / SEO scores for
both mobile and desktop strategies.

Usage:
    python scripts/check-pagespeed.py https://example.com
    python scripts/check-pagespeed.py https://example.com --strategy mobile
    python scripts/check-pagespeed.py https://example.com --api-key YOUR_KEY

Output: JSON with scores per strategy.

Score thresholds:
    >= 90  → pass
    90-89  → warn  (actually 80-89)
    < 80   → fail
"""

import argparse
import json
import sys
from typing import Optional
from urllib.parse import urlencode

import requests

# PageSpeed Insights API endpoint
PSI_API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

# Categories to extract from API response
CATEGORIES = ["performance", "accessibility", "best-practices", "seo"]

# Per-category, per-strategy thresholds (pass_min, warn_min)
# SEO / Best Practices / Accessibility: must reach 100 on both strategies
# Performance: desktop ≥ 90, mobile ≥ 80
THRESHOLDS: dict[str, dict[str, tuple[int, int]]] = {
    "mobile": {
        "performance":     (80, 70),   # pass≥80, warn≥70, <70=fail
        "accessibility":   (100, 90),  # pass=100, warn≥90, <90=fail
        "best-practices":  (100, 90),
        "seo":             (100, 90),
    },
    "desktop": {
        "performance":     (90, 80),   # pass≥90, warn≥80, <80=fail
        "accessibility":   (100, 90),
        "best-practices":  (100, 90),
        "seo":             (100, 90),
    },
}


def _status_for_score(score: int, pass_min: int, warn_min: int) -> str:
    """Map numeric score to pass / warn / fail using per-category thresholds."""
    if score >= pass_min:
        return "pass"
    if score >= warn_min:
        return "warn"
    return "fail"


def _overall_status(score_statuses: dict[str, str]) -> str:
    """Return worst status across all category statuses."""
    statuses = list(score_statuses.values())
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "pass"


def _run_strategy(
    url: str,
    strategy: str,
    api_key: Optional[str],
    timeout: int,
) -> dict:
    """
    Call PSI API for one strategy (mobile or desktop).
    Returns a result dict with scores and status.
    """
    params: dict[str, str] = {"url": url, "strategy": strategy}
    # Add requested categories to limit response size
    for cat in CATEGORIES:
        params.setdefault("category", cat)

    # Build URL with repeated category params (requests encodes lists correctly)
    category_params = [("category", c) for c in CATEGORIES]
    base_params = {"url": url, "strategy": strategy}
    if api_key:
        base_params["key"] = api_key

    query = urlencode(base_params) + "&" + urlencode(category_params)
    api_url = f"{PSI_API}?{query}"

    try:
        resp = requests.get(api_url, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        return {
            "strategy": strategy,
            "status": "error",
            "error": f"Request timed out after {timeout}s.",
            "scores": {},
        }
    except requests.exceptions.RequestException as exc:
        return {
            "strategy": strategy,
            "status": "error",
            "error": str(exc),
            "scores": {},
        }

    data = resp.json()

    # Extract category scores (API returns 0.0–1.0, multiply by 100)
    lighthouse = data.get("lighthouseResult", {})
    categories = lighthouse.get("categories", {})

    scores: dict[str, int] = {}
    for cat in CATEGORIES:
        cat_data = categories.get(cat, {})
        raw = cat_data.get("score")
        scores[cat] = round(raw * 100) if raw is not None else -1

    # Build per-score status using per-category, per-strategy thresholds
    strategy_thresholds = THRESHOLDS.get(strategy, THRESHOLDS["mobile"])
    score_statuses: dict[str, str] = {}
    for cat, score in scores.items():
        if score < 0:
            continue
        pass_min, warn_min = strategy_thresholds.get(cat, (90, 80))
        score_statuses[cat] = _status_for_score(score, pass_min, warn_min)

    overall = _overall_status(score_statuses)

    # Identify non-passing categories for issue text
    failing = [cat for cat, st in score_statuses.items() if st != "pass"]
    issue_parts = [f"{cat.replace('-', ' ').title()} {scores[cat]}" for cat in failing]

    detail = (
        f"Performance {scores.get('performance', '?')} · "
        f"Accessibility {scores.get('accessibility', '?')} · "
        f"Best Practices {scores.get('best-practices', '?')} · "
        f"SEO {scores.get('seo', '?')}"
    )

    return {
        "strategy": strategy,
        "status": overall,
        "scores": scores,
        "score_statuses": score_statuses,
        "failing": issue_parts,
        "detail": detail,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check PageSpeed Insights scores (mobile + desktop) and output JSON."
    )
    parser.add_argument("url", help="Target page URL")
    parser.add_argument(
        "--strategy",
        choices=["mobile", "desktop", "both"],
        default="both",
        help="Strategy to run (default: both)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Optional Google API key (increases rate limit)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Request timeout in seconds (default: 60 — PSI API can be slow)",
    )
    args = parser.parse_args()

    strategies = (
        ["mobile", "desktop"] if args.strategy == "both" else [args.strategy]
    )

    results: dict[str, dict] = {}
    has_failure = False

    for strategy in strategies:
        result = _run_strategy(args.url, strategy, args.api_key, args.timeout)
        results[strategy] = result
        if result["status"] in ("fail", "error"):
            has_failure = True

    output = {
        "url": args.url,
        "results": results,
        "has_failure": has_failure,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))
    sys.exit(1 if has_failure else 0)


if __name__ == "__main__":
    main()

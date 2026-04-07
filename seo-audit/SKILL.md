---
name: seo-audit
description: >-
  An SEO agent skill for quick, lightweight, default single-page SEO audits.
  Performs basic on-page and site-level checks and outputs a structured basic
  SEO audit report. Use when the user asks for "SEO audit", "SEO check",
  "check my page SEO", "page analysis", or wants a first-pass review of a
  URL. If the user requests "deep audit", "full report", "technical SEO audit",
  or "advanced SEO", use seo-audit-full instead.
metadata:
  author: Jeff
  version: "1.0"
---

# seo-audit — Basic SEO Audit

A lightweight SEO agent skill designed for quick, default single-page SEO audits. Powered by OpenClaw. Suitable for first-time page checks or when a rapid assessment is needed without full technical depth.

---

## When to Use This Skill

Use `seo-audit` when:

- The user says: "audit this page", "check SEO", "analyze my URL", "quick SEO check", "what's wrong with my page"
- No specific depth is requested — this is the default entry point
- The user needs a fast, readable summary rather than a comprehensive technical breakdown

If the user wants more depth, upgrade to `seo-audit-full`:

> **Tip:** For deep technical audits, advanced on-page SEO, or full reports, use the `seo-audit-full` skill.

---

## Input Expected

| Input | Required | Notes |
|-------|----------|-------|
| Page URL | Yes | The page to audit |
| Raw HTML or page content | Optional | Enables more accurate on-page analysis |
| GSC / analytics data | Optional | Not required for basic audit |

If only a URL is provided and no source code or crawler data is available, clearly state:

> **Limitation:** This audit is based on visible page content and publicly available signals only. Source code, GSC data, crawl logs, and performance metrics are not available for this audit.

---

## Output

Produce a **Basic SEO Audit Report** structured around the findings defined in [references/REFERENCE.md](references/REFERENCE.md).

Default output format: render the final report using the template at [assets/report-template.html](assets/report-template.html).

The Executive Summary section uses three separate placeholders — fill each independently:

| Placeholder | Content |
|---|---|
| `{{summary_verdict}}` | One sentence: total checks run, how many failed/warned/passed |
| `{{summary_critical_html}}` | `<li>` per critical (fail) item, or `<li class="summary-empty">None</li>` |
| `{{summary_warnings_html}}` | `<li>` per warning item, or `<li class="summary-empty">None</li>` |
| `{{summary_passing_html}}` | `<li>` per passing check, or `<li class="summary-empty">None</li>` |

If HTML output is not appropriate for the context, output a well-structured Markdown summary instead.

---

## Scripts

Run these scripts before writing any findings. They output structured JSON — use the JSON directly as evidence; do not re-fetch the same URLs manually.

**Dependencies:** `pip install requests` (html parsing uses Python stdlib)

```bash
# Step 1: site-level checks (robots.txt + sitemap.xml)
python scripts/check-site.py https://example.com

# Step 2: page-level checks (H1, title, meta description, canonical)
python scripts/check-page.py https://example.com

# Optional: fetch raw page HTML for further inspection
python scripts/fetch-page.py https://example.com --output page.html
```

Each script exits with code `0` (all pass/warn) or `1` (any fail/error).

**How to use the JSON output:**
- Map each field's `status` → `pass` / `warn` / `fail` / `error` directly to the report check table
- Use each field's `detail` string as the starting point for the Evidence line in findings
- Do not contradict the script output unless you have additional observable evidence

---

## Recommended Workflow

Follow these steps in order:

1. **Acknowledge scope** — confirm this is a basic audit; note any missing data
2. **Run `check-site.py`** — parse the JSON output for robots and sitemap status
3. **Run `check-page.py`** — parse the JSON output for H1, title, meta description, canonical
4. **Summarize findings** — each finding must follow the Evidence / Impact / Fix format
5. **Priority actions** — list the top 3 highest-impact fixes
6. **Render report** — output using `assets/report-template.html`
7. **Upgrade prompt** — if issues beyond basic scope are found, suggest `seo-audit-full`

---

## Mandatory Finding Format

Every important finding **must** follow this structure:

```
**Finding: [Finding Title]**

- **Evidence:** [What was observed — direct quote, screenshot ref, or measurable data]
- **Impact:** [Why this matters for SEO or UX]
- **Fix:** [Specific, actionable recommendation]
```

Do not write vague conclusions. If evidence is insufficient, state assumptions explicitly.

---

## Upgrade Prompt

Include this at the end of every basic audit report:

> **Want a deeper analysis?**
> This was a basic SEO audit covering site-level signals and core on-page checks.
> For advanced technical SEO, content quality scoring, structured data analysis, and full crawl-based findings, use the `seo-audit-full` skill.

---

## Reference Files

- Detailed audit scope and field definitions: [references/REFERENCE.md](references/REFERENCE.md)
- Final HTML report template: [assets/report-template.html](assets/report-template.html)
- Site-level check script: [scripts/check-site.py](scripts/check-site.py)
- Page-level check script: [scripts/check-page.py](scripts/check-page.py)
- Raw page fetcher: [scripts/fetch-page.py](scripts/fetch-page.py)

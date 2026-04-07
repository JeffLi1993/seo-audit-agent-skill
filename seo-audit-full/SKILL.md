---
name: seo-audit-full
description: >-
  An advanced SEO agent skill for deep, comprehensive single-page SEO audits.
  Performs full technical SEO analysis, on-page SEO review, structured data
  validation, content quality assessment, and canonical/crawlability checks.
  Outputs an advanced full SEO audit report. Use when the user says "deep
  audit", "advanced audit", "technical SEO audit", "full SEO audit", "full
  report", "key report", "comprehensive SEO review", or explicitly asks for
  more than a basic check. Powered by OpenClaw and Claude.
metadata:
  author: Jeff
  version: "1.0"
---

# seo-audit-full — Advanced Full SEO Audit

A comprehensive SEO agent skill for deep single-page analysis. Goes beyond surface-level checks to cover technical SEO signals, on-page content quality, structured data, crawlability, and performance indicators. Powered by OpenClaw. Designed for users who need a thorough, evidence-backed report.

---

## When to Use This Skill

Use `seo-audit-full` when the user says any of the following:

- "deep audit"
- "advanced audit"
- "technical SEO audit"
- "full SEO audit" / "full report" / "key report"
- "comprehensive SEO review"
- "what's really wrong with my SEO"
- "I need a complete analysis"
- "audit everything"

Also use this skill when `seo-audit` (basic) was run first and the user asks: "what else should I check?" or "can you go deeper?"

---

## Input Expected

| Input | Required | Notes |
|-------|----------|-------|
| Page URL | Yes | The primary page to audit |
| Raw HTML / source code | Recommended | Enables accurate on-page and technical checks |
| Primary keyword | Recommended | Improves content relevance scoring |
| Google Search Console data | Optional | Enables impression/CTR/ranking analysis |
| Performance data (CWV) | Optional | Enables Core Web Vitals assessment |
| Crawl data / sitemap | Optional | Enables site architecture analysis |

If source code or additional data is unavailable, clearly state:

> **Limitation:** This audit is based on visible page content and publicly available signals only. Source code, GSC data, Core Web Vitals measurements, and crawl logs are not available. Findings are based on observable evidence and reasonable assumptions; these are marked accordingly.

---

## Output

Produce an **Advanced Full SEO Audit Report** structured around the audit modules defined in [references/REFERENCE.md](references/REFERENCE.md).

Default output format: render the final report using the template at [assets/report-template.html](assets/report-template.html).

If HTML output is not appropriate for the context, output a well-structured, detailed Markdown report instead.

---

## Recommended Workflow

Follow these steps in order:

1. **Confirm scope** — note the URL, primary keyword (if provided), and any data limitations
2. **Technical SEO checks** — crawlability, robots, sitemap, canonical, redirects, HTTPS
3. **On-page SEO checks** — title, meta description, H1–H3 structure, keyword usage, content length
4. **Structured data** — detect schema markup, validate types and required fields
5. **Content quality** — assess E-E-A-T signals, readability, and keyword relevance
6. **Performance signals** — note any available CWV data; flag if unavailable
7. **Internal linking** — assess anchor text quality and link distribution (if crawl data available)
8. **Summarize findings** — every finding must follow the Evidence / Impact / Fix format
9. **Priority actions** — list top 5 highest-impact fixes with effort/impact estimates
10. **Render report** — output using `assets/report-template.html`

---

## Mandatory Finding Format

Every important finding **must** follow this structure:

```
**Finding: [Finding Title]**

- **Evidence:** [Direct observation, measurable data, or quoted content]
- **Impact:** [Why this matters for SEO ranking, crawlability, or UX]
- **Fix:** [Specific, actionable recommendation with example if possible]
```

Do not write vague conclusions. If evidence is insufficient or based on assumption, write:

```
- **Evidence:** [ASSUMPTION] [What is assumed and why]
```

---

## Reference Files

- Detailed audit modules, field definitions, and agent instructions: [references/REFERENCE.md](references/REFERENCE.md)
- Final HTML report template: [assets/report-template.html](assets/report-template.html)

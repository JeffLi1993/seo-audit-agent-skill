---
name: seo-audit-full
description: >-
  An advanced SEO agent skill for deep, comprehensive single-page SEO audits.
  Includes ALL basic audit checks plus additional modules: Social Tags (OG +
  Twitter Card), and more. Outputs an advanced full SEO audit report.
  Use when the user says "deep audit", "advanced audit", "technical SEO audit",
  "full SEO audit", "full report", "key report", "comprehensive SEO review",
  or explicitly asks for more than a basic check. Powered by OpenClaw and Claude.
metadata:
  author: Jeff
  version: "2.0"
---

# seo-audit-full — Advanced Full SEO Audit

Full = Basic + Extra Checks. This skill runs **all** checks from `seo-audit` (basic) first,
then adds advanced modules on top. Both are single-page audits — Full simply covers more
dimensions and provides deeper analysis.

---

## When to Use This Skill

Use `seo-audit-full` when the user says any of the following:

- "deep audit" / "advanced audit" / "technical SEO audit"
- "full SEO audit" / "full report" / "key report"
- "comprehensive SEO review" / "audit everything"
- After `seo-audit` (basic) runs: "what else?", "go deeper", "full version"

---

## Input Expected

| Input | Required | Notes |
|-------|----------|-------|
| Page URL | Yes | The primary page to audit |
| Primary keyword | Recommended | Improves content relevance scoring |
| Raw HTML / source code | Optional | Enables more accurate on-page analysis |
| GSC API credentials | Optional | Enables search performance analysis (future) |

---

## Architecture: Full = Basic + Extra

```
┌─────────────────────────────────────────────────────────────┐
│  seo-audit-full Workflow                                    │
│                                                             │
│  Phase 1: Run ALL basic scripts (../seo-audit/scripts/)     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  check-site.py      → robots.txt, sitemap, 404, URL  │   │
│  │  check-page.py      → title, H1, meta desc, slug     │   │
│  │  check-schema.py    → JSON-LD validation              │   │
│  │  check-pagespeed.py → PageSpeed Insights              │   │
│  │  fetch-page.py      → raw HTML for analysis           │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  Phase 2: Run full-only scripts (./scripts/)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  check-social.py    → OG Tags + Twitter Card          │   │
│  │  (more scripts added here as modules grow)            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  Phase 3: LLM-only advanced checks                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  E-E-A-T content quality scoring                      │   │
│  │  Duplicate content signals                            │   │
│  │  Anchor text quality assessment                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Output

Produce an **Advanced Full SEO Audit Report** by filling the template at
[assets/report-template.html](assets/report-template.html),
then **save it to a file — never print raw HTML to the terminal**.

**File naming:** `reports/<hostname>-<slug>-full-audit.html`
```
https://example.com/blog/best-tools → reports/example-com-blog-best-tools-full-audit.html
https://example.com/                → reports/example-com-full-audit.html
```

**After saving, tell the user:**
```
✅ Full Report saved → reports/example-com-full-audit.html
   Open it now? (yes / no)
```
If yes → run: `open reports/example-com-full-audit.html`

---

## Scripts

Run scripts in two phases. All output structured JSON — use it directly as evidence.

**Dependencies:** `pip install requests`

### Phase 1: Basic scripts (from `../seo-audit/scripts/`)

```bash
# 1. site-level checks (robots.txt + sitemap.xml + 404 + URL canonicalization)
python ../seo-audit/scripts/check-site.py https://example.com

# 2. page-level checks (H1, title, meta description, canonical, URL slug)
python ../seo-audit/scripts/check-page.py https://example.com --keyword "primary keyword"

# 3. fetch raw HTML for downstream scripts
python ../seo-audit/scripts/fetch-page.py https://example.com --output /tmp/page.html

# 4. JSON-LD schema validation
python ../seo-audit/scripts/check-schema.py --file /tmp/page.html

# 5. PageSpeed Insights
python ../seo-audit/scripts/check-pagespeed.py https://example.com
```

### Phase 2: Full-only scripts (from `./scripts/`)

```bash
# 6. Social tags: OG + Twitter Card validation
python scripts/check-social.py --file /tmp/page.html
# Or directly from URL:
python scripts/check-social.py https://example.com
```

Each script exits with code `0` (all pass/warn) or `1` (any fail/error).

---

## Scope — Full Audit Check Whitelist

Full includes **everything in Basic** plus the items marked ★ below.

### Site-Level Checks (in `{{site_checks_html}}`)

Inherited from Basic:
- robots.txt · sitemap.xml · 404 Handling · URL Canonicalization · i18n / hreflang

### E-E-A-T Checks (in `{{eeat_checks_html}}`)

Inherited from Basic:
- About Us · Contact · Privacy Policy · Terms of Service · Media/Partners (only if present)

### Page-Level Checks (in `{{page_checks_html}}`), output in this exact order:

Inherited from Basic:
PageSpeed (Mobile) · PageSpeed (Desktop) · URL Slug · Title Tag · Meta Description ·
H1 Tag · Canonical Tag · Image Alt Text · Word Count · Keyword Placement ·
Heading Structure · Internal Links · Schema (JSON-LD)

★ Full-only additions:
- **OG Tags** — og:title, og:description, og:image, og:type, og:url presence and validity
- **Twitter Card** — twitter:card type, title/description/image (with OG fallback detection)

---

## How to Use Script JSON Output

Same rules as Basic — map each field's `status` directly to the report check table:
- `status` → `pass` / `warn` / `fail` / `error` → badge in report
- `detail` → starting point for Evidence line
- Do not contradict script output unless you have additional observable evidence

**For `check-social.py` output:**
- `og.status` → OG Tags row status
- `twitter_card.status` → Twitter Card row status
- `og.fields.*` → individual field details for the detail cell
- `twitter_card.fields.*` → individual field details, note fallback fields

---

## LLM Review Instructions

### Inherited from Basic

All `llm_review_required: true` handling from `seo-audit` applies here unchanged:
H1 semantic judgment, Title keyword position, URL Slug evaluation, Meta Description quality.
See `seo-audit/SKILL.md` for full instructions.

### Full-only LLM checks

**OG Tags quality (always review):**
```
og:title   : Does it differ meaningfully from <title>? It should be optimized for social sharing.
og:description : Is it compelling for social feeds? Different focus than meta description is OK.
og:image   : Is the URL an actual image path (not a page URL)?
```

**Twitter Card completeness:**
```
If twitter:card is "summary_large_image", twitter:image (or og:image fallback) must be
at least 300x157px. Flag if the image URL looks like a small icon or favicon.
```

---

## Recommended Workflow

1. **Acknowledge scope** — confirm this is a full audit; note any missing data or API keys
2. **Infer primary keyword** — same logic as Basic
3. **Phase 1: Run ALL basic scripts** — check-site → check-page → fetch-page → check-schema → check-pagespeed
4. **Basic checks** — 404 handling, URL canonicalization, E-E-A-T trust pages, i18n/hreflang (same as Basic)
5. **Phase 2: Run full-only scripts** — check-social
6. **LLM-only advanced checks** — E-E-A-T content quality, duplicate content signals, anchor text quality
7. **Summarize findings** — Evidence / Impact / Fix format
8. **Priority actions** — top 5 highest-impact fixes with effort/impact tags
9. **Render report** — save to `reports/<hostname>-<slug>-full-audit.html`

---

## Report Detail Writing Rules

Same as Basic — strict formatting:

**Pass → one short phrase. No lists, no elaboration.**

**Warn → one `<div class="detail-issue">` with ≤2 bullet points. One `<div class="detail-fix">`.**

**Fail → same as Warn. Lead with the exact failure.**

---

## Mandatory Finding Format

```
**Finding: [Finding Title]**

- **Evidence:** [Observable fact, data point, or marked assumption]
- **Impact:** [SEO / UX consequence]
- **Fix:** [Actionable recommendation with example]
```

For Priority Actions, add effort/impact tags:
```
1. [High Impact / Low Effort] Fix og:image — social shares currently show no preview.
```

---

## Reference Files

- Detailed audit modules and field definitions: [references/REFERENCE.md](references/REFERENCE.md)
- Final HTML report template: [assets/report-template.html](assets/report-template.html)
- Social tags validation script: [scripts/check-social.py](scripts/check-social.py)
- Basic scripts (inherited): `../seo-audit/scripts/` (check-site, check-page, check-schema, check-pagespeed, fetch-page)

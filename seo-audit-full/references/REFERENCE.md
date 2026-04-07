# seo-audit-full — Reference Guide

Detailed field definitions, audit modules, scope boundaries, trigger keywords, and agent instructions for the `seo-audit-full` advanced SEO audit skill.

---

## Positioning

`seo-audit-full` is the **advanced, comprehensive tier** of SEO auditing in the OpenClaw / Claude skill ecosystem. It is designed for users who need a thorough, evidence-based audit that goes well beyond surface-level checks.

**Compared to `seo-audit` (basic):**

| Dimension | seo-audit (basic) | seo-audit-full (advanced) |
|-----------|------------------|--------------------------|
| Scope | Core signals only | Full technical + on-page |
| Technical SEO | Sitemap, robots | + Redirects, canonical chains, HTTPS, hreflang |
| On-page | H1, title, meta desc | + H2–H3 structure, keyword density, content quality |
| Structured data | Not included | Schema markup detection and validation |
| Content quality | Not included | E-E-A-T signals, readability, topic depth |
| Performance | Not included | CWV flags (if data available) |
| Internal linking | Not included | Anchor text quality, orphan page signals |
| Report depth | Summary | Full findings with priority matrix |

---

## Audit Scope — Full Report Modules

### Module 1: Technical SEO

| Check | What to Verify |
|-------|---------------|
| HTTPS | Is the page served over HTTPS? No mixed-content warnings? |
| Canonical tag | Is `<link rel="canonical">` present? Correct URL? No chain? |
| Redirect chain | Does the URL resolve with no unnecessary 301/302 chain? |
| robots.txt | Is `Disallow` blocking the target page or key resources? |
| sitemap.xml | Is the page included in the sitemap? Correct priority/changefreq? |
| Hreflang | If multilingual, are hreflang tags correct and reciprocal? |
| Noindex signal | Is `noindex` accidentally present in meta robots or X-Robots-Tag? |
| Pagination | Are `rel="next"` / `rel="prev"` used correctly (if applicable)? |

### Module 2: On-Page SEO

| Check | What to Verify |
|-------|---------------|
| Title tag | Present? Length 50–60 chars? Primary keyword near front? |
| Meta description | Present? Length 120–160 chars? Compelling with CTA? |
| H1 | Single H1? Matches page intent? Contains primary keyword? |
| H2–H3 structure | Logical hierarchy? Keywords in subheadings? |
| Primary keyword usage | Keyword in title, H1, first 100 words, meta desc? |
| Content length | Is content depth appropriate for the query type? |
| Thin content | Is the page too shallow to rank competitively? |
| Duplicate content signals | Is there near-duplicate content on other pages? |

### Module 3: Structured Data

| Check | What to Verify |
|-------|---------------|
| Schema presence | Any `application/ld+json` or microdata present? |
| Schema type | Appropriate type for the page (Article, Product, FAQ, LocalBusiness, etc.)? |
| Required fields | Are all required fields for the schema type populated? |
| Validation warnings | Any obvious errors (missing `@context`, wrong `@type`)? |
| Rich result eligibility | Does the schema qualify for rich results based on Google's criteria? |

### Module 4: Content Quality (E-E-A-T Signals)

| Signal | What to Look For |
|--------|-----------------|
| Experience | First-hand experience signals in the content? |
| Expertise | Author credentials, citations, depth of explanation? |
| Authoritativeness | Site reputation signals, external links, brand mentions? |
| Trustworthiness | Accurate claims, clear authorship, privacy/contact info? |
| Readability | Sentence complexity, paragraph length, use of lists/headers |

### Module 5: Performance Signals

| Check | Note |
|-------|------|
| Core Web Vitals (LCP) | If data available — flag if LCP > 2.5s |
| Core Web Vitals (INP) | If data available — flag if INP > 200ms |
| Core Web Vitals (CLS) | If data available — flag if CLS > 0.1 |
| Image optimization | Oversized images? Missing `width`/`height`? No `loading="lazy"`? |
| Render-blocking resources | CSS/JS in `<head>` without `async`/`defer`? |

> If CWV data is not available, clearly state: `[UNVERIFIED] Core Web Vitals data not available for this audit.`

### Module 6: Internal Linking

| Check | What to Verify |
|-------|---------------|
| Inbound links | Does the page receive internal links from other site pages? |
| Anchor text quality | Are inbound anchor texts descriptive and keyword-relevant? |
| Orphan page risk | Does the page appear isolated from site architecture? |
| Outbound internal links | Does the page link to relevant related pages? |

> Internal linking analysis requires crawl data or site map access. If unavailable, flag as `[UNVERIFIED]`.

---

## Trigger Keywords

This skill should activate when the user says:

- "deep audit"
- "advanced audit"
- "technical SEO audit"
- "full SEO audit" / "full report" / "key report"
- "comprehensive SEO review"
- "complete analysis"
- "audit everything"
- "I need more than a basic check"
- After `seo-audit` runs: "what else?", "go deeper", "full version"

---

## Agent Instructions

### General quality rules

1. **Concrete over abstract.** "The title is 82 characters, which Google typically truncates at ~60" is better than "the title is too long."
2. **Proportional depth.** Spend more time on high-impact issues. Do not write equal-length findings for a missing meta description and a missing canonical.
3. **No false certainty.** If you cannot access source code or CWV data, do not invent scores. Mark assumptions with `[ASSUMPTION]` or `[UNVERIFIED]`.
4. **Priority matrix.** In the Priority Actions section, include an effort/impact estimate: `Low Effort / High Impact`, `Medium Effort / High Impact`, etc.

### Handling missing data

If source HTML is unavailable:
> "On-page and technical checks are based on rendered content and publicly observable HTTP headers only. JavaScript-rendered content, server-side logic, and HTTP response headers beyond what is publicly visible are not included in this analysis."

If GSC data is unavailable:
> "Keyword ranking, CTR, and impression data from Google Search Console are not available. Search performance analysis is not included in this audit."

If CWV / performance data is unavailable:
> "Core Web Vitals metrics are not available. Performance assessment cannot be included. Consider running a Lighthouse or PageSpeed Insights report separately."

### Scope of this demo implementation

The current version of `seo-audit-full` provides:
- Structured audit modules and finding templates (above)
- HTML report template for structured output
- Clear guidance for agents on what to check and how to report

**Not yet automated:**
- Live crawl execution
- Lighthouse / CWV integration
- GSC API data pull
- Structured data validator API calls

These can be added as scripts in the `scripts/` directory in future versions.

---

## Finding Format Reminder

Every important finding must follow:

```
**Finding: [Title]**
- **Evidence:** [Observable fact, data point, or marked assumption]
- **Impact:** [SEO / UX consequence]
- **Fix:** [Actionable recommendation with example]
```

For Priority Actions, add effort/impact tags:

```
1. [High Impact / Low Effort] Fix the canonical tag — it currently points to a non-HTTPS variant.
2. [High Impact / Medium Effort] Add FAQ schema to capture rich result eligibility.
3. [Medium Impact / Low Effort] Expand meta description from 95 to 140 characters.
```

---

## Limitations Disclosure

Always include a limitations section. Use language like:

> This audit is based on publicly accessible page signals at the time of analysis. Depending on data availability, the following may not be included: source code review, JavaScript rendering analysis, Core Web Vitals measurements, Google Search Console data, crawl log analysis, or competitive benchmarking. All findings marked [UNVERIFIED] or [ASSUMPTION] indicate areas where additional data collection is recommended before acting on the finding.

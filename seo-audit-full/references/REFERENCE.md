# seo-audit-full — Reference Guide

Detailed field definitions, audit modules, scope boundaries, and agent instructions
for the `seo-audit-full` advanced SEO audit skill.

---

## Positioning

`seo-audit-full` is the **advanced tier** — it runs ALL checks from `seo-audit` (basic)
first, then adds extra modules. Both target a single page.

**Compared to `seo-audit` (basic):**

| Dimension | seo-audit (Basic) | seo-audit-full (Advanced) |
|-----------|------------------|--------------------------|
| Scope | Core signals | Basic + extra modules |
| Technical SEO | robots.txt, sitemap, 404, canonical, HTTPS, hreflang | ★ Same (inherited) |
| On-page | H1, title, meta desc, canonical, slug, images, word count | ★ Same (inherited) |
| Schema | JSON-LD extraction + field validation | ★ Same (inherited) |
| PageSpeed | PSI API (mobile + desktop) | ★ Same (inherited) |
| E-E-A-T pages | Trust page existence + reachability | ★ Same (inherited) |
| Social Tags | Not included (banned) | ★ OG Tags + Twitter Card |
| E-E-A-T Content | Not included | ★ Experience/Expertise/Authority/Trust scoring (LLM) |
| Duplicate Content | Not included | ★ Near-duplicate signals (LLM) |
| Anchor Text | Not included | ★ Internal link anchor text quality (LLM) |
| Scripts | 5 Python scripts | 5 inherited + 1 own (`check-social.py`) |
| Report depth | Summary + Priority Actions + Insights | Full findings with effort/impact priority matrix |

---

## Audit Scope — Full Report Modules

### Module 1: Technical SEO (inherited from Basic scripts)

| Check | Script | Notes |
|-------|--------|-------|
| robots.txt | `check-site.py` | RFC 9309 group parsing, Allow directive support |
| sitemap.xml | `check-site.py` | Tracks robots.txt Sitemap directives |
| 404 Handling | `check-site.py` | Soft 404 detection |
| URL Canonicalization | `check-site.py` | HTTP→HTTPS, www, trailing slash, canonical match |
| i18n / hreflang | LLM check on HTML | BCP 47 codes, reciprocal symmetry, x-default |

### Module 2: On-Page SEO (inherited from Basic scripts)

| Check | Script | Notes |
|-------|--------|-------|
| Title Tag | `check-page.py` | Length, keyword presence/position |
| Meta Description | `check-page.py` | Length, keyword, quality |
| H1 Tag | `check-page.py` | Uniqueness, keyword match |
| URL Slug | `check-page.py` | Keyword presence, readability |
| Canonical Tag | `check-page.py` | Self-referencing validation |
| Image Alt Text | LLM check on HTML | Parse `<img>` tags from static HTML |
| Word Count | LLM check on HTML | < 100 fail, 100–499 warn, ≥ 500 pass |
| Keyword Placement | LLM check on HTML | Present in first 100 body words |
| Heading Structure | LLM check on HTML | H2 count, keyword in H2, H3/H2 ratio |
| Internal Links | LLM check on HTML | Same-origin `<a>` count (excl. nav/footer) |
| PageSpeed (Mobile) | `check-pagespeed.py` | PSI API scores |
| PageSpeed (Desktop) | `check-pagespeed.py` | PSI API scores |

### Module 3: Structured Data (inherited from Basic scripts)

| Check | Script | Notes |
|-------|--------|-------|
| Schema (JSON-LD) | `check-schema.py` | @type detection, required/recommended field validation |

### Module 4: Social Tags (★ Full-only — scripted)

| Check | Script | Notes |
|-------|--------|-------|
| OG Tags | `check-social.py` | og:title, og:description, og:image, og:type, og:url |
| Twitter Card | `check-social.py` | twitter:card type, title/desc/image with OG fallback |

**OG Tags status logic:**
- Pass: og:title + og:description + og:image + og:type all present and valid
- Warn: og:url missing or og:url/canonical mismatch, or length exceeds limits
- Fail: og:title or og:image completely missing

**Twitter Card status logic:**
- Pass: twitter:card present with valid type, title/desc/image present or OG fallback
- Warn: missing optional fields with no OG fallback
- Fail: twitter:card tag completely missing

### Module 5: E-E-A-T Trust Pages (inherited from Basic workflow)

| Page | Required |
|------|----------|
| About Us | Yes |
| Contact | Yes |
| Privacy Policy | Yes |
| Terms of Service | Yes |
| Media / Partners | No — include only if present |

### Module 6: LLM-Only Advanced Checks (★ Full-only)

These checks require semantic judgment and cannot be scripted:

| Check | What to assess |
|-------|---------------|
| E-E-A-T Content Quality | Experience signals, expertise depth, authority indicators, trust markers |
| Duplicate Content Signals | Near-duplicate paragraphs, boilerplate ratio, unique content percentage |
| Anchor Text Quality | Are internal link anchors descriptive and keyword-relevant? |

---

## Agent Instructions

### General quality rules

1. **Concrete over abstract.** "og:title is 112 chars, exceeding the 95-char limit" > "og:title is too long."
2. **Proportional depth.** More detail for high-impact issues.
3. **No false certainty.** Mark assumptions with `[ASSUMPTION]` or `[UNVERIFIED]`.
4. **Priority matrix.** Include effort/impact tags: `Low Effort / High Impact`, etc.

### Handling missing data

If API keys are not available:
> "GSC data is not available — search performance analysis is not included in this audit.
> To enable: set `GSC_API_KEY` environment variable."

If CWV data is limited:
> "Core Web Vitals assessment is based on PageSpeed Insights API data only.
> Field data from CrUX may differ from lab measurements."

---

## Finding Format Reminder

```
**Finding: [Title]**
- **Evidence:** [Observable fact, data point, or marked assumption]
- **Impact:** [SEO / UX consequence]
- **Fix:** [Actionable recommendation with example]
```

For Priority Actions:
```
1. [High Impact / Low Effort] Fix og:image — social shares currently show no preview.
```

---

## Limitations Disclosure

Always include a limitations section:

> This audit is based on publicly accessible page signals at the time of analysis.
> Depending on data availability, the following may not be included: source code review,
> JavaScript rendering analysis, Core Web Vitals field measurements, Google Search Console
> data, crawl log analysis, or competitive benchmarking. All findings marked [UNVERIFIED]
> or [ASSUMPTION] indicate areas where additional data collection is recommended.

# seo-audit-skill

**English** · [中文](README.zh.md)

Reusable Agent Skills for single-page SEO auditing — Basic and Full tiers.  

Works with Claude, Cursor, and OpenClaw.

---

## Skills

| Skill | Tier | When to use |
|---|---|---|
| `seo-audit` | Basic | Quick first-pass check — give it a URL, get a structured report |
| `seo-audit-full` | Full | Deep audit: technical SEO, on-page, schema, E-E-A-T, performance |

### What's covered

**Site-level checks**

| Check | Description | Basic | Full |
|---|---|:---:|:---:|
| robots.txt | Valid syntax, Sitemap directive, Googlebot not blocked | ✅ | ✅ |
| sitemap.xml | Valid XML, URL count, referenced in robots.txt | ✅ | ✅ |
| 404 handling | Non-existent URL returns true 404, not soft 404 or redirect | ✅ | ✅ |
| URL canonicalization | HTTPS enforced, www unified, trailing slash consistent, canonical matches URL | ✅ | ✅ |
| i18n / hreflang | Reciprocal symmetry, BCP 47 codes, x-default, URL structure | ✅ | ✅ |
| Schema (JSON-LD) | Page-type-aware: detect @type, validate required fields, no conflicts | ✅ | ✅ |
| E-E-A-T infrastructure | About / Contact / Privacy / Terms — exists + reachable from footer/nav | ✅ | ✅ |
| GSC crawl status | Index coverage, crawl errors, blocked resources | ❌ | ✅ |
| Core Web Vitals | LCP, CLS, INP via field data | ❌ | ✅ |
| PageSpeed Insights | Performance score, server response time, render-blocking resources | ❌ | ✅ |

**Page-level checks**

| Check | Description | Basic | Full |
|---|---|:---:|:---:|
| URL slug | Lowercase, hyphenated, keyword present, no stop words | ✅ | ✅ |
| Title tag | Length 50–60 chars, keyword leads (inner pages), brand leads (homepage) | ✅ | ✅ |
| Meta description | Length 120–160 chars, keyword present, specific and non-generic | ✅ | ✅ |
| H1 tag | Single H1, keyword present, semantic intent match | ✅ | ✅ |
| Canonical tag | Self-referencing canonical present and correct | ✅ | ✅ |
| H2/H3 hierarchy | Heading structure, keyword distribution across headings | ❌ | ✅ |
| Page content — quantity | Word count, content-to-HTML ratio | ❌ | ✅ |
| Page content — quality | E-E-A-T signals, readability, specificity vs competitors | ❌ | ✅ |

---

## Structure

```
seo-audit-skill/
├── seo-audit/
│   ├── SKILL.md
│   ├── references/REFERENCE.md
│   ├── assets/report-template.html
│   └── scripts/
│       ├── fetch-page.py
│       ├── check-site.py
│       └── check-page.py
└── seo-audit-full/
    ├── SKILL.md
    ├── references/REFERENCE.md
    └── assets/report-template.html
```

---

## Installation

**Option 1: CLI Install (Recommended)**

```bash
# Install all skills
npx skills add JeffLi1993/seo-audit-skill

# Install a specific skill
npx skills add JeffLi1993/seo-audit-skill --skill seo-audit
npx skills add JeffLi1993/seo-audit-skill --skill seo-audit-full

# List available skills
npx skills add JeffLi1993/seo-audit-skill --list
```

**Option 2: Claude Code Plugin**

```bash
# Add the marketplace
/plugin marketplace add JeffLi1993/seo-audit-skill

# Install
/plugin install seo-audit-skill
```

## Usage

Once installed, just say:

```
audit this page: https://example.com
```

```
deep audit: https://example.com
```

---

## Scripts (seo-audit)

| Script | What it does |
|---|---|
| `check-site.py` | Checks robots.txt + sitemap.xml, outputs JSON |
| `check-page.py` | Checks H1 / title / meta description / canonical, outputs JSON |
| `fetch-page.py` | Fetches raw page HTML with SSRF protection |

All scripts output structured JSON to stdout. Exit code `0` = pass/warn, `1` = any fail.

---

## License

MIT

# seo-audit-skill

[English](README.md) · **中文**

可复用的单页面 SEO 审计 Agent Skill，分 Basic 和 Full 两个层级。

支持 Claude、Cursor 和 OpenClaw。

---

## Skill 说明

| Skill | 层级 | 适用场景 |
|---|---|---|
| `seo-audit` | Basic | 快速初检 — 给一个 URL，输出结构化报告 |
| `seo-audit-full` | Full | 深度审计：技术 SEO、页面优化、Schema、E-E-A-T、性能 |

### 检查项覆盖范围

| 检查项 | Basic | Full |
|---|:---:|:---:|
| robots.txt | ✅ | ✅ |
| sitemap.xml | ✅ | ✅ |
| Canonical 策略 | ✅ | ✅ |
| URL 结构 | ✅ | ✅ |
| TDK（标题、描述、H1） | ✅ | ✅ |
| H2/H3 标题层级结构 | ✅ | ✅ |
| URL 关键词 | ✅ | ✅ |
| Schema 结构化数据 | ✅ | ✅ |
| i18n / hreflang 多语言 | ✅ | ✅ |
| E-E-A-T 权威信号 | ❌ | ✅ |
| GSC 抓取状态 | ❌ | ✅ ¹ |
| Core Web Vitals | ❌ | ✅ ¹ |
| PageSpeed Insights | ❌ | ✅ ² |
| 页面内容 — 定量 | ❌ | ✅ |
| 页面内容 — 定性 | ❌ | ✅ |

> ¹ 需要 GSC Service Account
> ² 需要 PageSpeed API Key

---

## 目录结构

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

## 安装

**方式一：CLI 安装（推荐）**

```bash
# 安装全部 skill
npx skills add JeffLi1993/seo-audit-skill

# 安装指定 skill
npx skills add JeffLi1993/seo-audit-skill --skill seo-audit
npx skills add JeffLi1993/seo-audit-skill --skill seo-audit-full

# 查看可用 skill 列表
npx skills add JeffLi1993/seo-audit-skill --list
```

**方式二：Claude Code Plugin**

```bash
# 添加 marketplace
/plugin marketplace add JeffLi1993/seo-audit-skill

# 安装
/plugin install seo-audit-skill
```

## 使用

安装后，直接说：

```
audit this page: https://example.com
```

```
deep audit: https://example.com
```

---

## 内置脚本（seo-audit）

| 脚本 | 功能 |
|---|---|
| `check-site.py` | 检查 robots.txt + sitemap.xml，输出 JSON |
| `check-page.py` | 检查 H1 / 标题 / meta description / canonical，输出 JSON |
| `fetch-page.py` | 获取原始页面 HTML，含 SSRF 防护 |

所有脚本均输出结构化 JSON 到 stdout。退出码 `0` = 通过/警告，`1` = 存在失败项。

---

## License

MIT

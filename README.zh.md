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

**站点级检查**

| 检查项 | 说明 | Basic | Full |
|---|---|:---:|:---:|
| robots.txt | 语法正确、Sitemap 指令存在、Googlebot 未被屏蔽 | ✅ | ✅ |
| sitemap.xml | 有效 XML、URL 数量、在 robots.txt 中已引用 | ✅ | ✅ |
| 404 处理 | 不存在的 URL 返回真实 404，而非软 404 或跳转首页 | ✅ | ✅ |
| URL 规范化 | HTTPS 强制、www 统一、尾斜杠一致、Canonical 与 URL 匹配 | ✅ | ✅ |
| i18n / hreflang | 互相引用对称、BCP 47 语言码、x-default、URL 结构建议 | ✅ | ✅ |
| Schema（JSON-LD） | 按页面类型检测 @type、验证必填字段、无冲突 | ✅ | ✅ |
| E-E-A-T 基础建设 | About / Contact / Privacy / Terms — 页面存在且 footer/nav 可达 | ✅ | ✅ |
| GSC 抓取状态 | 索引覆盖、抓取错误、被屏蔽资源 | ❌ | ✅ |
| Core Web Vitals | LCP、CLS、INP 字段数据 | ❌ | ✅ |
| PageSpeed Insights | 性能评分、服务器响应时间、阻塞渲染资源 | ❌ | ✅ |

**页面级检查**

| 检查项 | 说明 | Basic | Full |
|---|---|:---:|:---:|
| URL Slug | 小写、连字符、含关键词、无停用词 | ✅ | ✅ |
| Title 标题 | 50–60 字符、内页关键词开头、首页品牌词开头 | ✅ | ✅ |
| Meta Description | 120–160 字符、含关键词、具体而非泛泛 | ✅ | ✅ |
| H1 标签 | 唯一 H1、含关键词、语义意图匹配 | ✅ | ✅ |
| Canonical 标签 | 自引用 Canonical 存在且正确 | ✅ | ✅ |
| H2/H3 层级结构 | 标题结构、关键词在各级标题中的分布 | ❌ | ✅ |
| 页面内容 — 定量 | 字数、内容与 HTML 比例 | ❌ | ✅ |
| 页面内容 — 定性 | E-E-A-T 信号、可读性、与竞品的具体程度对比 | ❌ | ✅ |

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

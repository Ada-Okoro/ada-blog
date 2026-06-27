# Ada's Personal Blog

> _Keep learning, keep improving._

🌐 **Live site:** https://ada-okoro.github.io/ada-blog/
🔗 **LinkedIn:** https://www.linkedin.com/in/qianli-cv/
📍 Calgary, AB, Canada · 🗣️ English · Mandarin · Cantonese

Personal blog of **Qian Li (Ada)** — a PMP-certified business & data analyst. I write about
data analytics, project management, and bridging business and technology for impactful solutions.

---

## 👋 About me

PMP-certified professional with **6+ years of experience** in business analysis, project
coordination, and data analytics across **insurance, IT, and financial services**. Skilled in
data-driven decision-making, requirements gathering, and process optimization. Currently advancing
my expertise in data management and analytics.

**Skills & tools**
- **Data Analytics & Visualization:** SQL · Excel (Power Query / Pivot) · Power BI · Tableau
- **Project Management:** MS Project · Visio · Agile / Scrum · Stakeholder Engagement
- **Business Analysis:** Requirements Gathering · UAT / SIT Testing · Workflow Optimization
- **Platforms:** SharePoint · Google Workspace · CRM Systems

## 📊 Featured data projects

| Project | What it does |
|---|---|
| [Climate & Sales Correlation](https://github.com/Ada-Okoro/Climate-and-Sales-Correlation) | How temperature & precipitation affect retail sales across AB / BC / ON — a decade of monthly data, segmented across 11 retail categories, to inform inventory, marketing & staffing. |
| [Data Analysis II Projects](https://github.com/Ada-Okoro/Data-Anlysis-II-Projects) | Coursework projects incl. a median-income filter. |
| [Class Record](https://github.com/Ada-Okoro/Class_Record) | Data-analytics class records & exercises. |

---

## 🛠️ How this blog is built

Authored in **[Ghost](https://ghost.org/)** running locally in **Docker**, exported to static HTML,
and published to **GitHub Pages** — free hosting, no server to maintain.

```
本地写作                       生成                      发布
┌──────────────┐  docker    ┌──────────────┐  push    ┌─────────────┐
│ Ghost + MySQL │ ─────────▶ │ ./static (gssg)│ ───────▶ │ gh-pages 分支│ ─▶ GitHub Pages
│ localhost:2368│           └──────────────┘          └─────────────┘
└──────────────┘
```

**Quick start**
```bash
cp .env.example .env          # 设置 PAGES_URL 与数据库密码
docker compose up -d          # 启动写作后台 → http://localhost:2368/ghost
./scripts/publish-pages.sh    # 生成静态站并发布到 GitHub Pages
./.ops-venv/bin/python scripts/backup.py   # 备份(MySQL + 内容)
```

📖 **完整部署指南(含网页版步骤):** [DEPLOY.md](DEPLOY.md)

> ℹ️ 会员登录、邮件订阅 / newsletter、原生评论需要服务器版 Ghost,静态站不支持;纯展示型博客不受影响。

---

<sub>Content © Qian Li (Ada). Built with Ghost + Docker, deployed on GitHub Pages.</sub>

# 博客视觉完善设计稿(方向 C · Ghost 原生 + Code Injection)

- 日期:2026-06-27
- 项目:`~/projects/ghost-site`(Ada's Personal Blog)
- 线上:https://ada-okoro.github.io/ada-blog/
- 状态:设计已通过,待写实现计划

## 1. 目标

完善博客视觉与品牌:**去掉首页大订阅框**,**结合 GitHub / LinkedIn**,**使用 Ada 的 GitHub 头像**,
落地为首页头部"方向 C"(横向:头像 + 姓名 + 一句专业简介 + 彩色 GitHub/LinkedIn 按钮)。

## 2. 关键决策

| 维度 | 决策 |
|---|---|
| 视觉方向 | C · 横向简介式头部(可视化伴侣中已确认) |
| 实现方式 | **Ghost 原生**:Admin API 改设置 + Code Injection,再用 gssg 导出静态 |
| 凭据 | 用 **Admin API Key**(Custom Integration);此前管理员密码登录失败,改用 Key(更稳、不触发锁定) |
| 主题 | 保持当前 `source`(嵌在镜像内、软链接,不直接改模板;靠 Code Injection 注入) |
| 头像来源 | `https://github.com/Ada-Okoro.png` 下载后上传到 Ghost |

## 3. 改动范围

1. **关闭会员/订阅**:`members_signup_access = "none"` → 首页大订阅框、文章页底部 signup CTA 原生消失。
2. **头像品牌化**:下载 GitHub 头像 → 上传 Ghost(`/images/upload/`)→ 设为站点 `icon` 与 `logo`。
3. **站点描述**:`description` = `PMP-certified business & data analyst · data-driven decisions · SQL · Power BI · Tableau`。
4. **导航**:`navigation` = Home(`/`)、About(`/about/`)、GitHub(`https://github.com/Ada-Okoro`)、LinkedIn(`https://www.linkedin.com/in/qianli-cv/`)。
5. **Code Injection**(站点级,gssg 导出到每页):
   - `codeinjection_head`:CSS —(a)兜底隐藏残留订阅/会员元素;(b)C 版头部与彩色社交按钮样式(深色 GitHub / 蓝色 LinkedIn)。
   - `codeinjection_foot`:必要时一小段 JS,把 C 版头部块(头像+姓名+简介+社交)插到正文顶部(若主题原生头部 + logo/description 已够则尽量少用 JS)。
   - 实现时**先看 `static/index.html` 的真实 class** 再定选择器,避免猜。
6. **About 页**:用简历内容创建/更新并发布(`/pages/?source=html`):
   > Hi, I'm Qian Li (Ada). PMP-certified professional, 6+ years in business analysis / project coordination / data analytics(insurance, IT, financial services). Tools: SQL · Excel(Power Query/Pivot)· Power BI · Tableau · MS Project · Visio · Agile/Scrum. Recent projects: Climate & Retail-Sales Correlation(AB/BC/ON); Median-Income analysis. Languages: English · Mandarin · Cantonese. 📍 Calgary · LinkedIn。
7. **发布**:`./scripts/publish-pages.sh` 重新生成 → 推 `gh-pages` → 线上更新。

## 4. 实现机制

- 一个脚本(`scripts/personalize.py`,跑在 `.ops-venv`)用 **Admin API Key** 走 JWT 鉴权,顺序调用:
  `images/upload`(头像)→ `settings`(members access / icon / logo / description / navigation / codeinjection_*)→ `pages`(About,存在则更新)。
- Key 通过环境变量传入,**不写进仓库**。CSS/JS 文案存为仓库内文件(`tools/inject/blog.css` 等)供以后在 GitHub 上改,再由脚本写入 Ghost 的 codeinjection 字段。
- 之后 `publish-pages.sh` 导出并发布。

## 5. 验收标准

1. 线上首页**无大订阅框**、文章页**无底部 signup CTA**。
2. 首页头部显示 **圆形头像 + "Qian Li (Ada)" + 一句简介 + GitHub(深)/LinkedIn(蓝)按钮**。
3. 导航含 Home/About/GitHub/LinkedIn,外链可点。
4. `/about/` 页为她的简历版内容,含 LinkedIn 链接。
5. 资源在 `…/ada-blog/` 子路径下正常加载(沿用既有 `--subDir` 机制)。
6. 改动可重复:再次运行脚本 + 发布,结果一致。

## 6. 不做 / 风险

- 不改主题源码(主题在镜像内);C 头部依赖 Code Injection,主题大改时需微调选择器。
- 不开会员/邮件(静态站不支持)。
- 需要可用的 Admin API Key 才能落地(实现前向用户索取)。

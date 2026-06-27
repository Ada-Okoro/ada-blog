# 博客重设计:编辑极简(求职导向)设计稿

- 日期:2026-06-27
- 项目:`~/projects/ghost-site`,线上 https://ada-okoro.github.io/ada-blog/
- 状态:设计已通过,待写实现计划
- **本稿取代** 2026-06-27 视觉打磨稿里「满屏 Tiffany 蓝背景」的决定(改为中性底 + Tiffany 点缀)

## 1. 目标

按**业界设计美学 + 信息获取原则**重做博客视觉与信息架构,定位为 **求职 / 职业发展为主、个人写作为辅** 的数据分析师作品集博客。

## 2. 关键决策(已确认)

| 维度 | 决策 |
|---|---|
| 站名(title) | **Qian Li · Data & Business Analyst** |
| 副标题(description) | turning data into decisions · PMP · Calgary |
| 受众/目标 | 求职为主(招聘/HR/用人经理),兼顾持续写作 |
| 信息层级 | 简介 → 精选项目 → 文章 |
| 美学方向 | 编辑/极简:中性浅底 + 强字体层级 + 大留白 |
| 强调色 | Tiffany Blue **#0ABAB5** 仅作点缀(标签/链接/细线/hover/按钮描边);**去掉满屏蓝背景** |

## 3. 视觉系统

- **底色**:暖白 `#FAFAF9`;卡片/内容区 `#FFFFFF`。
- **文字**:主文 `#1A1A1A`,次要 `#5B6470`,弱化 `#9AA0A6`。
- **强调色**:`#0ABAB5`,用于 eyebrow 小标签、链接、分隔细线、hover/focus、按钮描边。
- **字体层级**:H1 大而克制;区块标签 `SELECTED WORK / WRITING` 用小号大写 + letter-spacing + 弱化色;正文 ~17px / 行高 1.6 / 阅读宽 ~680px。
- **间距/对齐**:统一容器宽(~880px),大量留白,左对齐为主。

## 4. 首页信息架构

1. **顶栏**:小圆头像(Tiffany 描边)+ `Qian Li` + 导航 `Work · Writing · About` + GitHub/LinkedIn。
2. **Hero / 简介**:角色 eyebrow(`DATA & BUSINESS ANALYST · CALGARY`)+ H1「Turning data into decisions.」+ 一句价值主张 + GitHub/LinkedIn。
3. **SELECTED WORK**:2 张项目卡(题图 + 标签 + 标题 + 一句话)。内容 = 被标记为 `featured` 的项目文章(Climate×Sales、Grad Income)。
4. **WRITING**:非 featured 文章列表(标题 + 摘要 + 日期)。
5. **页脚**:© Qian Li (Ada) · GitHub · LinkedIn · Email。

> 文章页 / About 页:沿用同一视觉系统(中性底、Tiffany 点缀、阅读宽 680px),自定义 hero 不在文章页出现。

## 5. 实现机制(沿用 Ghost 设置 + Code Injection + gssg)

- **Ghost 设置**:`title` 改为站名;`description` 改为副标题;`accent_color=#0ABAB5`;`navigation = Work(/)、Writing、About`(GitHub/LinkedIn 仍在 hero/页脚)。
- **文章分区**:把两篇项目文(`weather-retail-sales`、`alberta-graduate-income`)设 `featured=true`;Welcome 等设 `featured=false`。
- **Code Injection(`tools/inject/blog.css` + `blog.js`,仓库可改)**:
  - CSS:实现整套编辑风(底色、字体层级、区块标签、卡片、链接 Tiffany 点缀);**移除满屏蓝背景 + 白卡那套规则**。
  - JS(首页):构建 Hero;读取首页文章流,把 `featured` 项重排进「SELECTED WORK」卡片网格、其余进「WRITING」列表;构建页脚版权/社交。实现时先看真实 DOM 的 featured 标记/class 再写选择器;若重排不稳,**退化为**单一编辑风文章流(featured 仅加视觉标签),保证不崩。
- **发布**:`./scripts/publish-pages.sh`(gssg 导出 + 补原图 → gh-pages)。
- 静态站无效功能(评论/搜索/订阅)继续隐藏。

## 6. 验收标准

1. 站名显示为 **Qian Li · Data & Business Analyst**;accent 为 Tiffany 蓝(链接/标签)。
2. **无满屏蓝背景**;整体为中性底 + 大留白的编辑风。
3. 首页可见 **Hero → SELECTED WORK(≥2 项目卡,带真实题图)→ WRITING(列表)→ 页脚**(若 JS 重排退化,则为统一编辑风文章流,projects 在前且带题图)。
4. 文章页/About 页采用同一视觉系统,正文阅读宽 ~680px。
5. 移动端正常(单列、间距合理)。
6. 线上(gh-pages)与本地渲染一致;图片可达(沿用补原图逻辑)。

## 7. 不做 / 风险

- 不开会员/邮件/评论(静态站不支持)。
- Hero 与 Work/Writing 分区由注入 JS 客户端生成(gssg 不跑 JS),静态 HTML 里为基础内容 + 脚本;禁用 JS 的访客看到的是基础编辑风文章流(可接受)。
- 不做服务器版 Ghost(在线后台)——如需另立方案。

# Ghost 网站(Docker + GitHub Pages)设计稿

- 日期:2026-06-27
- 项目目录:`~/projects/ghost-site`
- 站点标题:**Ada's Personal Blog**(Ghost 后台站点名,与目录名独立)
- 状态:已通过设计评审;**2026-06-27 修订:部署目标由「服务器 + Caddy」改为「GitHub Pages 静态导出」**

## 1. 目标

用 Ghost(开源发布平台/CMS)做内容后台,产出一个**能稳定运行的个人博客**——"Ada's Personal Blog"。
Ghost 在**本机 Docker** 里当写作后台;对外则把站点**导出为静态文件发布到 GitHub Pages**(免费、免服务器)。

## 2. 核心决策(已确认)

| 维度 | 决策 | 理由 |
|---|---|---|
| 内容后台 | Docker Compose:Ghost 6 + MySQL 8,仅本机 | Node 应用标准隔离;本机写作 |
| Ghost 版本 | `ghost:6`(debian/bookworm,当前 6.47.0) | v6 当前稳定;debian 镜像 native 模块最稳 |
| 数据库 | MySQL 8.0 | Ghost 官方生产推荐 |
| 「虚拟环境」含义 | 三类工具各自隔离:Ghost=容器;静态生成器=容器;备份脚本=Python uv venv | 不污染宿主(用户偏好 clean base),各工具用各自最合适的隔离 |
| 对外部署 | **GitHub Pages 静态导出**(`gh-pages` 分支) | 免费、免服务器;个人博客读多写少,够用 |
| 静态生成器 | `ghost-static-site-generator`(gssg)v1.1.4,**跑在一次性 Docker 容器里** | 宿主无需装 wget/node;可复现 |
| 发布方式 | 本地生成 `./static` → 推到 `gh-pages` 分支 → Pages 从该分支提供服务 | 主分支不混入生成产物;一条命令发布 |
| 会员/邮件/newsletter | 配置项预留,**静态站不支持**;留待将来上服务器再启用 | 现在不接外部邮件服务 |
| 密钥 | 全部进 `.env`(gitignore);`.env.example` 留占位 | 标准密钥管理 |
| 备份 | `scripts/backup.py`(uv venv 运行):mysqldump + 打包 content | 生意内容不能丢 |
| 主题 | 默认 Casper,`content/themes` 可挂载换主题 | 干净专业,日后可换模板 |

## 3. 架构与组件

- **`ghost` 容器** — 官方 `ghost:6`,`NODE_ENV=production`,`url=http://localhost:2368`,连 `db`。仅映射到 `127.0.0.1:2368`,不暴露公网。
- **`db` 容器** — `mysql:8.0`,独立命名卷 + healthcheck。
- **`generate` 容器(profile: `generate`,一次性)** — 由 `tools/gssg/Dockerfile` 构建(node+wget+gssg)。`network_mode: "service:ghost"` 共享 Ghost 网络命名空间,因此容器内 `localhost:2368` 即 Ghost,与其 `url` 一致,gssg 能正确把站内链接改写为 `PAGES_URL`。产出挂载到宿主 `./static`。
- **GitHub Pages** — 静态文件托管;从 `gh-pages` 分支提供服务,支持自定义域名 + 免费 HTTPS。

## 4. 项目结构

```
ghost-site/
├── docker-compose.yml        # ghost + db;generate 在 generate profile
├── tools/gssg/Dockerfile     # 一次性静态生成器镜像(gssg)
├── .env                      # 密钥/密码/PAGES_URL(gitignore)
├── .env.example              # 配置模板(进 git,含邮件占位)
├── .gitignore
├── content/                  # Ghost 内容卷:主题/图片/数据(bind mount,便于备份)
├── static/                   # 生成的静态站(gitignore;发布到 gh-pages 分支)
├── scripts/
│   ├── backup.py             # mysqldump + 打包 content,带时间戳
│   ├── pyproject.toml        # uv 管理
│   ├── generate.sh           # 起一次性容器生成 ./static
│   └── publish-pages.sh      # 生成 + 推送到 gh-pages 分支
├── .ops-venv/                # 备份脚本 Python venv(uv 建,gitignore)
├── backups/                  # 备份产物(gitignore)
└── README.md                 # 写作/备份/生成/发布 一页说明
```

## 5. 数据流 / 生命周期

- **本地写作:** `docker compose up -d` → 打开 `http://localhost:2368/ghost` 建管理员、发文。内容落在 `./content` + MySQL 卷。
- **生成静态:** `scripts/generate.sh` 起一次性 `generate` 容器跑 gssg → 产出 `./static`(链接已改写为 `PAGES_URL`)。
- **发布:** `scripts/publish-pages.sh` 把 `./static` 推到 `gh-pages` 分支 → GitHub Pages 自动更新。
- **发新文章循环:** 本地写 → `publish-pages.sh` → 线上更新。

## 6. 业界实践细节

- **密钥管理:** 密码/密钥全部在 `.env`;`.env.example` 留占位;`.env` 进 `.gitignore`;MySQL 密码强随机。
- **持久化:** `content/` bind mount(备份直接 tar);MySQL 命名卷(备份走 mysqldump)。
- **备份:** `scripts/backup.py` 做 MySQL dump + 打包 `content/`,带时间戳存到 `backups/`;README 写明挂 cron。
- **干净宿主:** 静态生成跑在容器里,宿主不装 wget/node;备份脚本跑在独立 uv venv。
- **邮件(预留不启用):** `.env.example` 保留 `mail__*` 占位;静态站本就不支持动态邮件。
- **主题:** 默认 Casper;`content/themes` 可挂载换主题。

## 7. 明确不做(YAGNI)

- 不做服务器 + Caddy 路线(已从计划移除,git 历史可恢复)、不配真实邮件、不做自定义主题开发、不接 CDN/对象存储。
- GitHub 仓库创建 / 推送 / 开启 Pages 属对外动作,执行前与用户确认。

## 8. 验收标准

1. `docker compose up -d` 后,`http://localhost:2368` 返回 200,`/ghost` 可进后台建管理员;后台设置里把站点标题设为 "Ada's Personal Blog"(README 写明)。
2. 重启容器后文章/设置不丢(数据持久化)。
3. `.env`、`static/` 不进 git;`.env.example` 在 git 中且字段完整(含 `PAGES_URL` 与邮件占位)。
4. `scripts/backup.py` 在 `.ops-venv` 中跑通,产出带时间戳的备份(MySQL dump + content 包)。
5. `scripts/generate.sh` 产出 `./static`,首页 `static/index.html` 存在且非空,站内绝对链接已是 `PAGES_URL`。
6. `scripts/publish-pages.sh` 能把 `./static` 推到 `gh-pages` 分支(实际推送在用户确认建仓后执行)。
7. README 一页说清:写作、备份、生成、发布四步。

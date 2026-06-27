# Ghost 网站(Docker)设计稿

- 日期:2026-06-27
- 项目目录:`~/projects/ghost-site`
- 站点标题:**Ada's Personal Blog**(Ghost 后台站点名,与目录名独立)
- 状态:已通过设计评审,待写实现计划

## 1. 目标

用 Ghost(开源发布平台/CMS)搭一个**能稳定运行的博客/网站**——"Ada's Personal Blog",
定位为北美 home business 的个人博客。
本机先跑起来,但整套按**业界生产级实践**搭建,随时能上线到带域名的服务器。

## 2. 核心决策(已确认)

| 维度 | 决策 | 理由 |
|---|---|---|
| 运行方式 | Docker Compose:Ghost + MySQL 各一容器 | Node 应用的标准隔离方式 |
| Ghost 版本 | `ghost:6`(debian/bookworm,当前 6.47.0) | v6 为当前稳定大版本;debian 镜像 native 模块(图片处理 sharp 等)最稳 |
| 「虚拟环境」含义 | Ghost 的隔离 = Docker 容器;另设独立 Python venv 仅跑运维脚本 | Ghost 本体不需要 Python venv;脚本侧贴合用户 uv/Miniforge 习惯 |
| 数据库 | MySQL 8.0 | Ghost 官方生产推荐(非 SQLite) |
| 部署形态 | 本机优先,预留上线能力(Caddy 反代放 `online` profile) | 一套仓库从本地长到生产 |
| HTTPS/反代 | Caddy(自动签证书),上线才启用 | home business 上线最省心 |
| 会员/邮件/newsletter | 配置项预留,暂不启用 | 现在不接外部邮件服务,日后填凭据即开 |
| 密钥 | 全部进 `.env`(gitignore);`.env.example` 只留占位 | 标准密钥管理 |
| 备份 | `scripts/backup.py`(uv venv 运行):mysqldump + 打包 content | 生意内容不能丢 |
| 主题 | 默认 Casper,`content/themes` 可挂载换主题 | 干净专业,日后可换模板 |

## 3. 架构与组件

- **`ghost` 容器** — 官方 `ghost:6` 镜像(debian/bookworm,当前 6.47.0)。`NODE_ENV=production`,连 `db`。本地仅映射到 `127.0.0.1:2368`,不暴露公网。`depends_on` db 健康后启动。
- **`db` 容器** — `mysql:8.0`。独立数据卷 + healthcheck。
- **`caddy` 容器(profile: `online`,本地不跑)** — 上线时反代 Ghost,自动 HTTPS。

## 4. 项目结构

```
ghost-site/
├── docker-compose.yml        # ghost + db;caddy 在 online profile
├── Caddyfile                 # 反代配置(上线才用)
├── .env                      # 密钥/密码/域名(gitignore)
├── .env.example              # 配置模板(进 git,含邮件占位项)
├── .gitignore
├── content/                  # Ghost 内容卷:主题/图片/数据(bind mount,便于备份)
├── scripts/
│   ├── backup.py             # mysqldump + 打包 content,带时间戳
│   └── pyproject.toml        # uv 管理依赖
├── .ops-venv/                # 运维脚本 Python venv(uv 建,gitignore)
├── backups/                  # 备份产物(gitignore)
└── README.md                 # 起停/备份/上线 一页说明
```

## 5. 数据流 / 生命周期

- **本地:** `docker compose up -d` → 打开 `http://localhost:2368/ghost` 建管理员、发文。内容落在 `./content` + MySQL 卷。
- **上线:** `.env` 填真实域名 + 强密码 → `docker compose --profile online up -d` → Caddy 自动签证书,公网 HTTPS 访问;Ghost 端口不再直接对外。**同一套数据无缝延续。**

## 6. 业界实践细节(NA home business)

- **密钥管理:** 密码/密钥全部在 `.env`;`.env.example` 留占位;`.env` 进 `.gitignore`;MySQL 密码用强随机生成。
- **持久化:** `content/` 用 bind mount(备份直接 tar);MySQL 用命名卷(备份走 mysqldump)。
- **备份:** `scripts/backup.py` 做 MySQL dump + 打包 `content/`,带时间戳存到 `backups/`;README 写明如何挂 cron 定时执行。
- **邮件(预留不启用):** `.env.example` 与 compose 中保留 `mail__*` 配置位并注释说明;现在不接任何外部邮件服务。
- **主题:** 默认 Casper;`content/themes` 可挂载,换模板时丢进去即可。

## 7. 明确不做(YAGNI)

- 不配真实邮件凭据、不本地跑 Caddy、不做自定义主题开发、不接 CDN/对象存储。
- 以上均留好接口,需要时再加。

## 8. 验收标准

1. `docker compose up -d` 后,`http://localhost:2368` 能打开站点首页,`/ghost` 能进管理后台并建管理员;在后台设置里把站点标题设为 "Ada's Personal Blog"(README 写明此步)。
2. Ghost 数据持久化:重启容器后文章/设置不丢。
3. `.env` 不进 git;`.env.example` 在 git 中且字段完整(含邮件占位)。
4. `scripts/backup.py` 能在 `.ops-venv` 中跑通,产出带时间戳的备份(MySQL dump + content 包)。
5. 填入域名并加 `--profile online` 后,Caddy 配置在结构上可直接反代(本机不实测签证书)。
6. README 一页说清:起停、备份、上线三步。

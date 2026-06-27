# Ada's Personal Blog (Ghost · Docker · GitHub Pages)

Ghost 6 在本地 Docker 里当**写作后台**;对外把站点**导出为静态文件发布到 GitHub Pages**(免费、免服务器)。

## 架构一图

```
本地写作                      生成                     发布
┌──────────────┐  docker   ┌──────────────┐  push   ┌─────────────┐
│ Ghost 6 + DB │ ────────▶ │ ./static(gssg)│ ──────▶ │ gh-pages 分支│ ─▶ GitHub Pages
│ localhost:2368│          └──────────────┘         └─────────────┘
└──────────────┘
```

## 结构
- `docker-compose.yml` — `ghost`(6)+ `db`(mysql:8.0);`generate`(一次性静态生成器,profile `generate`)
- `tools/gssg/Dockerfile` — 静态生成器镜像(容器内含 wget + gssg,宿主无需安装)
- `.env` — 密钥/密码/`PAGES_URL`(**不进 git**;由 `.env.example` 生成)
- `content/` — Ghost 内容(主题/图片/数据,bind mount)
- `static/` — 生成的静态站(不进 git;发布到 gh-pages)
- `scripts/backup.py` — 备份(MySQL dump + content 打包),跑在 `.ops-venv`
- `scripts/generate.sh` — 生成 `./static`
- `scripts/publish-pages.sh` — 生成并推送到 `gh-pages`

---

## 1. 首次启动(本机写作后台)
```bash
cp .env.example .env     # 已存在则跳过
# 给 MySQL 设强密码(可选,首次建库前):
python3 - <<'PY'
import secrets,re,pathlib
p=pathlib.Path(".env");t=p.read_text()
f=lambda t,k,v:re.sub(rf"(?m)^{k}=.*$",f"{k}={v}",t)
t=f(t,"MYSQL_ROOT_PASSWORD",secrets.token_hex(24));t=f(t,"MYSQL_PASSWORD",secrets.token_hex(24))
p.write_text(t);print("strong passwords set")
PY

docker compose up -d
# 等 30–90s 让 Ghost 初始化数据库,然后打开:
open http://localhost:2368/ghost
```
在后台创建管理员,**Settings → Title & description** 把标题设为 `Ada's Personal Blog`。
> Ghost 站点标题只能在后台设置,没有环境变量。

## 2. 日常起停
```bash
docker compose up -d            # 启动
docker compose stop             # 停止(保留数据)
docker compose logs -f ghost    # 看日志
```

## 3. 备份
```bash
# 首次:建运维虚拟环境
uv venv .ops-venv && uv pip install --python .ops-venv/bin/python -e ./scripts
# 备份(需 Ghost 在跑)
./.ops-venv/bin/python scripts/backup.py
```
产物在 `backups/`(MySQL dump + content 打包,带时间戳)。定时备份(每天 03:00,`crontab -e`):
```cron
0 3 * * * cd ~/projects/ghost-site && ./.ops-venv/bin/python scripts/backup.py >> backups/cron.log 2>&1
```

## 4. 生成静态站(本地预览/检查)
```bash
./scripts/generate.sh     # 起一次性容器跑 gssg,输出到 ./static
# 本地预览:
python3 -m http.server -d static 8080   # 打开 http://localhost:8080
```
`generate.sh` 会按 `.env` 的 `PAGES_URL` 自动决定是否用子路径(见下)。

## 5. 部署到 GitHub Pages

> **交付场景**:本项目是给客户做的,客户在**自己账号**下发布。完整、账号无关的步骤(含网页版开 Pages)见 **[DEPLOY.md](DEPLOY.md)**。下面是命令行速查。

1. `.env` 把 `PAGES_URL` 设为 `https://<USER>.github.io/<REPO>`(`<USER>` = 客户 GitHub 用户名)。
2. 用客户自己的账号建仓 + 推源码:`gh repo create <REPO> --public --source=. --remote=origin --push`
3. 生成并发布:`./scripts/publish-pages.sh`
4. 开 Pages(只需一次):`gh api -X POST repos/<USER>/<REPO>/pages -f 'source[branch]=gh-pages' -f 'source[path]=/'`(或仓库 Settings → Pages → 选 `gh-pages` / `/(root)`)。

发新文章循环:本地后台写好 → `./scripts/publish-pages.sh` → 线上自动更新。

---

## 6. 会员 / 邮件 / newsletter
静态站**不支持**会员登录、原生评论、newsletter 发送(这些需要服务器跑 Ghost)。
`.env.example` 与 `docker-compose.yml` 已为邮件留好占位;将来若要这些动态功能,需要把 Ghost 部署到带域名的服务器(本仓库 git 历史里保留过 Caddy 反代方案,可恢复)。

## 7. 故障排查
- **Ghost 起不来**:`docker compose logs ghost`;首启迁移较慢,稍等。
- **静态站样式丢失/链接 404**:多半是 `PAGES_URL` 与实际访问地址不一致(子路径没对上);改对后重跑 `publish-pages.sh`。
- **Linux 服务器上 content 权限**:`sudo chown -R 1000:1000 content`(macOS 无需)。

# Ghost 网站(Docker + GitHub Pages)Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `~/projects/ghost-site` 用 Docker 跑 Ghost 6 当本地写作后台("Ada's Personal Blog"),并把站点导出为静态文件发布到 GitHub Pages。

**Architecture:** Docker Compose 编排 `ghost:6` + `mysql:8.0`(仅本机);静态导出用 Dockerized `ghost-static-site-generator`(`generate` profile),产出 `./static`,推到 `gh-pages` 分支由 GitHub Pages 托管。备份脚本跑在独立 Python uv venv。

**Tech Stack:** Docker Compose · Ghost 6 · MySQL 8.0 · ghost-static-site-generator(容器内)· GitHub Pages · Python 3 + uv

**Conventions:**
- 工作目录始终是 `~/projects/ghost-site`。
- git 提交用:`git -c user.name="ShepherdLoveYou" -c user.email="yunfansong0@gmail.com" commit ...`。当前在 `feat/ghost-docker-setup` 分支。
- 本项目为基础设施/配置类,"测试" = 起栈后实际验证。

> **修订记录(2026-06-27):** 部署目标由「服务器 + Caddy」改为「GitHub Pages 静态导出」。原 Task 4(Caddyfile)移除;新增静态生成/发布相关任务。

---

## Task 1: 仓库骨架与 .gitignore ✅(已完成)
创建 `.gitignore`(忽略 `.env`、`content/*`、`backups/*`、`.ops-venv/`、`static/`)、`content/.gitkeep`、`backups/.gitkeep`。

## Task 2: 环境变量 ✅(已完成)
`.env.example`(进 git,含 `GHOST_URL`/`MYSQL_*`/`PAGES_URL`/邮件占位);`.env`(gitignore,强随机 MySQL 密码)。

## Task 3: docker-compose.yml ✅(已完成)
`db`(mysql:8.0 + healthcheck)、`ghost`(ghost:6,127.0.0.1:2368,bind mount `./content`)、`generate`(profile `generate`,`build ./tools/gssg`,`network_mode: service:ghost`,挂载 `./static`)。

## Task 3b: 静态生成器镜像 ✅(已完成)
`tools/gssg/Dockerfile`:`node:22-alpine` + `wget` + `gssg@1.1.4`,CMD 跑 `gssg --url "$PAGES_URL"`。

---

## Task 5: 本地起栈并验证(核心验收)

**Files:** 无(运行时验证)

- [ ] **Step 1: 拉镜像并启动**

Run: `docker compose up -d`
Expected: `ghost-db`、`ghost-app` 创建成功(首次拉镜像)。

- [ ] **Step 2: 等数据库健康 + Ghost 起来**

Run:
```bash
until [ "$(docker inspect -f '{{.State.Health.Status}}' ghost-db 2>/dev/null)" = "healthy" ]; do sleep 3; done; echo "db healthy"
until curl -sf -o /dev/null http://localhost:2368/; do sleep 3; done; echo "ghost up"
```
Expected: 依次打印 `db healthy` → `ghost up`(首启迁移 30–90s)。

- [ ] **Step 3: 首页 200 / 后台可达 / 内容落地**

Run:
```bash
curl -s -o /dev/null -w "home=%{http_code}\n" http://localhost:2368/
curl -s -o /dev/null -w "admin=%{http_code}\n" -L http://localhost:2368/ghost/
ls content/ && test -d content/themes/source && echo "default theme present"
```
Expected: `home=200`;`admin=200`;看到 content 子目录;打印默认主题存在(Ghost 6 默认主题为 `source`)。

- [ ] **Step 4: 手动首配(记录到 README,不阻塞)**

人工:打开 `http://localhost:2368/ghost` 建管理员,Settings → 把站点标题设为 **Ada's Personal Blog**。

---

## Task 6: 持久化验证

- [ ] **Step 1: 记录表数量 > 0**

Run: `docker compose exec -T db mysql -uroot -p"$(grep '^MYSQL_ROOT_PASSWORD=' .env | cut -d= -f2)" -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='ghost';"`
Expected: > 0。

- [ ] **Step 2: 重启 + 复验**

Run:
```bash
docker compose restart && until curl -sf -o /dev/null http://localhost:2368/; do sleep 3; done
docker compose exec -T db mysql -uroot -p"$(grep '^MYSQL_ROOT_PASSWORD=' .env | cut -d= -f2)" -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='ghost';"
```
Expected: 站点恢复 200;表数量与 Step 1 一致。

---

## Task 7: 备份脚本 + uv venv

**Files:** Create `scripts/pyproject.toml`, `scripts/backup.py`

- [ ] **Step 1: `scripts/pyproject.toml`**
```toml
[project]
name = "ghost-site-ops"
version = "0.1.0"
description = "Ops scripts for ghost-site (backup)"
requires-python = ">=3.10"
dependencies = []
```

- [ ] **Step 2: `scripts/backup.py`**(mysqldump via `docker compose exec` + tar `content/`,带时间戳,产物校验非空)— 完整代码见仓库实现。

- [ ] **Step 3: 建 venv 并安装**

Run: `uv venv .ops-venv && uv pip install --python .ops-venv/bin/python -e ./scripts`
> uv 不在 PATH 时:`conda run -n tools uv ...` 或退回 `python3 -m venv .ops-venv`。

- [ ] **Step 4: 运行 + 校验产物**

Run: `./.ops-venv/bin/python scripts/backup.py && ls -lh backups/ | grep -E 'ghost-(db|content)-'`
Expected: 打印 done;`backups/` 下出现非空 `.sql` 与 `.tar.gz`。

- [ ] **Step 5: 提交** `scripts/pyproject.toml scripts/backup.py`

---

## Task 8: 静态生成脚本 + 实际生成

**Files:** Create `scripts/generate.sh`

- [ ] **Step 1: `scripts/generate.sh`**
```bash
#!/usr/bin/env bash
# 生成静态站到 ./static(起一次性 gssg 容器;需 Ghost 已在跑)
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p static
echo "[generate] building + running gssg -> ./static ..."
docker compose --profile generate run --rm --build generate
echo "[generate] done -> ./static"
```

- [ ] **Step 2: 赋可执行 + 运行**

Run: `chmod +x scripts/generate.sh && ./scripts/generate.sh`
Expected: 构建生成器镜像、跑 gssg,结束打印 done。

- [ ] **Step 3: 校验静态产物**

Run: `test -s static/index.html && echo "index ok" && grep -c "shepherdloveyou.github.io/ada-blog" static/index.html`
Expected: 打印 `index ok`;`PAGES_URL` 在首页中出现(链接已改写)次数 > 0。

- [ ] **Step 4: 提交** `scripts/generate.sh`(`static/` 已被 gitignore)

---

## Task 9: 发布脚本(gh-pages 分支)

**Files:** Create `scripts/publish-pages.sh`

- [ ] **Step 1: `scripts/publish-pages.sh`**
```bash
#!/usr/bin/env bash
# 生成静态站并发布到 gh-pages 分支(需先有 origin 远端)
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
bash scripts/generate.sh
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "ERROR: 没有 'origin' 远端。先建 GitHub 仓库并 git remote add origin ..." >&2; exit 1
fi
WT="$(mktemp -d)"
trap 'git worktree remove --force "$WT" 2>/dev/null || true; rm -rf "$WT"' EXIT
git worktree add --force -B gh-pages "$WT"
rsync -a --delete --exclude='.git' "$ROOT/static/" "$WT/"
touch "$WT/.nojekyll"
cd "$WT"; git add -A
if git diff --cached --quiet; then echo "[publish] 无变化"; else
  git -c user.name="ShepherdLoveYou" -c user.email="yunfansong0@gmail.com" commit -q -m "publish static site"
fi
git push -u origin gh-pages --force
echo "[publish] 已推送 gh-pages"
```

- [ ] **Step 2: 赋可执行 + 语法检查**

Run: `chmod +x scripts/publish-pages.sh && bash -n scripts/publish-pages.sh && echo "syntax ok"`
Expected: `syntax ok`(实际推送等建仓后)。

- [ ] **Step 3: 提交** `scripts/publish-pages.sh`

---

## Task 10: README

**Files:** Create `README.md` — 覆盖:写作(起停 Ghost)、备份、生成静态、发布到 Pages、首配站点标题、邮件预留说明、上线 GitHub 步骤。

- [ ] **Step 1: 写 README** — 完整内容见仓库实现。
- [ ] **Step 2: 提交** `README.md`

---

## Task 11: GitHub 仓库 + 启用 Pages(**对外动作,执行前与用户确认**)

- [ ] **Step 1: 与用户确认** 仓库名、public/private(Pages 免费公开站需 public)。
- [ ] **Step 2: 建仓 + 推 main**

Run: `gh repo create <name> --public --source=. --remote=origin --push`

- [ ] **Step 3: 首次发布静态站**

Run: `./scripts/publish-pages.sh`

- [ ] **Step 4: 启用 Pages 指向 gh-pages**

Run: `gh api -X POST repos/ShepherdLoveYou/<name>/pages -f source.branch=gh-pages -f source.path=/`
Expected: 返回 Pages 配置;几分钟后 `PAGES_URL` 可访问。

---

## Task 12: 收尾 + finishing-a-development-branch

- [ ] **Step 1:** `git status` 干净(`.env`/`content/*`/`backups/*`/`static/`/`.ops-venv/` 均忽略)。
- [ ] **Step 2:** 对照 spec 第 8 节逐条验收。
- [ ] **Step 3:** 用 superpowers:finishing-a-development-branch 合并 `feat/ghost-docker-setup` → `main`。

---

## Self-Review(作者已核对)

- **Spec 覆盖:** Ghost本地/MySQL8/三类隔离/Pages导出/gssg容器/gh-pages发布/邮件预留/密钥/备份/主题/站点标题/验收 → 分别落在 Task 3、3b、5、7、8、9、11、2、10。无缺口。
- **占位扫描:** backup.py / README 标注"完整内容见仓库实现",实现时给全。
- **一致性:** `.env` 键(`GHOST_URL`/`MYSQL_*`/`PAGES_URL`)在 compose、backup.py、scripts、README 一致;服务名 `db`/`ghost`/`generate`、容器名 `ghost-db`/`ghost-app` 一致;`PAGES_URL` 默认 `https://shepherdloveyou.github.io/ada-blog`。

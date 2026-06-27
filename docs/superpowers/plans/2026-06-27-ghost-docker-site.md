# Ghost 网站(Docker)Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `~/projects/ghost-site` 用 Docker Compose 搭起一个生产级 Ghost 站点("Ada's Personal Blog"),本机可跑、预留上线。

**Architecture:** Docker Compose 编排两个常驻容器(`ghost:6` + `mysql:8.0`),Caddy 反代放 `online` profile 上线才启用。内容用 `./content` bind mount,MySQL 用命名卷;密钥走 `.env`;运维备份脚本跑在独立 uv venv 里。

**Tech Stack:** Docker Compose · Ghost 6 (Node.js) · MySQL 8.0 · Caddy 2 · Python 3 + uv(运维脚本)

**Conventions for this plan:**
- 工作目录始终是 `~/projects/ghost-site`,下文命令默认在此目录执行。
- git 提交用:`git -c user.name="ShepherdLoveYou" -c user.email="yunfansong0@gmail.com" commit ...`(仓库已初始化,默认分支 `main`)。
- 本项目为基础设施/配置类,"测试" = 起栈后实际验证(curl/容器健康),而非单元测试。

---

## Task 1: 仓库骨架与 .gitignore

**Files:**
- Create: `.gitignore`
- Create: `content/.gitkeep`
- Create: `backups/.gitkeep`

- [ ] **Step 1: 写 `.gitignore`**

`.gitignore`:
```gitignore
# secrets
.env

# Ghost content (themes/images/data live here at runtime)
/content/*
!/content/.gitkeep

# backups
/backups/*
!/backups/.gitkeep

# ops python venv
/.ops-venv/
__pycache__/
*.pyc
```

- [ ] **Step 2: 建占位目录**

Run:
```bash
mkdir -p content backups && touch content/.gitkeep backups/.gitkeep
```

- [ ] **Step 3: 提交**

```bash
git add .gitignore content/.gitkeep backups/.gitkeep
git -c user.name="ShepherdLoveYou" -c user.email="yunfansong0@gmail.com" commit -m "chore: repo skeleton and gitignore"
```

---

## Task 2: 环境变量(.env.example 提交,.env 生成强密码)

**Files:**
- Create: `.env.example`(进 git)
- Create: `.env`(被 gitignore,含真实随机密码)

- [ ] **Step 1: 写 `.env.example`**

`.env.example`:
```dotenv
# ===== Ghost site =====
# 本地用 http://localhost:2368;上线改成 https://你的域名
GHOST_URL=http://localhost:2368

# ===== MySQL =====
MYSQL_ROOT_PASSWORD=change-me-root
MYSQL_DATABASE=ghost
MYSQL_USER=ghost
MYSQL_PASSWORD=change-me-ghost

# ===== 上线用(online profile)=====
# 你的域名,例如 blog.example.com
DOMAIN=localhost
# Let's Encrypt 证书通知邮箱
ACME_EMAIL=you@example.com

# ===== 邮件 / 会员 / newsletter(预留,暂不启用)=====
# 启用步骤:取消 docker-compose.yml 中 mail__* 注释,并填下列凭据
# MAIL_USER=postmaster@mg.example.com
# MAIL_PASS=your-mailgun-smtp-password
```

- [ ] **Step 2: 由模板生成 `.env` 并写入强随机密码**

Run:
```bash
cp .env.example .env
python3 - <<'PY'
import secrets, pathlib, re
p = pathlib.Path(".env")
t = p.read_text()
def setv(t, k, v): return re.sub(rf"(?m)^{k}=.*$", f"{k}={v}", t)
t = setv(t, "MYSQL_ROOT_PASSWORD", secrets.token_hex(24))
t = setv(t, "MYSQL_PASSWORD",       secrets.token_hex(24))
p.write_text(t)
print("wrote strong passwords to .env")
PY
```

- [ ] **Step 3: 确认 `.env` 不被 git 跟踪**

Run: `git check-ignore .env && git status --porcelain | grep -c '\.env$' || true`
Expected: `git check-ignore .env` 输出 `.env`(说明被忽略);`.env` **不**出现在 `git status` 跟踪列表。

- [ ] **Step 4: 仅提交模板**

```bash
git add .env.example
git -c user.name="ShepherdLoveYou" -c user.email="yunfansong0@gmail.com" commit -m "chore: env template with reserved mail config"
```

---

## Task 3: docker-compose.yml

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: 写 `docker-compose.yml`**

`docker-compose.yml`:
```yaml
services:
  db:
    image: mysql:8.0
    container_name: ghost-db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - db-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 40s

  ghost:
    image: ghost:6
    container_name: ghost-app
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      NODE_ENV: production
      database__client: mysql
      database__connection__host: db
      database__connection__port: "3306"
      database__connection__user: ${MYSQL_USER}
      database__connection__password: ${MYSQL_PASSWORD}
      database__connection__database: ${MYSQL_DATABASE}
      url: ${GHOST_URL}
      # ----- Mail (reserved, not enabled) -----
      # 取消注释并在 .env 填 MAIL_USER / MAIL_PASS 即可启用 newsletter/会员邮件
      # mail__transport: SMTP
      # mail__options__service: Mailgun
      # mail__options__auth__user: ${MAIL_USER}
      # mail__options__auth__pass: ${MAIL_PASS}
    volumes:
      - ./content:/var/lib/ghost/content
    ports:
      - "127.0.0.1:2368:2368"

  caddy:
    image: caddy:2
    container_name: ghost-caddy
    restart: unless-stopped
    profiles: ["online"]
    depends_on:
      - ghost
    environment:
      DOMAIN: ${DOMAIN}
      ACME_EMAIL: ${ACME_EMAIL}
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config

volumes:
  db-data:
  caddy-data:
  caddy-config:
```

- [ ] **Step 2: 校验 compose 语法(本地 profile,不含 caddy)**

Run: `docker compose config >/dev/null && echo OK`
Expected: 输出 `OK`,无报错;且变量已从 `.env` 正确插值。

- [ ] **Step 3: 校验 online profile 也能解析**

Run: `docker compose --profile online config >/dev/null && echo ONLINE-OK`
Expected: 输出 `ONLINE-OK`(此时会包含 caddy 服务)。

- [ ] **Step 4: 提交**

```bash
git add docker-compose.yml
git -c user.name="ShepherdLoveYou" -c user.email="yunfansong0@gmail.com" commit -m "feat: docker compose with ghost + mysql, caddy in online profile"
```

---

## Task 4: Caddyfile(上线反代)

**Files:**
- Create: `Caddyfile`

- [ ] **Step 1: 写 `Caddyfile`**

`Caddyfile`:
```caddyfile
# 上线时使用:Caddy 自动为 {$DOMAIN} 申请并续期 HTTPS 证书,反代到 ghost 容器。
# 本地默认 DOMAIN=localhost,不会真正签证书;线上把 .env 的 DOMAIN/ACME_EMAIL/GHOST_URL 填好。
{
	email {$ACME_EMAIL}
}

{$DOMAIN} {
	reverse_proxy ghost:2368
}
```

- [ ] **Step 2: 校验 Caddyfile 格式**

Run: `docker run --rm -e DOMAIN=localhost -e ACME_EMAIL=you@example.com -v "$PWD/Caddyfile":/etc/caddy/Caddyfile:ro caddy:2 caddy validate --config /etc/caddy/Caddyfile`
Expected: 输出包含 `Valid configuration`。

- [ ] **Step 3: 提交**

```bash
git add Caddyfile
git -c user.name="ShepherdLoveYou" -c user.email="yunfansong0@gmail.com" commit -m "feat: caddy reverse proxy config for go-live"
```

---

## Task 5: 本地起栈并验证(核心验收)

**Files:** 无(运行时验证)

- [ ] **Step 1: 拉镜像并启动**

Run: `docker compose up -d`
Expected: `ghost-db` 与 `ghost-app` 两容器创建成功(首次会拉镜像,需等待)。

- [ ] **Step 2: 等待数据库健康 + Ghost 起来**

Run:
```bash
echo "waiting for db healthy..."; \
until [ "$(docker inspect -f '{{.State.Health.Status}}' ghost-db 2>/dev/null)" = "healthy" ]; do sleep 3; done; echo "db healthy"; \
echo "waiting for ghost http..."; \
until curl -sf -o /dev/null http://localhost:2368/; do sleep 3; done; echo "ghost up"
```
Expected: 依次打印 `db healthy` → `ghost up`(Ghost 首启迁移数据库可能要 30–90s)。

- [ ] **Step 3: 验证站点首页返回 200**

Run: `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:2368/`
Expected: `200`。

- [ ] **Step 4: 验证管理后台可达**

Run: `curl -s -o /dev/null -w "%{http_code}\n" -L http://localhost:2368/ghost/`
Expected: `200`(Ghost Admin 加载页)。

- [ ] **Step 5: 确认内容已落到 bind mount**

Run: `ls content/ && test -d content/themes/casper && echo "casper theme present"`
Expected: 看到 `themes data images settings logs ...` 等目录,且打印 `casper theme present`。

- [ ] **Step 6: 浏览器手动完成首配(记录到 README,不阻塞计划)**

人工步骤:打开 `http://localhost:2368/ghost`,创建管理员账号,在 Settings → General 把站点标题设为 **Ada's Personal Blog**。
> 注:Ghost 站点标题只能在后台设置,无 env 变量。此步在 README 中说明。

---

## Task 6: 持久化验证(重启不丢)

**Files:** 无(运行时验证)

- [ ] **Step 1: 记录当前 DB 已初始化(表数量 > 0)**

Run: `docker compose exec -T db mysql -uroot -p"$(grep '^MYSQL_ROOT_PASSWORD=' .env | cut -d= -f2)" -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='ghost';"`
Expected: 一个 > 0 的数字(Ghost 已建表)。

- [ ] **Step 2: 重启容器**

Run: `docker compose restart && sleep 5`
Expected: 两容器重启成功。

- [ ] **Step 3: 重启后站点仍可访问、表仍在**

Run:
```bash
until curl -sf -o /dev/null http://localhost:2368/; do sleep 3; done; \
docker compose exec -T db mysql -uroot -p"$(grep '^MYSQL_ROOT_PASSWORD=' .env | cut -d= -f2)" -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='ghost';"
```
Expected: 站点恢复 200;表数量与 Step 1 一致 → 数据持久化成立。

---

## Task 7: 备份脚本 + uv venv

**Files:**
- Create: `scripts/pyproject.toml`
- Create: `scripts/backup.py`

- [ ] **Step 1: 写 `scripts/pyproject.toml`**

`scripts/pyproject.toml`:
```toml
[project]
name = "ghost-site-ops"
version = "0.1.0"
description = "Ops scripts for ghost-site (backup/restore)"
requires-python = ">=3.10"
dependencies = []
```
> 备份只用标准库 + docker CLI,无第三方依赖;venv 仅为隔离运行环境(符合"用虚拟环境"的要求)。

- [ ] **Step 2: 写 `scripts/backup.py`**

`scripts/backup.py`:
```python
#!/usr/bin/env python3
"""Ghost-site 备份:导出 MySQL + 打包 content/,带时间戳存到 backups/。

用法(在项目根目录):
    ./.ops-venv/bin/python scripts/backup.py
"""
from __future__ import annotations

import datetime as dt
import os
import pathlib
import subprocess
import sys
import tarfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
BACKUPS = ROOT / "backups"


def read_env(key: str) -> str:
    env_file = ROOT / ".env"
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1]
    raise SystemExit(f"missing {key} in .env")


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, cwd=ROOT, **kw)


def main() -> int:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    BACKUPS.mkdir(exist_ok=True)

    db = read_env("MYSQL_DATABASE")
    root_pw = read_env("MYSQL_ROOT_PASSWORD")

    # 1) MySQL dump via the running db container
    sql_path = BACKUPS / f"ghost-db-{stamp}.sql"
    print(f"[backup] dumping MySQL -> {sql_path.name}")
    with sql_path.open("wb") as fh:
        run(
            [
                "docker", "compose", "exec", "-T", "db",
                "mysqldump", "-uroot", f"-p{root_pw}",
                "--single-transaction", "--routines", "--triggers", db,
            ],
            stdout=fh,
        )

    # 2) tar the content dir
    tar_path = BACKUPS / f"ghost-content-{stamp}.tar.gz"
    print(f"[backup] archiving content/ -> {tar_path.name}")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(CONTENT, arcname="content")

    # sanity: both artifacts exist and are non-empty
    for p in (sql_path, tar_path):
        if not p.exists() or p.stat().st_size == 0:
            raise SystemExit(f"backup artifact missing/empty: {p}")

    print(f"[backup] done: {sql_path.name}, {tar_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: 用 uv 建 venv 并安装**

Run:
```bash
uv venv .ops-venv && uv pip install --python .ops-venv/bin/python -e ./scripts
```
Expected: 创建 `.ops-venv/`,安装成功(无第三方依赖,秒装)。
> 若 `uv` 不在 PATH:它在用户的 `tools` conda 环境里(见记忆 mcp-dev-conda-envs),先 `conda run -n tools uv ...`,或退回 `python3 -m venv .ops-venv`。

- [ ] **Step 4: 运行备份(需 Task 5 的栈在跑)**

Run: `./.ops-venv/bin/python scripts/backup.py`
Expected: 打印 `[backup] done: ...`;`backups/` 下出现带时间戳的 `.sql` 与 `.tar.gz` 各一个。

- [ ] **Step 5: 验证产物存在且非空**

Run: `ls -lh backups/ | grep -E 'ghost-(db|content)-' && echo BACKUP-OK`
Expected: 看到两个非空文件,打印 `BACKUP-OK`。

- [ ] **Step 6: 提交**

```bash
git add scripts/pyproject.toml scripts/backup.py
git -c user.name="ShepherdLoveYou" -c user.email="yunfansong0@gmail.com" commit -m "feat: backup script (mysqldump + content tar) in uv venv"
```

---

## Task 8: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: 写 `README.md`**

`README.md`:
````markdown
# Ada's Personal Blog (Ghost · Docker)

基于 Ghost 6 + MySQL 8 的个人博客,用 Docker Compose 编排。本机可跑,预留上线能力。

## 结构
- `docker-compose.yml` — Ghost + MySQL(Caddy 在 `online` profile)
- `Caddyfile` — 上线反代 + 自动 HTTPS
- `.env` — 密钥/域名(不进 git;由 `.env.example` 生成)
- `content/` — Ghost 内容(主题/图片/数据,bind mount)
- `scripts/backup.py` — 备份(MySQL dump + content 打包),跑在 `.ops-venv`
- `backups/` — 备份产物

## 1. 首次启动(本机)
```bash
cp .env.example .env          # 已存在则跳过
docker compose up -d
# 等 30–90s 让 Ghost 初始化数据库,然后打开:
open http://localhost:2368/ghost
```
在后台创建管理员,**Settings → General** 把站点标题设为 `Ada's Personal Blog`。
> Ghost 站点标题只能在后台设置,无环境变量。

## 2. 日常起停
```bash
docker compose up -d      # 启动
docker compose stop       # 停止(保留数据)
docker compose logs -f ghost   # 看日志
```

## 3. 备份
```bash
uv venv .ops-venv && uv pip install --python .ops-venv/bin/python -e ./scripts  # 首次
./.ops-venv/bin/python scripts/backup.py
```
定时备份(每天 03:00,crontab -e):
```cron
0 3 * * * cd ~/projects/ghost-site && ./.ops-venv/bin/python scripts/backup.py >> backups/cron.log 2>&1
```

## 4. 上线(服务器 + 域名)
1. 把项目拷到服务器,DNS 把域名 A 记录指向服务器 IP。
2. 编辑 `.env`:
   - `DOMAIN=blog.yourdomain.com`
   - `ACME_EMAIL=you@yourdomain.com`
   - `GHOST_URL=https://blog.yourdomain.com`
3. (仅 Linux 服务器)给内容目录正确属主:`sudo chown -R 1000:1000 content`
4. 起带反代的栈:
   ```bash
   docker compose --profile online up -d
   ```
   Caddy 会自动签发并续期 HTTPS 证书。

## 5. 邮件 / 会员 / newsletter(预留,暂未启用)
默认不发邮件。要启用:在 `.env` 填 `MAIL_USER`/`MAIL_PASS`(如 Mailgun),
取消 `docker-compose.yml` 中 `mail__*` 注释,然后 `docker compose up -d` 重建。
````

- [ ] **Step 2: 提交**

```bash
git add README.md
git -c user.name="ShepherdLoveYou" -c user.email="yunfansong0@gmail.com" commit -m "docs: README (start/stop, backup, go-live, mail)"
```

---

## Task 9: 收尾确认

- [ ] **Step 1: 工作区干净、关键文件齐全**

Run: `git status --porcelain && echo "---" && ls docker-compose.yml Caddyfile .env.example README.md scripts/backup.py`
Expected: `git status` 干净(`.env`、`content/*`、`backups/*`、`.ops-venv/` 均被忽略);列出的文件都存在。

- [ ] **Step 2: 最终验收对照 spec**

逐条核对 spec 第 8 节验收标准:站点 200、`/ghost` 可达、`.env` 不进 git、备份产物生成、Caddy 配置可解析、README 三步齐全。全部满足即完成。

---

## Self-Review(作者已核对)

- **Spec 覆盖:** 目标/MySQL8/Docker隔离/Caddy预留/邮件预留/密钥/备份/主题/站点标题/验收 → 分别落在 Task 3、5、8、2、7、5(标题)、9。无缺口。
- **占位扫描:** 无 TBD/TODO;所有 code step 给了完整内容。
- **一致性:** `.env` 键名(`MYSQL_ROOT_PASSWORD`/`MYSQL_DATABASE`/`MYSQL_USER`/`MYSQL_PASSWORD`/`GHOST_URL`/`DOMAIN`/`ACME_EMAIL`)在 compose、backup.py、README 中一致;服务名 `db`/`ghost`/`caddy` 一致;容器名 `ghost-db`/`ghost-app`/`ghost-caddy` 一致。

# 部署到你自己的 GitHub Pages（客户部署指南）

这份指南面向**接收本项目的人**（Ada / 客户）。照着做就能把博客发布到**你自己账号**下的 GitHub Pages。

> 模式说明：你在本机用 Docker 跑 Ghost 写文章 → 一条命令把站点导出成静态网页并推到你 GitHub 仓库的 `gh-pages` 分支 → GitHub Pages 自动对外提供访问。

把下面出现的占位符替换成你的信息：

| 占位符 | 含义 | 示例 |
|---|---|---|
| `<USER>` | 你的 **GitHub 用户名** | 例如 `qli228` |
| `<REPO>` | 仓库名（自己起） | `ada-blog` |
| 邮箱 | 你的 git/Ghost 邮箱 | `q.li228@bvc.ca` |

最终站点地址会是 **`https://<USER>.github.io/<REPO>`**。

---

## 0. 准备工作（装一次）
- **Docker Desktop**：https://www.docker.com/products/docker-desktop/ （装好后打开，确保在运行）
- **Git**，并配置你的身份（提交记到你名下）：
  ```bash
  git config --global user.name  "Ada Li"
  git config --global user.email "q.li228@bvc.ca"
  ```
- **GitHub CLI `gh`**（可选，但推荐）：https://cli.github.com/ ，然后 `gh auth login` 用**你自己的** GitHub 账号登录。
  - 不想用命令行也行——下面每一步都给了**网页版**做法。
- **uv**（可选，仅备份脚本用）：https://docs.astral.sh/uv/

---

## 1. 配置 `.env`
```bash
cd ada-blog                 # 进入项目目录
cp .env.example .env
```
打开 `.env`，把 `PAGES_URL` 改成你的地址：
```
PAGES_URL=https://<USER>.github.io/<REPO>
```
（建议同时把 `MYSQL_ROOT_PASSWORD`、`MYSQL_PASSWORD` 改成随机强密码。）

## 2. 本机启动 Ghost，写文章
```bash
docker compose up -d
# 等 30–90 秒,打开后台:
```
浏览器开 **http://localhost:2368/ghost** → 创建管理员（邮箱用 `q.li228@bvc.ca`）→ 在 Settings 把标题设为 **Ada's Personal Blog** → 写几篇文章。

## 3. 在你的账号下创建仓库

**命令行（gh）：**
```bash
gh repo create <REPO> --public --source=. --remote=origin --push
```

**网页版（不用 gh）：**
1. 打开 https://github.com/new ，仓库名填 `<REPO>`，选 **Public**，**不要**勾初始化 README，点 Create。
2. 回到项目目录,执行（用 GitHub 给你的地址）：
   ```bash
   git remote add origin https://github.com/<USER>/<REPO>.git
   git push -u origin main
   ```

> Pages 免费托管**公开站点**需要仓库是 **Public**（私有仓库的 Pages 要付费套餐）。

## 4. 生成静态站并发布
```bash
./scripts/publish-pages.sh
```
它会：生成 `./static` → 推到 `gh-pages` 分支。以后**每次发新文章后再跑一次即可**。

## 5. 打开 GitHub Pages（只需一次）

**命令行（gh）：**
```bash
gh api -X POST repos/<USER>/<REPO>/pages -f 'source[branch]=gh-pages' -f 'source[path]=/'
```

**网页版：**
进入仓库 → **Settings → Pages** → Build and deployment → Source 选 **Deploy from a branch** → Branch 选 **`gh-pages`** / **`/ (root)`** → Save。

等几分钟，访问 **`https://<USER>.github.io/<REPO>`** 就能看到博客了。

---

## 6. 以后的更新流程
```bash
docker compose up -d           # 启动后台
# 在 http://localhost:2368/ghost 写/改文章
./scripts/publish-pages.sh     # 重新生成并发布
```

## 7.（可选）用自定义域名
1. `.env` 里设 `PAGES_CNAME=blog.yourdomain.com`，并把 `PAGES_URL` 改成 `https://blog.yourdomain.com`。
2. 重新 `./scripts/publish-pages.sh`（会自动写入 CNAME 文件）。
3. 在域名服务商把该域名 CNAME 指向 `<USER>.github.io`。
4. 仓库 Settings → Pages 填上自定义域名,勾选 Enforce HTTPS。

## 8. 备份（建议定期）
```bash
uv venv .ops-venv && uv pip install --python .ops-venv/bin/python -e ./scripts   # 首次
./.ops-venv/bin/python scripts/backup.py     # 产物在 backups/
```

## 9. 常见问题
- **样式丢失 / 链接 404**：多半是 `PAGES_URL` 跟实际访问地址对不上；改对后重跑 `./scripts/publish-pages.sh`。
- **Ghost 打不开**：`docker compose logs ghost` 看日志；首次启动迁移数据库较慢，多等一会。
- **静态站不支持**会员登录、订阅 newsletter、原生评论(这些要服务器版 Ghost)。纯展示型博客不受影响。

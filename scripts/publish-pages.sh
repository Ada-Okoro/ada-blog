#!/usr/bin/env bash
# 生成静态站并发布到 gh-pages 分支(需先有 origin 远端)。
# GitHub Pages 设置为从 gh-pages 分支根目录提供服务。
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

# 1) 生成最新静态站
bash scripts/generate.sh

# 2) 必须已有 origin 远端
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "ERROR: 没有 'origin' 远端。先创建 GitHub 仓库,例如:" >&2
  echo "  gh repo create ada-blog --public --source=. --remote=origin --push" >&2
  exit 1
fi

# 3) 用临时 worktree 把 ./static 完整替换到 gh-pages 分支
WT="$(mktemp -d)"
trap 'git worktree remove --force "$WT" 2>/dev/null || true; rm -rf "$WT"' EXIT
git worktree add --force -B gh-pages "$WT"
rsync -a --delete --exclude='.git' "$ROOT/static/" "$WT/"
touch "$WT/.nojekyll"   # 关闭 Jekyll,正常提供 _ 开头的资源目录

# 自定义域名:每次发布都写回 CNAME,避免 force-push 丢失(.env 里设 PAGES_CNAME=blog.example.com)
PAGES_CNAME="$(grep -E '^PAGES_CNAME=' .env 2>/dev/null | head -1 | cut -d= -f2- || true)"
if [ -n "${PAGES_CNAME:-}" ]; then
  echo "$PAGES_CNAME" > "$WT/CNAME"
  echo "[publish] wrote CNAME: $PAGES_CNAME"
fi

cd "$WT"
git add -A
if git diff --cached --quiet; then
  echo "[publish] 无变化,跳过提交"
else
  git -c user.name="ShepherdLoveYou" -c user.email="yunfansong0@gmail.com" \
      commit -q -m "publish static site"
fi
# 优先 --force-with-lease(不盲目覆盖他人改动);分支首次不存在时回退到 --force
git push -u origin gh-pages --force-with-lease 2>/dev/null \
  || git push -u origin gh-pages --force
echo "[publish] 已推送到 gh-pages 分支"

#!/usr/bin/env bash
# 生成静态站到 ./static(起一次性 gssg 容器;需 Ghost 已在跑)。
#
# 从 .env 的 PAGES_URL 自动推导:
#   - 项目站(子路径)  PAGES_URL=https://user.github.io/ada-blog
#       -> gssg --url https://user.github.io --subDir ada-blog(资源用相对路径,子路径下可用)
#   - 用户站/自定义域名 PAGES_URL=https://blog.example.com
#       -> gssg --url https://blog.example.com(根路径,无需 subDir)
set -euo pipefail
cd "$(dirname "$0")/.."
# 干净构建:清空旧产物,避免已删除的文章/页面在 static 里残留(gssg 镜像不会删旧文件)
rm -rf static && mkdir -p static

PAGES_URL="$(grep -E '^PAGES_URL=' .env | head -1 | cut -d= -f2-)"
[ -n "$PAGES_URL" ] || { echo "ERROR: PAGES_URL not set in .env" >&2; exit 1; }

origin="$(printf '%s' "$PAGES_URL" | sed -E 's#^(https?://[^/]+).*#\1#')"
subpath="$(printf '%s' "$PAGES_URL" | sed -E 's#^https?://[^/]+/?##; s#/$##')"

args=(--url "$origin")
if [ -n "$subpath" ]; then
  args+=(--subDir "$subpath")
  echo "[generate] subdir mode: ${origin} /${subpath}"
else
  echo "[generate] root mode: ${origin}"
fi

echo "[generate] building + running gssg -> ./static ..."
docker compose --profile generate run --rm --build generate gssg "${args[@]}"
echo "[generate] done -> ./static"

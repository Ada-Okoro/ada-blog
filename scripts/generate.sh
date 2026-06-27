#!/usr/bin/env bash
# 生成静态站到 ./static(起一次性 gssg 容器;需 Ghost 已在跑)。
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p static
echo "[generate] building + running gssg -> ./static ..."
docker compose --profile generate run --rm --build generate
echo "[generate] done -> ./static"

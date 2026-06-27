#!/usr/bin/env python3
"""Ghost-site 备份:导出 MySQL + 打包 content/,带时间戳存到 backups/。

用法(在项目根目录):
    ./.ops-venv/bin/python scripts/backup.py

说明:mysqldump 在 db 容器内执行,密码从容器自身环境变量(MYSQL_PWD)读取,
不经过宿主机命令行参数(避免出现在 `ps`/进程列表里)。
"""
from __future__ import annotations

import datetime as dt
import pathlib
import subprocess
import sys
import tarfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
BACKUPS = ROOT / "backups"


def read_env(key: str) -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"missing {key} in .env")


def main() -> int:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    BACKUPS.mkdir(exist_ok=True)

    db = read_env("MYSQL_DATABASE")  # 非敏感

    # 1) MySQL dump —— 密码在容器内从 $MYSQL_ROOT_PASSWORD 读取(经 MYSQL_PWD),不进宿主 argv
    sql_path = BACKUPS / f"ghost-db-{stamp}.sql"
    print(f"[backup] dumping MySQL -> {sql_path.name}")
    inner = (
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" '
        'mysqldump -uroot --single-transaction --routines --triggers "$1"'
    )
    with sql_path.open("wb") as fh:
        subprocess.run(
            ["docker", "compose", "exec", "-T", "db", "sh", "-c", inner, "_", db],
            check=True, cwd=ROOT, stdout=fh,
        )

    # 完整性:mysqldump 正常结束会写入 "-- Dump completed"
    tail = sql_path.read_bytes()[-200:]
    if b"Dump completed" not in tail:
        raise SystemExit(f"dump looks incomplete (no end marker): {sql_path}")

    # 2) 打包 content/(排除 logs,避免把实时日志卷进备份)
    tar_path = BACKUPS / f"ghost-content-{stamp}.tar.gz"
    print(f"[backup] archiving content/ -> {tar_path.name}")

    def _filter(info: tarfile.TarInfo):
        return None if info.name.startswith("content/logs") else info

    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(CONTENT, arcname="content", filter=_filter)

    for p in (sql_path, tar_path):
        if not p.exists() or p.stat().st_size == 0:
            raise SystemExit(f"backup artifact missing/empty: {p}")

    print(f"[backup] done: {sql_path.name}, {tar_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

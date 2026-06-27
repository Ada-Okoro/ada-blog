#!/usr/bin/env python3
"""Ghost-site 备份:导出 MySQL + 打包 content/,带时间戳存到 backups/。

用法(在项目根目录):
    ./.ops-venv/bin/python scripts/backup.py
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

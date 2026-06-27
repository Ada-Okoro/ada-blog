#!/usr/bin/env python3
"""清掉 demo 文章,并基于 tools/posts/*.html 发布 Ada 的真实项目文章(幂等:按 slug upsert)。

    GHOST_USER=... GHOST_PASS=... ./.ops-venv/bin/python scripts/seed-posts.py
"""
from __future__ import annotations
import os, json, datetime as dt, pathlib, urllib.request, urllib.error, http.cookiejar

BASE = "http://localhost:2368/ghost/api/admin"
ORIGIN = "http://localhost:2368"
ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "tools/posts"

# 展示顺序(从上到下):climate, income, welcome
SPEC = [
    {"slug": "weather-retail-sales", "file": "weather-retail-sales.html",
     "title": "Does Weather Drive Retail Sales? Climate–Sales Correlation across AB, BC & ON (2013–2022)",
     "excerpt": "A decade of data on how temperature and precipitation relate to retail sales — and what it means for forecasting.",
     "tag": "Data Analytics"},
    {"slug": "alberta-graduate-income", "file": "alberta-graduate-income.html",
     "title": "Cleaning & Filtering Alberta Graduate Income Data with Python (pandas)",
     "excerpt": "Turning a bulky Statistics Canada table into a focused, analysis-ready dataset.",
     "tag": "Data Analytics"},
    {"slug": "welcome", "file": "welcome.html",
     "title": "Welcome — data, decisions, and a bit of weather",
     "excerpt": "What this blog is about, and what you'll find here.",
     "tag": "Updates"},
]
DEMO_SLUGS = {"hi", "coming-soon", "welcome-short", "welcome-to-ghost"}

cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def req(method, path, body=None):
    h = {"Origin": ORIGIN, "Accept": "application/json"}
    data = None
    if isinstance(body, (dict, list)):
        data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    def parse(raw):
        if not raw.strip():
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    try:
        resp = OP.open(r); return resp.status, parse(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, parse(e.read().decode())


def main() -> int:
    s, r = req("POST", "/session/", {"username": os.environ["GHOST_USER"],
                                     "password": os.environ["GHOST_PASS"]})
    print("[login]", s)
    if s not in (200, 201):
        raise SystemExit(f"login failed: {r}")

    # 1) 删除 demo 文章
    s, r = req("GET", "/posts/?limit=all&fields=id,slug,title")
    existing = {p["slug"]: p for p in r.get("posts", [])} if isinstance(r, dict) else {}
    for slug, p in list(existing.items()):
        if slug in DEMO_SLUGS or p.get("title") in ("HI", "Coming soon"):
            ds, _ = req("DELETE", f"/posts/{p['id']}/")
            print(f"[delete demo] {p.get('title')} ({slug}): {ds}")

    # 2) upsert 真实文章
    now = dt.datetime.now(dt.timezone.utc)
    for i, sp in enumerate(SPEC):
        html = (POSTS / sp["file"]).read_text()
        pub = (now - dt.timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        payload = {
            "title": sp["title"], "slug": sp["slug"], "html": html,
            "custom_excerpt": sp["excerpt"], "status": "published",
            "tags": [{"name": sp["tag"]}], "published_at": pub,
        }
        s, r = req("GET", f"/posts/?filter=slug:{sp['slug']}&fields=id,updated_at")
        found = r.get("posts") if isinstance(r, dict) else None
        if found:
            payload["updated_at"] = found[0]["updated_at"]
            s, r = req("PUT", f"/posts/{found[0]['id']}/?source=html", {"posts": [payload]})
            print(f"[update] {sp['slug']}: {s}")
        else:
            s, r = req("POST", "/posts/?source=html", {"posts": [payload]})
            print(f"[create] {sp['slug']}: {s}")
        if s not in (200, 201):
            print("   ->", str(r)[:200])

    print("[done] posts seeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

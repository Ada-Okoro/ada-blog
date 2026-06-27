#!/usr/bin/env python3
"""把项目文设 featured=true,其余 false(用于首页 Work/Writing 分区)。

    GHOST_USER=... GHOST_PASS=... ./.ops-venv/bin/python scripts/mark-featured.py
"""
import os, json, urllib.request, urllib.error, http.cookiejar

BASE = "http://localhost:2368/ghost/api/admin"
ORIGIN = "http://localhost:2368"
FEATURED = {"weather-retail-sales", "alberta-graduate-income"}

cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def parse(r):
    if not r.strip():
        return {}
    try:
        return json.loads(r)
    except json.JSONDecodeError:
        return r


def req(m, p, b=None):
    h = {"Origin": ORIGIN, "Accept": "application/json"}
    d = None
    if isinstance(b, (dict, list)):
        d = json.dumps(b).encode(); h["Content-Type"] = "application/json"
    rq = urllib.request.Request(BASE + p, data=d, headers=h, method=m)
    try:
        x = OP.open(rq); return x.status, parse(x.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, parse(e.read().decode())


s, _ = req("POST", "/session/", {"username": os.environ["GHOST_USER"],
                                 "password": os.environ["GHOST_PASS"]})
if s not in (200, 201):
    raise SystemExit(f"login failed: {s}")
s, r = req("GET", "/posts/?limit=all&fields=id,slug,featured,updated_at")
for p in r["posts"]:
    want = p["slug"] in FEATURED
    if p["featured"] != want:
        st, _ = req("PUT", f"/posts/{p['id']}/",
                    {"posts": [{"featured": want, "updated_at": p["updated_at"]}]})
        print(f"{p['slug']} featured={want}: {st}")
print("done")

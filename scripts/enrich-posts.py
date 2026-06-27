#!/usr/bin/env python3
"""为 Climate 文章上传真实仪表盘图:设题图 + 正文嵌图;并设置站点分享图(og/twitter)。

    GHOST_USER=... GHOST_PASS=... ./.ops-venv/bin/python scripts/enrich-posts.py
"""
from __future__ import annotations
import os, json, uuid, pathlib, urllib.request, urllib.error, http.cookiejar

BASE = "http://localhost:2368/ghost/api/admin"
ORIGIN = "http://localhost:2368"
ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "tools/posts/img"

cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def parse(raw):
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def req(method, path, body=None, headers=None):
    h = {"Origin": ORIGIN, "Accept": "application/json"}
    data = None
    if isinstance(body, (dict, list)):
        data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    elif isinstance(body, (bytes, bytearray)):
        data = body
    if headers:
        h.update(headers)
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        resp = OP.open(r); return resp.status, parse(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, parse(e.read().decode())


def upload(path: pathlib.Path, ctype: str) -> str:
    data = path.read_bytes()
    b = "----ada" + uuid.uuid4().hex
    pre = (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
           f"Content-Type: {ctype}\r\n\r\n").encode()
    mid = (f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nimage\r\n--{b}--\r\n").encode()
    s, r = req("POST", "/images/upload/", body=pre + data + mid,
               headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    if s in (200, 201) and isinstance(r, dict):
        return r["images"][0]["url"]
    raise SystemExit(f"upload failed {s}: {r}")


def fig(url, cap, alt):
    return (f'<figure class="kg-card kg-image-card kg-card-hascaption">'
            f'<img src="{url}" alt="{alt}"><figcaption>{cap}</figcaption></figure>')


def main() -> int:
    s, r = req("POST", "/session/", {"username": os.environ["GHOST_USER"],
                                     "password": os.environ["GHOST_PASS"]})
    print("[login]", s)
    if s not in (200, 201):
        raise SystemExit(r)

    feat = upload(IMG / "dashboard-correlation-ab.png", "image/png")
    prep = upload(IMG / "tableau-prep-flow.png", "image/png")
    ind = upload(IMG / "industry-correlations-ab.jpg", "image/jpeg")
    print("[uploaded]", feat.split('/')[-1], prep.split('/')[-1], ind.split('/')[-1])

    html = (ROOT / "tools/posts/weather-retail-sales.html").read_text()
    html = html.replace(
        "<h2>Key findings</h2>",
        fig(prep, "Cleaning and shaping the climate &amp; retail data in Tableau Prep.",
            "Tableau Prep flow") + "\n<h2>Key findings</h2>", 1)
    html = html.replace(
        "<h2>What I'd recommend</h2>",
        fig(ind, "Industry-level temperature &amp; precipitation correlations (Alberta example).",
            "Industry correlation dashboard") + "\n<h2>What I'd recommend</h2>", 1)

    s, r = req("GET", "/posts/?filter=slug:weather-retail-sales&fields=id,updated_at")
    p = r["posts"][0]
    payload = {
        "title": "Does Weather Drive Retail Sales? Climate–Sales Correlation across AB, BC & ON (2013–2022)",
        "slug": "weather-retail-sales",
        "html": html, "feature_image": feat, "status": "published",
        "custom_excerpt": "A decade of data on how temperature and precipitation relate to retail sales — and what it means for forecasting.",
        "tags": [{"name": "Data Analytics"}],
        "updated_at": p["updated_at"],
    }
    s, r = req("PUT", f"/posts/{p['id']}/?source=html", {"posts": [payload]})
    print("[climate post update]", s)
    if s != 200:
        print("   ->", str(r)[:200])

    # 站点分享图(og/twitter)
    s, r = req("PUT", "/settings/", {"settings": [
        {"key": "og_image", "value": feat}, {"key": "twitter_image", "value": feat}]})
    print("[og/twitter image]", s)

    print("[done] climate post enriched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""配图 + 排序:
- 气候文:题图(AB 仪表盘)+ 正文嵌图(Tableau Prep 流程、分省系列 BC/ON、行业相关性)
- 收入文:notebook 截图作题图
- 置顶 Welcome(featured + 最新 published_at)
- 站点分享图 og/twitter

    GHOST_USER=... GHOST_PASS=... ./.ops-venv/bin/python scripts/enrich-posts.py
"""
from __future__ import annotations
import os, json, uuid, datetime as dt, pathlib, urllib.request, urllib.error, http.cookiejar

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


def upload(name: str, ctype: str) -> str:
    p = IMG / name
    data = p.read_bytes()
    b = "----ada" + uuid.uuid4().hex
    pre = (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
           f"Content-Type: {ctype}\r\n\r\n").encode()
    mid = (f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nimage\r\n--{b}--\r\n").encode()
    s, r = req("POST", "/images/upload/", body=pre + data + mid,
               headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    if s in (200, 201) and isinstance(r, dict):
        return r["images"][0]["url"]
    raise SystemExit(f"upload {name} failed {s}: {r}")


def fig(url, cap, alt):
    return (f'<figure class="kg-card kg-image-card kg-card-hascaption">'
            f'<img src="{url}" alt="{alt}"><figcaption>{cap}</figcaption></figure>')


def get_post(slug):
    s, r = req("GET", f"/posts/?filter=slug:{slug}&fields=id,updated_at")
    return r["posts"][0] if isinstance(r, dict) and r.get("posts") else None


def main() -> int:
    s, r = req("POST", "/session/", {"username": os.environ["GHOST_USER"],
                                     "password": os.environ["GHOST_PASS"]})
    print("[login]", s)
    if s not in (200, 201):
        raise SystemExit(r)

    feat = upload("dashboard-correlation-ab.png", "image/png")
    prep = upload("tableau-prep-flow.png", "image/png")
    ind = upload("industry-correlations-ab.jpg", "image/jpeg")
    bc = upload("dashboard-correlation-bc.png", "image/png")
    on = upload("dashboard-correlation-on.png", "image/png")
    nb = upload("notebook-income-filter.png", "image/png")
    print("[uploaded] 6 images")

    # ---- 气候文:题图 + 嵌图 + 分省系列 ----
    html = (ROOT / "tools/posts/weather-retail-sales.html").read_text()
    html = html.replace(
        "<h2>Key findings</h2>",
        fig(prep, "Cleaning and shaping the climate &amp; retail data in Tableau Prep.",
            "Tableau Prep flow") + "\n<h2>Key findings</h2>", 1)
    province = (
        "<h2>A closer look by province</h2>"
        "<p>Scale and climate differ across the three provinces, but the signal is consistent. "
        "British Columbia is the mildest and wettest (avg ~10.9°C, ~119&nbsp;mm precipitation), "
        "Alberta the coldest and driest (~1.2°C, ~28&nbsp;mm), and Ontario sits in between "
        "(~4.6°C, ~86&nbsp;mm) while being by far the largest retail market. Despite these "
        "differences, precipitation tracks near zero with sales in every province, while "
        "temperature shows a small positive correlation — strongest in Ontario. "
        "(Alberta's dashboard is shown at the top of this post.)</p>"
        + fig(bc, "British Columbia — precipitation vs. temperature correlation with sales.",
              "British Columbia correlation dashboard")
        + fig(on, "Ontario — precipitation vs. temperature correlation with sales.",
              "Ontario correlation dashboard")
    )
    html = html.replace(
        "<h2>What I'd recommend</h2>",
        province + "\n"
        + fig(ind, "Industry-level temperature &amp; precipitation correlations (Alberta example).",
              "Industry correlation dashboard")
        + "\n<h2>What I'd recommend</h2>", 1)

    p = get_post("weather-retail-sales")
    payload = {
        "title": "Does Weather Drive Retail Sales? Climate–Sales Correlation across AB, BC & ON (2013–2022)",
        "slug": "weather-retail-sales", "html": html, "feature_image": feat,
        "status": "published",
        "custom_excerpt": "A decade of data on how temperature and precipitation relate to retail sales — and what it means for forecasting.",
        "tags": [{"name": "Data Analytics"}], "updated_at": p["updated_at"],
    }
    s, r = req("PUT", f"/posts/{p['id']}/?source=html", {"posts": [payload]})
    print("[climate] feature + province series + figures:", s)
    if s != 200:
        print("   ->", str(r)[:200])

    # ---- 收入文:notebook 题图 ----
    p = get_post("alberta-graduate-income")
    s, r = req("PUT", f"/posts/{p['id']}/",
               {"posts": [{"feature_image": nb, "updated_at": p["updated_at"]}]})
    print("[income] notebook feature image:", s)

    # ---- 置顶 Welcome:featured + 最新发布时间 ----
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    p = get_post("welcome")
    s, r = req("PUT", f"/posts/{p['id']}/",
               {"posts": [{"featured": True, "published_at": now, "updated_at": p["updated_at"]}]})
    print("[welcome] pinned (featured + newest):", s)
    if s != 200:
        print("   ->", str(r)[:200])

    # ---- 站点分享图 ----
    s, r = req("PUT", "/settings/", {"settings": [
        {"key": "og_image", "value": feat}, {"key": "twitter_image", "value": feat}]})
    print("[og/twitter image]", s)

    print("[done] enrichment + ordering applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

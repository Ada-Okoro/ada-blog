#!/usr/bin/env python3
"""个性化 Ghost 站点(方向 C):关闭订阅、设头像/简介/导航、注入 CSS、建 About 页。

凭据走环境变量(不写进仓库):
    GHOST_USER='ada.li.career@gmail.com' GHOST_PASS='...' ./.ops-venv/bin/python scripts/personalize.py
"""
from __future__ import annotations
import json, os, pathlib, urllib.request, urllib.error, http.cookiejar, uuid

BASE = "http://localhost:2368/ghost/api/admin"
ORIGIN = "http://localhost:2368"
ROOT = pathlib.Path(__file__).resolve().parent.parent

NAME = "Qian Li · Data & Business Analyst"   # 站点标题
HERO_NAME = "Qian Li (Ada)"                   # hero 里显示的个人名字
GITHUB_URL = "https://github.com/Ada-Okoro"
LINKEDIN_URL = "https://www.linkedin.com/in/qianli-cv/"
BIO = ("PMP-certified analyst with 6+ years in business analysis & data analytics — "
       "helping teams make data-driven decisions. SQL · Power BI · Tableau.")
NAV = [
    {"label": "Work", "url": "/"},
    {"label": "Writing", "url": "/#writing"},
    {"label": "About", "url": "/about/"},
]
ABOUT_HTML = (
    "<p><strong>Hi, I'm Qian Li (Ada) 👋</strong></p>"
    "<p>PMP-certified professional with 6+ years of experience in business analysis, project "
    "coordination, and data analytics across insurance, IT, and financial services. I focus on "
    "data-driven decision-making, requirements gathering, and process optimization — and I'm "
    "currently deepening my data analytics expertise.</p>"
    "<p><strong>What I work with:</strong> SQL · Excel (Power Query/Pivot) · Power BI · Tableau · "
    "MS Project · Visio · Agile/Scrum</p>"
    "<p><strong>Recent projects:</strong> Climate &amp; Retail-Sales Correlation (AB/BC/ON); "
    "Median-Income analysis.</p>"
    "<p><strong>Languages:</strong> English · Mandarin · Cantonese</p>"
    "<p>📍 Calgary, AB &middot; 🔗 <a href=\"https://www.linkedin.com/in/qianli-cv/\">LinkedIn</a> "
    "&middot; <a href=\"https://github.com/Ada-Okoro\">GitHub</a></p>"
)

cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


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


def upload_avatar() -> str:
    print("[avatar] downloading GitHub avatar ...")
    img = urllib.request.urlopen("https://github.com/Ada-Okoro.png?size=400").read()
    boundary = "----ada" + uuid.uuid4().hex
    pre = (f"--{boundary}\r\n"
           f'Content-Disposition: form-data; name="file"; filename="avatar.png"\r\n'
           f"Content-Type: image/png\r\n\r\n").encode()
    mid = (f"\r\n--{boundary}\r\n"
           f'Content-Disposition: form-data; name="purpose"\r\n\r\nimage\r\n'
           f"--{boundary}--\r\n").encode()
    body = pre + img + mid
    s, r = req("POST", "/images/upload/", body=body,
               headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    if s in (200, 201) and isinstance(r, dict):
        url = r["images"][0]["url"]; print("[avatar] uploaded ->", url); return url
    raise SystemExit(f"avatar upload failed ({s}): {r}")


def main() -> int:
    s, r = req("POST", "/session/", {"username": os.environ["GHOST_USER"],
                                     "password": os.environ["GHOST_PASS"]})
    print("[login]", s)
    if s not in (200, 201):
        raise SystemExit(f"login failed: {r}")

    avatar_url = upload_avatar()

    css = (ROOT / "tools/inject/blog.css").read_text().replace("{{AVATAR_URL}}", avatar_url)
    code_head = f"<style>\n{css}\n</style>"

    js = ((ROOT / "tools/inject/blog.js").read_text()
          .replace("{{AVATAR_URL}}", avatar_url)
          .replace("{{NAME}}", HERO_NAME)
          .replace("{{BIO}}", BIO)
          .replace("{{GITHUB}}", GITHUB_URL)
          .replace("{{LINKEDIN}}", LINKEDIN_URL))
    code_foot = f"<script>\n{js}\n</script>"

    settings = [
        {"key": "title", "value": NAME},
        {"key": "members_signup_access", "value": "none"},
        {"key": "portal_button", "value": False},
        {"key": "accent_color", "value": "#0ABAB5"},  # Tiffany Blue
        {"key": "description", "value": BIO},
        {"key": "icon", "value": avatar_url},
        {"key": "navigation", "value": json.dumps(NAV)},
        {"key": "twitter", "value": ""},
        {"key": "facebook", "value": ""},
        {"key": "codeinjection_head", "value": code_head},
        {"key": "codeinjection_foot", "value": code_foot},
    ]
    # 逐项写,容忍个别失败(如 icon 校验)
    for st in settings:
        s, r = req("PUT", "/settings/", {"settings": [st]})
        print(f"[setting] {st['key']}: {s}")
        if s != 200:
            print("   ->", str(r)[:160])

    # About 页:存在则更新,否则新建
    s, r = req("GET", "/pages/?filter=slug:about&fields=id,updated_at")
    pages = r.get("pages") if isinstance(r, dict) else None
    if pages:
        pg = pages[0]
        s, r = req("PUT", f"/pages/{pg['id']}/?source=html",
                   {"pages": [{"title": "About", "html": ABOUT_HTML, "status": "published",
                               "updated_at": pg["updated_at"]}]})
        print("[about] updated:", s)
    else:
        s, r = req("POST", "/pages/?source=html",
                   {"pages": [{"title": "About", "html": ABOUT_HTML, "status": "published"}]})
        print("[about] created:", s)
    if s not in (200, 201):
        print("   ->", str(r)[:200])

    print("[done] personalization applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

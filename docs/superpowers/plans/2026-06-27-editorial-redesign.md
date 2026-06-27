# 编辑极简重设计 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 "Qian Li · Data & Business Analyst" 博客改成业界编辑/极简风(中性底 + Tiffany #0ABAB5 点缀),首页按 简介 → 精选项目 → 文章 分区,求职导向。

**Architecture:** 沿用 Ghost 本地 + Code Injection + gssg 静态导出。改动集中在:Ghost 设置(`scripts/personalize.py`)、注入样式与脚本(`tools/inject/blog.css`、`tools/inject/blog.js`)、项目文 `featured` 标记。无需改主题源码。

**Tech Stack:** Ghost 6 Admin API(会话)· Code Injection(CSS/JS)· gssg · Playwright(视觉验证)

**Conventions:**
- 工作目录 `~/projects/ghost-site`;凭据走环境变量 `GHOST_USER='ada.li.career@gmail.com' GHOST_PASS='AdaOkoro0303!'`。
- "测试" = 截图 + DOM grep 验证(本项目为 CSS/JS/配置)。
- 本地改 CSS/JS 后只需 `personalize.py` 推注入即可在 localhost:2368 即时看到,无需每次发布。

---

## Task 1: 探明首页 DOM(文章卡选择器)

**Files:** 无(只读探查)

- [ ] **Step 1: 起栈并抓首页结构**

Run:
```bash
cd ~/projects/ghost-site && docker compose up -d
until curl -sf -o /dev/null http://localhost:2368/; do sleep 3; done
python3 - <<'PY'
import re,urllib.request
h=urllib.request.urlopen("http://localhost:2368/").read().decode()
for pat in [r'<main[^>]*class="[^"]*"', r'<article[^>]*class="[^"]*"', r'class="[^"]*(post-card|gh-card|gh-postlist|feed)[^"]*"']:
    for m in re.findall(pat,h)[:6]: print(m)
PY
```
Expected: 看到首页文章列表容器与单卡的 class(如 `article class="gh-card post-card ..."`)。记录:**文章卡选择器**、**卡内 标题链接 / 题图 / 摘要 / 日期 的选择器**,供 Task 4 的 JS 使用。

- [ ] **Step 2: 确认两篇项目文的 slug**

Run: `curl -s "http://localhost:2368/" | grep -oE '/(weather-retail-sales|alberta-graduate-income|welcome)/' | sort -u`
Expected: 三个 slug 都在(featured 项目 = 前两个)。

---

## Task 2: Ghost 设置(站名/副标题/accent/导航 + 项目文 featured)

**Files:** Modify `scripts/personalize.py`

- [ ] **Step 1: 改 personalize.py 的常量与设置**

把顶部常量改为:
```python
NAME = "Qian Li · Data & Business Analyst"     # 站点标题
HERO_NAME = "Qian Li (Ada)"
GITHUB_URL = "https://github.com/Ada-Okoro"
LINKEDIN_URL = "https://www.linkedin.com/in/qianli-cv/"
BIO = "Turning data into decisions · PMP-certified data & business analyst · Calgary"
NAV = [
    {"label": "Work", "url": "/"},
    {"label": "Writing", "url": "/#writing"},
    {"label": "About", "url": "/about/"},
]
```
设置项里把 `title` 也写上(新增一行),并保留 `accent_color=#0ABAB5`:
```python
        {"key": "title", "value": NAME},
        {"key": "accent_color", "value": "#0ABAB5"},
```
(`description` 已用 `BIO`;`members_signup_access=none`、`portal_button=False`、`twitter/facebook=""`、`navigation` 保留。)

- [ ] **Step 2: 新增脚本标记项目文 featured**

Create `scripts/mark-featured.py`:
```python
#!/usr/bin/env python3
"""把项目文设 featured=true,其余 false(用于首页 Work/Writing 分区)。"""
import os, json, urllib.request, urllib.error, http.cookiejar
BASE="http://localhost:2368/ghost/api/admin"; ORIGIN="http://localhost:2368"
FEATURED={"weather-retail-sales","alberta-graduate-income"}
cj=http.cookiejar.CookieJar(); OP=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def parse(r):
    if not r.strip(): return {}
    try: return json.loads(r)
    except json.JSONDecodeError: return r
def req(m,p,b=None):
    h={"Origin":ORIGIN,"Accept":"application/json"}; d=None
    if isinstance(b,(dict,list)): d=json.dumps(b).encode(); h["Content-Type"]="application/json"
    rq=urllib.request.Request(BASE+p,data=d,headers=h,method=m)
    try: x=OP.open(rq); return x.status,parse(x.read().decode())
    except urllib.error.HTTPError as e: return e.code,parse(e.read().decode())
req("POST","/session/",{"username":os.environ["GHOST_USER"],"password":os.environ["GHOST_PASS"]})
s,r=req("GET","/posts/?limit=all&fields=id,slug,featured,updated_at")
for p in r["posts"]:
    want = p["slug"] in FEATURED
    if p["featured"]!=want:
        st,_=req("PUT",f"/posts/{p['id']}/",{"posts":[{"featured":want,"updated_at":p["updated_at"]}]})
        print(f"{p['slug']} featured={want}: {st}")
print("done")
```

- [ ] **Step 3: 运行并验证**

Run:
```bash
export GHOST_USER='ada.li.career@gmail.com' GHOST_PASS='AdaOkoro0303!'
./.ops-venv/bin/python scripts/personalize.py 2>&1 | grep -E 'title|accent|navigation|done'
./.ops-venv/bin/python scripts/mark-featured.py
```
Expected: title/accent/navigation 都 200;两篇项目文 featured=true。

- [ ] **Step 4: 提交** `git add scripts/personalize.py scripts/mark-featured.py && git commit -m "feat: editorial settings (title/nav/accent) + mark project posts featured"`

---

## Task 3: 编辑风 CSS(替换满屏蓝,改中性底 + 字体层级 + 卡片)

**Files:** Modify `tools/inject/blog.css`

- [ ] **Step 1: 重写 `tools/inject/blog.css`** 为下列内容(保留 `{{AVATAR_URL}}` 占位;移除旧的「满屏蓝背景 + 白卡」与 Tiffany 描边覆盖):

```css
/* ===== Qian Li · Data & Business Analyst — 编辑/极简 ===== */
:root { --accent:#0ABAB5; --ink:#1a1a1a; --muted:#5b6470; --faint:#9aa0a6; --line:#ececea; --bg:#fafaf9; }

/* 0) 底色:中性暖白(移除满屏蓝/白卡) */
body { background: var(--bg); color: var(--ink); }
.gh-viewport { background: transparent; max-width: none; margin: 0; border-radius: 0; box-shadow: none; }
.gh-inner, .gh-viewport .gh-inner { max-width: 880px; }

/* 1) 隐藏会员/订阅 + 静态站无效功能 */
.gh-footer-signup,.gh-navigation-members,.nav-sign-up,form[data-members-form],
.gh-comments,.gh-search { display:none !important; }
body.home-template .gh-header { display:none !important; }

/* 2) 顶栏头像(Tiffany 细描边,克制) */
.gh-navigation-logo.is-title { display:inline-flex; align-items:center; gap:10px; font-size:1.05rem; }
.gh-navigation-logo.is-title::before {
  content:""; width:30px; height:30px; border-radius:50%;
  background:url("{{AVATAR_URL}}") center/cover no-repeat; flex:none; border:1.5px solid var(--accent);
}

/* 3) Tiffany 作点缀:链接、强调 */
a { color: var(--accent); }
.gh-navigation a { color: var(--ink); }
.gh-navigation a:hover { color: var(--accent); }

/* 4) Hero(blog.js 生成) */
.ada-hero { max-width:880px; margin:40px auto 8px; padding:0 24px; }
.ada-hero__eyebrow { font-size:.75rem; letter-spacing:.12em; font-weight:700; color:var(--accent); text-transform:uppercase; }
.ada-hero__title { font-size:2.1rem; font-weight:800; line-height:1.15; margin:.4rem 0 .5rem; }
.ada-hero__bio { font-size:1.05rem; color:var(--muted); max-width:62ch; line-height:1.55; margin:0 0 1rem; }
.ada-hero__links a { display:inline-flex; align-items:center; padding:8px 16px; border-radius:8px;
  font-size:.85rem; font-weight:600; text-decoration:none; margin-right:8px; border:1px solid #d8dcda; color:var(--muted); }
.ada-hero__links a.primary { border-color:var(--accent); color:var(--accent); }

/* 5) 区块标签 */
.ada-section-label { max-width:880px; margin:30px auto 0; padding:0 24px 8px;
  font-size:.72rem; letter-spacing:.12em; font-weight:700; color:var(--faint);
  text-transform:uppercase; border-bottom:1px solid var(--line); }

/* 6) SELECTED WORK 卡片网格 */
.ada-work { max-width:880px; margin:16px auto 0; padding:0 24px;
  display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.ada-work .post-card, .ada-work article {
  border:1px solid var(--line); border-radius:10px; overflow:hidden; background:#fff; margin:0; }
.ada-work img { width:100%; height:150px; object-fit:cover; }

/* 7) WRITING 列表 */
.ada-writing { max-width:880px; margin:8px auto 0; padding:0 24px; }
.ada-writing .post-card, .ada-writing article { border:0; border-bottom:1px solid #f2f2f0; border-radius:0; padding:16px 0; margin:0; }
.ada-writing img { display:none; }

/* 8) 文章/页面正文阅读宽 */
.gh-content, .post-content, .gh-article .gh-content { max-width:680px; margin-left:auto; margin-right:auto; }
.gh-article-title, .article-title { line-height:1.2; }

/* 9) 文章配图 */
figure.kg-image-card img { border-radius:8px; border:1px solid var(--line); }
figure.kg-image-card figcaption { font-size:.82rem; color:var(--faint); text-align:center; margin-top:6px; }

/* 10) 页脚 */
.ada-foot { margin-top:10px; font-size:.85rem; color:var(--faint); }
.ada-foot a { color:var(--accent); text-decoration:none; }

@media (max-width:640px){ .ada-work{grid-template-columns:1fr;} .ada-hero__title{font-size:1.7rem;} }
```
> 选择器(`.post-card`/`article`)以 Task 1 探到的为准,实现时对齐。

- [ ] **Step 2: 推注入并截图首页(本地)**

Run:
```bash
export GHOST_USER='ada.li.career@gmail.com' GHOST_PASS='AdaOkoro0303!'
./.ops-venv/bin/python scripts/personalize.py 2>&1 | grep -E 'codeinjection_head|done'
```
然后用 Playwright 截 `http://localhost:2368/`,确认:无满屏蓝、中性底、Tiffany 仅在链接/头像描边。
Expected: 编辑风底色生效;暂时文章流还是默认排列(分区在 Task 4)。

- [ ] **Step 3: 提交** `git add tools/inject/blog.css && git commit -m "style: editorial CSS system (neutral bg, type scale, accent)"`

---

## Task 4: blog.js(Hero + Work/Writing 分区 + 页脚)

**Files:** Modify `tools/inject/blog.js`

- [ ] **Step 1: 重写 `tools/inject/blog.js`**(保留占位;用 slug 区分项目/文章,稳健):

```js
/* ===== Qian Li blog — hero + Work/Writing 分区 + footer ===== */
(function () {
  var AV="{{AVATAR_URL}}", NM="{{NAME}}", BIO="{{BIO}}", GH="{{GITHUB}}", LI="{{LINKEDIN}}";
  var FEATURED=["weather-retail-sales","alberta-graduate-income"];  // 精选项目 slug

  function isHome(){return document.body.classList.contains("home-template")||location.pathname.replace(/\/+$/,"")==="";}
  function sectionLabel(t){var d=document.createElement("div");d.className="ada-section-label";d.textContent=t;return d;}

  function run(){
    document.querySelectorAll(".gh-footer-signup,.gh-navigation-members,form[data-members-form]").forEach(function(e){e.remove();});

    // 页脚(所有页)
    var foot=document.querySelector(".gh-footer .gh-inner")||document.querySelector(".gh-footer");
    if(foot&&!foot.querySelector(".ada-foot")){
      var n=document.createElement("div");n.className="ada-foot";
      n.innerHTML="© "+new Date().getFullYear()+" Qian Li (Ada) · "+
        '<a href="'+GH+'" target="_blank" rel="noopener">GitHub</a> · '+
        '<a href="'+LI+'" target="_blank" rel="noopener">LinkedIn</a>';
      foot.appendChild(n);
    }

    if(!isHome()||document.querySelector(".ada-hero"))return;

    // Hero
    var hero=document.createElement("section");hero.className="ada-hero";
    hero.innerHTML='<div class="ada-hero__eyebrow">Data &amp; Business Analyst · Calgary</div>'+
      '<h1 class="ada-hero__title">Turning data into decisions.</h1>'+
      '<p class="ada-hero__bio">'+BIO+'</p>'+
      '<div class="ada-hero__links"><a class="primary" href="#work">View work ↓</a>'+
      '<a href="'+GH+'" target="_blank" rel="noopener">GitHub</a>'+
      '<a href="'+LI+'" target="_blank" rel="noopener">LinkedIn</a></div>';
    var nav=document.getElementById("gh-navigation");
    if(nav&&nav.parentNode) nav.parentNode.insertBefore(hero,nav.nextSibling);

    // 分区:找文章卡(选择器以 Task 1 为准),按 slug 拆成 Work / Writing
    var cards=Array.prototype.slice.call(document.querySelectorAll(".gh-postlist .post-card, .gh-postlist article, article.post-card"));
    if(!cards.length) return; // 退化:无法识别就保留默认流
    var work=document.createElement("div");work.className="ada-work";work.id="work";
    var writing=document.createElement("div");writing.className="ada-writing";writing.id="writing";
    cards.forEach(function(c){
      var a=c.querySelector('a[href]'); var href=a?a.getAttribute("href"):"";
      var isFeat=FEATURED.some(function(s){return href.indexOf("/"+s)>=0;});
      (isFeat?work:writing).appendChild(c);
    });
    var anchor=hero.nextSibling;
    var parent=hero.parentNode;
    if(work.children.length){ parent.insertBefore(sectionLabel("Selected work"),anchor); parent.insertBefore(work,anchor); }
    if(writing.children.length){ parent.insertBefore(sectionLabel("Writing"),anchor); parent.insertBefore(writing,anchor); }
    // 移除原列表容器(已清空)
    var oldList=document.querySelector(".gh-postlist, .gh-feed"); if(oldList) oldList.remove();
  }
  if(document.readyState!=="loading")run();else document.addEventListener("DOMContentLoaded",run);
})();
```
> `.gh-postlist`/`.post-card` 选择器对齐 Task 1 实际值。

- [ ] **Step 2: 推注入 + 截图首页**

Run: `./.ops-venv/bin/python scripts/personalize.py 2>&1 | grep -E 'codeinjection_foot|done'`
然后 Playwright 截 `http://localhost:2368/`。
Expected: Hero → **Selected work(2 卡)** → **Writing(列表)** → 页脚;若卡未识别则保持默认流(退化)。迭代调整选择器直到分区正确。

- [ ] **Step 3: 提交** `git add tools/inject/blog.js && git commit -m "feat: hero + Selected work / Writing sections via injected JS"`

---

## Task 5: 文章页 / About 页验证(同一视觉系统)

**Files:** 无(验证 + 必要时微调 blog.css)

- [ ] **Step 1: 截图文章页与 About**

Playwright 截 `http://localhost:2368/weather-retail-sales/` 和 `http://localhost:2368/about/`。
Expected: 中性底、Tiffany 点缀、正文阅读宽 ~680px、配图样式正常、无评论/搜索。

- [ ] **Step 2: 如有问题微调 `tools/inject/blog.css`**(阅读宽/标题/间距),重推 `personalize.py` 复验。提交微调。

---

## Task 6: 发布到 gh-pages + 线上验证

- [ ] **Step 1: 发布**

Run: `./scripts/publish-pages.sh 2>&1 | grep -E '\[publish\]'`

- [ ] **Step 2: 线上验证**

Run:
```bash
for i in $(seq 1 20); do curl -s "https://ada-okoro.github.io/ada-blog/?cb=$i" | grep -q 'ada-hero' && { echo live; break; }; sleep 6; done
curl -s -o /dev/null -w "home %{http_code}\n" https://ada-okoro.github.io/ada-blog/
```
然后 Playwright 截线上首页,确认与本地一致(Hero/Work/Writing、Tiffany 点缀、无满屏蓝)。

- [ ] **Step 3: 推源码** `git push origin main`

---

## Task 7: 收尾

- [ ] **Step 1:** `git status` 干净(`.superpowers/`、`static/`、`.env` 均忽略)。
- [ ] **Step 2:** 对照 spec 第 6 节逐条验收。
- [ ] **Step 3:** 关闭可视化伴侣:`bash <brainstorm>/scripts/stop-server.sh <session-dir>`。

---

## Self-Review(作者已核对)

- **Spec 覆盖:** 站名/副标题(T2)、中性底去满屏蓝(T3)、Tiffany 点缀(T3)、字体层级(T3)、Hero+Work+Writing 分区(T4)、featured 标记(T2)、文章/About 同系统+680px(T3/T5)、移动端(T3 media query)、线上验证(T6)。无缺口。
- **占位扫描:** 选择器以 Task 1 探查为准是显式步骤,非占位;CSS/JS 均给全。
- **一致性:** `{{AVATAR_URL}}/{{NAME}}/{{BIO}}/{{GITHUB}}/{{LINKEDIN}}` 占位由 `personalize.py` 替换(与现有逻辑一致);featured slug 集合在 mark-featured.py 与 blog.js 一致(`weather-retail-sales`、`alberta-graduate-income`)。

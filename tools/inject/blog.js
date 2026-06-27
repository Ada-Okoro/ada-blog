/* ===== Qian Li blog — editorial hero + Selected work / Writing 分区 + footer =====
   占位符由 scripts/personalize.py 替换。首页:文本 hero(无大头像)+ 按 slug 拆 Work/Writing。 */
(function () {
  var BIO = "{{BIO}}", GH = "{{GITHUB}}", LI = "{{LINKEDIN}}";
  var FEATURED = ["weather-retail-sales", "alberta-graduate-income"]; // 精选项目 slug

  function isHome() {
    return document.body.classList.contains("home-template") ||
           location.pathname.replace(/\/+$/, "") === "";
  }
  function label(t, id) {
    var d = document.createElement("div");
    d.className = "ada-section-label"; d.textContent = t; if (id) d.id = id;
    return d;
  }

  function run() {
    document.querySelectorAll(".gh-footer-signup,.gh-navigation-members,form[data-members-form]")
      .forEach(function (e) { e.remove(); });

    // 页脚版权 + 社交(所有页面)
    var foot = document.querySelector(".gh-footer .gh-inner") || document.querySelector(".gh-footer");
    if (foot && !foot.querySelector(".ada-foot")) {
      var n = document.createElement("div");
      n.className = "ada-foot";
      n.innerHTML = "© " + new Date().getFullYear() + " Qian Li (Ada) · " +
        '<a href="' + GH + '" target="_blank" rel="noopener">GitHub</a> · ' +
        '<a href="' + LI + '" target="_blank" rel="noopener">LinkedIn</a>';
      foot.appendChild(n);
    }

    if (!isHome() || document.querySelector(".ada-hero")) return;

    var nav = document.getElementById("gh-navigation");
    if (!nav || !nav.parentNode) return;
    var parent = nav.parentNode;            // .gh-viewport — 在此层插入,与 .gh-inner 同级,避免双重内边距

    // 文本 hero(无大头像;头像已在导航栏)
    var hero = document.createElement("section");
    hero.className = "ada-hero";
    hero.innerHTML =
      '<div class="ada-hero__eyebrow">Data &amp; Business Analyst · Calgary</div>' +
      '<h1 class="ada-hero__title">Turning data into decisions.</h1>' +
      '<p class="ada-hero__bio">' + BIO + '</p>' +
      '<div class="ada-hero__links">' +
        '<a class="primary" href="#work">View work ↓</a>' +
        '<a href="' + GH + '" target="_blank" rel="noopener">GitHub</a>' +
        '<a href="' + LI + '" target="_blank" rel="noopener">LinkedIn</a>' +
      '</div>';

    // 收集文章卡,按 slug 拆分
    var cards = Array.prototype.slice.call(document.querySelectorAll(".gh-feed .gh-card"));
    var frag = document.createDocumentFragment();
    frag.appendChild(hero);

    if (cards.length) {
      var work = document.createElement("div"); work.className = "ada-work"; work.id = "work";
      var writing = document.createElement("div"); writing.className = "ada-writing"; writing.id = "writing";
      cards.forEach(function (c) {
        var a = c.querySelector("a.gh-card-link, a[href]");
        var href = a ? a.getAttribute("href") : "";
        var feat = FEATURED.some(function (s) { return href.indexOf("/" + s + "/") >= 0; });
        (feat ? work : writing).appendChild(c);
      });
      if (work.children.length) { frag.appendChild(label("Selected work")); frag.appendChild(work); }
      if (writing.children.length) { frag.appendChild(label("Writing", "writing-label")); frag.appendChild(writing); }
    }

    parent.insertBefore(frag, nav.nextSibling);

    // 移除原文章流容器(卡片已移走)
    var container = document.querySelector(".gh-container.is-list") || document.querySelector(".gh-feed");
    if (container) container.remove();
  }

  if (document.readyState !== "loading") run();
  else document.addEventListener("DOMContentLoaded", run);
})();

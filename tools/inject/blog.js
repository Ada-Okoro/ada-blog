/* ===== Ada's blog hero(注入到 Ghost code injection foot)=====
   占位符由 scripts/personalize.py 替换。首页插入"方向 C"头部,并清掉残留订阅元素。 */
(function () {
  var AV = "{{AVATAR_URL}}", NM = "{{NAME}}", BIO = "{{BIO}}",
      GH = "{{GITHUB}}", LI = "{{LINKEDIN}}";

  function isHome() {
    return document.body.classList.contains("home-template") ||
           location.pathname.replace(/\/+$/, "") === "";
  }

  function run() {
    // 任意页面都移除订阅残留
    document.querySelectorAll(".gh-footer-signup,.gh-navigation-members,form[data-members-form]")
      .forEach(function (e) { e.remove(); });

    // 页脚加版权 + 社交(所有页面)
    var foot = document.querySelector(".gh-footer .gh-inner") || document.querySelector(".gh-footer");
    if (foot && !foot.querySelector(".ada-foot")) {
      var yr = new Date().getFullYear();
      var note = document.createElement("div");
      note.className = "ada-foot";
      note.innerHTML = "© " + yr + " Qian Li (Ada) · " +
        '<a href="' + GH + '" target="_blank" rel="noopener">GitHub</a> · ' +
        '<a href="' + LI + '" target="_blank" rel="noopener">LinkedIn</a>';
      foot.appendChild(note);
    }

    if (!isHome() || document.querySelector(".ada-hero")) return;

    var hero = document.createElement("section");
    hero.className = "ada-hero gh-outer";
    hero.innerHTML =
      '<div class="ada-hero__inner gh-inner">' +
        '<img class="ada-hero__avatar" src="' + AV + '" alt="' + NM + '">' +
        '<div class="ada-hero__text">' +
          '<h1 class="ada-hero__name">' + NM + '</h1>' +
          '<p class="ada-hero__bio">' + BIO + '</p>' +
          '<div class="ada-hero__links">' +
            '<a class="gh" href="' + GH + '" target="_blank" rel="noopener">GitHub</a>' +
            '<a class="li" href="' + LI + '" target="_blank" rel="noopener">LinkedIn</a>' +
          '</div>' +
        '</div>' +
      '</div>';

    var nav = document.getElementById("gh-navigation");
    if (nav && nav.parentNode) nav.parentNode.insertBefore(hero, nav.nextSibling);
    else document.body.insertBefore(hero, document.body.firstChild);
  }

  if (document.readyState !== "loading") run();
  else document.addEventListener("DOMContentLoaded", run);
})();

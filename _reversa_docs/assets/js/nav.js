// Reversa Docs - Navegação (gerado pelo Publisher)
// Lê window.RV_DATA.nav e preenche cada <nav class="reversa-doc-nav">.
// A página atual recebe o atributo aria-current="page".
(function () {
  "use strict";
  function ready(fn) {
    if (document.readyState !== "loading") { fn(); }
    else { document.addEventListener("DOMContentLoaded", fn); }
  }
  ready(function () {
    if (!window.RV_DATA || !window.RV_DATA.nav) { return; }
    var navs = document.querySelectorAll("nav.reversa-doc-nav");
    var pageId = (document.querySelector('meta[name="reversa-page-id"]') || {}).content;
    // Computa o prefixo relativo para alcançar a raiz do mini-site a partir
    // da página atual. Detecta a base pelas metas do documento (não pelo
    // pathname, que no Windows/file:// carrega o caminho completo do disco).
    // A página expõe sua pasta via data-base-path ("" na raiz, "../" em features/).
    var relPrefix = "";
    var basePath = (document.documentElement.getAttribute("data-base-path")) || "";
    if (basePath) { relPrefix = basePath; }
    window.RV_DATA.nav.forEach(function (item) {
      navs.forEach(function (nav) {
        var a = document.createElement("a");
        a.href = relPrefix + item.href;
        a.textContent = item.label;
        a.setAttribute("data-page-id", item.id);
        if (pageId === "index" && item.id === "index") { a.setAttribute("aria-current", "page"); }
        if (item.id !== "index" && pageId === "feature-" + item.href.replace(/.*\//, "").replace(/\.html$/, "")) {
          a.setAttribute("aria-current", "page");
        }
        nav.appendChild(a);
      });
    });
    // active state precisa refletir página atual de feature
    if (pageId && pageId.indexOf("feature-") === 0) {
      var slug = pageId.replace("feature-", "");
      document.querySelectorAll('nav.reversa-doc-nav a[data-page-id="features"]').forEach(function (a) {
        a.setAttribute("aria-current", "page");
      });
    }
  });
})();
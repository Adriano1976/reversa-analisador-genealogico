// Reversa Docs - Navegacao (gerado pelo Publisher em 2026-10-06)
// Le window.RV_DATA.nav e preenche cada <nav class="reversa-doc-nav"> que
// ainda estiver vazio. Se o Publisher ja injetou os <a> estaticamente, este
// script apenas marca a pagina atual com aria-current="page".
(function () {
  "use strict";
  function ready(fn) {
    if (document.readyState !== "loading") { fn(); }
    else { document.addEventListener("DOMContentLoaded", fn); }
  }
  ready(function () {
    var navs = document.querySelectorAll("nav.reversa-doc-nav");
    if (!navs.length) { return; }
    var pageId = (document.querySelector('meta[name="reversa-page-id"]') || {}).content;
    // Prefixo relativo ate a raiz do mini-site. Vem do proprio documento
    // ("" na raiz, "../" em features/), nunca do pathname, que em file://
    // carrega o caminho completo do disco.
    var relPrefix = document.documentElement.getAttribute("data-base-path") || "";
    var itens = (window.RV_DATA && window.RV_DATA.nav) || [];

    function linkPara(item) {
      var a = document.createElement("a");
      a.href = relPrefix + item.href;
      a.textContent = item.label;
      a.setAttribute("data-page-id", item.id);
      return a;
    }

    function ehPaginaAtual(id) {
      if (pageId === "index" && id === "index") { return true; }
      if (pageId && pageId.indexOf("feature-") === 0) {
        return id === pageId.replace("feature-", "");
      }
      return id === pageId;
    }

    Array.prototype.forEach.call(navs, function (nav) {
      if (!nav.children.length) {
        itens.forEach(function (item) { nav.appendChild(linkPara(item)); });
      }
      var links = nav.querySelectorAll("a[data-page-id]");
      Array.prototype.forEach.call(links, function (a) {
        if (ehPaginaAtual(a.getAttribute("data-page-id"))) {
          a.setAttribute("aria-current", "page");
        }
      });
    });
  });
})();

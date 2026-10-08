// Verificacao de render do mini-site: carrega data.js num window falso,
// confere o inventario das chaves e checa a sintaxe do script inline de cada
// pagina (extraido para arquivo temporario e passado por node --check).
//
// Uso: node .reversa/_docs_render_check.js
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const DOCS = path.join(ROOT, "_reversa_docs");
const TMP = path.join(ROOT, ".reversa", "_tmp_scripts");
fs.mkdirSync(TMP, { recursive: true });

const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(DOCS, "assets", "js", "data.js"), "utf8"), sandbox);
const D = sandbox.window.RV_DATA || {};

// Inventario: compara o que o data.js embute com os JSONs de assets/data/.
// Sem contagem fixa aqui, para o verificador nao envelhecer junto com os dados.
const FONTES = {
  modules: "modules.json",
  deps: "deps.json",
  metrics: "metrics.json",
  timeline: "timeline.json",
  glossary: "soul.json",
  featuresIndex: "features-index.json",
};
console.log("=== data.js x assets/data/ (o embutido tem de ser igual ao arquivo) ===");
let falhas = 0;
for (const chave of Object.keys(FONTES)) {
  const arq = path.join(DOCS, "assets", "data", FONTES[chave]);
  if (!fs.existsSync(arq)) { falhas++; console.log(`  FALHA ${chave}: ${FONTES[chave]} nao existe`); continue; }
  const disco = JSON.parse(fs.readFileSync(arq, "utf8"));
  const embutido = D[chave];
  const igual = JSON.stringify(disco) === JSON.stringify(embutido);
  if (!igual) falhas++;
  const resumo = {
    modules: (o) => `${(o.modules || []).length} modulos`,
    deps: (o) => `${(o.nodes || []).length} nos, ${(o.edges || []).length} arestas, ${(o.cycles || []).length} ciclos`,
    metrics: (o) => `${o.code ? o.code.modules : "?"} modulos, ${o.code ? o.code.locNaoVazio : "?"} linhas`,
    timeline: (o) => `${(o.events || []).length} eventos`,
    glossary: (o) => `${(o.concepts || []).length} conceitos`,
    featuresIndex: (o) => `${(o.specs || []).length} specs`,
  }[chave];
  console.log(`  ${igual ? "OK  " : "FALHA"} ${chave.padEnd(14)} ${resumo(disco)}${igual ? "" : "   DIVERGE do data.js"}`);
}
console.log(`  ${D.seedShort ? "OK  " : "FALHA"} seedShort      ${D.seedShort}`);
console.log(`  ${Array.isArray(D.nav) ? "OK  " : "FALHA"} nav            ${(D.nav || []).length} itens`);
if (!D.seedShort || !Array.isArray(D.nav)) falhas++;

// O logo e carregado por <img src>, nao pelo data.js. Confere o arquivo e, mais
// abaixo, se cada pagina aponta para o caminho relativo certo.
console.log("=== logo ===");
for (const nome of ["logo.png", "logo-mini.png"]) {
  const f = path.join(DOCS, "assets", "img", nome);
  const ok = fs.existsSync(f);
  if (!ok) falhas++;
  console.log(`  ${ok ? "OK  " : "FALHA"} assets/img/${nome.padEnd(15)} ${ok ? fs.statSync(f).size + " bytes" : "AUSENTE"}`);
}

console.log("=== numeros que as paginas exibem (informativos) ===");
console.log(`  modulos ${(D.modules.modules || []).length} | pastas ${new Set((D.modules.modules || []).map((m) => m.folder)).size}`);
console.log(`  pacotes ${(D.deps.nodes || []).length} | arestas ${(D.deps.edges || []).length} | ciclos ${(D.deps.cycles || []).length}`);
console.log(`  eventos ${(D.timeline.events || []).length} | conceitos ${(D.glossary.concepts || []).length}`);

console.log("=== navegacao ===");
const nav = D.nav || [];
console.log(`  ${nav.length} itens`);
let navQuebrado = 0;
for (const it of nav) {
  const alvo = path.join(DOCS, it.href);
  const existe = fs.existsSync(alvo);
  if (!existe) navQuebrado++;
  console.log(`  ${existe ? "OK  " : "FALHA"} ${it.id.padEnd(16)} -> ${it.href}  "${it.label}"`);
}
falhas += navQuebrado;

console.log("=== o data.js injeta o que as paginas leem? ===");
const paginas = [
  "index.html", "arquitetura.html", "modulos.html", "metricas.html",
  "timeline.html", "glossario.html", "deck.html",
  "features/upload-gedcom.html", "features/busca-caminho.html", "features/analise-dna.html",
];
for (const p of paginas) {
  const txt = fs.readFileSync(path.join(DOCS, p), "utf8");
  const chaves = new Set();
  const re = /RV_DATA(?:\.(\w+))?/g;
  let m;
  while ((m = re.exec(txt)) !== null) { if (m[1]) chaves.add(m[1]); }
  const ausentes = [...chaves].filter((k) => !(k in D));
  const ok = ausentes.length === 0;
  if (!ok) falhas++;
  console.log(`  ${ok ? "OK  " : "FALHA"} ${p.padEnd(32)} le: ${[...chaves].join(", ") || "(nada)"}${ok ? "" : "  AUSENTE NO data.js: " + ausentes.join(", ")}`);

  // o <img> do logo tem de resolver no disco a partir da propria pagina
  const imgs = [...txt.matchAll(/<img[^>]+class="seal[^"]*"[^>]+src="([^"]+)"/g)].map((x) => x[1]);
  if (imgs.length === 0) {
    falhas++;
    console.log(`  FALHA ${p}: nenhum <img class="seal...">`);
  }
  for (const src of imgs) {
    const alvo = path.join(DOCS, path.dirname(p), src);
    const existe = fs.existsSync(alvo);
    if (!existe) falhas++;
    console.log(`  ${existe ? "OK  " : "FALHA"} ${p.padEnd(32)} img -> ${src}`);
  }

  // e o icone da aba tem de estar declarado e resolver
  const ic = txt.match(/<link rel="icon"[^>]*href="([^"]+)"/);
  if (!ic) {
    falhas++;
    console.log(`  FALHA ${p}: sem <link rel="icon">`);
  } else {
    const alvo = path.join(DOCS, path.dirname(p), ic[1]);
    const existe = fs.existsSync(alvo);
    if (!existe) falhas++;
    console.log(`  ${existe ? "OK  " : "FALHA"} ${p.padEnd(32)} icon -> ${ic[1]}`);
  }
}

console.log("=== sintaxe do script inline de cada pagina ===");
let scriptsChecados = 0;
for (const p of paginas) {
  const txt = fs.readFileSync(path.join(DOCS, p), "utf8");
  const re = /<script(?![^>]*type="application\/json")[^>]*>([\s\S]*?)<\/script>/g;
  let m, i = 0;
  while ((m = re.exec(txt)) !== null) {
    const corpo = m[1];
    if (!corpo.trim() || m[0].includes("src=")) { continue; }
    i++;
    const tmp = path.join(TMP, `${p.replace(/[\\/]/g, "_")}.${i}.js`);
    fs.writeFileSync(tmp, corpo, "utf8");
    try {
      // vm.Script compila sem executar (equivale ao node --check) e nao
      // precisa de processo filho, que o sandbox bloqueia com EPERM.
      new vm.Script(corpo, { filename: tmp });
      scriptsChecados++;
    } catch (e) {
      falhas++;
      console.log(`  FALHA ${p} script #${i}: ${e.name}: ${e.message}`);
    }
  }
  const jsons = [...txt.matchAll(/<script type="application\/json" id="rv-snapshot">([\s\S]*?)<\/script>/g)];
  for (const j of jsons) {
    try { JSON.parse(j[1]); } catch (e) { falhas++; console.log(`  FALHA ${p}: snapshot JSON invalido (${e.message})`); }
  }
}
console.log(`  ${scriptsChecados} scripts inline passaram por node --check`);

fs.rmSync(TMP, { recursive: true, force: true });
console.log(falhas === 0 ? "\nRESULTADO: tudo verde" : `\nRESULTADO: ${falhas} falha(s)`);
process.exit(falhas === 0 ? 0 : 1);

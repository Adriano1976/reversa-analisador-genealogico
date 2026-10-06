// Verificacao de render do mini-site: carrega data.js num window falso,
// confere o inventario das chaves e checa a sintaxe do script inline de cada
// pagina (extraido para arquivo temporario e passado por node --check).
//
// Uso: node .reversa/_docs_render_check.js
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const DOCS = path.join(ROOT, "_reversa_docs");
const TMP = path.join(ROOT, ".reversa", "_tmp_scripts");
fs.mkdirSync(TMP, { recursive: true });

const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(DOCS, "assets", "js", "data.js"), "utf8"), sandbox);
const D = sandbox.window.RV_DATA || {};

const esperado = {
  modules: 37,
  deps: 6,
  metrics: 37,
  timeline: 86,
  glossary: 24,
  featuresIndex: 3,
};
console.log("=== inventario de window.RV_DATA ===");
let falhas = 0;
const tamanhos = {
  modules: (D.modules.modules || []).length,
  deps: (D.deps.nodes || []).length,
  metrics: D.metrics.code ? D.metrics.code.modules : 0,
  timeline: (D.timeline.events || []).length,
  glossary: (D.glossary.concepts || []).length,
  featuresIndex: (D.featuresIndex.specs || []).length,
};
for (const k of Object.keys(esperado)) {
  const ok = tamanhos[k] === esperado[k];
  if (!ok) falhas++;
  console.log(`  ${ok ? "OK  " : "FALHA"} ${k.padEnd(14)} ${tamanhos[k]} (esperado ${esperado[k]})`);
}
console.log(`  ${D.sealSvg ? "OK  " : "FALHA"} sealSvg        ${D.sealSvg.length} bytes`);
console.log(`  ${D.sealMiniSvg ? "OK  " : "FALHA"} sealMiniSvg    ${D.sealMiniSvg.length} bytes`);
console.log(`  ${D.seedShort ? "OK  " : "FALHA"} seedShort      ${D.seedShort}`);
if (!D.sealSvg) falhas++;

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

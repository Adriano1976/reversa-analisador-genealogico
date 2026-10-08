"""Publisher, passo 3: gera _reversa_docs/assets/js/data.js com todas as chaves
que as paginas consomem via window.RV_DATA.

Uso: python .reversa/_docs_build_datajs.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import json
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _docs_nav import nav_para  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_reversa_docs"
DATA = DOCS / "assets" / "data"
STATE = DOCS / ".state.json"
CONFIG = DOCS / ".config.json"
OUT = DOCS / "assets" / "js" / "data.js"

CHAVES = [
    ("modules", "modules.json"),
    ("deps", "deps.json"),
    ("metrics", "metrics.json"),
    ("timeline", "timeline.json"),
    ("glossary", "soul.json"),
    ("featuresIndex", "features-index.json"),
]


def ler(p: Path):
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    state = ler(STATE)
    config = ler(CONFIG)
    paginas = list(state.get("pagesGenerated", []))
    if "index.html" not in paginas:
        paginas.append("index.html")

    itens = nav_para(paginas)
    do_nav = {n["href"] for n in itens}
    faltando_nav = [p for p in paginas if p.endswith(".html") and p not in do_nav]

    obj = {}
    ausentes = []
    for chave, arquivo in CHAVES:
        f = DATA / arquivo
        if f.exists():
            obj[chave] = ler(f)
        else:
            obj[chave] = {}
            ausentes.append(arquivo)

    # As imagens do logo sao carregadas por <img src>, nao pelo data.js: nao ha
    # por que embutir 50 KB de base64 que nenhuma pagina le. A existencia delas e
    # verificada pelo smoke test (GET em cada src) e pelo finalize.
    logos = {}
    for nome in ("logo.png", "logo-mini.png"):
        f = DOCS / "assets" / "img" / nome
        logos[nome] = f.stat().st_size if f.exists() else 0

    obj["seedShort"] = str(config.get("seed", {}).get("hash", "")).replace("sha256:", "")[:8]
    obj["nav"] = itens
    obj["config"] = {
        "visualStyle": config.get("interview", {}).get("visualStyle", "sober"),
        "readerProfile": config.get("interview", {}).get("readerProfile", "stakeholder"),
        "depth": config.get("interview", {}).get("depth", "full"),
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    partes = ["// Reversa Docs - dados do mini-site (gerado pelo Publisher em 2026-10-06)",
              "// Fonte unica de dados das paginas: window.RV_DATA.<chave>.",
              "// Nenhuma pagina usa fetch() para arquivo local, porque isso quebra via file://."]
    for chave, _ in CHAVES:
        partes.append("window.RV_DATA = window.RV_DATA || {};")
        partes.append("window.RV_DATA.%s = %s;" % (chave, json.dumps(obj[chave], ensure_ascii=False)))
    partes.append("window.RV_DATA.seedShort = %s;" % json.dumps(obj["seedShort"], ensure_ascii=False))
    partes.append("window.RV_DATA.nav = %s;" % json.dumps(obj["nav"], ensure_ascii=False, indent=2))
    partes.append("window.RV_DATA.config = %s;" % json.dumps(obj["config"], ensure_ascii=False))

    OUT.write_text("\n".join(partes) + "\n", encoding="utf-8")

    print("data.js gravado: %d bytes" % OUT.stat().st_size)
    for chave, arquivo in CHAVES:
        v = obj[chave]
        n = len(v) if isinstance(v, (list, dict)) else 0
        print("  %-14s <- %-22s %s" % (chave, arquivo, ("%d chaves/itens" % n) if n else "VAZIO"))
    print("  seedShort=%s  logos=%s" % (obj["seedShort"], logos))
    print("  nav: %d itens -> %s" % (len(itens), [i["href"] for i in itens]))
    if ausentes:
        print("  AUSENTES (gravados como {}): %s" % ausentes)
    if faltando_nav:
        print("  paginas nao listadas no nav: %s" % faltando_nav)


if __name__ == "__main__":
    main()

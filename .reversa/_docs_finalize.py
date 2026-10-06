"""Recalcula o hash de todos os artefatos registrados em _reversa_docs/.state.json
e confere a coerencia final do mini-site.

Uso: python .reversa/_docs_finalize.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_reversa_docs"
STATE = DOCS / ".state.json"


def sha(p: Path) -> str:
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    s = json.loads(STATE.read_text(encoding="utf-8"))
    alterados, ausentes = [], []
    for p, meta in s["pages"].items():
        f = DOCS / p
        if not f.exists():
            ausentes.append(p)
            continue
        novo = sha(f)
        if meta.get("hash") != novo:
            alterados.append((p, meta.get("agent", "?"), meta.get("hash", "")[:16], novo[:16]))
        meta["hash"] = novo

    # os selos tambem entram no registro
    for p in ("assets/img/seal.svg", "assets/img/seal-mini.svg"):
        f = DOCS / p
        s["pages"].setdefault(p, {"status": "created", "agent": "reversa-docs-publisher"})
        s["pages"][p]["hash"] = sha(f)

    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("hashes recalculados: %d artefatos registrados" % len(s["pages"]))
    for p, ag, antes, depois in alterados:
        print("  %-34s %-26s %s -> %s" % (p, ag, antes, depois))
    if ausentes:
        print("  AUSENTES: %s" % ausentes)
    if not alterados:
        print("  nenhum hash mudou")

    # coerencia final
    print("\ncoerencia final:")
    print("  pagesGenerated=%d  pagesOmitted=%d" % (len(s["pagesGenerated"]), len(s["pagesOmitted"])))
    print("  completedAgents=%s  pendingAgents=%s" % (s["completedAgents"], s["pendingAgents"]))
    print("  smokeTestFailed=%s  brokenLinks=%d  vendorMissing=%s"
          % (s["smokeTestFailed"], len(s["brokenLinks"]), s["vendorMissing"]))

    selo = (DOCS / "assets" / "img" / "seal.svg").read_text(encoding="utf-8").strip()
    datajs = (DOCS / "assets" / "js" / "data.js").read_text(encoding="utf-8")
    i = datajs.index("window.RV_DATA.sealSvg = ") + len("window.RV_DATA.sealSvg = ")
    embutido = json.loads(datajs[i:datajs.index(";", i)])
    print("  selo do disco == selo embutido no data.js: %s" % (selo == embutido))

    faltam = []
    for p in s["pagesGenerated"]:
        txt = (DOCS / p).read_text(encoding="utf-8")
        if "data.js" not in txt or "nav.js" not in txt:
            faltam.append((p, "sem data.js/nav.js"))
        if not re.search(r'<nav class="reversa-doc-nav">\s*<a ', txt):
            faltam.append((p, "nav vazio"))
        if "seal-mini" not in txt:
            faltam.append((p, "sem mini-selo"))
        if "fetch(" in txt:
            faltam.append((p, "usa fetch()"))
        if re.search(r'src="https?://', txt):
            faltam.append((p, "script externo"))
    print("  pendencias nas 10 paginas: %s" % (faltam or "nenhuma"))


if __name__ == "__main__":
    main()

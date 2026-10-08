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
import os
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

    # as imagens do logo tambem entram no registro
    for p in ("assets/img/logo.png", "assets/img/logo-mini.png"):
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

    # o logo e carregado por <img src>, entao a checagem e a de referencia:
    # cada pagina aponta para o arquivo, e o arquivo existe
    faltando_logo = []
    for p in s["pagesGenerated"]:
        txt = (DOCS / p).read_text(encoding="utf-8")
        refs = re.findall(r'<img[^>]+class="seal[^"]*"[^>]+src="([^"]+)"', txt)
        if not refs:
            faltando_logo.append((p, "sem <img> do logo"))
        for src in refs:
            alvo = DOCS / os.path.dirname(p) / src
            if not alvo.exists():
                faltando_logo.append((p, "src inexistente: %s" % src))
    print("  paginas sem referencia valida ao logo: %s" % (faltando_logo or "nenhuma"))
    print("  logo.png=%d bytes  logo-mini.png=%d bytes"
          % ((DOCS / "assets" / "img" / "logo.png").stat().st_size,
             (DOCS / "assets" / "img" / "logo-mini.png").stat().st_size))

    faltam = []
    for p in s["pagesGenerated"]:
        txt = (DOCS / p).read_text(encoding="utf-8")
        if "data.js" not in txt or "nav.js" not in txt:
            faltam.append((p, "sem data.js/nav.js"))
        if not re.search(r'<nav class="reversa-doc-nav">\s*<a ', txt):
            faltam.append((p, "nav vazio"))
        if "seal-mini" not in txt:
            faltam.append((p, "sem <img> do logo no header"))
        if "fetch(" in txt:
            faltam.append((p, "usa fetch()"))
        if re.search(r'src="https?://', txt):
            faltam.append((p, "script externo"))
    print("  pendencias nas 10 paginas: %s" % (faltam or "nenhuma"))


if __name__ == "__main__":
    main()

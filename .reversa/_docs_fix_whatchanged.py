"""Corrige a lista regeneration.whatChanged em _reversa_docs/.state.json,
restaurando as entradas do backup desta execucao e acrescentando a nova.

Uso: python .reversa/_docs_fix_whatchanged.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_reversa_docs"
STATE = DOCS / ".state.json"
BACKUP = DOCS / ".backup-20261006-022411" / ".state.json"

NOVA = ("reexecucao isolada do Publisher (passos 0 a 11): selos regerados pela skill "
        "reversa-selo-generativo a partir da mesma seed, padrao crystal-lattice, agora na variante "
        "dark prevista pela paleta sober para header escuro, com descarte de #3d4a5c por contraste "
        "abaixo de 2,5:1; o selo do hero deixou de ser <img> e virou SVG inline no index.html; "
        "data.js reembutido; mini-selo e nav reinjetados nas 10 paginas; auto-discovery com 0 "
        "auxiliares; placeholder de topologia omitido porque a pagina nao esta no nav")


def main():
    s = json.loads(STATE.read_text(encoding="utf-8"))
    atual = s["regeneration"].get("whatChanged", [])
    ruins = [x for x in atual if isinstance(x, dict)]

    anteriores = []
    if BACKUP.exists():
        b = json.loads(BACKUP.read_text(encoding="utf-8"))
        anteriores = b.get("regeneration", {}).get("whatChanged", [])

    lista = [x for x in anteriores if isinstance(x, str)]
    if NOVA not in lista:
        lista.append(NOVA)
    # dedupe preservando a ordem
    visto, final = set(), []
    for x in lista:
        if x not in visto:
            visto.add(x)
            final.append(x)

    s["regeneration"]["whatChanged"] = final
    s["regeneration"].pop("whatChangedCorrupted", None)
    if ruins:
        s["regeneration"]["notaInterna"] = ("uma gravacao minha colapsou whatChanged em um objeto; "
                                            "a lista foi restaurada do backup desta execucao")
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("whatChanged restaurado: %d entradas" % len(final))
    for x in final:
        print("  - %s..." % x[:100])
    print("backup usado: %s (existe: %s)" % (BACKUP.name, BACKUP.exists()))


if __name__ == "__main__":
    main()

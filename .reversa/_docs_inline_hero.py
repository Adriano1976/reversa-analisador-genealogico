"""Publisher, passo 6: coloca o selo grande inline no hero do index.html.

Uso: python .reversa/_docs_inline_hero.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_reversa_docs"
INDEX = DOCS / "index.html"
SEAL = DOCS / "assets" / "img" / "seal.svg"

ALVO = '  <img class="seal" src="assets/img/seal.svg" alt="Selo do projeto">'


def main():
    t = INDEX.read_text(encoding="utf-8")
    svg = SEAL.read_text(encoding="utf-8").strip()
    svg = svg.replace(
        "<svg xmlns=",
        '<svg class="seal" role="img" aria-label="Selo generativo do projeto" xmlns=',
        1,
    )
    if ALVO in t:
        t = t.replace(ALVO, svg, 1)
        acao = "img substituido pelo SVG inline"
    elif '<svg class="seal"' in t:
        ini = t.index('<svg class="seal"')
        fim = t.index("</svg>", ini) + 6
        t = t[:ini] + svg + t[fim:]
        acao = "SVG inline anterior substituido (idempotente)"
    else:
        print("ERRO: nao achei nem o <img> nem um <svg class=\"seal\"> no hero")
        return 1
    INDEX.write_text(t, encoding="utf-8")
    print("hero: %s" % acao)
    print("index.html: %d bytes" % len(t.encode("utf-8")))
    print("referencias a assets/img/seal.svg no index: %d" % t.count("assets/img/seal.svg"))
    print("elementos <svg> no index: %d" % t.count("<svg"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

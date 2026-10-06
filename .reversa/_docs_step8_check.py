"""Publisher, passo 8 e conferencia final dos selos.

Uso: python .reversa/_docs_step8_check.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_reversa_docs"


def main():
    st = json.loads((DOCS / ".state.json").read_text(encoding="utf-8"))
    nav = json.loads((DOCS / "assets" / "js" / "data.js").read_text(encoding="utf-8")
                     .split("window.RV_DATA.nav = ", 1)[1].split(";\n", 1)[0])
    hrefs = {n["href"] for n in nav}

    print("passo 8, placeholders de paginas omitidas:")
    for item in st["pagesOmitted"]:
        p = item["page"]
        no_nav = p not in hrefs
        print("  %-18s no nav: %-5s -> %s" % (p, "nao" if no_nav else "sim",
                                              "precondicao nao atendida, placeholder omitido"
                                              if no_nav else "placeholder recomendado"))

    print("\nsanidade geometrica dos selos:")
    for nome, tamanho in (("seal.svg", 800), ("seal-mini.svg", 64)):
        t = (DOCS / "assets" / "img" / nome).read_text(encoding="utf-8")
        pts = re.findall(r'points="([^"]+)"', t)
        todos = []
        for p in pts:
            for par in p.split():
                x, y = par.split(",")
                todos.append((float(x), float(y)))
        fora = [p for p in todos if not (0 <= p[0] <= tamanho and 0 <= p[1] <= tamanho)]
        xs = [p[0] for p in todos]
        ys = [p[1] for p in todos]
        print("  %-16s polygonos=%d vertices=%d fora_do_viewBox=%d  x=[%.1f,%.1f] y=[%.1f,%.1f]"
              % (nome, len(pts), len(todos), len(fora), min(xs), max(xs), min(ys), max(ys)))
        print("                   tracos=%s  cores=%s"
              % (sorted(set(re.findall(r'stroke-width="([\d.]+)"', t))),
                 sorted(set(re.findall(r'#[0-9a-f]{6}', t)))))

    print("\npaginas: um mini-selo cada, e o index com o selo grande inline:")
    for f in sorted(list(DOCS.glob("*.html")) + list(DOCS.glob("features/*.html"))):
        t = f.read_text(encoding="utf-8")
        print("  %-30s seal-mini=%d  seal-grande=%d"
              % (f.relative_to(DOCS), t.count('class="seal-mini"'), t.count('class="seal"')))


if __name__ == "__main__":
    main()

"""Publisher: declara o logo como icone da aba nas paginas do mini-site.

Reusa o assets/img/logo-mini.png (64x64) que ja existe, em vez de criar um
segundo arquivo com os mesmos bytes, e em vez de repetir um data URI de 8 KB em
10 paginas. O caminho e relativo, entao a pagina de features/ recebe "../".

Idempotente: se o <link rel="icon"> ja existe, substitui.

Uso: python .reversa/_docs_favicon.py [--seco]
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_reversa_docs"
ICONE = "assets/img/logo-mini.png"

MARCA = "<!-- icone da aba: logo do projeto -->"
RE_LINK = re.compile(r"[ \t]*" + re.escape(MARCA) + r"\n[ \t]*<link rel=\"icon\"[^>]*>\n?")
RE_TITULO = re.compile(r"[ \t]*<title>[^<]*</title>\n")
RE_QUALQUER_ICONE = re.compile(r"[ \t]*<link rel=\"icon\"[^>]*>\n?")


def paginas():
    return sorted(list(DOCS.glob("*.html")) + list(DOCS.glob("features/*.html")))


def main():
    seco = "--seco" in sys.argv
    feitas = []
    for f in paginas():
        rel = f.relative_to(DOCS)
        prefixo = "../" * (len(rel.parts) - 1)
        bloco = '%s\n    <link rel="icon" type="image/png" sizes="64x64" href="%s%s">\n' % (
            MARCA, prefixo, ICONE)
        t = f.read_text(encoding="utf-8")
        orig = t

        if RE_LINK.search(t):
            t = RE_LINK.sub(bloco, t, count=1)
            via = "substituido"
        elif RE_QUALQUER_ICONE.search(t):
            t = RE_QUALQUER_ICONE.sub(bloco, t, count=1)
            via = "icone anterior substituido"
        else:
            alvo = RE_TITULO.search(t)
            if not alvo:
                print("  AVISO: %s nao tem <title>, pulado" % rel)
                continue
            t = t[:alvo.end()] + bloco + t[alvo.end():]
            via = "inserido depois do title"

        if not seco and t != orig:
            f.write_text(t, encoding="utf-8")
        feitas.append((rel.as_posix(), via, len(t.encode("utf-8")) - len(orig.encode("utf-8"))))

    print("paginas com icone: %d de %d" % (len(feitas), len(paginas())))
    for nome, via, delta in feitas:
        print("  %-30s %-26s delta=%+d" % (nome, via, delta))
    if seco:
        print("--seco: nada gravado")

    # verificacao: o alvo de cada link resolve no disco
    problemas = []
    for f in paginas():
        t = f.read_text(encoding="utf-8")
        m = re.search(r'<link rel="icon"[^>]*href="([^"]+)"', t)
        if not m:
            problemas.append((f.name, "sem link de icone"))
            continue
        alvo = f.parent / m.group(1)
        if not alvo.exists():
            problemas.append((f.name, "nao resolve: %s" % m.group(1)))
    print("problemas: %s" % (problemas or "nenhum"))
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())

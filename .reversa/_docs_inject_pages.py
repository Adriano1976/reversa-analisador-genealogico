"""Publisher, passo 4: injeta o mini-selo novo e os links de navegacao
estaticos em todas as paginas do mini-site, de forma idempotente.

Uso: python .reversa/_docs_inject_pages.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _docs_nav import nav_para, html_links  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_reversa_docs"
SEAL_MINI = DOCS / "assets" / "img" / "seal-mini.svg"

RE_HEADER_SVG = re.compile(r'(<header class="site">\s*)(<svg\b.*?</svg>)', re.S)
RE_NAV = re.compile(r'(<nav class="reversa-doc-nav">)(.*?)(</nav>)', re.S)
RE_ANCORAS_SOLTAS = re.compile(
    r'((?:<a href="[^"]+" data-page-id="[^"]+">[^<]*</a>\s*)+)(<nav class="reversa-doc-nav">)')
RE_HTML_TAG = re.compile(r"<html\b[^>]*>")
AGORA = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def selo_mini() -> str:
    svg = SEAL_MINI.read_text(encoding="utf-8").strip()
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    if 'class="seal-mini"' not in svg:
        svg = svg.replace("<svg", '<svg class="seal-mini"', 1)
    return "\n".join("  " + l if l.strip() else l for l in svg.splitlines())


def garantir_base_path(txt: str) -> str:
    def repl(m):
        tag = m.group(0)
        if "data-base-path" in tag:
            return tag
        return tag[:-1] + ' data-base-path="">'
    return RE_HTML_TAG.sub(repl, txt, count=1)


def garantir_ordem_scripts(txt: str) -> str:
    i_data = txt.find('src="assets/js/data.js"')
    i_nav = txt.find('src="assets/js/nav.js"')
    if i_data != -1 and i_nav != -1 and i_nav < i_data:
        linhas = txt.splitlines(keepends=True)
        idx = [i for i, l in enumerate(linhas) if "assets/js/data.js" in l or "assets/js/nav.js" in l]
        if len(idx) == 2:
            a, b = idx
            linhas[a], linhas[b] = linhas[b], linhas[a]
            return "".join(linhas)
    return txt


def main():
    state = json.loads((DOCS / ".state.json").read_text(encoding="utf-8"))
    paginas = list(state.get("pagesGenerated", []))
    if "index.html" not in paginas:
        paginas.append("index.html")
    paginas = [p for p in paginas if (DOCS / p).exists()]

    itens = nav_para(paginas)
    selo = selo_mini()

    backup = DOCS / (".backup-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    backup.mkdir(parents=True, exist_ok=True)

    rel = []
    for p in sorted(paginas):
        f = DOCS / p
        txt = f.read_text(encoding="utf-8")
        orig = txt

        bkp = backup / p
        bkp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, bkp)

        # prefixo relativo ate a raiz do mini-site, conforme a profundidade
        prefixo = "../" * (len(Path(p).parts) - 1)
        links = html_links(itens, prefixo)

        # 1. mini-selo
        if "<!-- MINI_SEAL_SVG -->" in txt:
            txt = txt.replace("<!-- MINI_SEAL_SVG -->", selo, 1)
            via = "marcador MINI_SEAL_SVG"
        elif RE_HEADER_SVG.search(txt):
            txt = RE_HEADER_SVG.sub(lambda m: m.group(1) + "\n" + selo + "\n", txt, count=1)
            via = "svg do header substituido"
        else:
            via = "SEM SELO (nao achei marcador nem svg no header)"

        # 2. nav estatico, sempre DENTRO do elemento <nav>, nunca solto
        if RE_NAV.search(txt):
            txt = RE_NAV.sub(lambda m: m.group(1) + "\n" + links + "\n" + m.group(3), txt, count=1)
            nav_via = "conteudo do nav substituido"
        elif "<!-- NAV_LINKS -->" in txt:
            txt = txt.replace("<!-- NAV_LINKS -->",
                              '<nav class="reversa-doc-nav">\n%s\n</nav>' % links, 1)
            nav_via = "marcador virou o nav"
        else:
            nav_via = "SEM NAV"
        # limpa ancoras soltas que uma execucao anterior possa ter deixado
        # fora do <nav> (o marcador NAV_LINKS fica antes do elemento)
        txt, n_soltas = RE_ANCORAS_SOLTAS.subn(r"\g<2>", txt)
        if n_soltas:
            nav_via += " + %d bloco(s) solto(s) removido(s)" % n_soltas

        # 3. data-base-path, ordem dos scripts e carimbo de geracao
        txt = garantir_base_path(txt)
        txt = garantir_ordem_scripts(txt)
        txt = re.sub(r'(<meta name="reversa-generated-at" content=")[^"]*(")',
                     r'\g<1>%s\g<2>' % AGORA, txt, count=1)

        # 4. remove o marcador do hero, que ja tem <img src="assets/img/seal.svg">
        txt = txt.replace("<!-- SEAL_HERO -->\n", "").replace("<!-- SEAL_HERO -->", "")

        if txt != orig:
            f.write_text(txt, encoding="utf-8")
            rel.append((p, via, nav_via, len(txt) - len(orig)))
        else:
            rel.append((p, via, nav_via, 0))

    print("backup: %s (%d arquivos)" % (backup.name, len(list(backup.rglob("*.html")))))
    for p, via, nav_via, delta in rel:
        print("  %-32s selo=%-28s nav=%-26s delta=%+d bytes" % (p, via, nav_via, delta))


if __name__ == "__main__":
    main()

"""Publisher, passo 9 (smoke test) + passo 7 (validacao de links).

Sobe um http.server efemero servindo _reversa_docs/, faz GET em cada pagina,
em cada <script src> relativo e em cada <img src>, e valida os links relativos
do nav e do index contra o disco.

Uso: python .reversa/_docs_smoke_test.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import functools
import http.server
import json
import re
import socketserver
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_reversa_docs"

PADROES_DE_ERRO = ["is not defined", "Failed to fetch", "Access to fetch",
                   "NetworkError", "Erro ao carregar o dado"]

RE_SCRIPT = re.compile(r'<script[^>]+src="([^"]+)"')
RE_IMG = re.compile(r'<img[^>]+src="([^"]+)"')
RE_HREF = re.compile(r'<a[^>]+href="([^"]+)"')


def paginas():
    state = json.loads((DOCS / ".state.json").read_text(encoding="utf-8"))
    p = [x for x in state.get("pagesGenerated", []) if (DOCS / x).exists()]
    if "index.html" not in p:
        p.append("index.html")
    return sorted(set(p))


def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
    handler.log_message = lambda *a, **k: None
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        porta = httpd.server_address[1]
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        base = "http://127.0.0.1:%d/" % porta

        erros = []
        verificados = 0
        paginas_ok = 0
        for p in paginas():
            try:
                with urllib.request.urlopen(base + p, timeout=10) as r:
                    corpo = r.read().decode("utf-8", "replace")
                    if r.status != 200:
                        erros.append({"page": p, "kind": "http", "detail": "status %s" % r.status})
                        continue
            except (urllib.error.URLError, OSError) as e:
                erros.append({"page": p, "kind": "http", "detail": str(e)})
                continue
            paginas_ok += 1

            for pat in PADROES_DE_ERRO:
                if pat in corpo:
                    erros.append({"page": p, "kind": "padrao-de-erro", "detail": pat})

            parent = (DOCS / p).parent
            for src in set(RE_SCRIPT.findall(corpo)) | set(RE_IMG.findall(corpo)):
                if src.startswith(("http://", "https://", "//", "data:")):
                    erros.append({"page": p, "kind": "recurso-externo", "detail": src})
                    continue
                verificados += 1
                try:
                    with urllib.request.urlopen(base + str(Path(p).parent / src).replace("\\", "/")
                                                if str(Path(p).parent) != "." else base + src, timeout=10) as r:
                        if r.status != 200:
                            erros.append({"page": p, "kind": "asset", "detail": "%s status %s" % (src, r.status)})
                except (urllib.error.URLError, OSError) as e:
                    erros.append({"page": p, "kind": "asset", "detail": "%s -> %s" % (src, e)})

        httpd.shutdown()

    # passo 7: links relativos do nav e do index contra o disco
    quebrados = []
    for p in paginas():
        txt = (DOCS / p).read_text(encoding="utf-8")
        for href in set(RE_HREF.findall(txt)):
            if href.startswith(("http://", "https://", "#", "mailto:", "data:")):
                continue
            alvo = (DOCS / p).parent / href.split("#")[0]
            if href and not alvo.exists():
                quebrados.append({"from": p, "href": href, "expected_path": str(alvo.relative_to(DOCS))})

    print("paginas verificadas no servidor: %d/%d" % (paginas_ok, len(paginas())))
    print("assets locais verificados por GET: %d" % verificados)
    print("erros do smoke test: %d" % len(erros))
    for e in erros:
        print("  [%s] %s -> %s" % (e["kind"], e["page"], e["detail"]))
    print("links quebrados: %d" % len(quebrados))
    for b in quebrados:
        print("  %s: %s (esperado em %s)" % (b["from"], b["href"], b["expected_path"]))

    (DOCS / ".smoke-result.json").write_text(json.dumps(
        {"smokeTestFailed": bool(erros), "smokeTestErrors": erros},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DOCS / ".links-result.json").write_text(json.dumps(quebrados, ensure_ascii=False, indent=2) + "\n",
                                             encoding="utf-8")
    return 0 if not erros else 1


if __name__ == "__main__":
    sys.exit(main())

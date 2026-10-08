"""Coloca o logo do projeto como icone da aba do navegador no template do app.

Estrategia: data URI embutido no proprio HTML, em vez de arquivo servido. Motivos:
nao cria rota nova (a aplicacao tem rota unica, documentada), nao cria src/static/
(proibida pelo watch item W004) e nao depende de configuracao de static_folder.

Uso:
  python .reversa/_favicon.py <caminho-do-png> [--tamanho 64] [--seco]
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import base64
import io
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "src" / "templates" / "index.html"

MARCA = "<!-- icone da aba: logo do projeto em data URI, ver .reversa/_favicon.py -->"
RE_LINK_ICONE = re.compile(
    r"[ \t]*" + re.escape(MARCA) + r"\n[ \t]*<link rel=\"icon\"[^>]*>\n?")


def gerar_data_uri(origem: Path, tamanho: int):
    from PIL import Image
    im = Image.open(origem)
    if im.mode not in ("RGBA", "RGB"):
        im = im.convert("RGBA")
    im = im.resize((tamanho, tamanho), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    png = buf.getvalue()
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii"), png, im.size


def main():
    if len(sys.argv) < 2:
        print("uso: python .reversa/_favicon.py <caminho-do-png> [--tamanho N] [--seco]")
        return 2
    origem = Path(sys.argv[1])
    tamanho = 64
    if "--tamanho" in sys.argv:
        tamanho = int(sys.argv[sys.argv.index("--tamanho") + 1])
    seco = "--seco" in sys.argv

    if not origem.exists():
        print("ERRO: imagem nao encontrada em %s" % origem)
        return 2

    uri, png, dim = gerar_data_uri(origem, tamanho)
    print("origem: %s (%d bytes)" % (origem.name, origem.stat().st_size))
    print("icone: %dx%d, PNG de %d bytes, data URI de %d bytes (%.1f KB)"
          % (dim[0], dim[1], len(png), len(uri), len(uri) / 1024.0))

    t = TEMPLATE.read_text(encoding="utf-8")
    bloco = '%s\n    <link rel="icon" type="image/png" sizes="%dx%d" href="%s">\n' % (
        MARCA, tamanho, tamanho, uri)

    if RE_LINK_ICONE.search(t):
        novo = RE_LINK_ICONE.sub(bloco, t, count=1)
        acao = "icone existente substituido (idempotente)"
    else:
        alvo = re.search(r"[ \t]*<title>[^<]*</title>\n", t)
        if not alvo:
            print("ERRO: nao achei a linha do <title> para ancorar o icone")
            return 2
        novo = t[:alvo.end()] + bloco + t[alvo.end():]
        acao = "icone inserido logo depois do <title>"

    if seco:
        print("--seco: nada gravado. Acao prevista: %s" % acao)
        return 0

    TEMPLATE.write_text(novo, encoding="utf-8")
    print("template: %s" % acao)
    print("index.html: %d -> %d bytes (%+d)"
          % (len(t.encode("utf-8")), len(novo.encode("utf-8")),
             len(novo.encode("utf-8")) - len(t.encode("utf-8"))))

    # verificacao: o data URI no arquivo decodifica para um PNG valido
    conf = TEMPLATE.read_text(encoding="utf-8")
    m = re.search(r'<link rel="icon"[^>]*href="data:image/png;base64,([^"]+)"', conf)
    if not m:
        print("ERRO: o link do icone nao esta no arquivo depois da gravacao")
        return 1
    dados = base64.b64decode(m.group(1))
    ok = dados[:8] == b"\x89PNG\r\n\x1a\n"
    print("verificacao: base64 decodifica em %d bytes, assinatura PNG valida: %s" % (len(dados), ok))
    print("ocorrencias de rel=\"icon\" no template: %d" % conf.count('rel="icon"'))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

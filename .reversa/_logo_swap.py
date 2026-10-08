"""Troca o selo generativo pelo logo do projeto no mini-site.

Gera as duas imagens (hero e mini) a partir do PNG de origem, substitui o selo
inline do hero e os 10 mini-selos das paginas por <img>, e remove os dois SVGs
antigos. Idempotente: rodar de novo apenas regera as imagens.

Uso:
  python .reversa/_logo_swap.py <caminho-do-png> [--seco]
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
IMG = DOCS / "assets" / "img"

HERO_PX = 512
MINI_PX = 64

RE_HERO_SVG = re.compile(r'<svg class="seal"[^>]*>.*?</svg>', re.S)
RE_HERO_IMG = re.compile(r'<img class="seal"[^>]*>')
RE_MINI_SVG = re.compile(r'<svg class="seal-mini"[^>]*>.*?</svg>', re.S)
RE_MINI_IMG = re.compile(r'<img class="seal-mini"[^>]*>')


def gerar(origem: Path, destino: Path, px: int):
    from PIL import Image
    im = Image.open(origem)
    tem_alfa = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    im = im.resize((px, px), Image.LANCZOS)
    im.save(destino, format="PNG", optimize=True)

    # diagnostico do canto: diz se o fundo e transparente ou opaco
    canto = im.getpixel((0, 0))
    cantos = [im.getpixel(p) for p in ((0, 0), (px - 1, 0), (0, px - 1), (px - 1, px - 1))]
    return {
        "bytes": destino.stat().st_size,
        "modo": im.mode,
        "tem_alfa": tem_alfa,
        "canto": canto,
        "cantos_transparentes": all(c[3] == 0 for c in cantos),
    }


def paginas():
    return sorted(list(DOCS.glob("*.html")) + list(DOCS.glob("features/*.html")))


def main():
    if len(sys.argv) < 2:
        print("uso: python .reversa/_logo_swap.py <caminho-do-png> [--seco]")
        return 2
    origem = Path(sys.argv[1])
    seco = "--seco" in sys.argv
    if not origem.exists():
        print("ERRO: imagem nao encontrada: %s" % origem)
        return 2

    hero = IMG / "logo.png"
    mini = IMG / "logo-mini.png"
    if not seco:
        info_h = gerar(origem, hero, HERO_PX)
        info_m = gerar(origem, mini, MINI_PX)
    else:
        info_h = info_m = {"bytes": 0, "modo": "?", "tem_alfa": None,
                           "canto": None, "cantos_transparentes": None}
    for nome, info in (("logo.png", info_h), ("logo-mini.png", info_m)):
        print("%-16s %6d bytes  modo=%s  tem_alfa=%s  canto=%s  cantos_transparentes=%s"
              % (nome, info["bytes"], info["modo"], info["tem_alfa"], info["canto"],
                 info["cantos_transparentes"]))

    trocas = []
    for f in paginas():
        t = f.read_text(encoding="utf-8")
        orig = t
        prefixo = "../" * (len(f.relative_to(DOCS).parts) - 1)

        if RE_HERO_SVG.search(t):
            t = RE_HERO_SVG.sub(
                '<img class="seal" src="%sassets/img/logo.png" alt="Logo do projeto: '
                'livro aberto com hélice de DNA e árvore genealógica">' % prefixo, t, count=1)
            acao_hero = "svg do hero -> img"
        elif RE_HERO_IMG.search(t):
            t = RE_HERO_IMG.sub(
                '<img class="seal" src="%sassets/img/logo.png" alt="Logo do projeto: '
                'livro aberto com hélice de DNA e árvore genealógica">' % prefixo, t, count=1)
            acao_hero = "img do hero atualizado"
        else:
            acao_hero = "-"

        if RE_MINI_SVG.search(t):
            t = RE_MINI_SVG.sub(
                '<img class="seal-mini" src="%sassets/img/logo-mini.png" alt="Logo do projeto">'
                % prefixo, t, count=1)
            acao_mini = "svg mini -> img"
        elif RE_MINI_IMG.search(t):
            t = RE_MINI_IMG.sub(
                '<img class="seal-mini" src="%sassets/img/logo-mini.png" alt="Logo do projeto">'
                % prefixo, t, count=1)
            acao_mini = "img mini atualizado"
        else:
            acao_mini = "-"

        if t != orig:
            if not seco:
                f.write_text(t, encoding="utf-8")
            trocas.append((f.relative_to(DOCS).as_posix(), acao_hero, acao_mini,
                           len(t.encode("utf-8")) - len(orig.encode("utf-8"))))

    print()
    print("paginas alteradas: %d de %d" % (len(trocas), len(paginas())))
    for nome, ah, am, delta in trocas:
        print("  %-30s hero=%-18s mini=%-18s delta=%+d" % (nome, ah, am, delta))

    # remocao dos SVGs antigos, so depois de as paginas apontarem para os PNGs
    for antigo in (IMG / "seal.svg", IMG / "seal-mini.svg"):
        if antigo.exists():
            if seco:
                print("--seco: %s seria removido" % antigo.name)
            else:
                antigo.unlink()
                print("removido: %s" % antigo.name)

    restantes = sorted(p.name for p in IMG.iterdir())
    print("assets/img agora: %s" % restantes)
    return 0


if __name__ == "__main__":
    sys.exit(main())

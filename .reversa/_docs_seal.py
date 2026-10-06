"""Publisher, passos 1 e 2: gera os dois selos a partir da seed, seguindo a skill
reversa-selo-generativo.

Regras aplicadas da skill:
  - padrao = int(seed[0:2], 16) % 5, na ordem [flow-field, particle-orbit,
    crystal-lattice, wave-interference, noise-strata]
  - seedInt = int(seed[0:16], 16), consumido por um PRNG semeado
  - paleta do estilo visual vem de references/PALETTE_BY_STYLE.md
  - mini (<200px) simplifica a paleta para as 3 primeiras cores
  - crystal-lattice em camadas: externas com as cores 1 e 2, internas com 3, 4, 5
  - contraste accent x bg conferido contra WCAG AA (4.5:1)

p5.js nao esta disponivel offline e a invariante do mini-site proibe CDN, entao o
PRNG semeado e implementado aqui (mulberry32) em vez de randomSeed() do p5. O
resultado e deterministico e reproduzivel por script.

Uso: python .reversa/_docs_seal.py
"""
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_reversa_docs"
IMG = DOCS / "assets" / "img"

PADROES = ["flow-field", "particle-orbit", "crystal-lattice", "wave-interference", "noise-strata"]

PALETA_SOBER = {
    "bg": "#f5f3ee",
    "foreground": ["#3d4a5c", "#7c8a99", "#a06b4a", "#4f6b5d", "#bdb4a4"],
    "accent": "#1e2937",
    "fg": "#1e2937",
}


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def linear(c):
    v = c / 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def luminancia(h):
    r, g, b = hex_rgb(h)
    return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)


def contraste(h1, h2):
    l1, l2 = luminancia(h1), luminancia(h2)
    claro, escuro = max(l1, l2), min(l1, l2)
    return (claro + 0.05) / (escuro + 0.05)


def espelhar_paleta(paleta):
    """Variante dark da skill: 'espelhar (bg <-> fg)'.

    Em vez de inverter a luminancia de cada cor (o que escureceria elementos
    sobre um fundo escuro), troca os PAPEIS: o extremo escuro da paleta vira
    fundo e o extremo claro vira elemento, ordenado do mais claro para o mais
    escuro, de modo que a camada externa, que ocupa mais area, tenha o maior
    contraste com o fundo.
    """
    todas = [paleta["bg"]] + paleta["foreground"] + [paleta["accent"]]
    ordenadas = sorted(set(todas), key=luminancia, reverse=True)
    bg = ordenadas[-1]
    elementos = ordenadas[:-1]
    elemento_central = ordenadas[0]
    return bg, elementos, elemento_central


class Semente:
    """mulberry32: PRNG deterministico de 32 bits."""

    def __init__(self, seed_int):
        self.estado = seed_int & 0xFFFFFFFF

    def r(self):
        self.estado = (self.estado + 0x6D2B79F5) & 0xFFFFFFFF
        t = self.estado
        t = (t ^ (t >> 15)) * (t | 1) & 0xFFFFFFFF
        t ^= (t + ((t ^ (t >> 7)) * (t | 61) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    def entre(self, a, b):
        return a + (b - a) * self.r()


def poligono(cx, cy, raio, lados, rot):
    pts = []
    for i in range(lados):
        a = rot + 2 * math.pi * i / lados
        pts.append((cx + raio * math.cos(a), cy + raio * math.sin(a)))
    return " ".join("%.2f,%.2f" % (x, y) for x, y in pts)


def gerar(seed_hex, estilo, tamanho):
    paleta = PALETA_SOBER
    padrao_idx = int(seed_hex[0:2], 16) % len(PADROES)
    padrao = PADROES[padrao_idx]
    seed_int = int(seed_hex[0:16], 16)
    prng = Semente(seed_int)

    mini = tamanho < 200
    # variante dark: o extremo escuro da paleta vira fundo e o claro vira elemento
    bg, fg, accent = espelhar_paleta(paleta)
    descartadas = [c for c in fg if contraste(c, bg) < 2.5]
    fg = [c for c in fg if contraste(c, bg) >= 2.5]
    if mini:
        fg = fg[:3]

    lados = 5 + int(prng.r() * 4)
    camadas = 3 + int(prng.r() * 4)
    phi = prng.r() * (math.pi / lados)
    giro = prng.r() * 2 * math.pi
    camadas = min(camadas, len(fg))
    if mini:
        camadas = min(camadas, 3)

    c = tamanho / 2.0
    raio_max = c * (0.86 if mini else 0.88)
    passo = 0.70 / camadas
    traco = 1.4 if mini else 3.0

    partes = []
    if not mini:
        partes.append("<title>Selo generativo de analisador-genealogico: %s</title>" % padrao)
    partes.append('<rect width="%d" height="%d" rx="%d" fill="%s"/>'
                  % (tamanho, tamanho, 14 if mini else 28, bg))

    # arestas radiais, so no hero, como vestigio da estrutura cristalina
    if not mini:
        arestas = []
        for i in range(lados):
            a = phi + 2 * math.pi * i / lados + giro
            x2 = c + raio_max * math.cos(a)
            y2 = c + raio_max * math.sin(a)
            arestas.append('    <line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (c, c, x2, y2))
        partes.append('<g stroke="%s" stroke-width="1" stroke-opacity="0.22">\n%s\n</g>'
                      % (fg[4 % len(fg)], "\n".join(arestas)))

    # camadas do cristal: externa dominante, internas com as cores seguintes
    camadas_svg = []
    for i in range(camadas):
        raio = raio_max * (1.0 - i * passo)
        cor = fg[i % len(fg)]
        jitter = (prng.r() - 0.5) * 0.10 if i else 0.0
        ptos = poligono(c, c, raio, lados, phi + giro + i * phi / 2.0 + jitter)
        camadas_svg.append('    <polygon points="%s" fill="%s"/>' % (ptos, cor))
    partes.append('<g stroke="%s" stroke-width="%.2f" stroke-linejoin="round">\n%s\n</g>'
                  % (bg, traco, "\n".join(camadas_svg)))

    # nucleo
    raio_nucleo = raio_max * (0.20 if mini else 0.17)
    ptos = poligono(c, c, raio_nucleo, lados, phi + giro)
    partes.append('  <polygon points="%s" fill="%s" stroke="%s" stroke-width="%.2f" '
                  'stroke-linejoin="round"/>' % (ptos, accent, bg, traco))

    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">\n'
           % (tamanho, tamanho, tamanho, tamanho)) + "\n".join(partes) + "\n</svg>\n"

    meta = {
        "seed": seed_hex, "estilo": estilo, "padrao": padrao, "tamanho": tamanho,
        "seedInt": seed_int, "lados": lados, "camadas": camadas,
        "phi": round(phi, 6), "giro": round(giro, 6),
        "cores": {"bg": bg, "accent": accent, "foreground": fg},
        "descartadas": descartadas,
        "contrasteAccentBg": round(contraste(accent, bg), 2),
        "mini": mini,
    }
    return svg, meta


def main():
    config = json.loads((DOCS / ".config.json").read_text(encoding="utf-8"))
    seed_hex = config["seed"]["hash"].replace("sha256:", "")
    estilo = config["interview"]["visualStyle"]

    resultados = {}
    for nome, tamanho in (("seal.svg", 800), ("seal-mini.svg", 64)):
        svg, meta = gerar(seed_hex, estilo, tamanho)
        # determinismo: gera duas vezes e compara
        svg2, _ = gerar(seed_hex, estilo, tamanho)
        det = "identico" if svg == svg2 else "DIVERGENTE"
        p = IMG / nome
        antes = hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else "(novo)"
        p.write_text(svg, encoding="utf-8")
        depois = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:16]
        resultados[nome] = meta
        print("%s: %d bytes  sha256=%s  (antes %s)  determinismo=%s"
              % (nome, len(svg.encode("utf-8")), depois, antes, det))
        print("   padrao=%s lados=%d camadas=%d phi=%.4f giro=%.3f  contraste=%.2f:1  mini=%s"
              % (meta["padrao"], meta["lados"], meta["camadas"], meta["phi"], meta["giro"],
                 meta["contrasteAccentBg"], meta["mini"]))
        print("   cores: bg=%s accent=%s fg=%s" % (meta["cores"]["bg"], meta["cores"]["accent"],
                                                   ",".join(meta["cores"]["foreground"])))
        if meta.get("descartadas"):
            print("   descartadas por contraste < 2.5:1 contra o fundo: %s" % ",".join(meta["descartadas"]))
        for c in [meta["cores"]["accent"]] + meta["cores"]["foreground"]:
            r = contraste(c, meta["cores"]["bg"])
            flag = "ok" if r >= 2.0 else "BAIXO"
            print("     contraste %s x bg = %5.2f:1  %s" % (c, r, flag))
        if meta["contrasteAccentBg"] < 4.5:
            print("   AVISO: contraste do nucleo abaixo de WCAG AA 4.5:1")
        if det != "identico":
            print("   AVISO: geracao nao reproduzivel")

    (ROOT / ".reversa" / "_docs_seal_meta.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

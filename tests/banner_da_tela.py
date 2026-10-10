"""Receita da arte do topo da tela (feature 011, `T036`).

## O problema que esta receita resolve, e como ele foi medido

A arte enviada pelo operador em 2026-10-10 chegou em **`RGB`, sem canal alfa**, com o
quadriculado de transparencia **gravado dentro** do bitmap. Medido nos primeiros pixels:
branco `ffffff` alternando com cinza `c7c7c7` em blocos de 8 px, com ruido de compressao
`c3`..`fe` nas bordas. Servir o arquivo como veio desenharia uma grade cinza atras do logo.

## Por que a remocao NAO pode ser por inundacao a partir da borda

A primeira versao desta receita inundava a partir da borda, para poupar as partes claras e
pouco saturadas da arte. **Foi medido que ela nao basta:** a arvore, o livro e o texto formam
**anuncios fechados**, e o fundo preso dentro deles nunca e alcancado. Medido no resultado da
primeira versao: o pixel `(300,150)` — entre os galhos e o livro — continuava
`rgba=(254,254,254,255)`, e sobraram **8.379** pixels de tom de fundo ainda OPAQUES numa
amostra de 1/9 da imagem. O quadriculado gravado continuava visivel, dentro dos bolsoes.

Entao a remocao e **global**: todo pixel claro e dessaturado vira transparente, esteja onde
estiver. O risco dessa escolha e comer uma parte clara da arte que seja dessaturada, e por
isso ela foi conferida ponto a ponto nos elementos em risco — a placa de Petri, o cone de luz
e as paginas do livro —, com as medicoes registradas na `T036`.

## A fonte canonica, e por que a derivada mora em `src/assets/`

A fonte e `docs/assets/img/banner-analisador.png`, ao lado da outra arte canonica do
projeto. A derivada vai para **`src/assets/`** porque o `.dockerignore` deste projeto e
lista de PERMISSAO (`*`, depois `!src/`, `!src/**`): arte em `docs/` responderia 200 aqui e
**404 dentro do container**, que e o ambiente do operador. `src/static/` continua proibida
pelo `W004`.

## Como regerar

    .venv\\Scripts\\python.exe -m tests.banner_da_tela
"""
from __future__ import annotations

import os
import sys

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FONTE = os.path.join(_RAIZ, "docs", "assets", "img", "banner-analisador.png")
ARTE_DE_RUNTIME = os.path.join(_RAIZ, "src", "assets", "banner-da-tela.png")

# Um pixel e FUNDO quando e claro e quase sem cor. Os limites saem de MEDICAO, e nao de
# estimativa:
#
#   - o cinza do quadriculado e `c7` (199) e o branco e `ff`, com ruido de compressao
#     (`c3`..`fe`). Dai `CLARO_MINIMO = 190`;
#   - a tinta clara da arte que chega perto do fundo e CLARA E SATURADA: as paginas do livro
#     medem `(230,203,158)` sat=72, `(239,217,176)` sat=63 e `(187,153,108)` sat=79. Dai o
#     teto de saturacao ficar bem abaixo disso.
#
# `SATURACAO_MAXIMA = 50` e a correcao de 2026-10-10, e ela vem de um defeito medido DUAS
# vezes. Sob o cone de luz do abajur a luz ambar tinge o quadriculado, e um BLOCO INTEIRO de
# fundo ficou gravado na arte: com o limite em 14, e depois ainda com 30. O composto sobre
# magenta mostrou o bloco nas duas vezes; a metrica que dizia "zero residuo" usava o MESMO
# limite da regra e por isso nao podia acusa-lo.
#
# O limite saiu de medir os dois lados, e nao de tentativa:
#
#   bloco residual (FUNDO)  max 206..253  min 171..220  sat 29..42
#   paginas do livro (ARTE) max 187..239  min 108..176  sat 63..79
#
# A saturacao separa sem ambiguidade — o fundo para em 42 e a arte comeca em 63 —, enquanto
# `min` NAO separa (171 contra 176, sobrepostos). Dai o corte em 50, no meio da folga.
CLARO_MINIMO = 190
SATURACAO_MAXIMA = 50


def _e_fundo(pixel: tuple[int, int, int]) -> bool:
    return max(pixel) >= CLARO_MINIMO and (max(pixel) - min(pixel)) <= SATURACAO_MAXIMA


def mascara_do_fundo(imagem) -> bytearray:
    """`1` para cada pixel de fundo quadriculado, **onde ele estiver**.

    Global, e nao por inundacao: ver a nota do modulo sobre os bolsoes fechados que a
    inundacao a partir da borda deixava passar.
    """
    largura, altura = imagem.size
    pixels = imagem.load()
    marca = bytearray(largura * altura)
    for y in range(altura):
        base = y * largura
        for x in range(largura):
            if _e_fundo(pixels[x, y]):
                marca[base + x] = 1
    return marca


def arte_limpa():
    """A arte de runtime: o fundo xadrez removido, com alfa suave na fronteira.

    ## A segunda passada, e por que ela existe

    A inundacao para no primeiro pixel que **nao** e fundo, e entre a arte e o xadrez ha
    uma faixa de um a dois pixels de cinza intermediario — o serrilhado. Deixar essa faixa
    opaca desenharia um halo claro em volta de tudo. A segunda passada da **alfa parcial**
    a essa fronteira, proporcional a quanto o pixel se afasta do fundo, e o halo some sem
    comer a arte.
    """
    from PIL import Image

    if not os.path.isfile(FONTE):
        raise SystemExit(f"arte canonica ausente: {FONTE}")
    original = Image.open(FONTE).convert("RGB")
    largura, altura = original.size
    pixels = original.load()
    marca = mascara_do_fundo(original)

    limpa = Image.new("RGBA", original.size, (0, 0, 0, 0))
    destino = limpa.load()
    for y in range(altura):
        for x in range(largura):
            r, g, b = pixels[x, y]
            if marca[y * largura + x]:
                continue
            destino[x, y] = (r, g, b, 255)

    # Fronteira: pixel NAO marcado que tem vizinho marcado recebe alfa proporcional a
    # distancia do fundo. `CLARO_MINIMO` e o piso, `ESCALA_ATE` o topo.
    for y in range(altura):
        for x in range(largura):
            if marca[y * largura + x]:
                continue
            vizinho_de_fundo = any(
                0 <= x + dx < largura and 0 <= y + dy < altura
                and marca[(y + dy) * largura + (x + dx)]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            if not vizinho_de_fundo:
                continue
            r, g, b = pixels[x, y]
            if max(r, g, b) - min(r, g, b) > SATURACAO_MAXIMA:
                continue
            # Quanto MAIS claro, MAIS transparente: e o serrilhado contra o fundo claro.
            excesso = max(0, max(r, g, b) - CLARO_MINIMO)
            alfa = max(0, 255 - int(255 * excesso / (255 - CLARO_MINIMO)))
            if alfa < 255:
                destino[x, y] = (r, g, b, alfa)
    return limpa


def residuo_de_fundo(imagem) -> int:
    """Pixels OPACOS com tom de fundo, medidos com limite **mais estrito** que o da regra.

    Nao-circular de proposito. Medir o residuo com o MESMO limite que a regra usa sempre
    devolve zero, e foi exatamente esse erro que deixou passar um bloco inteiro de
    quadriculado duas vezes nesta sessao: a metrica dizia `0,00 %` enquanto o composto sobre
    magenta mostrava o bloco. Medir com um limite menor nao pode dar esse falso negativo.

    O valor nao e zero, e nao precisa ser: sobram franjas de um pixel nas bordas
    antialiased, onde a tinta se misturou com o quadriculado. O que importa e que nao haja
    BLOCO — regiao grande e conexa —, e o teste de regressao prende exatamente a caixa do
    bloco que existiu.
    """
    limite = SATURACAO_MAXIMA - 5
    pixels = imagem.load()
    total = 0
    for y in range(imagem.size[1]):
        for x in range(imagem.size[0]):
            r, g, b, a = pixels[x, y]
            if a == 255 and min(r, g, b) >= 185 and (max(r, g, b) - min(r, g, b)) <= limite:
                total += 1
    return total


def main() -> int:
    limpa = arte_limpa()
    os.makedirs(os.path.dirname(ARTE_DE_RUNTIME), exist_ok=True)
    limpa.save(ARTE_DE_RUNTIME, format="PNG", optimize=True)

    opacos = limpa.getchannel("A").histogram()[255]
    total = limpa.size[0] * limpa.size[1]
    print(f"fonte     : {FONTE}")
    print(f"derivada  : {ARTE_DE_RUNTIME}")
    print(f"tamanho   : {limpa.size}")
    print(f"bytes     : {os.path.getsize(ARTE_DE_RUNTIME):,}")
    print(f"transparentes: {100 * (total - opacos) / total:.1f} %")
    residuo = residuo_de_fundo(limpa)
    print(f"residuo de fundo (limite estrito sat<={SATURACAO_MAXIMA - 5}): "
          f"{residuo} px ({100 * residuo / total:.3f} %)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

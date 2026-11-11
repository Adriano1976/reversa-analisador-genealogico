"""Faixas do ideograma por cromossomo (feature 056).

Converte as regiões já projetadas em linhas de um ideograma: uma linha por
cromossomo, uma faixa por região, posicionada pela coordenada.

## A régua, e por que ela é declarada

O CSV de matches **não declara o build** do genoma. A régua usada aqui é o
**GRCh37** (build 37), a mesma convenção que o GEDmatch usa nos exports de
triangulação. A diferença para o GRCh38 é de alguns megabases em poucos
cromossomos e não muda a leitura visual de uma faixa. Posição que passa do
comprimento é presa na borda; cromossomo desconhecido cai para a maior
coordenada vista no próprio arquivo, e a linha declara isso.

Nenhum número de genética é inventado aqui: o comprimento só serve de escala de
desenho, e o tooltip mostra as coordenadas exatas do arquivo.

## O que este módulo NÃO faz

Não lê arquivo, não importa `core/` (`ADR-34`) e não decide desfecho: recebe os
dicionários que `application.regioes.projetar_regioes` já montou.
"""
from __future__ import annotations

from collections import defaultdict

#: Comprimentos do GRCh37, em pares de bases. Fonte: assembly GRCh37 (build 37),
#: a mesma convenção dos exports do GEDmatch. Serve de régua de desenho; não é
#: medida do arquivo.
COMPRIMENTO_GRCH37 = {
    "1": 249_250_621,
    "2": 243_199_373,
    "3": 198_022_430,
    "4": 191_154_276,
    "5": 180_915_260,
    "6": 171_115_067,
    "7": 159_138_663,
    "8": 146_364_022,
    "9": 141_213_431,
    "10": 135_534_747,
    "11": 135_006_516,
    "12": 133_851_895,
    "13": 115_169_878,
    "14": 107_349_540,
    "15": 102_531_392,
    "16": 90_354_753,
    "17": 81_195_210,
    "18": 78_077_248,
    "19": 59_128_983,
    "20": 63_025_520,
    "21": 48_129_895,
    "22": 51_304_566,
    "X": 155_270_560,
    "Y": 59_373_566,
    "MT": 16_569,
}

#: Largura mínima de uma faixa, em % do trilho. Sem ela, uma região de 1 Mb num
#: cromossomo de 250 Mb viraria um pixel e desapareceria.
LARGURA_MINIMA = 0.6

#: O cartão do hover tem 280 px e abre a partir da faixa. Colado numa das bordas
#: do trilho ele sairia para fora, então o lado acompanha o terço em que a faixa
#: cai: até 35% abre para a direita (`left:0`), acima de 55% para a esquerda
#: (`right:0`), e no meio fica centrado. Os números não são medidos no arquivo:
#: são a largura do cartão contra a largura do trilho, e vale para a tela de
#: trabalho (o trilho fica entre 600 e 900 px).
LADO_DIREITA = 35.0
LADO_ESQUERDA = 55.0


def _lado(esquerda: float) -> str:
    """Para que lado o cartão do hover abre, a partir da posição da faixa."""
    if esquerda <= LADO_DIREITA:
        return "direita"
    if esquerda > LADO_ESQUERDA:
        return "esquerda"
    return "centro"


def _ordem_do_cromossomo(cromossomo: str):
    texto = cromossomo.strip().upper()
    if texto.isdigit():
        return (0, int(texto), "")
    return (1, 0, texto)


def _comprimento(cromossomo: str, maior_fim: int) -> tuple[int, bool]:
    """Comprimento da régua e se ele veio do GRCh37 ou do próprio arquivo."""
    chave = cromossomo.strip().upper()
    if chave in COMPRIMENTO_GRCH37:
        return COMPRIMENTO_GRCH37[chave], True
    # Convenções numéricas de X e Y em alguns exports.
    if chave in ("23", "X"):
        return COMPRIMENTO_GRCH37["X"], chave == "X"
    if chave in ("24", "Y"):
        return COMPRIMENTO_GRCH37["Y"], chave == "Y"
    if chave in ("M", "MT"):
        return COMPRIMENTO_GRCH37["MT"], chave == "MT"
    # Desconhecido: escala o próprio arquivo. Melhor uma régua honesta do que
    # um cromossomo inventado.
    return max(maior_fim, 1), False


def montar_ideograma(itens, largura_minima: float = LARGURA_MINIMA) -> list[dict]:
    """Agrupa as regiões por cromossomo e calcula a posição de cada faixa."""
    por_cromossomo: dict[str, list[dict]] = defaultdict(list)
    for item in itens or ():
        por_cromossomo[str(item.get("cromossomo") or "").strip().upper()].append(item)

    linhas = []
    for cromossomo, lista in sorted(por_cromossomo.items(), key=lambda par: _ordem_do_cromossomo(par[0])):
        maior_fim = max(int(item.get("fim") or 0) for item in lista) or 1
        comprimento, regua_oficial = _comprimento(cromossomo, maior_fim)
        faixas = []
        for item in sorted(lista, key=lambda entrada: int(entrada.get("inicio") or 0)):
            inicio = max(0, int(item.get("inicio") or 0))
            fim = max(inicio, int(item.get("fim") or 0))
            esquerda = max(0.0, min(100.0, 100.0 * inicio / comprimento))
            largura = 100.0 * (fim - inicio) / comprimento
            largura = max(largura, largura_minima)
            largura = min(largura, 100.0 - esquerda)
            faixas.append({
                **item,
                "esquerda": round(esquerda, 2),
                "largura": round(largura, 2),
                # Perto de uma das bordas o cartão do hover abriria para fora.
                "lado": _lado(esquerda),
            })
        linhas.append({
            "cromossomo": cromossomo,
            "comprimento_mb": round(comprimento / 1_000_000, 1),
            "regua_oficial": regua_oficial,
            "faixas": faixas,
        })
    return linhas


__all__ = [
    "COMPRIMENTO_GRCH37",
    "LADO_DIREITA",
    "LADO_ESQUERDA",
    "LARGURA_MINIMA",
    "montar_ideograma",
]

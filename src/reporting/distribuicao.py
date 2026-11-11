"""Desenho do grafico de distribuicao por cromossomo (feature 057).

Converte os dicionarios que `application.distribuicao` projetou em geometria: topo de
cada eixo, marcas de escala e altura das barras em porcentagem. Nao le arquivo, nao
importa `core/` (`ADR-34`) e nao formata numero — o template formata.

## Os dois eixos

Sao duas escalas independentes (`RN-04`): Matches a esquerda, cM medio a direita. As duas
**partem de zero** (`RN-08`): barra pressupoe base zero, e eixo com base deslocada exagera
diferenca e mente sobre o que o arquivo tem. O topo e arredondado para um valor redondo
para a escala ficar legivel — topo no maior valor exato faz a barra mais alta encostar na
borda e as outras ficarem com altura arbitraria.

## O passo "redondo"

Os passos sao fixos e pequenos de proposito: o dominio e de poucas dezenas (kits) e de
poucas dezenas de cM, entao um passo tirado de uma lista fixa e testavel e nao precisa da
aritmetica generica de escalas continuas. O topo e `passo * INTERVALOS_POR_EIXO`.
"""
from __future__ import annotations

#: Passos possiveis do eixo de Matches, em kits. Inteiros, porque a serie e contagem.
PASSOS_DE_MATCHES = (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000)

#: Passos possiveis do eixo de cM medio, em centimorgans.
PASSOS_DE_CM = (1, 2, 4, 5, 8, 10, 20, 25, 50, 100)

#: Intervalos por eixo: o topo e o maior multiplo do passo, e as marcas vao de zero ao
#: topo nesse numero de intervalos (cinco marcas, contando o zero).
INTERVALOS_POR_EIXO = 4

#: O cartao do hover tem 280 px e abre a partir de uma coluna estreita. Ate 20% da
#: largura ele abre para a direita (`left:0`), acima de 80% para a esquerda (`right:0`),
#: e no meio fica centrado. Sao limites de desenho, nao de dominio.
LADO_DIREITA = 20.0
LADO_ESQUERDA = 80.0


def _passo(valor_maximo: float, passos) -> float:
    """Menor passo da lista que cobre `valor_maximo` em `INTERVALOS_POR_EIXO` partes."""
    if valor_maximo <= 0:
        return passos[0]
    alvo = valor_maximo / INTERVALOS_POR_EIXO
    for passo in passos:
        if passo >= alvo:
            return passo
    # Acima do maior passo conhecido: o proximo multiplo de 10 que cobre o alvo.
    expoente = 1
    while 10 ** expoente < alvo:
        expoente += 1
    return 10 ** expoente


def _eixo(valor_maximo: float, passos) -> dict:
    passo = _passo(valor_maximo, passos)
    topo = passo * INTERVALOS_POR_EIXO
    marcas = [
        {"valor": passo * indice, "posicao": round(100.0 * passo * indice / topo, 2)}
        for indice in range(INTERVALOS_POR_EIXO + 1)
    ]
    return {"topo": topo, "passo": passo, "marcas": marcas}


def _lado(posicao: float, total: int) -> str:
    esquerda = 100.0 * (posicao + 0.5) / total if total else 50.0
    if esquerda <= LADO_DIREITA:
        return "direita"
    if esquerda >= LADO_ESQUERDA:
        return "esquerda"
    return "centro"


def montar_distribuicao(itens) -> dict:
    """Geometria do grafico: eixos, marcas e uma coluna por cromossomo."""
    base = list(itens or ())
    if not base:
        return {"eixo_matches": {}, "eixo_cm": {}, "colunas": []}

    maior_kits = max(int(item.get("kits") or 0) for item in base)
    maior_cm = max(float(item.get("cm_medio") or 0.0) for item in base)
    eixo_matches = _eixo(maior_kits, PASSOS_DE_MATCHES)
    eixo_cm = _eixo(maior_cm, PASSOS_DE_CM)

    total = len(base)
    colunas = []
    for posicao, item in enumerate(base):
        kits = int(item.get("kits") or 0)
        cm_medio = float(item.get("cm_medio") or 0.0)
        colunas.append({
            **item,
            "altura_matches": round(100.0 * kits / eixo_matches["topo"], 2),
            "altura_cm": round(100.0 * cm_medio / eixo_cm["topo"], 2),
            "lado": _lado(posicao, total),
        })

    return {"eixo_matches": eixo_matches, "eixo_cm": eixo_cm, "colunas": colunas}


__all__ = [
    "INTERVALOS_POR_EIXO",
    "LADO_DIREITA",
    "LADO_ESQUERDA",
    "PASSOS_DE_CM",
    "PASSOS_DE_MATCHES",
    "montar_distribuicao",
]

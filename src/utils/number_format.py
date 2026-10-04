"""Formato dos numeros que o operador le na tela.

Autoridade unica da regra de exibicao numerica, no mesmo espirito de
`utils/text_cleaning.py` para limpeza de mojibake: a regra mora em um lugar so, e
nao espalhada pelo template.

Nasceu do BUG-20261004-EWSJ: o badge de cM exibia `19.200000000000003` porque o
valor somado em ponto flutuante ia cru para o HTML.
"""
from __future__ import annotations

# Teto de casas decimais, e nao numero fixo: o CSV de origem pode trazer duas
# casas, e trunca-las perderia dado.
CASAS = 2


def formatar_cm(valor) -> str:
    """Total de cM no formato que o operador le: `19,2`, `19,25`, `20`.

    Ate duas casas decimais, com virgula decimal, e sem zeros a direita. Zeros a
    direita saem porque o dado de origem normalmente tem uma casa, e `20,0`
    sugeriria uma precisao que nao existe.

    O arredondamento e **so de apresentacao**. O valor armazenado em
    `result["cm"]` continua o `float` exato, porque a paridade contra o oraculo
    congelado exige igualdade exata, sem tolerancia e sem arredondamento
    (`_reversa_sdd/migration/parity_specs.md`).

    Nao ha separador de milhar, por decisao: os totais de cM ficam na casa das
    centenas, e um separador mudaria a leitura de um valor exportado.

    Aceita o que `float()` aceita, e levanta `TypeError`/`ValueError` fora disso,
    em vez de inventar um valor.
    """
    texto = f"{float(valor):.{CASAS}f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def formatar_inteiro(valor) -> str:
    """Inteiro no formato que o operador le: `1134` vira `1.134`.

    Nasceu com a evidencia genetica: SNPs e posicoes sao numeros grandes e
    contados, e a leitura sem separador de milhar convida a erro. Valor ausente
    sai como travessao, e nao como zero: ausencia de dado nao e dado zero.
    """
    if valor is None or valor == "":
        return "—"
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return "—"
    return f"{numero:,}".replace(",", ".")

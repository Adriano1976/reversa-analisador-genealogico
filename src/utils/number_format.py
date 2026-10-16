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


# As bases sao 1024, e nao 1000, porque sao as MESMAS que o projeto ja usa no teto de upload
# (`TETO_DE_UPLOAD_EM_MB`, em `src/app.py`): duas regras para a mesma grandeza dariam dois
# numeros para o mesmo arquivo.
BYTES_POR_KILOBYTE = 1024
BYTES_POR_MEGABYTE = 1024 * 1024
#: De 1 MB para cima o valor sai em MB; abaixo disso, em KB.
LIMITE_PARA_MEGABYTE = BYTES_POR_MEGABYTE


def _com_unidade(quantidade: float, unidade: str) -> str:
    """O numero com no maximo `CASAS` casas, virgula decimal, e a unidade colada.

    Zeros a direita saem: `100 MB`, e nao `100,00 MB`. E a mesma politica de `formatar_cm`,
    pela mesma razao — zero a direita sugere uma precisao que o dado nao tem.
    """
    texto = f"{quantidade:.{CASAS}f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto.replace(".", ",") + " " + unidade


def formatar_tamanho(valor) -> str:
    """Tamanho de arquivo na unidade que se le de relance: `100 MB`, `8,54 MB`, `55 KB`.

    ## Duas unidades, e o corte em 1 MB

    Abaixo de 1 MB o valor sai em **KB**; de 1 MB para cima, em **MB**. O corte existe porque
    uma unidade so' mente numa das pontas: em MB, um arquivo de 55 KB vira `0,05 MB`, que
    ninguem le; e em bytes, um GEDCOM de 8,9 MB vira `8.955.472 bytes`, que foi exatamente o
    que o operador pediu para sair da tela em 2026-10-16.

    ## A precisao e a de `formatar_cm`, e nao uma nova

    Ate duas casas, com virgula decimal e **sem zeros a direita**.

    ## O que fica de fora, e por que

    Arquivo abaixo de 1 KB continua em KB: um de 512 bytes sai como `0,5 KB`, e um de 0 bytes
    como `0 KB`. Nao ha terceira unidade — o acervo deste aplicativo e' de GEDCOM e CSV, que
    comecam na casa dos KB, e o numero exato em bytes vive no `title` da celula. Se um dia
    entrar arquivo de dezenas de bytes, o que falta e' uma faixa em bytes, e nao mais casas
    decimais: `0,01 KB` continua ilegivel.
    """
    if valor is None or valor == "":
        return "—"
    try:
        total = float(valor)
    except (TypeError, ValueError):
        return "—"
    if total >= LIMITE_PARA_MEGABYTE:
        return _com_unidade(total / BYTES_POR_MEGABYTE, "MB")
    return _com_unidade(total / BYTES_POR_KILOBYTE, "KB")

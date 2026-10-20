"""Textos humanos dos motivos de descarte (feature 038).

## Por que este módulo existe

Até a 037, o motivo de uma recusa por semelhança era uma string montada dentro do bloco de
scoring de `core/matching.py`:

    score insuficiente ou conflito de sobrenome (given=100, final=88.25, inter=1/1, jacc=0.50)

Três defeitos, e nenhum é de estilo: (a) oferece **duas** causas e não diz qual; (b) omite o
portão que de fato recusou — a penalidade de token do meio só age depois de todos os outros
passarem, e não aparecia em número nenhum; (c) fala em nome de variável de máquina, que não
significa nada para quem lê a planilha em outra ferramenta. O adendo `024` já tinha medido
que a metade "conflito de sobrenome" **nunca** era a causa literal em 325 descartes.

Este módulo guarda o que o núcleo precisa dizer, longe da decisão: o catálogo
`código -> frase`, o diagnóstico por precedência e a montagem do detalhe técnico. Texto de
apresentação não muda veredito — `core/matching.py` continua decidindo exatamente como antes,
e só passa a **relatar** o que decidiu.

## A precedência não é arbitrária

A ordem vai do mais acionável ao menos acionável: o primeiro motivo pede conferir um nome, o
último avisa que não há o que conferir. Ela também é parte do contrato (`RN-26`): o mesmo par
de nomes recebe sempre a mesma frase, e um teste prende isso.

O veto do token do meio vem primeiro porque é o único portão que **desfaz** um aceite já
obtido — quando ele age, todos os demais já passaram, e acusar qualquer outro seria mentira.
"""

from __future__ import annotations

from dataclasses import dataclass

# Códigos estáveis (`RN-27`). O texto pode ser reescrito sem quebrar quem lê o código.
NAO_ENCONTRADO = "nao_encontrado"
NOME_DO_MEIO_AUSENTE = "nome_do_meio_ausente"
SOBRENOMES_EM_COMUM_INSUFICIENTES = "sobrenomes_em_comum_insuficientes"
SOBRENOME_POUCO_PARECIDO = "sobrenome_pouco_parecido"
PRENOME_DIFERENTE = "prenome_diferente"
SEMELHANCA_INSUFICIENTE = "semelhanca_insuficiente"
SEM_SOBRENOME_COMUM = "sem_sobrenome_comum"
SOBRENOME_LIDO_COMO_PRENOME = "sobrenome_lido_como_prenome"
NOME_UNICO = "nome_unico"
SOBRENOME_CURTO = "sobrenome_curto"
SEM_SOBRENOME_NO_GEDCOM = "sem_sobrenome_no_gedcom"

#: Menor limiar de prenome entre as portas de aceite de `core/matching.py`. Espelha a decisão
#: de propósito: o diagnóstico não pode discordar do portão que recusou. Há teste que prende
#: este valor justamente para que a mudança do limiar apareça antes de a frase mentir.
LIMIAR_DE_PRENOME = 85

#: O catálogo. Uma frase por causa, curta, com sujeito e predicado, sem número e sem termo
#: técnico. Os quatro motivos do adendo `024` entraram como estavam — eles já falavam em
#: português; o que mudou neles foi só o parêntese do filtro anti-falso-positivo.
TEXTOS = {
    NOME_DO_MEIO_AUSENTE:
        "o nome tem uma parte a mais que não aparece na árvore",
    SOBRENOMES_EM_COMUM_INSUFICIENTES:
        "há sobrenome em comum, mas de menos para este prenome",
    SOBRENOME_POUCO_PARECIDO:
        "o sobrenome é parecido, mas não o suficiente",
    PRENOME_DIFERENTE:
        "o prenome é diferente do que está na árvore",
    SEMELHANCA_INSUFICIENTE:
        "o nome é parecido, mas não o suficiente para ser a mesma pessoa",
    SEM_SOBRENOME_COMUM:
        "nenhum sobrenome em comum entre o nome e o da árvore",
    SOBRENOME_LIDO_COMO_PRENOME:
        "o sobrenome foi lido como prenome (nome sem sobrenome isolável)",
    NOME_UNICO:
        "o nome não tem sobrenome (nome único)",
    SOBRENOME_CURTO:
        "sobrenome curto demais para buscar (inicial ou abreviação)",
    SEM_SOBRENOME_NO_GEDCOM:
        "nenhum sobrenome do nome existe no GEDCOM",
    NAO_ENCONTRADO:
        "não encontrado",
}


@dataclass(frozen=True)
class Motivo:
    """Uma recusa, com a parte estável (`codigo`), a legível (`texto`) e a conferível (`detalhe`).

    `detalhe` vazio significa "esta recusa não vem do bloco de semelhança": as causas do
    adendo `024` não têm número nenhum a mostrar, e inventar um seria pior que omitir.
    """

    codigo: str
    texto: str
    detalhe: str = ""


def motivo(codigo: str, detalhe: str = "") -> Motivo:
    """Monta um `Motivo` a partir do catálogo. Levanta `KeyError` se o código não existir."""
    return Motivo(codigo=codigo, texto=TEXTOS[codigo], detalhe=detalhe)


def _numero(valor) -> str:
    """Número como o Excel em português lê: vírgula decimal, sem zero à direita.

    Mesma regra de `reporting/csv_de_descartes._numero` (`035`), repetida aqui porque a
    `reporting/` não pode ser importada pelo núcleo (`ADR-34`).
    """
    return f"{float(valor):.2f}".rstrip("0").rstrip(".").replace(".", ",")


def detalhe_tecnico(*, prenome, nota, intersecao, exigidas, grafia) -> str:
    """Os quatro números da decisão, com rótulo em português (`RN-28`).

    Separador `·` e não `;`: a planilha usa ponto e vírgula como delimitador, e um `;` aqui
    obrigaria escape à toa.
    """
    return (f"prenome {float(prenome):.0f} · nota {_numero(nota)} · "
            f"sobrenomes em comum {intersecao} de {exigidas} · "
            f"grafia do sobrenome {_numero(grafia)}")


def diagnosticar(*, prenome, nota, intersecao, exigidas, grafia, grafia_ok, meio_vetado) -> Motivo:
    """Nomeia **uma** causa de recusa, por precedência fixa (`RN-26`).

    Recebe os valores que a decisão já calculou — não recalcula nada, não consulta a árvore e
    não altera veredito. `meio_vetado` diz se o sétimo portão desfez um aceite que já existia.
    """
    if meio_vetado:
        codigo = NOME_DO_MEIO_AUSENTE
    elif intersecao < exigidas:
        codigo = SOBRENOMES_EM_COMUM_INSUFICIENTES
    elif not grafia_ok:
        codigo = SOBRENOME_POUCO_PARECIDO
    elif prenome < LIMIAR_DE_PRENOME:
        codigo = PRENOME_DIFERENTE
    else:
        codigo = SEMELHANCA_INSUFICIENTE

    return Motivo(
        codigo=codigo,
        texto=TEXTOS[codigo],
        detalhe=detalhe_tecnico(prenome=prenome, nota=nota, intersecao=intersecao,
                                exigidas=exigidas, grafia=grafia),
    )

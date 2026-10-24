"""CSV da lista de trabalho dos descartes (feature 035).

Os descartes são os nomes do CSV que não viraram cartão. A tela já mostra o motivo e,
desde a `034`, os candidatos que a árvore oferecia. O que faltava era **levar a lista
para fora**: é no cadastro da árvore que esses nomes se resolvem, e isso acontece em
outra ferramenta.

- **Ponto e vírgula como separador.** O Excel em português trata `,` como decimal; com
  vírgula como separador cada valor viraria texto.
- **BOM no começo.** Sem ele, o Excel abre o arquivo em ANSI e os acentos viram lixo.
- **Decimal com vírgula** pela mesma razão.
- **Guarda contra fórmula.** Nome de pessoa pode começar com `=`, `+`, `-` ou `@`; o
  Excel avaliaria a célula como fórmula. O prefixo `'` desarma a avaliação sem mudar o
  texto lido.
- **Uma linha por descarte.** Quando há mais de um candidato compatível, todos vão na
  mesma célula separados por ` | ` — a lista é de nomes a conferir, não de candidatos.
- **Detalhe técnico ao fim (feature 038).** A coluna Motivo passou a falar português comum;
  os quatro números que explicam a recusa (`prenome`, `nota`, `sobrenomes em comum`,
  `grafia`) foram para uma nona coluna, à direita. As oito primeiras não mudaram de nome
  nem de posição.

Função pura: recebe os descartes como a tela os tem e devolve texto. Não lê arquivo,
não fala com a rede e não importa `core/` (`ADR-34`).
"""
from __future__ import annotations

import csv
import io

CABECALHO = (
    "Nome no CSV",
    "Kit",
    "cM",
    "Motivo",
    "Candidato na árvore",
    "Nascimento",
    "Prenome",
    "Nota",
    # A nona coluna nasceu na feature 038. As oito primeiras mantêm nome e posição: a
    # planilha é lida em outra ferramenta, e quem lê por índice não pode quebrar.
    "Detalhe técnico",
)

_PERIGOSOS = ("=", "+", "-", "@")


def _texto(valor) -> str:
    """Célula de texto, desarmada contra fórmula do Excel."""
    if valor is None:
        return ""
    texto = str(valor)
    if texto.startswith(_PERIGOSOS):
        return "'" + texto
    return texto


def _numero(valor) -> str:
    """Número no formato que o Excel em português lê como número.

    Duas casas e sem zeros à direita: a nota do casamento tem duas casas (88,25), e
    arredondar para uma inventaria precisão que a decisão não tem.
    """
    if valor is None or valor == "":
        return ""
    try:
        texto = f"{float(valor):.2f}".rstrip("0").rstrip(".")
        return texto.replace(".", ",")
    except (TypeError, ValueError):
        return _texto(valor)


def _candidatos(item: dict) -> tuple[str, str, str, str]:
    """As quatro colunas do candidato, e **só** do compatível.

    Quem não tem candidato compatível sai com as colunas vazias. O "melhor avaliado"
    aparece na tela para explicar a recusa, mas nesta planilha ele seria enganoso: a
    lista é de nomes a cadastrar, e um homônimo de outro século (medido: *Luzia Martins
    dos Santos*, 1798) não é endereço de ninguém. O Motivo continua dizendo o que houve.
    """
    candidatos = [c for c in (item.get("candidatos") or []) if c.get("compativel")]
    if not candidatos:
        return "", "", "", ""
    return (
        " | ".join(_texto(c.get("nome")) for c in candidatos),
        " | ".join(_texto(c.get("nascimento") or "") for c in candidatos),
        " | ".join(_numero(c.get("prenome")) for c in candidatos),
        " | ".join(_numero(c.get("nota")) for c in candidatos),
    )


def csv_de_descartes(itens) -> str:
    """Uma linha por descarte, no formato que o operador abre na planilha."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", lineterminator="\r\n")
    escritor.writerow(CABECALHO)
    for item in itens or ():
        candidato, nascimento, prenome, nota = _candidatos(item)
        escritor.writerow([
            _texto(item.get("csv_name")),
            _texto(item.get("kit") or ""),
            _numero(item.get("cm")),
            _texto(item.get("motivo")),
            candidato,
            nascimento,
            prenome,
            nota,
            # Feature 038: os números que explicam a recusa saem da coluna Motivo (que agora
            # fala português) e vão para cá, rotulados. Vazio quando a recusa não vem do
            # bloco de semelhança — as causas de sobrenome não medem nada.
            _texto(item.get("motivo_detalhe")),
        ])
    return "\ufeff" + saida.getvalue()

"""Fachada de correção: do GEDCOM e do CSV até a árvore sugerida.

O núcleo (`core.cirurgia_do_grafo`) é puro: recebe a árvore, o parentesco documental
e o veredito, e devolve a sugestão. Esta camada faz o trabalho de borda — lê os dois
arquivos uma vez, delega a validação para `application.validacao` e monta uma
sugestão por comparação.

## O que NÃO acontece aqui

- **Nenhum parser novo:** `validar_arquivos` já parseia a árvore e a devolve.
- **Nenhum veredito novo:** o status vem de `core.validator`, pela `028`.
- **Nenhuma decisão de cirurgia:** toda ela é de `core.cirurgia_do_grafo`.
- **Nenhuma escrita:** nem `.ged`, nem banco, nem tela. A sugestão é efêmera.

## Por que `incluir_documental=True`

O resultado do validador não carrega `path.ids` nem `evidence`. Sem o parâmetro, esta
fachada teria de refazer o laço de matching para redescobrir quem é o match — uma
segunda verdade sobre a mesma pergunta. Com ele, a árvore e o parentesco documental
chegam de uma única passada.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.cirurgia_do_grafo import arvore_sugerida


@dataclass(frozen=True)
class DependenciasDeCorrecao:
    """A validação injetável, para o teste não precisar de arquivo real."""

    validar: Callable


def _dependencias_padrao() -> DependenciasDeCorrecao:
    from application.validacao import validar_arquivos

    return DependenciasDeCorrecao(validar=validar_arquivos)


def sugerir_correcao(caminho_gedcom: str, caminho_dna: str, nome_doador: str,
                     ano_referencia: int | None = None,
                     deps: DependenciasDeCorrecao | None = None) -> dict:
    """Valida os dois arquivos e devolve uma árvore sugerida por comparação.

    O retorno é ``{"doador", "sugestoes", "resumo", "ano_referencia",
    "intervalo_de_geracao"}``. Cada item de ``sugestoes`` é o contrato de §4.7 do
    requirements: ``grafo`` é ``None`` quando não há o que sugerir, e ``avisos[0]``
    diz por quê.

    A árvore é parseada **uma vez** — a mesma tupla serve à validação e à cirurgia.
    """
    deps = deps or _dependencias_padrao()
    validacao = deps.validar(caminho_gedcom, caminho_dna, nome_doador, ano_referencia,
                             incluir_documental=True)

    arvore = validacao.get("arvore")
    doador_id = (validacao.get("doador") or {}).get("id")

    sugestoes = []
    for comparacao in validacao.get("comparacoes") or []:
        documental = comparacao.get("documental") or {}
        sugestoes.append(arvore_sugerida(arvore, documental, comparacao, doador_id))

    com_sugestao = sum(1 for sugestao in sugestoes if sugestao.get("grafo") is not None)
    return {
        "doador": validacao.get("doador"),
        "sugestoes": sugestoes,
        "resumo": {
            "comparacoes": len(sugestoes),
            "com_sugestao": com_sugestao,
            "geracoes_virtuais": sum(len(sugestao.get("geracoes_virtuais") or [])
                                     for sugestao in sugestoes),
        },
        "ano_referencia": validacao.get("ano_referencia"),
        "intervalo_de_geracao": validacao.get("intervalo_de_geracao"),
    }


__all__ = ["DependenciasDeCorrecao", "sugerir_correcao"]

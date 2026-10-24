"""Tarefa 01 — Rotinas de limpeza de nome.

Autoridade unica da limpeza de mojibake (`strip_bad_utf`, `demojibake`), consumida
por `csv_ingest`, `name_normalization` e `dna_analysis`, que a reexporta. O nome
antigo do arquivo descrevia uma camada de dominio que ele nunca foi; a renomeacao
esta na OPP-20261003-LMAY.

DECISAO DO USUARIO (2026-09-30, _reversa_sdd/questions.md#pergunta-3): `Family`,
`GenealogyGraph` e `DNAGroup` foram REMOVIDAS. Eram arquitetura abandonada no meio
do caminho: nenhuma das tres era instanciada em qualquer caminho de producao,
confirmado por varredura de referencias, e o fluxo real usa os dicionarios de
pessoas e de familias e os registros do ged4py diretamente. Preservar as classes
sem uso custaria a quem reimplementar a obrigacao de decidir entre adotar ou
descartar algo que o legado nunca adotou.

Nota historica: a docstring anterior dizia que o modulo representava "PERSON,
FAMILIA e DNA_MATCH em memoria" — nunca foi verdade, e o fluxo real sempre usou
dicionarios e registros do ged4py; as entidades eram decorativas.
"""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Correção de mojibake (encoding corrompido Latin-1 lido como UTF-8)
# ---------------------------------------------------------------------------

# Limpeza de nome: autoridade unica do projeto.
#
# Os dois corpos vieram de `dna_analysis`, que os usava de fato. A versao anterior
# deste modulo apenas removia U+FFFD, nao era consumida por nenhum caminho de
# producao, e as duas implementacoes divergiam em 5 de 9 casos.
# Ver `_reversa_sdd/addenda/003-refactor-code-quality.md`.


def strip_bad_utf(s):
    if s is None:
        return ""
    s = str(s)
    fixes = {
        "A�": "ç", "Ã§": "ç",
        "Ã£": "ã", "Ã¡": "á", "Ã¢": "â",
        "Ã©": "é", "Ãª": "ê", "Ã¨": "è",
        "Ã­": "í", "Ã³": "ó", "Ã´": "ô", "Ãº": "ú",
        "Ã": "Ã",
        "GouvA�": "Gouvê",
        "A�": "ç",
        "JoA�o": "João", "SA�": "Sá", "GonA�": "Gonç",
    }
    for bad, good in fixes.items():
        s = s.replace(bad, good)
    return re.sub(r"[^\w\sÁ-ú'-]", " ", s)


def demojibake(s):
    if not s:
        return s
    if any(p in s for p in ("Ã", "Â", "A�", "�")):
        try:
            fixed = s.encode("latin1").decode("utf-8")
            if "�" not in fixed and "Ã" not in fixed and "A�" not in fixed:
                return fixed
        except Exception:
            pass
    return s


# ---------------------------------------------------------------------------
# Entidades de domínio — REMOVIDAS em 2026-09-30
# ---------------------------------------------------------------------------
#
# `Family`, `GenealogyGraph` e `DNAGroup` viviam aqui e sairam por decisao do
# usuario (_reversa_sdd/questions.md#pergunta-3); nenhuma das tres era instanciada
# em producao:
#
#   - `Family`         aparecia apenas na propria definicao e na anotacao de
#                      `GenealogyGraph.register_family`; o fluxo real guarda os
#                      registros `FAM` do ged4py no dicionario de familias.
#   - `GenealogyGraph` nao era instanciada, e o docstring mentia: o grafo real e um
#                      `nx.Graph` nao direcionado sobre pessoas e familias, nao o
#                      `nx.MultiGraph` que ele afirmava.
#   - `DNAGroup`       nao era instanciada; `dna_analysis` monta `dict` simples.
#
# Ver `_reversa_sdd/upload-gedcom/design.md` para o registro completo.

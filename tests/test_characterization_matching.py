"""Caracterizacao do matching de DNA.

Congela as decisoes e as saidas atuais do cruzamento GEDCOM x CSV para as fixtures
sinteticas. Caracterizacao no sentido de Feathers: fixa o comportamento atual como
ele esta, INCLUSIVE o que pareca defeito, para que qualquer mudanca apareca como
falha de teste.

Origem: rede de seguranca da transformacao OPP-20260929-AU76, promovida a teste
permanente em 2026-09-29. Isto e teste de REGRESSAO, nao prova de paridade com o
legado: o oraculo diferencial nao existe mais na arvore.

Achado caracterizado, deliberadamente sem correcao: um nome cujo unico token
nao-generico e o sobrenome, como "Joao Silva", tem o sobrenome interpretado como
prenome por `split_name_pt`, e o pool de candidatos fica vazio. Ver a tabela de
decisoes. Corrigir isso mudaria comportamento, logo e feature, nao refactor.

## Mudanca deliberada de 2026-10 (regra final da analise)

A forma do payload do fluxo mudou por ordem explicita: o campo `relationships`
(cM -> "relacionamento provavel") foi removido do fluxo e da interface, e
entraram `documentary`, `genetic_evidence`, `hypotheses` e `comparison`. Os
valores congelados abaixo foram atualizados para o novo contrato; caminho,
descartados e mensagem continuam iguais. Este e o registro de que a quebra foi
intencional, e nao um efeito colateral.
"""
import inspect
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tests.fixtures.sample_dna import (
    DNA_CSV_DUPLICATED,
    DNA_CSV_NO_INTERSECTION,
    DNA_CSV_UTF8,
    DNA_GED,
)

from parsers import gedcom_parser
from core import gedcom_state
from core.dna_analysis import build_ged_indexes, dna_analysis, match_candidates


@pytest.fixture(scope="module")
def tree():
    """Carrega o GEDCOM sintetico de DNA uma unica vez para toda a suite."""
    fd, path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_GED)
        gedcom_parser.load_gedcom_and_build_graph(path)
    finally:
        os.remove(path)
    return gedcom_state


def _csv(texto):
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(texto)
    return path


def _decidir(nome, cm):
    """Chama match_candidates adaptando a aridade, para o teste falar de decisao."""
    indices = build_ged_indexes()
    if len(inspect.signature(match_candidates).parameters) >= 5:
        return match_candidates(nome, cm, indices[0], indices[1], indices[-1])
    return match_candidates(nome, cm, indices[0], indices[1])


# --- saida completa do fluxo, por fixture -------------------------------------
#
# ATUALIZADO pela regra final da analise (GEDCOM / DNA / confronto separados).
# O que mudou, deliberadamente, e a FORMA do payload: `relationships` (cM ->
# "relacionamento provável") deixou de existir e entrou `documentary` (GEDCOM),
# `genetic_evidence` (CSV), `hypotheses` (Shared cM 4.0) e `comparison`. O
# caminho, os descartados e a mensagem continuam congelados.
#
# Ana Silva Souza e irma de Carlos Silva Souza na fixture, e a fixture declara
# 200 cM para ela: irmaos completos têm faixa publicada de 1613–3488 cM, e
# nenhuma relacao que admite 200 cM alcança essa faixa. Dai CONFLITANTE.

PIPELINE = {
    "utf8": (
        DNA_CSV_UTF8,
        {"match_name": "Ana Silva Souza", "cm": 200,
         "text_path": "Carlos Silva Souza → Joaquim Silva → Ana Silva Souza",
         "csv_name": "Ana Silva Souza"},
        "found",
        "CONFLITANTE",
        [],
        "1 conexões encontradas. 0 descartadas.",
    ),
    "duplicado": (
        DNA_CSV_DUPLICATED,
        {"match_name": "Ana Silva Souza", "cm": 537,
         "text_path": "Carlos Silva Souza → Joaquim Silva → Ana Silva Souza",
         "csv_name": "Ana Silva Souza"},
        "found",
        "CONFLITANTE",
        [],
        "1 conexões encontradas. 0 descartadas.",
    ),
    "sem-intersecao": (
        DNA_CSV_NO_INTERSECTION,
        None,
        None,
        None,
        [{"csv_name": "Zzz Ninguem dos Santos",
          "kit": None,
          "cm": 150,
          "motivo": "sem candidatos por sobrenome (abreviação/corrupção?)"}],
        "0 conexões encontradas. 1 descartadas.",
    ),
}


@pytest.mark.parametrize("caso", sorted(PIPELINE))
def test_pipeline_caracterizado(tree, caso):
    """Resultados, descartados e mensagem continuam exatamente iguais."""
    csv, esperado_res, esperado_doc, esperado_comparacao, esperado_skipped, esperado_msg = PIPELINE[caso]
    path = _csv(csv)
    try:
        res, skipped, msg = dna_analysis(path, "Carlos Silva Souza")
    finally:
        os.remove(path)

    assert msg == esperado_msg
    if esperado_res:
        campos = list(esperado_res)
        assert [{k: r[k] for k in campos} for r in res] == [esperado_res]
        assert res[0]["documentary"]["label"] == "Irmãos"
        assert res[0]["documentary"]["status"] == esperado_doc
        assert res[0]["comparison"]["status"] == esperado_comparacao
        assert res[0]["hypotheses"][0]["possible_relationships"]
    else:
        assert res == []
    assert skipped == esperado_skipped


# --- decisoes do matching, caso a caso ----------------------------------------

DECISOES = [
    ("Ana Silva Souza", ["@I13@"], None),
    ("Ana Silva Souza Ferreira", ["@I13@"], None),
    ("Carlos Silva Souza", ["@I12@"], None),
    ("Marta Souza", ["@I11@"], None),
    ("Joaquim Silva", ["@I10@"], None),
    ("Lone Ranger", ["@I90@"], None),
    ("ana silva souza", ["@I13@"], None),
    ("Joao Silva", [], "sem candidatos por sobrenome (abreviação/corrupção?)"),
    ("Ana Souza", [], "sem candidatos por sobrenome (abreviação/corrupção?)"),
    ("Ana Silva", [], "sem candidatos por sobrenome (abreviação/corrupção?)"),
    ("Silva", [], "sem candidatos por sobrenome (abreviação/corrupção?)"),
    ("Souza", [], "sem candidatos por sobrenome (abreviação/corrupção?)"),
    ("Maria Oliveira", [], "sem candidatos por sobrenome (abreviação/corrupção?)"),
    ("Zzz Ninguem dos Santos", [], "sem candidatos por sobrenome (abreviação/corrupção?)"),
]


@pytest.mark.parametrize("nome,pids,motivo", DECISOES)
def test_decisao_de_matching(tree, nome, pids, motivo):
    """A decisao continua a mesma, aceitando ou descartando o mesmo nome."""
    assert _decidir(nome, 200) == (pids, motivo)


@pytest.mark.parametrize("cm", [0, -1, 150, 3720])
def test_limiar_de_cm_nao_muda_a_decisao(tree, cm):
    """O nome valido e aceito independentemente do cM, como hoje."""
    assert _decidir("Ana Silva Souza", cm) == (["@I13@"], None)

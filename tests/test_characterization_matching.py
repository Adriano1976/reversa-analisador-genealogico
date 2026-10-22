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

**O ACHADO CONTINUA SEM CORRECAO; o MOTIVO deixou de acusa-lo (adendo `024`).** O
comportamento congelado abaixo e' exatamente o mesmo — pool vazio descarta o nome, e
nenhuma decisao mudou. O que mudou e' so' o TEXTO: o motivo unico "sem candidatos por
sobrenome (abreviação/corrupção?)" acusava o ARQUIVO do operador, e passou a dizer qual
das tres causas aconteceu — sobrenome lido como prenome, nome unico, ou sobrenome que
nao existe no GEDCOM.

A escala foi medida no arquivo real do operador (13.716 pessoas, 454 nomes distintos):
dos **94** grupos com pool vazio, **87** nao tinham sobrenome nenhum para procurar.
`Marcos Antonio de Melo` nao e' abreviacao nem corrupcao — "marcos" e "antonio" estao os
dois em `GENERIC_GIVENS`, entao "melo" virou o prenome. Dos 87, **19** tem mais de um
token (havia sobrenome de verdade e ele foi comido) e 68 sao mononimos legitimos. Este
segundo caso — dois genericos seguidos, com o sobrenome no meio de um nome completo —
NAO estava descrito aqui: o achado original falava do nome cujo UNICO token nao-generico
e' o sobrenome.

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
from core.dna_analysis import build_ged_indexes, dna_analysis, match_candidates
from tests.fixtures.helpers import arvore_de as _arvore_de
from tests.fixtures.helpers import deps as _deps
from tests.fixtures.arvore_atual import atual, guardar


@pytest.fixture(scope="module")
def tree():
    """Carrega o GEDCOM sintetico de DNA uma unica vez para toda a suite.

    Le a ARVORE devolvida pelo parse (feature 005), e a registra em `atual()`
    porque `test_pipeline_caracterizado` a alcanca por la, sem receber a fixture.
    """
    fd, path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_GED)
        return guardar(gedcom_parser.carregar_arvore(path))
    finally:
        os.remove(path)


def _csv(texto):
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(texto)
    return path


def _decidir(arvore, nome, cm):
    """Chama match_candidates com a arvore, na assinatura de `T013`.

    O adaptador de aridade que existia aqui saiu: `match_candidates` passou a
    receber `arvore` como primeiro parametro (feature 005, `T013`), e a funcao
    nao consulta a arvore nesta decisao — ela usa os indices. Isso e propriedade
    a preservar, e nao detalhe: e o que permite testar a regra de aceitacao com
    um pool montado a mao.
    """
    indices = build_ged_indexes(arvore)
    return match_candidates(arvore, nome, cm, indices[0], indices[1], indices[-1])


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
        # Feature 039/E002: o descarte de cM alto sem correspondencia passou a ser
        # TAMBEM um cartao na lista de resultados. A forma congelada aqui e' a do
        # cartao; a decisao de matching continua a mesma, e o item continua na lista
        # completa de descartes.
        {"match_name": "Zzz Ninguem dos Santos", "cm": 150,
         "text_path": "", "csv_name": "Zzz Ninguem dos Santos",
         "sem_correspondencia": True},
        "not_found",
        "INCONCLUSIVO",
        [{"csv_name": "Zzz Ninguem dos Santos",
          "kit": None,
          "cm": 150,
          "motivo": "nenhum sobrenome do nome existe no GEDCOM",
          # Feature 038: a causa e o detalhe tecnico passaram a viajar ao lado do texto.
          # O MOTIVO nao mudou — e' o que este contrato congela desde a 034. Recusa por
          # sobrenome nao mede nada, entao o detalhe nasce vazio, nunca com zero.
          "motivo_codigo": "sem_sobrenome_no_gedcom",
          "motivo_detalhe": "",
          # Feature 034: o descarte passou a levar os candidatos avaliados. Este nome
          # nao tem sobrenome que exista no GEDCOM, entao a lista e' vazia — o unico
          # delta da 034 neste contrato e' a chave nova, nunca o motivo.
          "candidatos": [],
          # Feature 039: o MRCA do kit viaja ao lado do descarte. A fixture nao traz a
          # coluna, entao o valor e' None — e a decisao continua a mesma.
          "mrca_generations": None}],
        "1 conexões encontradas. 1 descartadas.",
    ),
}


@pytest.mark.parametrize("caso", sorted(PIPELINE))
def test_pipeline_caracterizado(tree, caso):
    """Resultados, descartados e mensagem continuam exatamente iguais."""
    csv, esperado_res, esperado_doc, esperado_comparacao, esperado_skipped, esperado_msg = PIPELINE[caso]
    path = _csv(csv)
    try:
        res, skipped, msg = dna_analysis(path, "Carlos Silva Souza", _deps(), atual())
    finally:
        os.remove(path)

    assert msg == esperado_msg
    if esperado_res:
        campos = list(esperado_res)
        assert [{k: r[k] for k in campos} for r in res] == [esperado_res]
        if esperado_res.get("sem_correspondencia"):
            assert res[0]["documentary"]["label"] == "Parentesco documental não encontrado"
        else:
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
    ("Joao Silva", [], "o sobrenome foi lido como prenome (nome sem sobrenome isolável)"),
    ("Ana Souza", [], "o sobrenome foi lido como prenome (nome sem sobrenome isolável)"),
    ("Ana Silva", [], "o sobrenome foi lido como prenome (nome sem sobrenome isolável)"),
    ("Silva", [], "o nome não tem sobrenome (nome único)"),
    ("Souza", [], "o nome não tem sobrenome (nome único)"),
    ("Maria Oliveira", [], "o sobrenome foi lido como prenome (nome sem sobrenome isolável)"),
    ("Zzz Ninguem dos Santos", [], "nenhum sobrenome do nome existe no GEDCOM"),
    ("A CF", [], "sobrenome curto demais para buscar (inicial ou abreviação)"),
    ("*Roger S", [], "sobrenome curto demais para buscar (inicial ou abreviação)"),
    # Os dois caminhos que empurram o sobrenome para a casa do prenome — o segundo
    # estava fora da descricao original do achado caracterizado (adendo 024).
    ("Marcos Antonio de Melo", [], "o sobrenome foi lido como prenome (nome sem sobrenome isolável)"),
    ("*Coutinho Neto", [], "o sobrenome foi lido como prenome (nome sem sobrenome isolável)"),
    # E o que NAO perdeu sobrenome nenhum: um token so'.
    ("PAULO", [], "o nome não tem sobrenome (nome único)"),
]


@pytest.mark.parametrize("nome,pids,motivo", DECISOES)
def test_decisao_de_matching(tree, nome, pids, motivo):
    """A decisao continua a mesma, aceitando ou descartando o mesmo nome."""
    assert _decidir(tree, nome, 200) == (pids, motivo)


@pytest.mark.parametrize("cm", [0, -1, 150, 3720])
def test_limiar_de_cm_nao_muda_a_decisao(tree, cm):
    """O nome valido e aceito independentemente do cM, como hoje."""
    assert _decidir(tree, "Ana Silva Souza", cm) == (["@I13@"], None)


# --- desempate deterministico -------------------------------------------------
#
# DECISAO DO USUARIO, 2026-09-30, retomada e executada em 2026-10-05.
#
# O legado resolvia empate exato nos tres criterios pela ORDEM DE ITERACAO do
# `set` de candidatos (`pool`), que muda a cada processo por causa do
# PYTHONHASHSEED. O vencedor, portanto, variava entre execucoes identicas - e a
# escolha propaga para o caminho documental, o rotulo, a janela de cM e o estado
# do confronto.
#
# O criterio final decidido foi o MENOR `xref_id` entre os empatados.
#
# Este teste NAO usa subprocesso nem semente de hash: monta dois candidatos
# IDENTICOS, que empatam nos tres criterios por construcao, e afirma o vencedor
# com o pool inserido nas DUAS ordens. E prova mais direta do que comparar duas
# execucoes - e nao depende de o empate acontecer por acaso no dado real.


def _feature(norm, givens, surnames, tokens):
    """Atributos normalizados no mesmo formato que `build_ged_indexes` produz."""
    return {
        "norm": norm,
        "given_tokens": list(givens),
        "surnames": set(surnames),
        "surnames_list": list(surnames),
        "tokens": set(tokens),
    }


def _pool_empatado(ordem):
    """Indices sinteticos com dois candidatos identicos, na ordem pedida.

    O nome do CSV e "Mariana Silva Souza" de proposito: `split_name_pt` escolhe
    como prenome o primeiro token que nao seja stop word nem GENERICO. Com o
    prenome "Ana" (que esta em GENERIC_GIVENS), o prenome escolhido passa a ser
    "silva" e o cM do pool nao e aceito. "Mariana" nao esta na lista, entao a
    decomposicao sai como esperado - o mesmo cuidado que o teste de decisoes
    documenta para "Joao Silva".
    """
    surnames = ("silva", "souza")
    tokens = ("mariana", "silva", "souza")
    features = {pid: _feature("mariana silva souza", ["mariana"], surnames, tokens)
                for pid in ("@I1@", "@I2@")}
    surname_index = {"silva": list(ordem), "souza": list(ordem)}
    return {}, surname_index, features


@pytest.mark.parametrize("ordem", [("@I1@", "@I2@"), ("@I2@", "@I1@")])
def test_desempate_escolhe_o_menor_xref_id(ordem):
    """Empate exato nos tres criterios e resolvido pelo menor `xref_id`."""
    ged_index, surname_index, features = _pool_empatado(ordem)
    vencedores, motivo = match_candidates(None, "Mariana Silva Souza", 200, ged_index, surname_index, features)
    assert vencedores == ["@I1@"], (
        "o menor xref_id deve vencer o empate, qualquer que seja a ordem de "
        "insercao dos candidatos no pool"
    )
    assert motivo is None


def test_desempate_nao_depende_da_ordem_do_pool():
    """A decisao e a mesma com o pool inserido em ordem direta e inversa."""
    resultados = []
    for ordem in (("@I1@", "@I2@"), ("@I2@", "@I1@")):
        ged_index, surname_index, features = _pool_empatado(ordem)
        resultados.append(match_candidates(None, "Mariana Silva Souza", 200, ged_index, surname_index, features))
    assert resultados[0] == resultados[1]

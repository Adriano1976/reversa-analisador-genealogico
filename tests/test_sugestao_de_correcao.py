"""Testes do contrato de `arvore_sugerida`.

O resultado da validação é montado à mão, para que cada cenário seja determinístico e
não dependa da tabela de cM: o que se testa aqui é a decisão do núcleo (status, hiato,
junção, injeção, avisos), não a estimativa da feature `028`.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.cirurgia_do_grafo import (  # noqa: E402
    AFINIDADE_NAO_INJETAVEL,
    DOIS_LADOS_ACUSADOS,
    HIATO_NAO_POSITIVO,
    LADO_DOADOR,
    LADO_MATCH,
    NATUREZA,
    SEM_CAMINHO_DOCUMENTAL,
    SEM_MRCA_ESTIMADO,
    SUGESTAO_INDISPONIVEL,
    SUGESTAO_INSUFICIENTE,
    arvore_sugerida,
)
from core.documentary_relationship import documentary_relationship  # noqa: E402
from core.validator import ERRO_CRONICO, INCONCLUSIVO, VALIDADO  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from tests.fixtures.arvore_para_cirurgia import (  # noqa: E402
    GED_DOIS_LADOS,
    GED_SALTO_IMPOSSIVEL,
)


def _arvore(tmp_path, ged=GED_SALTO_IMPOSSIVEL):
    caminho = tmp_path / "arvore.ged"
    caminho.write_text(ged, encoding="utf-8")
    return carregar_arvore(str(caminho))


def _resultado(status=ERRO_CRONICO, geracoes=6.0, intervalo=None):
    estimado = None
    if geracoes is not None:
        estimado = {"ano": 1700, "ano_min": 1650, "ano_max": 1750,
                    "geracoes": geracoes, "metodo": "scp40:mediana"}
    return {"status": status, "mrca_estimado": estimado, "codigos": [],
            "geracoes_documentais": {"doador": 2, "match": 2, "total": 4},
            "comparacao_existente": None, "intervalo_de_geracao": intervalo}


def _documental(arvore, a_id="@I1@", b_id="@I4@"):
    return documentary_relationship(arvore, a_id, b_id)


def _codigos(sugestao):
    return [item["codigo"] for item in sugestao["avisos"]]


# ---------------------------------------------------------------------------
# Status que não geram sugestão
# ---------------------------------------------------------------------------

def test_validado_nao_gera_sugestao(tmp_path):
    arvore = _arvore(tmp_path)
    sugestao = arvore_sugerida(arvore, _documental(arvore), _resultado(VALIDADO))

    assert sugestao["grafo"] is None
    assert sugestao["natureza"] == NATUREZA
    assert sugestao["status_origem"] == VALIDADO
    assert _codigos(sugestao) == [SUGESTAO_INDISPONIVEL]
    assert sugestao["geracoes_virtuais"] == []


def test_inconclusivo_nao_gera_sugestao(tmp_path):
    arvore = _arvore(tmp_path)
    sugestao = arvore_sugerida(arvore, _documental(arvore), _resultado(INCONCLUSIVO))

    assert sugestao["grafo"] is None
    assert _codigos(sugestao) == [SUGESTAO_INDISPONIVEL]


# ---------------------------------------------------------------------------
# Contrato da sugestão
# ---------------------------------------------------------------------------

def test_erro_gera_sugestao_com_contrato_completo(tmp_path):
    arvore = _arvore(tmp_path)
    sugestao = arvore_sugerida(arvore, _documental(arvore), _resultado())

    assert sugestao["natureza"] == NATUREZA
    assert sugestao["status_origem"] == ERRO_CRONICO
    assert sugestao["grafo"] is not None
    assert sugestao["juncao"]["familia_id"] == "@F2@"
    assert sugestao["ramo_base"]["intacto"] is True
    assert sugestao["ramo_base"]["ids"] == ["@I1@", "@F1@", "@I2@", "@F2@", "@I10@"]
    assert sugestao["hiato"] == {"calculado": 4, "aplicado": 4,
                                 "por_lado": {LADO_DOADOR: 4, LADO_MATCH: 0}}
    assert [g["label"] for g in sugestao["geracoes_virtuais"]] == [
        "Geração 1", "Geração 2", "Geração 3", "Geração 4"]
    assert len(sugestao["geracoes_virtuais"]) == sugestao["hiato"]["aplicado"]
    assert sugestao["arestas_removidas"] == [("@F2@", "@I10@")]
    assert sugestao["avisos"] == []
    assert sugestao["doador"]["id"] == "@I1@"
    assert sugestao["ancestral"]["ano"] == 1650


def test_o_grafo_original_nao_e_mutado(tmp_path):
    arvore = _arvore(tmp_path)
    antes = (sorted(arvore[2].nodes()), sorted(arvore[2].edges()))

    arvore_sugerida(arvore, _documental(arvore), _resultado())

    depois = (sorted(arvore[2].nodes()), sorted(arvore[2].edges()))
    assert antes == depois
    assert all(arvore[2].nodes[no]["type"] != "virtual" for no in arvore[2].nodes())


def test_ids_e_ordem_sao_deterministicos(tmp_path):
    arvore = _arvore(tmp_path)
    documental = _documental(arvore)
    resultado = _resultado()

    primeira = arvore_sugerida(arvore, documental, resultado)
    segunda = arvore_sugerida(arvore, documental, resultado)

    assert primeira["nos_adicionados"] == segunda["nos_adicionados"]
    assert [g["id"] for g in primeira["geracoes_virtuais"]] == [
        g["id"] for g in segunda["geracoes_virtuais"]]
    assert sorted(primeira["grafo"].nodes()) == sorted(segunda["grafo"].nodes())
    assert primeira["geracoes_virtuais"][0]["id"] == "VIRTUAL:@I1@:@I10@:doador:1"


# ---------------------------------------------------------------------------
# Hiato
# ---------------------------------------------------------------------------

def test_hiato_arredonda_meio_para_cima(tmp_path):
    arvore = _arvore(tmp_path)
    # 2.5 gerações estimadas com a_up=2: floor(2.5 + 0.5) = 3, então hiato = 1.
    sugestao = arvore_sugerida(arvore, _documental(arvore), _resultado(geracoes=2.5))

    assert sugestao["hiato"]["calculado"] == 1
    assert len(sugestao["geracoes_virtuais"]) == 1


def test_hiato_zero_nao_injeta(tmp_path):
    arvore = _arvore(tmp_path)
    sugestao = arvore_sugerida(arvore, _documental(arvore), _resultado(geracoes=2.0))

    assert sugestao["grafo"] is None
    assert _codigos(sugestao) == [HIATO_NAO_POSITIVO]
    assert sugestao["hiato"]["aplicado"] == 0


def test_hiato_negativo_nao_injeta(tmp_path):
    arvore = _arvore(tmp_path)
    sugestao = arvore_sugerida(arvore, _documental(arvore), _resultado(geracoes=1.0))

    assert sugestao["grafo"] is None
    assert _codigos(sugestao) == [HIATO_NAO_POSITIVO]


def test_sem_mrca_estimado(tmp_path):
    arvore = _arvore(tmp_path)
    sugestao = arvore_sugerida(arvore, _documental(arvore), _resultado(geracoes=None))

    assert sugestao["grafo"] is None
    assert _codigos(sugestao) == [SEM_MRCA_ESTIMADO]


def test_sugestao_insuficiente_quando_a_janela_nao_fecha(tmp_path):
    arvore = _arvore(tmp_path)
    # 3 gerações estimadas e a_up=2 → hiato 1; com 3 gerações entre 1650 e 1985 sobram
    # 111,7 anos por geração, fora de 12–70. A sugestão sai, mas declarada insuficiente.
    sugestao = arvore_sugerida(arvore, _documental(arvore), _resultado(geracoes=3.0))

    assert sugestao["grafo"] is not None
    assert sugestao["hiato"]["aplicado"] == 1
    assert SUGESTAO_INSUFICIENTE in _codigos(sugestao)


# ---------------------------------------------------------------------------
# Recusas
# ---------------------------------------------------------------------------

def test_afinidade_nao_e_injetavel(tmp_path):
    arvore = _arvore(tmp_path)
    documental = dict(_documental(arvore))
    documental["status"] = "affinity"

    sugestao = arvore_sugerida(arvore, documental, _resultado())

    assert sugestao["grafo"] is None
    assert _codigos(sugestao) == [AFINIDADE_NAO_INJETAVEL]


def test_sem_caminho_documental(tmp_path):
    arvore = _arvore(tmp_path)
    documental = {"status": "not_found", "path": {"ids": []}, "common_ancestor": None,
                  "degrees": {"a_up": 0, "b_up": 0}, "evidence": []}

    sugestao = arvore_sugerida(arvore, documental, _resultado())

    assert sugestao["grafo"] is None
    assert _codigos(sugestao) == [SEM_CAMINHO_DOCUMENTAL]


# ---------------------------------------------------------------------------
# Dois lados
# ---------------------------------------------------------------------------

def test_dois_lados_com_juncoes_distintas_dividem_proporcionalmente(tmp_path):
    arvore = _arvore(tmp_path, GED_DOIS_LADOS)
    documental = _documental(arvore, "@I1@", "@I13@")

    sugestao = arvore_sugerida(arvore, documental, _resultado())

    assert sugestao["grafo"] is not None
    assert len(sugestao["juncoes"]) == 2
    assert sugestao["hiato"]["calculado"] == 4
    assert sugestao["hiato"]["por_lado"] == {LADO_DOADOR: 2, LADO_MATCH: 2}
    assert len(sugestao["geracoes_virtuais"]) == 4
    assert DOIS_LADOS_ACUSADOS in _codigos(sugestao)
    assert len(sugestao["arestas_removidas"]) == 2


def test_dois_lados_com_a_mesma_juncao_usam_uma_cadeia(tmp_path):
    arvore = _arvore(tmp_path)
    documental = _documental(arvore)
    # Força o salto do lado do match a ficar implausível também.
    documental["evidence"][2]["plausible"] = False

    sugestao = arvore_sugerida(arvore, documental, _resultado())

    assert len(sugestao["juncoes"]) == 1
    assert sugestao["hiato"]["por_lado"] == {LADO_DOADOR: 4, LADO_MATCH: 0}
    assert len(sugestao["geracoes_virtuais"]) == 4
    assert DOIS_LADOS_ACUSADOS in _codigos(sugestao)

"""Testes do núcleo puro de validação temporal (`core.validator`).

Nenhum dado real: as comparações são montadas à mão, com nomes e datas
sintéticos. Os testes cobrem os três status, os códigos críticos, os casos de
borda e a precedência entre kits.
"""
from __future__ import annotations

import copy
import os
import sys
from dataclasses import replace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.validator import (  # noqa: E402
    ERRO_CRONICO,
    INCONCLUSIVO,
    VALIDADO,
    ComparacaoParaValidar,
    agregar_resultados,
    estimar_mrca,
    validar_comparacao,
)


def _hop(pai: str, filho: str, ano_pai: int, ano_filho: int, plausivel=True) -> dict:
    return {
        "parent_id": pai,
        "child_id": filho,
        "parent_birth": str(ano_pai),
        "child_birth": str(ano_filho),
        "age_at_birth": ano_filho - ano_pai,
        "plausible": plausivel,
    }


def _documental() -> dict:
    return {
        "status": "found",
        "label": "Primos de 1º grau",
        "relationship_key": "1C",
        "meioses": 4,
        "degrees": {"a_up": 2, "b_up": 2},
        "common_ancestor": {"id": "@I10@", "name": "Ancestral Sintetico", "birth": "1900"},
        "path": {
            "ids": ["@I1@", "@I2@", "@I10@", "@I5@", "@I4@"],
            "names": ["Doador", "Pai", "Ancestral", "Tia", "Primo"],
        },
        "evidence": [
            _hop("@I2@", "@I1@", 1945, 1970),
            _hop("@I10@", "@I2@", 1900, 1945),
            _hop("@I10@", "@I5@", 1900, 1925),
            _hop("@I5@", "@I4@", 1925, 1950),
        ],
        "ambiguous_identity": False,
        "homonyms": {},
    }


def _comparacao(**overrides) -> ComparacaoParaValidar:
    dados = {
        "doador": {"id": "@I1@", "nome": "Doador Sintetico", "nascimento": "1970"},
        "match": {"id": "@I4@", "nome": "Primo Sintetico", "nascimento": "1950"},
        "documental": _documental(),
        "kit": {
            "kit": "AB1234567",
            "total_cm": 800.0,
            "largest_segment_cm": 80.0,
            "mrca_generations": None,
        },
        "ano_referencia": 2026,
        "intervalo_de_geracao": 25.0,
        "comparacao_existente": {"status": "COMPATIVEL"},
    }
    dados.update(overrides)
    return ComparacaoParaValidar(**dados)


def _codigos(resultado: dict) -> set[str]:
    return {item["codigo"] for item in resultado["codigos"]}


# ---------------------------------------------------------------------------
# Estimativa do MRCA
# ---------------------------------------------------------------------------


def test_estimar_mrca_usa_mrca_do_kit():
    estimativa = estimar_mrca(800, 1970, mrca_do_kit=2.0, intervalo_de_geracao=25.0)

    assert estimativa is not None
    assert estimativa.ano == 1920
    assert estimativa.geracoes == 2.0
    assert estimativa.metodo == "mrca_do_kit"


def test_estimar_mrca_usa_mediana_do_scp40():
    estimativa = estimar_mrca(
        500, 1970,
        relacoes=[{"key": "1C"}, {"key": "1C1R"}],
        intervalo_de_geracao=25.0,
    )

    assert estimativa is not None
    assert estimativa.metodo == "scp40:mediana"
    # 1C tem 4 meioses totais e 1C1R tem 5; a mediana é 4,5, então 2,25 gerações.
    assert estimativa.geracoes == pytest.approx(2.25)
    assert estimativa.ano == 1914


def test_estimar_mrca_usa_intervalo_de_geracao_informado():
    estimativa = estimar_mrca(
        1000, 1970,
        relacoes=[{"key": "1C"}],
        intervalo_de_geracao=30.0,
    )

    assert estimativa is not None
    assert estimativa.metodo == "scp40:mediana"
    assert estimativa.geracoes == 2.0
    assert estimativa.ano == 1910


def test_estimar_mrca_sem_cm_devolve_none():
    assert estimar_mrca(None, 1970) is None
    assert estimar_mrca(0, 1970) is None


def test_estimar_mrca_sem_nascimento_do_doador_devolve_none():
    assert estimar_mrca(800, None) is None


def test_estimar_mrca_devolve_janela_coerente():
    estimativa = estimar_mrca(800, 1970, intervalo_de_geracao=25.0)

    assert estimativa is not None
    assert estimativa.ano_min <= estimativa.ano <= estimativa.ano_max


# ---------------------------------------------------------------------------
# Status e códigos
# ---------------------------------------------------------------------------


def test_comparacao_valida():
    resultado = validar_comparacao(_comparacao())

    assert resultado["status"] == VALIDADO
    assert resultado["codigos"] == []
    assert resultado["mrca_estimado"] is not None
    assert resultado["geracoes_documentais"] == {"doador": 2, "match": 2, "total": 4}


def test_doador_vivo_ligado_a_ancestral_do_seculo_xvii():
    documental = copy.deepcopy(_documental())
    documental["common_ancestor"]["birth"] = "1650"
    documental["evidence"] = [
        _hop("@I2@", "@I1@", 1960, 1985),
        _hop("@I10@", "@I2@", 1650, 1960, plausivel=False),
        _hop("@I10@", "@I5@", 1650, 1925, plausivel=False),
        _hop("@I5@", "@I4@", 1925, 1950),
    ]
    resultado = validar_comparacao(_comparacao(
        doador={"id": "@I1@", "nome": "Doador", "nascimento": "1985"},
        documental=documental,
    ))

    assert resultado["status"] == ERRO_CRONICO
    assert "PROFUNDIDADE_TEMPORAL_INCOMPATIVEL" in _codigos(resultado)
    assert "DOADOR_VIVO_EM_LINHA_INCOMPATIVEL" in _codigos(resultado)
    assert "GENITOR_FORA_DA_JANELA_BIOLOGICA" in _codigos(resultado)


def test_salto_pai_filho_de_11_anos_e_erro():
    documental = copy.deepcopy(_documental())
    documental["evidence"][0] = _hop("@I2@", "@I1@", 1959, 1970, plausivel=False)
    resultado = validar_comparacao(_comparacao(documental=documental))

    assert resultado["status"] == ERRO_CRONICO
    assert "GENITOR_FORA_DA_JANELA_BIOLOGICA" in _codigos(resultado)


def test_mrca_posterior_ao_descendente_e_erro():
    documental = copy.deepcopy(_documental())
    documental["common_ancestor"]["birth"] = "1975"
    resultado = validar_comparacao(_comparacao(documental=documental))

    assert resultado["status"] == ERRO_CRONICO
    assert "MRCA_POSTERIOR_A_DESCENDENTE" in _codigos(resultado)


def test_cm_incompativel_com_profundidade_sem_comparacao_existente():
    documental = copy.deepcopy(_documental())
    documental["degrees"] = {"a_up": 1, "b_up": 1}
    documental["meioses"] = 2
    documental["common_ancestor"]["birth"] = "1910"
    resultado = validar_comparacao(_comparacao(
        documental=documental,
        kit={"kit": "AB1234567", "total_cm": 25.0, "largest_segment_cm": 10.0,
             "mrca_generations": None},
        comparacao_existente=None,
    ))

    assert resultado["status"] == ERRO_CRONICO
    assert "CM_INCOMPATIVEL_COM_PROFUNDIDADE" in _codigos(resultado)


def test_conflito_do_confronto_existente_e_erro():
    resultado = validar_comparacao(_comparacao(
        comparacao_existente={"status": "CONFLITANTE"},
    ))

    assert resultado["status"] == ERRO_CRONICO
    assert "CONFLITO_CM_DOCUMENTAL" in _codigos(resultado)


def test_mrca_documentado_fora_da_janela_e_erro():
    documental = copy.deepcopy(_documental())
    documental["common_ancestor"]["birth"] = "1800"
    documental["degrees"] = {"a_up": 3, "b_up": 3}
    documental["meioses"] = 6
    resultado = validar_comparacao(_comparacao(
        documental=documental,
        kit={"kit": "AB1234567", "total_cm": 800.0, "largest_segment_cm": 80.0,
             "mrca_generations": 2.0},
    ))

    assert resultado["status"] == ERRO_CRONICO
    assert "MRCA_DOCUMENTADO_FORA_DA_JANELA" in _codigos(resultado)


def test_mrca_estimado_fora_da_janela_e_atencao():
    documental = copy.deepcopy(_documental())
    documental["common_ancestor"]["birth"] = "ABT 1800"
    documental["degrees"] = {"a_up": 3, "b_up": 3}
    documental["meioses"] = 6
    resultado = validar_comparacao(_comparacao(
        documental=documental,
        kit={"kit": "AB1234567", "total_cm": 800.0, "largest_segment_cm": 80.0,
             "mrca_generations": 2.0},
    ))

    assert resultado["status"] == INCONCLUSIVO
    assert "MRCA_DOCUMENTADO_FORA_DA_JANELA_ESTIMADO" in _codigos(resultado)
    assert "DATA_ESTIMADA" in _codigos(resultado)


def test_data_ausente_e_inconclusivo_nao_erro():
    resultado = validar_comparacao(_comparacao(
        match={"id": "@I4@", "nome": "Primo", "nascimento": None},
    ))

    assert resultado["status"] == INCONCLUSIVO
    assert "SEM_DATA_DE_NASCIMENTO" in _codigos(resultado)
    assert not any(item["severidade"] == "critico" for item in resultado["codigos"])


def test_sem_cobertura_de_cm_e_inconclusivo():
    resultado = validar_comparacao(_comparacao(
        kit={"kit": "AB1234567", "total_cm": 4000.0, "largest_segment_cm": 80.0,
             "mrca_generations": None},
        comparacao_existente=None,
    ))

    assert resultado["status"] == INCONCLUSIVO
    assert "SEM_COBERTURA_DE_CM" in _codigos(resultado)


def test_sem_caminho_documental_e_inconclusivo():
    documental = {
        "status": "not_found",
        "label": "Parentesco documental não encontrado",
        "meioses": None,
        "degrees": {"a_up": 0, "b_up": 0},
        "common_ancestor": None,
        "path": {"ids": [], "names": []},
        "evidence": [],
        "ambiguous_identity": False,
    }
    resultado = validar_comparacao(_comparacao(documental=documental))

    assert resultado["status"] == INCONCLUSIVO
    assert "SEM_CAMINHO_DOCUMENTAL" in _codigos(resultado)


def test_afinidade_nao_e_linhagem_e_inconclusiva():
    documental = copy.deepcopy(_documental())
    documental["status"] = "affinity"
    resultado = validar_comparacao(_comparacao(documental=documental))

    assert resultado["status"] == INCONCLUSIVO
    assert "AFINIDADE_NAO_BIOLOGICA" in _codigos(resultado)


def test_identidade_ambigua_e_inconclusiva():
    documental = copy.deepcopy(_documental())
    documental["ambiguous_identity"] = True
    resultado = validar_comparacao(_comparacao(documental=documental))

    assert resultado["status"] == INCONCLUSIVO
    assert "IDENTIDADE_AMBIGUA" in _codigos(resultado)


def test_observacao_possivel_nao_valida():
    resultado = validar_comparacao(_comparacao(
        comparacao_existente={"status": "POSSIVEL"},
    ))

    assert resultado["status"] == INCONCLUSIVO
    assert "COMPARACAO_POSSIVEL" in _codigos(resultado)


def test_codigos_sem_duplicata_e_ordenados_por_severidade():
    documental = copy.deepcopy(_documental())
    documental["common_ancestor"]["birth"] = "1650"
    documental["evidence"] = [
        _hop("@I10@", "@I2@", 1650, 1960, plausivel=False),
        _hop("@I10@", "@I2@", 1650, 1965, plausivel=False),
    ]
    resultado = validar_comparacao(_comparacao(
        doador={"id": "@I1@", "nome": "Doador", "nascimento": "1985"},
        documental=documental,
    ))

    codigos = [item["codigo"] for item in resultado["codigos"]]
    assert len(codigos) == len(set(codigos))
    severidades = [item["severidade"] for item in resultado["codigos"]]
    ordem = {"critico": 0, "atencao": 1, "informativo": 2}
    assert severidades == sorted(severidades, key=lambda valor: ordem[valor])


# ---------------------------------------------------------------------------
# Agregação
# ---------------------------------------------------------------------------


def test_agregar_resultados_usa_o_pior_status():
    validado = validar_comparacao(_comparacao())
    erro = validar_comparacao(_comparacao(
        comparacao_existente={"status": "CONFLITANTE"},
    ))

    resumo = agregar_resultados([validado, erro])

    assert resumo["status"] == ERRO_CRONICO
    assert resumo["total"] == 2
    assert resumo["por_status"][VALIDADO] == 1
    assert resumo["por_status"][ERRO_CRONICO] == 1


def test_agregar_sem_evidencia_e_inconclusivo():
    resumo = agregar_resultados([])

    assert resumo["status"] == INCONCLUSIVO
    assert resumo["total"] == 0
    assert resumo["codigos"][0]["codigo"] == "SEM_EVIDENCIA"

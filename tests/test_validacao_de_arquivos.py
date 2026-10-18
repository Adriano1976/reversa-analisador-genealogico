"""Testes de integração da fachada `application.validacao`.

Escreve GEDCOM e CSV sintéticos no `tmp_path` da suíte e exercita o caminho
completo: parse da árvore, leitura do CSV, evidência genética, matching,
parentesco documental, confronto e validação. Nenhum dado real.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from application.validacao import (  # noqa: E402
    DependenciasDeValidacao,
    intervalo_de_geracao_mediano,
    validar_arquivos,
)
from core.genetic_evidence import build_genetic_evidence  # noqa: E402
from core.validator import ERRO_CRONICO, INCONCLUSIVO, VALIDADO  # noqa: E402
from parsers.csv_ingest import read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from tests.fixtures.arvore_com_datas import (  # noqa: E402
    CSV_DOIS_KITS,
    CSV_SEM_MATCH,
    CSV_UM_KIT,
    CSV_VAZIO,
    GED_DOADOR_VIVO_SECULO_XVII,
    GED_SEM_DATA,
    GED_VALIDO,
)


def _arquivo(tmp_path: Path, nome: str, conteudo: str) -> str:
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return str(caminho)


def test_um_kit_valida_a_linha_datada(tmp_path):
    ged = _arquivo(tmp_path, "valido.ged", GED_VALIDO)
    csv = _arquivo(tmp_path, "um_kit.csv", CSV_UM_KIT)

    resultado = validar_arquivos(ged, csv, "Doador Sintetico", ano_referencia=2026)

    assert resultado["doador"]["id"] == "@I1@"
    assert resultado["intervalo_de_geracao"] == 25.0
    assert len(resultado["comparacoes"]) == 1
    assert resultado["comparacoes"][0]["status"] == VALIDADO
    assert resultado["resumo"]["status"] == VALIDADO


def test_dois_kits_agregam_pelo_pior_status(tmp_path):
    ged = _arquivo(tmp_path, "valido.ged", GED_VALIDO)
    csv = _arquivo(tmp_path, "dois_kits.csv", CSV_DOIS_KITS)

    resultado = validar_arquivos(ged, csv, "Doador Sintetico", ano_referencia=2026)

    assert len(resultado["comparacoes"]) == 2
    assert {item["status"] for item in resultado["comparacoes"]} == {VALIDADO, ERRO_CRONICO}
    assert resultado["resumo"]["status"] == ERRO_CRONICO
    assert resultado["resumo"]["por_status"][VALIDADO] == 1
    assert resultado["resumo"]["por_status"][ERRO_CRONICO] == 1


def test_match_sem_caminho_devolve_inconclusivo_com_motivo(tmp_path):
    ged = _arquivo(tmp_path, "valido.ged", GED_VALIDO)
    csv = _arquivo(tmp_path, "sem_match.csv", CSV_SEM_MATCH)

    resultado = validar_arquivos(ged, csv, "Doador Sintetico", ano_referencia=2026)

    assert len(resultado["comparacoes"]) == 1
    assert resultado["comparacoes"][0]["status"] == INCONCLUSIVO
    assert "SEM_CAMINHO_DOCUMENTAL" in {
        item["codigo"] for item in resultado["comparacoes"][0]["codigos"]
    }
    assert resultado["resumo"]["status"] == INCONCLUSIVO


def test_csv_sem_linhas_devolve_sem_evidencia(tmp_path):
    ged = _arquivo(tmp_path, "valido.ged", GED_VALIDO)
    csv = _arquivo(tmp_path, "vazio.csv", CSV_VAZIO)

    resultado = validar_arquivos(ged, csv, "Doador Sintetico", ano_referencia=2026)

    assert resultado["comparacoes"] == []
    assert resultado["resumo"]["status"] == INCONCLUSIVO
    assert resultado["resumo"]["codigos"][0]["codigo"] == "SEM_EVIDENCIA"


def test_doador_vivo_com_ancestral_de_1650_e_erro(tmp_path):
    ged = _arquivo(tmp_path, "seculo_xvii.ged", GED_DOADOR_VIVO_SECULO_XVII)
    csv = _arquivo(tmp_path, "um_kit.csv", CSV_UM_KIT)

    resultado = validar_arquivos(ged, csv, "Doador Sintetico", ano_referencia=2026)

    assert resultado["comparacoes"][0]["status"] == ERRO_CRONICO
    codigos = {item["codigo"] for item in resultado["comparacoes"][0]["codigos"]}
    assert "PROFUNDIDADE_TEMPORAL_INCOMPATIVEL" in codigos
    assert "DOADOR_VIVO_EM_LINHA_INCOMPATIVEL" in codigos


def test_match_sem_data_de_nascimento_e_inconclusivo(tmp_path):
    ged = _arquivo(tmp_path, "sem_data.ged", GED_SEM_DATA)
    csv = _arquivo(tmp_path, "um_kit.csv", CSV_UM_KIT)

    resultado = validar_arquivos(ged, csv, "Doador Sintetico", ano_referencia=2026)

    assert resultado["comparacoes"][0]["status"] == INCONCLUSIVO
    assert "SEM_DATA_DE_NASCIMENTO" in {
        item["codigo"] for item in resultado["comparacoes"][0]["codigos"]
    }


def test_arvore_e_parseada_uma_vez(tmp_path):
    ged = _arquivo(tmp_path, "valido.ged", GED_VALIDO)
    csv = _arquivo(tmp_path, "dois_kits.csv", CSV_DOIS_KITS)
    chamadas = {"total": 0}

    def carregar_uma_vez(caminho):
        chamadas["total"] += 1
        return carregar_arvore(caminho)

    deps = DependenciasDeValidacao(
        carregar_arvore=carregar_uma_vez,
        ler_csv=read_csv_with_fallback,
        construir_evidencia=build_genetic_evidence,
    )

    validar_arquivos(ged, csv, "Doador Sintetico", ano_referencia=2026, deps=deps)

    assert chamadas["total"] == 1


def test_intervalo_de_geracao_da_arvore_sintetica(tmp_path):
    ged = _arquivo(tmp_path, "valido.ged", GED_VALIDO)
    arvore = carregar_arvore(ged)

    assert intervalo_de_geracao_mediano(arvore) == 25.0


def test_raiz_inexistente_sobe_o_erro_do_fluxo(tmp_path):
    ged = _arquivo(tmp_path, "valido.ged", GED_VALIDO)
    csv = _arquivo(tmp_path, "um_kit.csv", CSV_UM_KIT)

    from core.erros import PessoaNaoEncontrada

    try:
        validar_arquivos(ged, csv, "Pessoa Que Nao Existe", ano_referencia=2026)
    except PessoaNaoEncontrada as erro:
        assert "não foi encontrado no GEDCOM" in str(erro)
    else:  # pragma: no cover - só falha se o erro não subir
        raise AssertionError("PessoaNaoEncontrada não foi levantada")


def test_incluir_documental_e_aditivo_e_desligado_por_padrao(tmp_path):
    """A emenda da feature 029: nada muda sem o parâmetro.

    Com `incluir_documental=True`, cada comparação ganha `documental` e o retorno
    ganha `arvore`. Sem ele, o retorno é exatamente o de antes — é o que garante que
    a feature `028` continue com o mesmo contrato.
    """
    ged = _arquivo(tmp_path, "valido.ged", GED_VALIDO)
    csv = _arquivo(tmp_path, "um_kit.csv", CSV_UM_KIT)

    sem = validar_arquivos(ged, csv, "Doador Sintetico", ano_referencia=2026)
    com = validar_arquivos(ged, csv, "Doador Sintetico", ano_referencia=2026,
                           incluir_documental=True)

    assert "arvore" not in sem
    assert "documental" not in sem["comparacoes"][0]

    assert "arvore" in com
    assert com["comparacoes"][0]["documental"]["path"]["ids"]

    comparacao_sem = sem["comparacoes"][0]
    comparacao_com = {chave: valor for chave, valor in com["comparacoes"][0].items()
                      if chave != "documental"}
    assert comparacao_com == comparacao_sem

    resto_sem = {chave: valor for chave, valor in sem.items() if chave != "comparacoes"}
    resto_com = {chave: valor for chave, valor in com.items()
                 if chave not in ("comparacoes", "arvore")}
    assert resto_com == resto_sem

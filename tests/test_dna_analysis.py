"""Testes da Tarefa 04 — Análise de DNA (TT-01 a TT-07).

Carrega um GEDCOM sintético e exercita o fluxo de análise de DNA:
agregação de segmentos, fallback de encoding, matching difuso com
filtro anti-falso-positivo, cálculo de caminho e mensagens de erro.
"""
import io
import os
import sys
import tempfile

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from tests.fixtures.sample_dna import (
    DNA_CSV_DUPLICATED,
    DNA_CSV_LATIN1_RAW,
    DNA_CSV_NO_INTERSECTION,
    DNA_CSV_UTF8,
    DNA_GED,
)

from parsers import gedcom_parser
from core.dna_analysis import (
    dna_analysis,
    get_relationships_by_cm,
)
# `aggregate_matches`, `detect_columns` e `read_csv_with_fallback` deixaram de ser
# reexportados pelo nucleo em `T016`: a leitura do CSV passou a ser injetada pela
# borda, e reexporta-los la obrigaria `core/` a importar `parsers/`.
from parsers.csv_ingest import (
    aggregate_matches,
    detect_columns,
    read_csv_with_fallback,
)
from tests.fixtures.helpers import arvore_de as _arvore_de
from tests.fixtures.helpers import deps as _deps
from tests.fixtures.arvore_atual import atual, guardar


@pytest.fixture(scope="module")
def dna_loaded():
    """Carrega o GEDCOM sintético de DNA uma única vez para toda a suite.

    Escreve ``DNA_GED`` em um arquivo temporário, invoca
    ``gedcom_parser.carregar_arvore`` e guarda a arvore devolvida — os testes a
    alcancam por ``atual()`` —, removendo o arquivo ao final.

    Yields:
        tuple: A arvore ``(people, families, graph, child_to_family)`` carregada.
    """
    fd, ged_path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_GED)
        guardar(gedcom_parser.carregar_arvore(ged_path))
    finally:
        os.remove(ged_path)
    return atual()


# TT-03: encoding — CSV UTF-8 e Latin-1 são lidos.
def test_read_csv_utf8():
    """TT-03a: verifica leitura de CSV codificado em UTF-8.

    Escreve ``DNA_CSV_UTF8`` em um arquivo temporário e confirma que
    ``read_csv_with_fallback`` retorna um DataFrame com o nome esperado
    na coluna ``Name``.
    """
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_CSV_UTF8)
        df = read_csv_with_fallback(path)
        assert "Ana Silva Souza" in df["Name"].values
    finally:
        os.remove(path)


def test_read_csv_latin1(dna_loaded):
    """TT-03b: verifica leitura de CSV codificado em Latin-1 (ISO-8859-1).

    Escreve bytes raw de ``DNA_CSV_LATIN1_RAW`` em um arquivo temporário e
    confirma que ``read_csv_with_fallback`` aplica o fallback de encoding
    e retorna o DataFrame com o nome correto na coluna ``Name``.

    Args:
        dna_loaded: Fixture que carrega o GEDCOM sintético e guarda a arvore devolvida.
    """
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(DNA_CSV_LATIN1_RAW)
        df = read_csv_with_fallback(path)
        assert "Ana Silva Souza Ferreira" in df["Name"].values
    finally:
        os.remove(path)


def test_detect_columns(dna_loaded):
    """Verifica que ``detect_columns`` identifica corretamente as colunas padrão.

    Cria um DataFrame mínimo com colunas ``Name``, ``cM`` e ``email`` e
    confirma que os quatro valores retornados mapeiam para os nomes esperados.

    Args:
        dna_loaded: Fixture que carrega o GEDCOM sintético e guarda a arvore devolvida.
    """
    df = pd.DataFrame({"Name": ["A"], "cM": [1], "email": ["x"]})
    name_col, cm_col, id_col, email_col = detect_columns(df)
    assert name_col == "Name"
    assert cm_col == "cM"
    assert email_col == "email"


# TT-02: agregação de segmentos duplicados soma cM.
def test_aggregate_duplicated(dna_loaded):
    """TT-02: confirma que segmentos duplicados têm seus valores de cM somados.

    Carrega ``DNA_CSV_DUPLICATED``, agrega os matches e verifica que o
    indivíduo ``ana silva souza`` aparece uma única vez com a soma correta
    de cM (537).

    Args:
        dna_loaded: Fixture que carrega o GEDCOM sintético e guarda a arvore devolvida.
    """
    df = pd.read_csv(io.StringIO(DNA_CSV_DUPLICATED))
    name_col, cm_col, id_col, email_col = detect_columns(df)
    aggr = aggregate_matches(df, name_col, cm_col, id_col, email_col)
    row = aggr[aggr["_group_key"].str.contains("ana silva souza", case=False)]
    assert len(row) == 1
    assert row["cM"].iloc[0] == pytest.approx(537)


# TT-01 happy path: dna_analysis ordena por cM decrescente e gera texto/relação.
def test_dna_analysis_happy(dna_loaded):
    """TT-01: happy path — ``dna_analysis`` ordena por cM e gera texto/relação.

    Executa o fluxo completo de análise com um CSV válido e uma raiz presente
    no grafo. Verifica que:
    - A mensagem de retorno indica 1 conexão encontrada.
    - O resultado contém o nome correto do match.
    - O caminho textual inclui o nome da raiz.
    - O diagrama Mermaid começa com ``flowchart BT``.
    - A lista de relações não está vazia.

    Args:
        dna_loaded: Fixture que carrega o GEDCOM sintético e guarda a arvore devolvida.
    """
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_CSV_UTF8)
        results, skipped, msg = dna_analysis(path, "Carlos Silva Souza", _deps(), atual())
        assert msg.startswith("1 conexões encontradas")
        assert len(results) == 1
        assert "Ana Silva Souza" in results[0]["match_name"]
        assert "Carlos Silva Souza" in results[0]["text_path"]
        assert results[0]["mermaid_data"].startswith("flowchart BT")
        # Regra final da analise: as tres evidencias viajam SEPARADAS, e o rotulo
        # unico "Relacionamento Provável (DNA)" deixou de existir. O parentesco vem
        # do GEDCOM; o cM so vira lista de possibilidades + confronto.
        resultado = results[0]
        assert resultado["documentary"]["source"] == "GEDCOM"
        assert resultado["documentary"]["label"] == "Irmãos"
        assert resultado["genetic_evidence"]["kits"][0]["total_cm"] == 200
        assert resultado["hypotheses"][0]["possible_relationships"], "possibilidades não podem ficar vazias"
        assert resultado["comparison"]["status"] in (
            "COMPATIVEL", "POSSIVEL", "CONFLITANTE", "INCONCLUSIVO")
        assert "relationships" not in resultado, (
            "o campo legado 'relationships' apresentava o cM como parentesco provável")
    finally:
        os.remove(path)


# TT-04: anti-falso-positivo — match sem sobrenome em comum é descartado.
def test_anti_false_positive(dna_loaded):
    """TT-04: matches sem sobrenome em comum com a raiz são descartados.

    Usa ``DNA_CSV_NO_INTERSECTION`` (nomes sem sobreposição de tokens com
    ``Carlos Silva Souza``) e confirma que:
    - Nenhum resultado válido é retornado.
    - O match vai para ``skipped`` com motivo que contém ``não`` ou ``sem``.

    Args:
        dna_loaded: Fixture que carrega o GEDCOM sintético e guarda a arvore devolvida.
    """
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_CSV_NO_INTERSECTION)
        results, skipped, msg = dna_analysis(path, "Carlos Silva Souza", _deps(), atual())
        assert len(results) == 0
        assert len(skipped) == 1
        assert "não" in skipped[0]["motivo"] or "sem" in skipped[0]["motivo"]
    finally:
        os.remove(path)


# TT-05: raiz inexistente -> erro.
def test_root_not_found(dna_loaded):
    """TT-05: raiz inexistente no grafo deve levantar ``ValueError``.

    Passa um nome de raiz (``Zzz Ninguem``) que não existe no GEDCOM e
    verifica que ``dna_analysis`` lança ``ValueError`` com a mensagem
    contendo ``não foi encontrado``.

    Args:
        dna_loaded: Fixture que carrega o GEDCOM sintético e guarda a arvore devolvida.
    """
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_CSV_UTF8)
        with pytest.raises(ValueError) as excinfo:
            dna_analysis(path, "Zzz Ninguem", _deps(), atual())
        assert "não foi encontrado" in str(excinfo.value)
    finally:
        os.remove(path)


# TT-06: colunas ausentes no CSV -> erro amigável.
def test_missing_columns(dna_loaded):
    """TT-06: CSV sem colunas obrigatórias deve levantar ``ValueError`` amigável.

    Passa um CSV mínimo (colunas ``X`` e ``Y``) incapaz de ser mapeado pelas
    heurísticas de ``detect_columns`` e verifica que ``dna_analysis`` lança
    ``ValueError`` com a mensagem contendo ``não encontradas``.

    Args:
        dna_loaded: Fixture que carrega o GEDCOM sintético e guarda a arvore devolvida.
    """
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("X,Y\n1,2\n")
        with pytest.raises(ValueError) as excinfo:
            dna_analysis(path, "Carlos Silva Souza", _deps(), atual())
        assert "não encontradas" in str(excinfo.value)
    finally:
        os.remove(path)


# TT-07 (revisto pela regra final): match COM identidade resolvida e SEM caminho.
def test_match_without_path(dna_loaded):
    """TT-07: match sem caminho ancestral continua sendo analisado.

    Antes da regra final, este caso ia para ``skipped_matches`` e a evidência
    genética desaparecia da tela. Agora ele vira resultado com
    ``documentary.status == "not_found"``: o DNA é apresentado, o parentesco
    documental é declarado não encontrado e **nenhum caminho é inventado**.
    """
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("Name,cM\nLone Ranger,120\n")
        results, skipped, msg = dna_analysis(path, "Carlos Silva Souza", _deps(), atual())
        assert len(results) == 1
        assert results[0]["documentary"]["status"] == "not_found"
        assert results[0]["documentary"]["path"] is None
        assert results[0]["text_path"] == ""
        assert results[0]["genetic_evidence"]["available"] is True
        assert results[0]["genetic_evidence"]["kits"][0]["total_cm"] == 120
        assert results[0]["comparison"]["status"] == "INCONCLUSIVO"
        assert skipped == []
    finally:
        os.remove(path)


# Relação por faixa de cM.
def test_relationships_by_cm(dna_loaded):
    """Verifica as faixas de cM para relações genealógicas conhecidas.

    Testa três casos representativos de ``get_relationships_by_cm``:
    - 2500 cM → deve incluir ``Irmãos completos``.
    - 600 cM  → deve incluir ``Primos``.
    - 0 cM    → deve retornar lista vazia (comportamento legado).

    Args:
        dna_loaded: Fixture que carrega o GEDCOM sintético e guarda a arvore devolvida.
    """
    assert "Irmãos completos" in ", ".join(get_relationships_by_cm(2500))
    assert "Primos" in ", ".join(get_relationships_by_cm(600))
    assert get_relationships_by_cm(0) == []  # cM <= 0 -> sem relação (legado)


def test_relationships_by_cm_out_of_range(dna_loaded):
    """Verifica o retorno padrão para valores de cM fora de todas as faixas.

    Passa 5000 cM (acima de qualquer faixa mapeada) e confirma que
    ``get_relationships_by_cm`` retorna a lista com o texto padrão
    ``Relação distante ou indeterminada``.

    Args:
        dna_loaded: Fixture que carrega o GEDCOM sintético e guarda a arvore devolvida.
    """
    # 5000 está acima de todas as faixas -> texto padrão do legado.
    assert get_relationships_by_cm(5000) == ["Relação distante ou indeterminada"]

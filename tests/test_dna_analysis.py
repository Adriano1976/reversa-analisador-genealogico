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
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analisador-genealogico"))

from tests.fixtures.sample_dna import (
    DNA_CSV_DUPLICATED,
    DNA_CSV_LATIN1_RAW,
    DNA_CSV_NO_INTERSECTION,
    DNA_CSV_UTF8,
    DNA_GED,
)

from reconstructed import upload
from reconstructed.dna_analysis import (
    aggregate_matches,
    detect_columns,
    dna_analysis,
    get_relationships_by_cm,
    read_csv_with_fallback,
)


@pytest.fixture(scope="module")
def dna_loaded():
    fd, ged_path = tempfile.mkstemp(suffix=".ged")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_GED)
        upload.load_gedcom_and_build_graph(ged_path)
    finally:
        os.remove(ged_path)
    return upload


# TT-03: encoding — CSV UTF-8 e Latin-1 são lidos.
def test_read_csv_utf8():
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_CSV_UTF8)
        df = read_csv_with_fallback(path)
        assert "Ana Silva Souza" in df["Name"].values
    finally:
        os.remove(path)


def test_read_csv_latin1(dna_loaded):
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(DNA_CSV_LATIN1_RAW)
        df = read_csv_with_fallback(path)
        assert "Ana Silva Souza Ferreira" in df["Name"].values
    finally:
        os.remove(path)


def test_detect_columns(dna_loaded):
    df = pd.DataFrame({"Name": ["A"], "cM": [1], "email": ["x"]})
    name_col, cm_col, id_col, email_col = detect_columns(df)
    assert name_col == "Name"
    assert cm_col == "cM"
    assert email_col == "email"


# TT-02: agregação de segmentos duplicados soma cM.
def test_aggregate_duplicated(dna_loaded):
    df = pd.read_csv(io.StringIO(DNA_CSV_DUPLICATED))
    name_col, cm_col, id_col, email_col = detect_columns(df)
    aggr = aggregate_matches(df, name_col, cm_col, id_col, email_col)
    row = aggr[aggr["_group_key"].str.contains("ana silva souza", case=False)]
    assert len(row) == 1
    assert row["cM"].iloc[0] == pytest.approx(537)


# TT-01 happy path: dna_analysis ordena por cM decrescente e gera texto/relação.
def test_dna_analysis_happy(dna_loaded):
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_CSV_UTF8)
        results, skipped, msg = dna_analysis(path, "Carlos Silva Souza")
        assert msg.startswith("1 conexões encontradas")
        assert len(results) == 1
        assert "Ana Silva Souza" in results[0]["match_name"]
        assert "Carlos Silva Souza" in results[0]["text_path"]
        assert results[0]["mermaid_data"].startswith("flowchart BT")
        assert results[0]["relationships"]
    finally:
        os.remove(path)


# TT-04: anti-falso-positivo — match sem sobrenome em comum é descartado.
def test_anti_false_positive(dna_loaded):
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_CSV_NO_INTERSECTION)
        results, skipped, msg = dna_analysis(path, "Carlos Silva Souza")
        assert len(results) == 0
        assert len(skipped) == 1
        assert "não" in skipped[0]["motivo"] or "sem" in skipped[0]["motivo"]
    finally:
        os.remove(path)


# TT-05: raiz inexistente -> erro.
def test_root_not_found(dna_loaded):
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(DNA_CSV_UTF8)
        with pytest.raises(ValueError) as excinfo:
            dna_analysis(path, "Zzz Ninguem")
        assert "não foi encontrado" in str(excinfo.value)
    finally:
        os.remove(path)


# TT-06: colunas ausentes no CSV -> erro amigável.
def test_missing_columns(dna_loaded):
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("X,Y\n1,2\n")
        with pytest.raises(ValueError) as excinfo:
            dna_analysis(path, "Carlos Silva Souza")
        assert "não encontradas" in str(excinfo.value)
    finally:
        os.remove(path)


# TT-07: match sem caminho ancestral -> entra em skipped_matches.
def test_match_without_path(dna_loaded):
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("Name,cM\nLone Ranger,120\n")
        results, skipped, msg = dna_analysis(path, "Carlos Silva Souza")
        assert len(results) == 0
        assert any("Lone" in s["csv_name"] for s in skipped)
    finally:
        os.remove(path)


# Relação por faixa de cM.
def test_relationships_by_cm(dna_loaded):
    assert "Irmãos completos" in ", ".join(get_relationships_by_cm(2500))
    assert "Primos" in ", ".join(get_relationships_by_cm(600))
    assert get_relationships_by_cm(0) == []  # cM <= 0 -> sem relação (legado)


def test_relationships_by_cm_out_of_range(dna_loaded):
    # 5000 está acima de todas as faixas -> texto padrão do legado.
    assert get_relationships_by_cm(5000) == ["Relação distante ou indeterminada"]

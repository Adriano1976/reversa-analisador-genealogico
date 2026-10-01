"""Testes da Tarefa 01 — Entidades de Domínio.

Cobre as rotinas de limpeza de mojibake (strip_bad_utf, demojibake)
documentadas em domain.md.

ALTERACAO REGISTRADA (2026-09-30): os testes de `Family`, `GenealogyGraph` e
`DNAGroup` foram REMOVIDOS junto com as classes que eles exercitavam. As tres
eram arquitetura abandonada: nenhuma era instanciada em qualquer caminho de
producao. Decisao do usuario em `_reversa_sdd/questions.md#pergunta-3`.

Removidos nesta data (9 testes):
  Family:          test_family_defaults, test_family_fields,
                   test_family_chil_is_isolated_per_instance
  GenealogyGraph:  test_register_person_normalizes_name,
                   test_register_person_ignores_duplicate,
                   test_get_person_missing_returns_none, test_register_family
  DNAGroup:        test_dna_group_fields, test_dna_group_defaults

O que permanece — e que continua sendo consumido por `upload.py` e
`dna_analysis.py` — sao as rotinas de limpeza de nome.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analisador-genealogico"))

from reconstructed.domain import (
    demojibake,
    strip_bad_utf,
)


# ---------------------------------------------------------------------------
# Mojibake (domain.md §2.3 / §1)
# ---------------------------------------------------------------------------

def test_strip_bad_utf_removes_replacement_char():
    assert "\ufffd" not in strip_bad_utf("Jo\uFFFDa\uFFFDo")


def test_strip_bad_utf_handles_none_and_empty():
    assert strip_bad_utf(None) == "" or strip_bad_utf("") == ""


def test_demojibake_fixes_cedilha():
    # "Ã§" corrompido deve virar "ç".
    assert "ç" in demojibake("FranÃ§isco")


def test_demojibake_returns_input_for_empty():
    assert demojibake("") == ""
    # Legado: `if not text: return text` -> None passa adiante.
    assert demojibake(None) is None


def test_demojibake_recupera_latin1_lido_como_utf8():
    """Afirma o comportamento vivo, que agora e o unico que existe.

    A assercao anterior verificava a substituicao de "A + til combinante" por "Ã",
    que so a implementacao morta de domain.py fazia. O corpo vivo, vindo de
    dna_analysis, recupera o texto quando a conversao latin1 para utf-8 e valida.
    """
    assert demojibake("FranÃ§isco") == "Françisco"
    assert demojibake("texto normal") == "texto normal"
    assert demojibake("") == ""
    assert demojibake(None) is None

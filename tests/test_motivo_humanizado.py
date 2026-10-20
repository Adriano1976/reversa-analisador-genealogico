"""Testes do motivo humanizado dos descartes (feature 038).

O operador lia `score insuficiente ou conflito de sobrenome (given=100, final=88.25,
inter=1/1, jacc=0.50)` e não conseguia decidir nada com isso. Estes testes fixam três
coisas, nesta ordem: **a frase existe e é legível**, **a causa é a verdadeira** (o veto de
token do meio, que a mensagem antiga não citava) e **a decisão não mudou** — só o texto.
"""
from __future__ import annotations

import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import pytest  # noqa: E402

from core.matching import avaliar_candidatos, match_candidates  # noqa: E402
from core.motivos_do_descarte import (  # noqa: E402
    LIMIAR_DE_PRENOME,
    NAO_ENCONTRADO,
    NOME_DO_MEIO_AUSENTE,
    NOME_UNICO,
    PRENOME_DIFERENTE,
    SEMELHANCA_INSUFICIENTE,
    SEM_SOBRENOME_COMUM,
    SEM_SOBRENOME_NO_GEDCOM,
    SOBRENOME_CURTO,
    SOBRENOME_LIDO_COMO_PRENOME,
    SOBRENOMES_EM_COMUM_INSUFICIENTES,
    SOBRENOME_POUCO_PARECIDO,
    TEXTOS,
    detalhe_tecnico,
    diagnosticar,
    motivo,
)

# Nomes de medida que a coluna Motivo deixou de exibir (RN-25). O detalhe técnico pode
# usá-los? Não: ele também usa rótulo em português ("prenome", "nota", "grafia").
TERMOS_DE_MAQUINA = ("given", "final=", "inter=", "jacc", "floor", "threshold")

# Um pool montado à mão, no mesmo desenho de `test_candidatos_do_descarte`: o caso do
# token do meio precisa de um par em que TODOS os portões de nota passem — só assim o
# sétimo portão é a causa, e não um acidente. A árvore oferece `Aparecida Oliveira`;
# `Maria` sobra como token do meio e não existe nela.
SURNAME_INDEX = {"oliveira": ["@I1@"]}
FEATURES = {
    "@I1@": {"nome": "Aparecida Oliveira", "norm": "aparecida oliveira",
             "given_tokens": ["aparecida"], "surnames": {"oliveira"},
             "surnames_list": ["oliveira"], "tokens": {"aparecida", "oliveira"}},
}


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------

def test_o_catalogo_cobre_os_onze_codigos():
    assert set(TEXTOS) == {
        NOME_DO_MEIO_AUSENTE, SOBRENOMES_EM_COMUM_INSUFICIENTES, SOBRENOME_POUCO_PARECIDO,
        PRENOME_DIFERENTE, SEMELHANCA_INSUFICIENTE, SEM_SOBRENOME_COMUM,
        SOBRENOME_LIDO_COMO_PRENOME, NOME_UNICO, SOBRENOME_CURTO, SEM_SOBRENOME_NO_GEDCOM,
        NAO_ENCONTRADO,
    }


@pytest.mark.parametrize("codigo", sorted(TEXTOS))
def test_nenhuma_frase_usa_nome_de_medida(codigo):
    frase = TEXTOS[codigo].lower()

    for termo in TERMOS_DE_MAQUINA:
        assert termo not in frase, f"o motivo {codigo!r} ainda fala em {termo!r}: {frase!r}"


@pytest.mark.parametrize("codigo", sorted(TEXTOS))
def test_nenhuma_frase_carrega_numero_solto(codigo):
    """Número no meio da frase é a fórmula de volta, com outro nome."""
    frase = TEXTOS[codigo]

    assert not any(caractere.isdigit() for caractere in frase), (
        f"o motivo {codigo!r} voltou a mostrar número: {frase!r}")


def test_o_filtro_anti_falso_positivo_perdeu_o_jargao():
    assert TEXTOS[SEM_SOBRENOME_COMUM] == "nenhum sobrenome em comum entre o nome e o da árvore"
    assert "filtro" not in TEXTOS[SEM_SOBRENOME_COMUM].lower()


def test_motivo_junta_codigo_texto_e_detalhe():
    um = motivo(NOME_DO_MEIO_AUSENTE, "prenome 100")

    assert um.codigo == NOME_DO_MEIO_AUSENTE
    assert um.texto == TEXTOS[NOME_DO_MEIO_AUSENTE]
    assert um.detalhe == "prenome 100"


# ---------------------------------------------------------------------------
# Precedência do diagnóstico (D-03)
# ---------------------------------------------------------------------------

def _diagnosticar(**troca):
    base = dict(prenome=100.0, nota=88.25, intersecao=1, exigidas=1,
                grafia=0.5, grafia_ok=True, meio_vetado=False)
    base.update(troca)
    return diagnosticar(**base)


def test_o_nome_do_meio_vem_primeiro():
    assert _diagnosticar(meio_vetado=True, intersecao=0, grafia_ok=False,
                         prenome=10.0).codigo == NOME_DO_MEIO_AUSENTE


def test_sobrenomes_de_menos_vem_antes_da_grafia():
    assert _diagnosticar(intersecao=1, exigidas=2, grafia_ok=False).codigo == \
        SOBRENOMES_EM_COMUM_INSUFICIENTES


def test_grafia_vem_antes_do_prenome():
    assert _diagnosticar(grafia_ok=False, prenome=10.0).codigo == SOBRENOME_POUCO_PARECIDO


def test_prenome_vem_antes_da_semelhanca_geral():
    assert _diagnosticar(prenome=LIMIAR_DE_PRENOME - 1).codigo == PRENOME_DIFERENTE


def test_sem_causa_dominante_e_semelhanca_insuficiente():
    assert _diagnosticar(nota=80.0).codigo == SEMELHANCA_INSUFICIENTE


def test_o_limiar_do_prenome_espelha_a_decisao():
    """85 é o menor limiar de prenome das portas de aceite. Se a decisão mudar, este valor
    muda junto — e o teste avisa antes de o diagnóstico começar a mentir."""
    assert LIMIAR_DE_PRENOME == 85


# ---------------------------------------------------------------------------
# Detalhe técnico (RN-28)
# ---------------------------------------------------------------------------

def test_o_detalhe_rotula_os_quatro_numeros():
    detalhe = detalhe_tecnico(prenome=100.0, nota=88.25, intersecao=1, exigidas=1, grafia=0.5)

    assert detalhe == ("prenome 100 · nota 88,25 · sobrenomes em comum 1 de 1 · "
                       "grafia do sobrenome 0,5")


def test_o_detalhe_usa_virgula_decimal():
    """O Excel em português trata `.` como texto na planilha exportada."""
    detalhe = detalhe_tecnico(prenome=100.0, nota=88.25, intersecao=1, exigidas=1, grafia=0.5)

    assert "88,25" in detalhe and "0,5" in detalhe
    assert "88.25" not in detalhe


def test_o_detalhe_nao_usa_o_separador_da_planilha():
    detalhe = detalhe_tecnico(prenome=100.0, nota=88.25, intersecao=1, exigidas=1, grafia=0.5)

    assert ";" not in detalhe


def test_o_detalhe_nao_usa_nome_de_maquina():
    detalhe = detalhe_tecnico(prenome=100.0, nota=88.25, intersecao=1, exigidas=1, grafia=0.5).lower()

    for termo in TERMOS_DE_MAQUINA:
        assert termo not in detalhe


# ---------------------------------------------------------------------------
# Ponta a ponta: o caso do token do meio
# ---------------------------------------------------------------------------

def test_o_caso_do_operador_recebe_a_causa_verdadeira():
    """`Maria Aparecida de Oliveira` × `Aparecida Oliveira`.

    Prenome idêntico, sobrenome idêntico, exigência de interseção cumprida: todos os
    portões de nota passam. O que recusa é o token do meio (`Maria`, que a árvore não
    tem) — a mensagem antiga dizia "score insuficiente OU conflito de sobrenome", as
    duas falsas. Medido aqui: `prenome 100`, `nota 88,75`, `sobrenomes em comum 1 de 1`.
    """
    pids, razao, _ = avaliar_candidatos(
        None, "Maria Aparecida de Oliveira", 100, {}, SURNAME_INDEX, FEATURES)

    assert pids == []
    assert razao.codigo == NOME_DO_MEIO_AUSENTE
    assert razao.texto == TEXTOS[NOME_DO_MEIO_AUSENTE]
    assert "prenome 100" in razao.detalhe
    assert "sobrenomes em comum 1 de 1" in razao.detalhe


def test_recusa_por_prenome_recebe_a_causa_do_prenome():
    """`Maria Cristina Oliveira` × `Aparecida Oliveira`: o prenome é que não bate."""
    pids, razao, _ = avaliar_candidatos(
        None, "Maria Cristina Oliveira", 100, {}, SURNAME_INDEX, FEATURES)

    assert pids == []
    assert razao.codigo == PRENOME_DIFERENTE
    assert "prenome 35" in razao.detalhe.lower() or "prenome 35" in razao.detalhe


def test_match_candidates_continua_entregando_texto():
    """O contrato de dois valores com texto é o que a aplicação e a caracterização usam."""
    pids, razao = match_candidates(
        None, "Maria Aparecida de Oliveira", 100, {}, SURNAME_INDEX, FEATURES)

    assert pids == []
    assert isinstance(razao, str)
    assert razao == TEXTOS[NOME_DO_MEIO_AUSENTE]


def test_o_nome_sem_sobrenome_continua_com_a_frase_do_adendo_024():
    pids, razao, _ = avaliar_candidatos(None, "PAULO", 100, {}, {"oliveira": ["@I1@"]}, FEATURES)

    assert pids == []
    assert razao.codigo == NOME_UNICO
    assert razao.detalhe == ""


# ---------------------------------------------------------------------------
# Tela e planilha
# ---------------------------------------------------------------------------

DESCARTE = {
    "csv_name": "Maria Aparecida de Jesus Oliveira",
    "kit": "TG0000001",
    "cm": 88.25,
    "motivo": TEXTOS[NOME_DO_MEIO_AUSENTE],
    "motivo_codigo": NOME_DO_MEIO_AUSENTE,
    "motivo_detalhe": ("prenome 100 · nota 88,25 · sobrenomes em comum 1 de 1 · "
                       "grafia do sobrenome 0,5"),
    "candidatos": [],
}


def _bloco(descartados) -> str:
    from flask import render_template

    from app import app

    with app.test_request_context("/"):
        pagina = render_template("index.html", skipped_matches=descartados)
    inicio = pagina.index("bloco-descartados")
    return pagina[inicio:pagina.index("</details>", inicio)]


def test_a_tela_mostra_a_frase_e_nao_a_formula():
    bloco = _bloco([DESCARTE])

    assert TEXTOS[NOME_DO_MEIO_AUSENTE] in bloco
    assert "given=" not in bloco
    assert "jacc=" not in bloco


def test_a_tela_diz_onde_estao_os_numeros():
    bloco = _bloco([DESCARTE])

    assert "Detalhe técnico" in bloco


def test_a_planilha_ganha_a_nona_coluna():
    from reporting.csv_de_descartes import CABECALHO, csv_de_descartes

    assert CABECALHO[-1] == "Detalhe técnico"
    assert len(CABECALHO) == 9

    linhas = list(csv.reader(io.StringIO(csv_de_descartes([DESCARTE]).lstrip("\ufeff")),
                             delimiter=";"))

    assert linhas[1][3] == TEXTOS[NOME_DO_MEIO_AUSENTE]
    assert linhas[1][8] == DESCARTE["motivo_detalhe"]


def test_a_planilha_sem_detalhe_fica_com_a_celula_vazia():
    from reporting.csv_de_descartes import csv_de_descartes

    sem_detalhe = {k: v for k, v in DESCARTE.items() if k != "motivo_detalhe"}
    linhas = list(csv.reader(io.StringIO(csv_de_descartes([sem_detalhe]).lstrip("\ufeff")),
                             delimiter=";"))

    assert linhas[1][8] == ""

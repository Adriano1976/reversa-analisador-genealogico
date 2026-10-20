"""Testes dos candidatos do descarte (feature 034).

A lista dos descartados mostrava so' o motivo tecnico. Estes testes fixam duas coisas:
o **contrato antigo** de `match_candidates` continua valendo (dois valores, mesmas
decisoes) e a lista passa a levar os tres melhores candidatos ate a tela, com nome e
ano de nascimento.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.matching import avaliar_candidatos, match_candidates  # noqa: E402

# Um pool montado a mao: `avaliar_candidatos` nao consulta a arvore, so' os indices.
# E' a mesma propriedade que `test_characterization_matching` preserva desde a 005.
SURNAME_INDEX = {
    "silva": ["@I1@", "@I2@", "@I3@", "@I4@"],
    "souza": ["@I1@", "@I2@", "@I3@"],
}
FEATURES = {
    "@I1@": {"nome": "Mariana Silva Souza", "norm": "mariana silva souza",
             "given_tokens": ["mariana"], "surnames": {"silva", "souza"},
             "surnames_list": ["silva", "souza"], "tokens": {"mariana", "silva", "souza"}},
    "@I2@": {"nome": "Mariana Souza", "norm": "mariana souza",
             "given_tokens": ["mariana"], "surnames": {"souza"},
             "surnames_list": ["souza"], "tokens": {"mariana", "souza"}},
    "@I3@": {"nome": "Maria Silva Souza", "norm": "maria silva souza",
             "given_tokens": ["maria"], "surnames": {"silva", "souza"},
             "surnames_list": ["silva", "souza"], "tokens": {"maria", "silva", "souza"}},
    "@I4@": {"nome": "Joana Silva", "norm": "joana silva",
             "given_tokens": ["joana"], "surnames": {"silva"},
             "surnames_list": ["silva"], "tokens": {"joana", "silva"}},
}


def _avaliar(nome="Mariana Silva Souza", cm=100):
    return avaliar_candidatos(None, nome, cm, {}, SURNAME_INDEX, FEATURES)


# ---------------------------------------------------------------------------
# O contrato antigo continua de pe'
# ---------------------------------------------------------------------------

def test_match_candidates_continua_devolvendo_dois_valores():
    resultado = match_candidates(None, "Mariana Silva Souza", 100, {}, SURNAME_INDEX, FEATURES)

    assert isinstance(resultado, tuple)
    assert len(resultado) == 2


def test_a_decisao_e_a_mesma_pelos_dois_caminhos():
    pids_wrapper, motivo_wrapper = match_candidates(
        None, "Mariana Silva Souza", 100, {}, SURNAME_INDEX, FEATURES)
    pids_avaliados, motivo_avaliados, _ = _avaliar()

    assert pids_wrapper == pids_avaliados
    # Desde a feature 038 `avaliar_candidatos` devolve `Motivo` e `match_candidates`
    # continua devolvendo o TEXTO — e' o contrato antigo que esta linha prende. Aceite nao
    # produz motivo nenhum, e `None` atravessa os dois caminhos do mesmo jeito.
    assert motivo_wrapper == (motivo_avaliados.texto if motivo_avaliados else None)


# ---------------------------------------------------------------------------
# Os candidatos
# ---------------------------------------------------------------------------

def test_devolve_no_maximo_tres_candidatos():
    _, _, proximos = _avaliar()

    assert len(proximos) == 3


def test_os_candidatos_vem_na_ordem_do_operador():
    """Compatível primeiro, e dentro de cada grupo a maior nota primeiro."""
    _, _, proximos = _avaliar()

    flags = [c["compativel"] for c in proximos]
    assert flags == sorted(flags, reverse=True)
    compativeis = [c["nota"] for c in proximos if c["compativel"]]
    assert compativeis == sorted(compativeis, reverse=True)


def test_o_candidato_aceito_aparece_entre_os_proximos():
    pids, _, proximos = _avaliar()

    assert pids, "o caso de teste deveria ser aceito"
    assert pids[0] in [c["id"] for c in proximos]


def test_o_candidato_leva_o_nome_de_exibicao():
    _, _, proximos = _avaliar()

    assert proximos[0]["nome"] == "Mariana Silva Souza"


def test_as_duas_medidas_da_decisao_viajam_no_candidato():
    _, _, proximos = _avaliar()

    assert {"prenome", "nota", "intersecao", "compativel"} <= set(proximos[0])


def test_o_candidato_com_prenome_e_sobrenome_e_marcado_compativel():
    _, _, proximos = _avaliar()

    assert proximos[0]["compativel"] is True


def test_o_candidato_fraco_nao_e_marcado_compativel():
    """`Joana Silva` para `Mariana Silva Souza`: sobrenome em comum, prenome distante."""
    _, _, proximos = avaliar_candidatos(
        None, "Mariana Silva Souza", 100, {}, SURNAME_INDEX, FEATURES)
    fraco = [c for c in proximos if c["id"] == "@I4@"]

    assert fraco == [] or fraco[0]["compativel"] is False


def test_nome_sem_candidato_nenhum_devolve_lista_vazia():
    _, _, proximos = avaliar_candidatos(
        None, "Zulmira Quaresma", 100, {}, SURNAME_INDEX, FEATURES)

    assert proximos == []


# ---------------------------------------------------------------------------
# Projeção e tela
# ---------------------------------------------------------------------------

DESCARTE = {
    "csv_name": "*Maria de Fátima Oliveira de Jesus",
    "kit": "TG0000001",
    "cm": 12.3,
    "motivo": "o nome tem uma parte a mais que não aparece na árvore",
    "motivo_codigo": "nome_do_meio_ausente",
    "motivo_detalhe": ("prenome 100 · nota 88,25 · sobrenomes em comum 1 de 1 · "
                       "grafia do sobrenome 0,5"),
    "candidatos": [
        {"id": "@I9@", "nome": "Maria de Fátima da Mata Oliveira",
         "nota": 84.1, "prenome": 100.0, "intersecao": 2, "nascimento": "6 AUG 1966",
         "compativel": True},
    ],
}


def test_a_projecao_leva_os_candidatos():
    from application.dna_analysis import projetar_analise

    analise = projetar_analise([], [DESCARTE], "msg", "arvore", "csv", "adriano")

    descartado = analise.descartados[0]
    assert descartado.candidatos[0].nome == "Maria de Fátima da Mata Oliveira"
    assert descartado.candidatos[0].nascimento == "6 AUG 1966"


def test_a_projecao_leva_a_causa_e_o_detalhe():
    """Feature 038: a causa e os números atravessam a projeção da porta."""
    from application.dna_analysis import projetar_analise

    analise = projetar_analise([], [DESCARTE], "msg", "arvore", "csv", "adriano")

    descartado = analise.descartados[0]
    assert descartado.reason == "o nome tem uma parte a mais que não aparece na árvore"
    assert descartado.reason_code == "nome_do_meio_ausente"
    assert descartado.detail.startswith("prenome 100")


def test_a_projecao_sem_candidato_fica_vazia():
    from application.dna_analysis import projetar_analise

    sem = {k: v for k, v in DESCARTE.items() if k != "candidatos"}
    analise = projetar_analise([], [sem], "msg", "arvore", "csv", "adriano")

    assert analise.descartados[0].candidatos == ()


def _bloco(descartados) -> str:
    from flask import render_template

    from app import app

    with app.test_request_context("/"):
        pagina = render_template("index.html", skipped_matches=descartados)
    inicio = pagina.index("bloco-descartados")
    return pagina[inicio:pagina.index("</details>", inicio)]


def test_a_tela_mostra_o_candidato_e_o_ano():
    bloco = _bloco([DESCARTE])

    assert "Maria de Fátima da Mata Oliveira" in bloco
    assert "6 AUG 1966" in bloco
    assert "prenome 100" in bloco


def test_a_tela_conta_quantos_tem_candidato():
    bloco = _bloco([DESCARTE, {k: v for k, v in DESCARTE.items() if k != "candidatos"}])

    assert "2)" in bloco or "(2" in bloco
    assert "1</strong> com candidato na árvore" in bloco


def test_a_tela_marca_ausencia_de_candidato():
    bloco = _bloco([{k: v for k, v in DESCARTE.items() if k != "candidatos"}])

    assert "Candidatos na árvore" in bloco
    assert "—" in bloco


def test_a_tela_marca_candidato_incompativel_como_melhor_avaliado():
    fraco = {
        "csv_name": "Manuel Sena", "kit": "TG1", "cm": 9.0,
        "motivo": "score insuficiente",
        "candidatos": [{"nome": "Mariana Sena da Silva", "prenome": 46.0, "nota": 57.4,
                        "nascimento": "ABOUT 1805", "compativel": False}],
    }

    bloco = _bloco([fraco])

    assert "sem candidato compatível" in bloco
    assert "melhor avaliado: Mariana Sena da Silva" in bloco
    assert "com candidato na árvore" not in bloco

"""Testes da derivação do hiato para a tela.

O que se testa aqui é o número que o cartão mostra — e o que ele **não** faz: a tela não
pode chamar `arvore_sugerida`, que copia o grafo (O(V+E)) por chamada.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from application.validacao import validar_arquivos  # noqa: E402
from core import cirurgia_do_grafo as cirurgia  # noqa: E402
from core.cirurgia_do_grafo import (  # noqa: E402
    IDENTIDADE_A_CONFIRMAR,
    JANELA_INCOMPATIVEL,
    JUNCAO_NAO_EVIDENCIADA,
    SUGESTAO_INSUFICIENTE,
    SUGESTAO_SEM_CONFLITO,
    arvore_sugerida,
    resumo_da_sugestao,
)
from core.dna_analysis import dna_analysis  # noqa: E402
from core.validator import ERRO_CRONICO, INCONCLUSIVO, VALIDADO  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from tests.fixtures.arvore_para_cirurgia import (  # noqa: E402
    GED_LINHA_VALIDA,
    GED_SALTO_IMPOSSIVEL,
)
from tests.fixtures.helpers import deps  # noqa: E402


def _arquivo(tmp_path: Path, nome: str, conteudo: str) -> str:
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return str(caminho)


def _comparacao(tmp_path, ged_texto: str, cm: float, nome="Doador Sintetico"):
    ged = _arquivo(tmp_path, "arvore.ged", ged_texto)
    csv = _arquivo(tmp_path, "matches.csv", f"Name,cM,Kit\nPrimo Sintetico,{cm},AB1234567\n")
    validacao = validar_arquivos(ged, csv, nome, ano_referencia=2026, incluir_documental=True)
    return validacao["comparacoes"][0]


# ---------------------------------------------------------------------------
# O número
# ---------------------------------------------------------------------------

def test_hiato_positivo_traz_geracoes_e_rotulos(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 25)

    resumo = resumo_da_sugestao(cartao, cartao["documental"])

    assert resumo["geracoes"] == 3
    assert resumo["resumo"] == "3 gerações sugeridas"
    assert resumo["rotulos"] == ["Geração 1", "Geração 2", "Geração 3"]
    assert resumo["aviso"] is None
    assert resumo["codigo"] == "SUGESTAO_DISPONIVEL"


def test_uma_geracao_usa_singular(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 200)

    resumo = resumo_da_sugestao(cartao, cartao["documental"])

    assert resumo["geracoes"] == 1
    assert resumo["resumo"] == "1 geração sugerida"


def test_hiato_zero_explica_so_em_cartao_em_conflito(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 800)
    assert cartao["status"] == ERRO_CRONICO

    resumo = resumo_da_sugestao(cartao, cartao["documental"])

    assert resumo["geracoes"] == 0
    assert resumo["resumo"] is None
    assert resumo["codigo"] == "HIATO_NAO_POSITIVO"
    assert "concordam" in resumo["aviso"]


def test_cartao_validado_nao_recebe_aviso(tmp_path):
    cartao = _comparacao(tmp_path, GED_LINHA_VALIDA, 800)
    assert cartao["status"] == VALIDADO

    resumo = resumo_da_sugestao(cartao, cartao["documental"])

    assert resumo["aviso"] is None
    assert resumo["geracoes"] == 0


def test_sem_estimativa_de_mrca(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 25)
    cartao_sem = {**cartao, "mrca_estimado": None, "status": ERRO_CRONICO}

    resumo = resumo_da_sugestao(cartao_sem, cartao["documental"])

    assert resumo["geracoes"] == 0
    assert resumo["codigo"] == "SEM_MRCA_ESTIMADO"
    assert "não caiu em nenhuma relação" in resumo["aviso"]


# ---------------------------------------------------------------------------
# A fórmula é a mesma da cirurgia
# ---------------------------------------------------------------------------

def test_o_numero_bate_com_a_arvore_sugerida(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 25)
    documental = cartao["documental"]

    resumo = resumo_da_sugestao(cartao, documental)

    ged = _arquivo(tmp_path, "arvore2.ged", GED_SALTO_IMPOSSIVEL)
    sugestao = arvore_sugerida(carregar_arvore(ged), documental, cartao, cartao["doador_id"]
                               if "doador_id" in cartao else documental["person_a"]["id"])
    assert resumo["geracoes"] == len(sugestao["geracoes_virtuais"])


# ---------------------------------------------------------------------------
# Custo: a tela não chama a cirurgia
# ---------------------------------------------------------------------------

def test_o_fluxo_de_dna_nao_chama_arvore_sugerida(tmp_path, monkeypatch):
    chamadas = {"total": 0}

    def proibida(*args, **kwargs):  # pragma: no cover - só roda se alguém chamar
        chamadas["total"] += 1
        raise AssertionError("a tela não pode chamar arvore_sugerida")

    monkeypatch.setattr(cirurgia, "arvore_sugerida", proibida)
    ged = _arquivo(tmp_path, "arvore.ged", GED_SALTO_IMPOSSIVEL)
    csv = _arquivo(tmp_path, "matches.csv", "Name,cM,Kit\nPrimo Sintetico,25,AB1234567\n")

    resultados, _descartados, _msg = dna_analysis(csv, "Doador Sintetico", deps(),
                                                  carregar_arvore(ged))

    assert chamadas["total"] == 0
    # O match desta fixture nasceu em 1710: a janela de vida é impossível, então o
    # portão de 2026-10-21 barra a árvore. O resumo continua sendo calculado — é ele
    # que diz POR QUE não há sugestão —, e a cirurgia continua sem ser chamada.
    assert resultados[0]["sugestao_geracoes"] == 0
    assert resultados[0]["sugestao_mermaid"] is None
    assert "não poderia ter doado DNA" in resultados[0]["sugestao_aviso"]


def test_o_resumo_aceita_apenas_dicionarios(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 25)

    # Sem grafo, sem árvore, sem tupla: só os dois dicionários.
    resumo = resumo_da_sugestao(dict(cartao), dict(cartao["documental"]))

    assert resumo["geracoes"] == 3


# ---------------------------------------------------------------------------
# Portões (2026-10-21): só há árvore quando há evidência de onde quebrou
# ---------------------------------------------------------------------------

def test_inconclusivo_com_hiato_nao_mostra_arvore(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 25)
    inconclusivo = {**cartao, "status": INCONCLUSIVO}

    resumo = resumo_da_sugestao(inconclusivo, cartao["documental"])

    assert resumo["geracoes"] == 0
    assert resumo["resumo"] is None
    assert resumo["codigo"] == SUGESTAO_SEM_CONFLITO
    assert "o veredito é INCONCLUSIVO" in resumo["aviso"]


def test_identidade_a_confirmar_bloqueia(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 25)

    resumo = resumo_da_sugestao(cartao, cartao["documental"], identidade="a_confirmar")

    assert resumo["geracoes"] == 0
    assert resumo["codigo"] == IDENTIDADE_A_CONFIRMAR
    assert "identidade do match" in resumo["aviso"]


def test_janela_impossivel_bloqueia(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 25)

    resumo = resumo_da_sugestao(cartao, cartao["documental"], janela="impossivel")

    assert resumo["geracoes"] == 0
    assert resumo["codigo"] == JANELA_INCOMPATIVEL
    assert "não poderia ter doado DNA" in resumo["aviso"]


def test_sem_salto_impossivel_nao_localiza_a_quebra(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 25)
    documental = {
        **cartao["documental"],
        "evidence": [{**salto, "plausible": None}
                     for salto in cartao["documental"]["evidence"]],
    }

    resumo = resumo_da_sugestao(cartao, documental)

    assert resumo["geracoes"] == 0
    assert resumo["codigo"] == JUNCAO_NAO_EVIDENCIADA
    assert "nenhum salto documentado" in resumo["aviso"]


def test_cadeia_que_cria_idade_impossivel_bloqueia(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 25)
    documental = json.loads(json.dumps(cartao["documental"]))
    a_up = documental["degrees"]["a_up"]
    # O salto documentado passa a ser 1920 → 1960 (40 anos, plausível); inserir as
    # 3 gerações do hiato daria 10 anos por geração. `plausible` fica False de
    # propósito: o portão que se testa aqui é o do TRECHO, não o da junção.
    documental["evidence"][a_up - 1]["parent_birth"] = "1920"

    resumo = resumo_da_sugestao(cartao, documental)

    assert resumo["geracoes"] == 0
    assert resumo["codigo"] == SUGESTAO_INSUFICIENTE
    assert "fora de 12–70" in resumo["aviso"]


def test_o_aviso_lista_todos_os_motivos_aplicaveis(tmp_path):
    cartao = _comparacao(tmp_path, GED_SALTO_IMPOSSIVEL, 25)
    inconclusivo = {**cartao, "status": INCONCLUSIVO}

    resumo = resumo_da_sugestao(inconclusivo, cartao["documental"],
                                identidade="a_confirmar")

    assert "o veredito é INCONCLUSIVO" in resumo["aviso"]
    assert "identidade do match" in resumo["aviso"]

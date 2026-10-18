"""Testes unitários da cirurgia do grafo.

Cobrem as seis funções públicas de `core.cirurgia_do_grafo` sobre GEDCOM sintético:
identificar o ramo protegido, localizar a junção, desacoplar sem tocar no original,
injetar as gerações virtuais e verificar o ramo depois da cirurgia.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.cirurgia_do_grafo import (  # noqa: E402
    AFINIDADE_NAO_INJETAVEL,
    JUNCAO_NAO_LOCALIZADA,
    LADO_DOADOR,
    LADO_MATCH,
    TIPO_FAMILIA_VIRTUAL,
    TIPO_VIRTUAL,
    desacoplar_identidade,
    injetar_geracoes,
    juncao,
    ramo_base,
    ramo_base_intacto,
)
from core.documentary_relationship import documentary_relationship  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from tests.fixtures.arvore_para_cirurgia import (  # noqa: E402
    GED_DOIS_LADOS,
    GED_SALTO_IMPOSSIVEL,
)


def _arvore(tmp_path, ged=GED_SALTO_IMPOSSIVEL):
    caminho = tmp_path / "arvore.ged"
    caminho.write_text(ged, encoding="utf-8")
    return carregar_arvore(str(caminho))


# ---------------------------------------------------------------------------
# ramo_base
# ---------------------------------------------------------------------------

def test_ramo_base_na_ordem_do_caminho_e_sem_a_juncao(tmp_path):
    arvore = _arvore(tmp_path)
    documental = documentary_relationship(arvore, "@I1@", "@I4@")
    caminho = documental["path"]["ids"]
    juncoes, avisos = juncao(arvore, documental)

    assert avisos == []
    ramo = ramo_base(arvore, "@I1@", "@I10@", caminho, juncao=juncoes[0])

    # A ordem é a do caminho, com as famílias intercaladas.
    assert ramo["ids"] == ["@I1@", "@F1@", "@I2@", "@F2@", "@I10@"]
    # A aresta da junção é justamente a que a cirurgia vai remover: fica fora.
    assert ("@F2@", "@I10@") not in ramo["arestas"]
    # As arestas saem em par ordenado: a família (@F...) vem antes da pessoa (@I...).
    assert ("@F1@", "@I1@") in ramo["arestas"]
    assert ramo["indice_ancestral"] == 2
    assert ramo["ancestral_id"] == "@I10@"


def test_ramo_base_sem_caminho_devolve_conjunto_vazio(tmp_path):
    arvore = _arvore(tmp_path)
    ramo = ramo_base(arvore, "@I1@", "@I10@", [])
    assert ramo["ids"] == []
    assert ramo["arestas"] == []


def test_ramo_base_intacto_quando_nada_muda(tmp_path):
    arvore = _arvore(tmp_path)
    documental = documentary_relationship(arvore, "@I1@", "@I4@")
    caminho = documental["path"]["ids"]
    juncoes, _ = juncao(arvore, documental)
    ramo = ramo_base(arvore, "@I1@", "@I10@", caminho, juncao=juncoes[0])

    copia = arvore[2].copy()
    copia.remove_edge(*juncoes[0]["aresta_removida"])

    assert ramo_base_intacto(arvore[2], copia, ramo) == []


def test_ramo_base_intacto_acusa_aresta_interna_removida(tmp_path):
    arvore = _arvore(tmp_path)
    documental = documentary_relationship(arvore, "@I1@", "@I4@")
    caminho = documental["path"]["ids"]
    juncoes, _ = juncao(arvore, documental)
    ramo = ramo_base(arvore, "@I1@", "@I10@", caminho, juncao=juncoes[0])

    copia = arvore[2].copy()
    copia.remove_edge("@I1@", "@F1@")

    violacoes = ramo_base_intacto(arvore[2], copia, ramo)
    assert [item["id"] for item in violacoes] == ["@F1@--@I1@"]


def test_ramo_base_intacto_acusa_atributo_alterado(tmp_path):
    arvore = _arvore(tmp_path)
    documental = documentary_relationship(arvore, "@I1@", "@I4@")
    caminho = documental["path"]["ids"]
    juncoes, _ = juncao(arvore, documental)
    ramo = ramo_base(arvore, "@I1@", "@I10@", caminho, juncao=juncoes[0])

    copia = arvore[2].copy()
    copia.nodes["@I2@"]["label"] = "Outro Nome"

    violacoes = ramo_base_intacto(arvore[2], copia, ramo)
    assert violacoes == [{"id": "@I2@", "motivo": "atributos do nó mudaram"}]


# ---------------------------------------------------------------------------
# juncao
# ---------------------------------------------------------------------------

def test_juncao_localiza_pelo_famc_do_filho(tmp_path):
    arvore = _arvore(tmp_path)
    documental = documentary_relationship(arvore, "@I1@", "@I4@")
    juncoes, avisos = juncao(arvore, documental)

    assert avisos == []
    assert len(juncoes) == 1
    dados = juncoes[0]
    assert dados["familia_id"] == "@F2@"
    assert dados["pai_id"] == "@I10@"
    assert dados["filho_id"] == "@I2@"
    assert dados["lado"] == LADO_DOADOR
    assert dados["aresta_removida"] == ("@F2@", "@I10@")


def test_juncao_sem_caminho_devolve_aviso(tmp_path):
    arvore = _arvore(tmp_path)
    documental = {"path": {"ids": []}, "common_ancestor": None, "evidence": []}
    juncoes, avisos = juncao(arvore, documental)
    assert juncoes == []
    assert avisos[0]["codigo"] == "SEM_CAMINHO_DOCUMENTAL"


def test_juncao_nao_localizada_quando_o_salto_nao_tem_familia(tmp_path):
    arvore = _arvore(tmp_path)
    documental = {
        "path": {"ids": ["@I1@", "@I4@", "@I10@"]},
        "common_ancestor": {"id": "@I10@"},
        "evidence": [],
    }
    juncoes, avisos = juncao(arvore, documental)
    assert juncoes == []
    assert avisos[0]["codigo"] == JUNCAO_NAO_LOCALIZADA


def test_juncao_dois_lados_quando_as_familias_diferem(tmp_path):
    arvore = _arvore(tmp_path, GED_DOIS_LADOS)
    documental = documentary_relationship(arvore, "@I1@", "@I13@")
    juncoes, avisos = juncao(arvore, documental)

    assert avisos == []
    assert [item["lado"] for item in juncoes] == [LADO_DOADOR, LADO_MATCH]
    assert {item["familia_id"] for item in juncoes} == {"@F2@", "@F4@"}


# ---------------------------------------------------------------------------
# desacoplar_identidade
# ---------------------------------------------------------------------------

def test_desacoplar_remove_a_aresta_so_na_copia(tmp_path):
    arvore = _arvore(tmp_path)
    documental = documentary_relationship(arvore, "@I1@", "@I4@")
    juncoes, _ = juncao(arvore, documental)
    dados = juncoes[0]

    sugerida, avisos = desacoplar_identidade(arvore, dados)

    assert avisos == []
    assert sugerida is not None
    assert not sugerida.has_edge(dados["familia_id"], dados["pai_id"])
    # O original continua com a aresta — a cirurgia não muta a árvore recebida.
    assert arvore[2].has_edge(dados["familia_id"], dados["pai_id"])
    # O registro histórico permanece, com as outras arestas dele.
    assert "@I10@" in sugerida
    assert sugerida.has_edge("@I10@", "@F2@") is False
    assert sugerida.degree("@I10@") == 0


def test_desacoplar_recusa_aresta_de_casamento(tmp_path):
    arvore = _arvore(tmp_path)
    # @I2@ e @I3@ são cônjuges em @F1@; @I3@ não é CHIL da família.
    dados = {"familia_id": "@F1@", "pai_id": "@I2@", "filho_id": "@I3@",
             "lado": LADO_DOADOR, "aresta_removida": ("@F1@", "@I2@")}

    sugerida, avisos = desacoplar_identidade(arvore, dados)

    assert sugerida is None
    assert avisos[0]["codigo"] == AFINIDADE_NAO_INJETAVEL
    assert arvore[2].has_edge("@F1@", "@I2@")


def test_desacoplar_recusa_juncao_incompleta(tmp_path):
    arvore = _arvore(tmp_path)
    sugerida, avisos = desacoplar_identidade(arvore, {"familia_id": "@F2@"})
    assert sugerida is None
    assert avisos[0]["codigo"] == JUNCAO_NAO_LOCALIZADA


# ---------------------------------------------------------------------------
# injetar_geracoes
# ---------------------------------------------------------------------------

def test_injetar_cria_cadeia_de_nos_virtuais(tmp_path):
    arvore = _arvore(tmp_path)
    documental = documentary_relationship(arvore, "@I1@", "@I4@")
    juncoes, _ = juncao(arvore, documental)
    dados = juncoes[0]
    grafo = arvore[2].copy()
    grafo.remove_edge(*dados["aresta_removida"])

    resultado = injetar_geracoes(grafo, dados, 3, doador_id="@I1@",
                                 nasc_ancestral=1650, nasc_filho=1960, intervalo=25)

    rotulos = [item["label"] for item in resultado["geracoes_virtuais"]]
    assert rotulos == ["Geração 1", "Geração 2", "Geração 3"]
    assert len(resultado["familias_virtuais"]) == 3
    for pessoa_id in resultado["nos_adicionados"]:
        assert pessoa_id in grafo
    assert grafo.nodes[resultado["geracoes_virtuais"][0]["id"]]["type"] == TIPO_VIRTUAL
    assert grafo.nodes[resultado["familias_virtuais"][0]]["type"] == TIPO_FAMILIA_VIRTUAL
    # A cadeia terminou na família de origem, que continua no lugar.
    assert grafo.has_edge(resultado["geracoes_virtuais"][-1]["id"], "@F2@")


def test_injetar_zero_nao_altera_o_grafo(tmp_path):
    arvore = _arvore(tmp_path)
    documental = documentary_relationship(arvore, "@I1@", "@I4@")
    juncoes, _ = juncao(arvore, documental)
    grafo = arvore[2].copy()
    antes = (sorted(grafo.nodes()), sorted(grafo.edges()))

    resultado = injetar_geracoes(grafo, juncoes[0], 0, doador_id="@I1@")

    assert resultado["geracoes_virtuais"] == []
    assert (sorted(grafo.nodes()), sorted(grafo.edges())) == antes


def test_no_virtual_nao_fabrica_pessoa(tmp_path):
    arvore = _arvore(tmp_path)
    documental = documentary_relationship(arvore, "@I1@", "@I4@")
    juncoes, _ = juncao(arvore, documental)
    grafo = arvore[2].copy()
    grafo.remove_edge(*juncoes[0]["aresta_removida"])

    resultado = injetar_geracoes(grafo, juncoes[0], 2, doador_id="@I1@",
                                 nasc_ancestral=1650, nasc_filho=1960, intervalo=25)

    for geracao in resultado["geracoes_virtuais"]:
        atributos = grafo.nodes[geracao["id"]]
        assert "name" not in atributos
        assert "birth" not in atributos
        assert "sex" not in atributos
        assert atributos["origem"] == "estimado"
        assert atributos["justificativa"]
        assert set(atributos["nascimento_estimado"]) == {"ano_min", "ano_max"}


def test_ids_sao_deterministicos(tmp_path):
    arvore = _arvore(tmp_path)
    documental = documentary_relationship(arvore, "@I1@", "@I4@")
    juncoes, _ = juncao(arvore, documental)

    primeiro = injetar_geracoes(arvore[2].copy(), juncoes[0], 2, doador_id="@I1@")
    segundo = injetar_geracoes(arvore[2].copy(), juncoes[0], 2, doador_id="@I1@")

    assert primeiro["nos_adicionados"] == segundo["nos_adicionados"]
    # O id vem do conteúdo, não de memória: nada de hexadecimal de endereço.
    assert primeiro["nos_adicionados"][0] == "VIRTUAL:@I1@:@I10@:doador:1"

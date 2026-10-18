"""Sugestão sintética para os testes do renderizador.

Independente da feature `029`: monta à mão o dicionário que `arvore_sugerida` devolveria,
para que o teste do desenho não dependa da cirurgia nem da validação. O cenário é o do
requirements: doador vivo (1985), ancestral em 1650, duas gerações documentadas e duas
gerações virtuais sugeridas.

    @I1@ Doador (1985)
      └─ @F1@ ─ @I2@ Pai (1960)
                  └─ @F2@ ─ @I10@ Ancestral (1650)
                              └─ @I4@ Primo (1710)

    @I5@ Irmão (1965) fica FORA do caminho: serve para provar que o recorte não o desenha.

As funções devolvem estruturas novas a cada chamada — um `nx.Graph` compartilhado entre
testes seria mutado por um e lido pelo outro.
"""
from __future__ import annotations

import networkx as nx

DOADOR_ID = "@I1@"
PAI_ID = "@I2@"
ANCESTRAL_ID = "@I10@"
MATCH_ID = "@I4@"
IRMAO_ID = "@I5@"
FAMILIA_JUNCAO = "@F2@"
FAMILIA_DOADOR = "@F1@"
FAMILIA_IRMAO = "@F3@"

VIRTUAL_1 = f"VIRTUAL:{DOADOR_ID}:{ANCESTRAL_ID}:doador:1"
VIRTUAL_2 = f"VIRTUAL:{DOADOR_ID}:{ANCESTRAL_ID}:doador:2"


def grafo() -> nx.Graph:
    """O grafo sugerido, como a `029` o devolveria (bipartido pessoa↔família)."""
    g = nx.Graph()
    g.add_node(DOADOR_ID, label="Doador Sintetico", type="person")
    g.add_node(PAI_ID, label="Pai Sintetico", type="person")
    g.add_node(ANCESTRAL_ID, label="Ancestral Sintetico", type="person")
    g.add_node(MATCH_ID, label="Primo Sintetico", type="person")
    g.add_node(IRMAO_ID, label="Irmão Sintetico", type="person")
    g.add_node(FAMILIA_DOADOR, label="Familia", type="family")
    g.add_node(FAMILIA_JUNCAO, label="Familia", type="family")
    g.add_node(FAMILIA_IRMAO, label="Familia", type="family")

    g.add_edge(DOADOR_ID, FAMILIA_DOADOR)
    g.add_edge(PAI_ID, FAMILIA_DOADOR)
    g.add_edge(PAI_ID, FAMILIA_JUNCAO)
    g.add_edge(ANCESTRAL_ID, FAMILIA_JUNCAO)
    g.add_edge(IRMAO_ID, FAMILIA_JUNCAO)
    g.add_edge(MATCH_ID, FAMILIA_IRMAO)
    g.add_edge(IRMAO_ID, FAMILIA_IRMAO)

    # A cadeia sugerida já existe no grafo da 029; aqui também, para o caso "grafo real".
    g.add_node(VIRTUAL_1, label="Geração 1", type="virtual",
               origem="estimado", justificativa="posição estimada",
               nascimento_estimado={"ano_min": 1630, "ano_max": 1690})
    g.add_node(VIRTUAL_2, label="Geração 2", type="virtual",
               origem="estimado", justificativa="posição estimada",
               nascimento_estimado={"ano_min": 1720, "ano_max": 1780})
    g.add_edge(ANCESTRAL_ID, VIRTUAL_1)
    g.add_edge(VIRTUAL_1, VIRTUAL_2)
    g.add_edge(VIRTUAL_2, PAI_ID)
    return g


def geracoes_virtuais() -> list:
    return [
        {"id": VIRTUAL_1, "label": "Geração 1", "lado": "doador", "ordem": 1,
         "nascimento_estimado": {"ano_min": 1630, "ano_max": 1690}},
        {"id": VIRTUAL_2, "label": "Geração 2", "lado": "doador", "ordem": 2,
         "nascimento_estimado": {"ano_min": 1720, "ano_max": 1780}},
    ]


def sugestao() -> dict:
    """O contrato de §4.7 da `029`, sem o grafo original."""
    return {
        "natureza": "sugestao",
        "status_origem": "ERRO CRONICO / QUEBRA DE LINHA",
        "grafo": grafo(),
        "doador": {"id": DOADOR_ID, "nome": "Doador Sintetico"},
        "ancestral": {"id": ANCESTRAL_ID, "nome": "Ancestral Sintetico", "ano": 1650},
        "juncao": {"familia_id": FAMILIA_JUNCAO, "pai_id": ANCESTRAL_ID,
                   "filho_id": PAI_ID, "lado": "doador",
                   "aresta_removida": (FAMILIA_JUNCAO, ANCESTRAL_ID)},
        "juncoes": [{"familia_id": FAMILIA_JUNCAO, "pai_id": ANCESTRAL_ID,
                     "filho_id": PAI_ID, "lado": "doador",
                     "aresta_removida": (FAMILIA_JUNCAO, ANCESTRAL_ID)}],
        "hiato": {"calculado": 2, "aplicado": 2,
                  "por_lado": {"doador": 2, "match": 0}},
        "geracoes_virtuais": geracoes_virtuais(),
        "familias_virtuais": [],
        "nos_adicionados": [VIRTUAL_1, VIRTUAL_2],
        "arestas_adicionadas": [],
        "arestas_removidas": [(FAMILIA_JUNCAO, ANCESTRAL_ID)],
        "ramo_base": {"ids": [DOADOR_ID, FAMILIA_DOADOR, PAI_ID],
                      "pessoas": [DOADOR_ID, PAI_ID, ANCESTRAL_ID],
                      "familias": [FAMILIA_DOADOR], "arestas": [],
                      "ancestral_id": ANCESTRAL_ID, "indice_ancestral": 2,
                      "intacto": True},
        "justificativa": "duas gerações inseridas na junção",
        "avisos": [],
    }


def documental() -> dict:
    """O parentesco documental: caminho ordenado doador → ancestral → match."""
    return {
        "status": "found",
        "path": {"ids": [DOADOR_ID, PAI_ID, ANCESTRAL_ID, MATCH_ID],
                 "names": ["Doador Sintetico", "Pai Sintetico",
                           "Ancestral Sintetico", "Primo Sintetico"]},
        "common_ancestor": {"id": ANCESTRAL_ID, "name": "Ancestral Sintetico",
                            "birth": "1650"},
        "degrees": {"a_up": 2, "b_up": 1},
        "meioses": 3,
        "person_a": {"id": DOADOR_ID, "name": "Doador Sintetico", "birth_year": 1985},
        "person_b": {"id": MATCH_ID, "name": "Primo Sintetico", "birth_year": 1710},
        "evidence": [
            {"child_id": DOADOR_ID, "parent_id": PAI_ID, "plausible": True},
            {"child_id": PAI_ID, "parent_id": ANCESTRAL_ID, "plausible": False},
            {"child_id": MATCH_ID, "parent_id": ANCESTRAL_ID, "plausible": True},
        ],
        "ambiguous_identity": False,
    }


def resultado(cm=21.6, geracoes=5.7,
              codigo="PROFUNDIDADE_TEMPORAL_INCOMPATIVEL") -> dict:
    """O contrato de §4.5 da `028`."""
    return {
        "status": "ERRO CRONICO / QUEBRA DE LINHA",
        "motivo": "Linha documental inviável.",
        "codigos": [{"codigo": codigo, "severidade": "critico",
                     "mensagem": "fora da janela"}],
        "kit": "AB1234567",
        "cm": cm,
        "mrca_estimado": {"ano": 1660, "ano_min": 1600, "ano_max": 1720,
                          "geracoes": geracoes, "metodo": "scp40:mediana"},
        "mrca_documentado": {"id": ANCESTRAL_ID, "nome": "Ancestral Sintetico",
                             "ano": 1650, "impreciso": False},
        "geracoes_documentais": {"doador": 2, "match": 1, "total": 3},
        "comparacao_existente": "CONFLITANTE",
    }

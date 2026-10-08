"""Projecao do resultado da analise no payload da porta (`D-15`).

Este arquivo existe por um achado da auditoria de 2026-10-08: o `B003` registrou
que a projecao era a unica parte central da feature **sem teste que rodasse sem
banco**. Ela e **pura** — le o que o nucleo devolveu e nada mais —, entao nao ha
razao para depender de `DATABASE_URL` para exercita-la.

O que ele prende, e por que cada um importa:

- **a ordem**: `result_ordinal` e a posicao na ordem APRESENTADA, e a projecao nao
  reordena (`RN-08`, `E-01` — "ordem e dado, nao consequencia");
- **dois kits nao se somam**: cada kit leva o cM DELE (`RF-05`), e o pareamento com
  o veredito e por indice, nao por rotulo — dois kits de mesmo nome nao confundem;
- **o estado da conexao e o do confronto**: a projecao nao recalcula a juncao
  conservadora, ela transporta (`RN-06`);
- **`completa` distingue ficha de identificacao**: a raiz e o match vem inteiros, os
  nos do caminho vem so com `id` e `nome` (`D-15`);
- **ausente e `None`, nunca zero** (`RN-11`);
- **o cM nao e recalculado** (`RN-05`, `RISK-004`).
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from application.dna_analysis import projetar_analise  # noqa: E402


def _resultado(**ajustes) -> dict:
    """Resultado sintetico com a MESMA forma que `core.dna_analysis` devolve.

    O formato nao e inventado aqui: cada chave corresponde a um campo que o fluxo
    do nucleo realmente produz, e o teste acompanha o formato de proposito — se o
    nucleo mudar a saida, este arquivo deixa de refletir a realidade e falha.
    """
    base = {
        "match_name": "Ana Silva Souza",
        "csv_name": "Ana Silva Souza",
        "cm": 200.0,
        "kit": "KIT-A",
        "text_path": "Carlos → Joaquim → Ana",
        "mermaid_data": None,
        "documentary": {
            "status": "found",
            "source": "GEDCOM",
            "label": "Irmãos",
            "relationship_key": "SIBLINGS",
            "meioses": 2,
            "person_a": {"id": "I12", "name": "Carlos Silva Souza", "sex": "M",
                         "birth": "1980", "birth_place": "Recife", "death": None},
            "person_b": {"id": "I13", "name": "Ana Silva Souza", "sex": "F",
                         "birth": None, "birth_place": None, "death": None},
            "common_ancestor": {"id": "I10", "name": "Joaquim Silva", "birth": "1950"},
            "path": {"ids": ["I12", "I10", "I13"],
                     "names": ["Carlos Silva Souza", "Joaquim Silva", "Ana Silva Souza"]},
            "warnings": [],
        },
        "genetic_evidence": {
            "available": True,
            "source": "GEDmatch",
            "kits": [
                {"kit": "KIT-A", "source": "GEDmatch", "total_cm": 200.0,
                 "segment_count": 3, "largest_segment_cm": 120.0},
                {"kit": "KIT-B", "source": "MyHeritage", "total_cm": 60.0,
                 "segment_count": 1, "largest_segment_cm": 60.0},
            ],
            "totals": {"cm": None, "cm_por_kit": {"KIT-A": 200.0, "KIT-B": 60.0}},
        },
        "hypotheses": [],
        "comparison": {
            "status": "CONFLITANTE",
            "label": "Conflitante",
            "message": "Conflitante: ...",
            "causes": ["colapso de pedigree", "endogamia"],
            "per_kit": [
                {"kit": "KIT-A", "status": "COMPATIVEL", "cm": 200.0, "note": "dentro"},
                {"kit": "KIT-B", "status": "CONFLITANTE", "cm": 60.0, "note": "fora"},
            ],
            "method": "scp40:Siblings",
            "expected_range": {"low": 1613, "high": 3488, "average": 2613},
            "detail": "Parentesco documental: Irmãos (2 meioses).",
            "observations": ["aviso do arquivo"],
        },
        "observations": ["aviso do arquivo"],
        "warnings": [],
    }
    base.update(ajustes)
    return base


def _projetar(resultados, descartados=()):
    return projetar_analise(
        resultados, list(descartados), "2 conexões encontradas. 1 descartada.",
        "abc123__arvore.ged", "def456__matches.csv", "Carlos Silva Souza",
    )


def test_ordem_preservada_e_nao_reordenada():
    """`result_ordinal` e a posicao recebida — a ordem e dado, e nao consequencia."""
    entradas = [_resultado(csv_name=f"Pessoa {i}", cm=cm)
                for i, cm in enumerate([10.0, 900.0, 400.0])]
    analise = _projetar(entradas)

    assert [c.ordinal for c in analise.conexoes] == [0, 1, 2]
    assert [c.csv_name for c in analise.conexoes] == ["Pessoa 0", "Pessoa 1", "Pessoa 2"]
    assert [c.total_cm for c in analise.conexoes] == [10.0, 900.0, 400.0], (
        "a projecao reordenou por cM — a ordem de apresentacao e do nucleo"
    )


def test_a_projecao_suporta_varios_kits_numa_conexao_sem_somar():
    """Defensivo: o payload aceita N kits, e nenhum total e somado.

    ⚠️ **Esta NAO e a forma que o fluxo de DNA produz hoje.** `core.dna_analysis`
    chama `evidence_for(por_kit, kit_key=chave_kit)`, e com o `kit_key` a evidencia
    traz **um** kit. O caso de "dois kits do mesmo nome" chega como **duas
    conexoes**, e nao como uma conexao com dois kits — e e o teste seguinte que o
    prende.

    Este aqui existe porque a projecao **nao pode** depender de N ser sempre 1: se o
    nucleo passar a agrupar kits numa conexao, o pareamento por indice e a ausencia
    de soma tem de continuar valendo.
    """
    resultado = _resultado()
    resultado["genetic_evidence"]["kits"][0]["kit"] = "MESMO"
    resultado["genetic_evidence"]["kits"][1]["kit"] = "MESMO"

    kits = _projetar([resultado]).conexoes[0].kits

    assert len(kits) == 2, "dois kits viraram um"
    assert [k.total_cm for k in kits] == [200.0, 60.0], (
        "os cM dos kits foram somados ou trocados — o pareamento por indice quebrou"
    )
    assert [k.ordinal for k in kits] == [0, 1]
    assert 260.0 not in [k.total_cm for k in kits], "apareceu a soma dos dois kits"


def test_dois_kits_do_mesmo_nome_chegam_como_duas_conexoes():
    """O caso **real** do `RF-05`: duas conexoes, um kit cada, e nenhuma soma.

    A chave da evidencia e `(nome do CSV, kit)`, entao dois kits do mesmo nome sao
    duas evidencias e viram **duas** conexoes. Cada uma leva o cM do SEU kit, e
    "nenhum total somado entre eles" e satisfeito por construcao — a soma nao
    existe em lugar nenhum.
    """
    primeira = _resultado(cm=200.0)
    primeira["genetic_evidence"]["kits"] = [primeira["genetic_evidence"]["kits"][0]]
    primeira["comparison"] = dict(primeira["comparison"], status="COMPATIVEL",
                                  per_kit=[primeira["comparison"]["per_kit"][0]])
    segunda = _resultado(cm=60.0)
    segunda["genetic_evidence"] = dict(segunda["genetic_evidence"],
                                       kits=[segunda["genetic_evidence"]["kits"][1]])
    segunda["comparison"] = dict(segunda["comparison"], status="CONFLITANTE",
                                 per_kit=[segunda["comparison"]["per_kit"][1]])

    conexoes = _projetar([primeira, segunda]).conexoes

    assert len(conexoes) == 2, "dois kits do mesmo nome nao viraram duas conexoes"
    assert [len(c.kits) for c in conexoes] == [1, 1]
    assert [c.kits[0].total_cm for c in conexoes] == [200.0, 60.0], "someou ou trocou os cM"
    assert [c.comparison_status for c in conexoes] == ["COMPATIVEL", "CONFLITANTE"], (
        "os estados das duas conexoes foram colapsados num so"
    )
    todos = [c.total_cm for c in conexoes] + [c.kits[0].total_cm for c in conexoes]
    assert 260.0 not in todos, "apareceu a soma dos dois kits em algum lugar"


def test_estado_da_conexao_e_o_do_confronto_e_o_por_kit_e_individual():
    """`RN-06`: a juncao conservadora e transportada, e cada kit guarda o seu estado."""
    conexao = _projetar([_resultado()]).conexoes[0]

    assert conexao.comparison_status == "CONFLITANTE", "o estado final nao veio do confronto"
    assert conexao.comparison_label == "Conflitante"
    assert [k.status for k in conexao.kits] == ["COMPATIVEL", "CONFLITANTE"], (
        "os estados por kit foram colapsados no estado final"
    )
    assert conexao.comparison_method == "scp40:Siblings"
    assert (conexao.expected_low, conexao.expected_high) == (1613, 3488)


def test_per_kit_vazio_herda_o_estado_final_sem_inventar_por_kit():
    """Confronto que termina antes de avaliar kit por kit: o kit herda o estado final."""
    resultado = _resultado()
    resultado["comparison"] = dict(resultado["comparison"], status="INCONCLUSIVO",
                                   label="Inconclusivo", per_kit=[])

    kits = _projetar([resultado]).conexoes[0].kits

    assert [k.status for k in kits] == ["INCONCLUSIVO", "INCONCLUSIVO"]
    assert [k.status_note for k in kits] == [None, None], (
        "apareceu justificativa por kit onde nao houve avaliacao por kit"
    )


def test_pessoas_deduplicadas_e_completa_distingue_ficha_de_identificacao():
    """`RF-04`/`D-15`: a ficha inteira vence, e o no do caminho fica identificado."""
    analise = _projetar([_resultado()])
    por_xref = {p.xref: p for p in analise.pessoas}

    assert set(por_xref) == {"I12", "I13", "I10"}, "faltou ou sobrou pessoa no retrato"
    assert analise.root_person_xref == "I12", "a raiz nao veio de `documentary.person_a`"

    assert por_xref["I12"].completa is True and por_xref["I12"].sexo == "M"
    assert por_xref["I12"].local_nascimento == "Recife"
    assert por_xref["I13"].completa is True
    assert por_xref["I13"].nascimento is None, "ausente virou valor"
    assert por_xref["I10"].completa is False, (
        "o no do caminho foi gravado como ficha completa — o nucleo nao o entrega assim"
    )
    assert por_xref["I10"].nome == "Joaquim Silva", "o nome do caminho se perdeu"


def test_ficha_incompleta_nao_apaga_a_completa_de_outra_conexao():
    """A mesma pessoa pode ser o match de uma conexao e no de caminho de outra."""
    primeira = _resultado()
    segunda = _resultado(csv_name="Outro")
    segunda["documentary"] = dict(segunda["documentary"],
                                  person_b={"id": "I10", "name": "Joaquim Silva",
                                            "sex": "M", "birth": "1950",
                                            "birth_place": "Olinda", "death": None})

    por_xref = {p.xref: p for p in _projetar([primeira, segunda]).pessoas}

    assert por_xref["I10"].completa is True, "a versao incompleta sobrescreveu a completa"
    assert por_xref["I10"].local_nascimento == "Olinda"


def test_papeis_do_caminho_saem_do_ancestral_comum():
    """O papel e derivado do divisor, e nao lido — o nucleo nao o entrega."""
    caminho = _projetar([_resultado()]).conexoes[0].caminho

    assert caminho == (("I12", "ascendente"), ("I10", "ascendente"),
                       ("I13", "descendente")), caminho
    assert all(papel in ("ascendente", "descendente") for _, papel in caminho), (
        "apareceu `afinidade`: quem a atribui e `path_search.py`, nao o fluxo de DNA"
    )


def test_recuo_quando_o_ancestral_comum_nao_esta_no_caminho():
    """O recuo e declarado: o corte cai no penultimo no, porque o ultimo e alcancado."""
    resultado = _resultado()
    resultado["documentary"] = dict(resultado["documentary"],
                                    common_ancestor={"id": "I99", "name": "Fora do caminho"})

    caminho = _projetar([resultado]).conexoes[0].caminho

    assert caminho == (("I12", "ascendente"), ("I10", "ascendente"),
                       ("I13", "descendente")), caminho


def test_sem_caminho_nao_inventa_papel():
    """Sem caminho documental, `caminho` e vazio — e nao uma lista de um no so."""
    resultado = _resultado()
    resultado["documentary"] = dict(resultado["documentary"], path={"ids": [], "names": []})

    assert _projetar([resultado]).conexoes[0].caminho == ()


def test_ausente_e_none_e_nunca_zero():
    """`RN-11`: `None` significa "nao sei / nao existe", e atravessa a persistencia."""
    resultado = _resultado()
    resultado["cm"] = None
    resultado["documentary"] = dict(resultado["documentary"], meioses=None,
                                    common_ancestor=None, relationship_key=None)
    resultado["comparison"] = dict(resultado["comparison"], method=None,
                                   expected_range=None, causes=None)
    resultado["observations"] = None

    conexao = _projetar([resultado]).conexoes[0]

    assert conexao.total_cm is None and conexao.total_cm != 0
    assert conexao.meioses is None
    assert conexao.mrca_xref is None
    assert conexao.comparison_method is None
    assert conexao.expected_low is None
    assert conexao.causes == () and conexao.observations == ()


def test_projecao_nao_recalcula_o_cm():
    """`RN-05`/`RISK-004`: o cM e transportado, nunca reagregado."""
    resultado = _resultado()
    resultado["cm"] = 46.0                      # valor de FRONTEIRA de faixa
    resultado["genetic_evidence"]["kits"][0]["total_cm"] = 46.0
    resultado["comparison"]["per_kit"][0]["cm"] = 46.0

    conexao = _projetar([resultado]).conexoes[0]

    assert conexao.total_cm == 46.0
    assert conexao.kits[0].total_cm == 46.0


def test_descartados_levam_o_motivo_do_nucleo_sem_virar_codigo():
    """`RN-07`: o motivo e o texto do nucleo, e nao um codigo inventado aqui."""
    analise = _projetar([], descartados=[
        {"csv_name": "Zzz Ninguem", "kit": None, "cm": 150.0, "motivo": "não encontrado"},
    ])

    assert analise.skipped_count == 1
    assert analise.descartados[0].reason == "não encontrado"
    assert analise.descartados[0].ordinal == 0
    assert analise.descartados[0].kit is None


def test_analise_sem_conexao_aceita_ainda_guarda_a_mensagem_e_a_contagem():
    """Analise sem resultado aceito nao vira analise vazia de significado."""
    analise = _projetar([], descartados=[
        {"csv_name": "A", "kit": "K", "cm": 1.0, "motivo": "não encontrado"},
        {"csv_name": "B", "kit": "K", "cm": 2.0, "motivo": "não encontrado"},
    ])

    assert analise.accepted_count == 0
    assert analise.skipped_count == 2
    assert analise.root_person_xref is None, "a raiz apareceu sem nenhuma conexao"
    assert analise.message.endswith("1 descartada."), "a mensagem de contrato foi reescrita"

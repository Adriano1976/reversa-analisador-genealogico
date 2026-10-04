"""Tarefa 03 — Busca de Caminho (parentesco documental).

Resolucao de pessoa por nome, conexao direta por ancestral comum (BFS
bidirecional, prof. max. 20) e fallback de conexao indireta por afinidade
(`shortest_path`, max. 40 hops) com compressao de nos de familia. Renderiza
caminho textual + diagrama Mermaid.

## Regra do projeto

Esta busca e **documental**: ela responde o que o GEDCOM afirma, e nada mais.
Nao existe DNA nesta tela. O parentesco sai de `core.documentary_relationship`,
que tambem entrega homonimos, caminhos multiplos, colapso de pedigree e a
evidencia de cada salto (inclusive datas cronologicamente impossiveis).

A conexao **indireta** (por casamento) nunca e apresentada como parentesco
consanguineo: ela vem marcada como afinidade, com aviso proprio.

Comportamento herdado preservado: homonimos ainda usam o 1o ID, mas agora a
escolha e **explicitada** no resultado (`homonyms`, aviso de identidade ambigua),
e nao mais silenciosa. Ver a regra de homonimos da nova regra de analise.


## Layout (OPP-20260929-UXEF)

Este modulo passou a compor o fluxo. As responsabilidades foram separadas em
`family_navigation` (parentesco), `path_finding` (os dois algoritmos de busca) e
`mermaid_render` (o diagrama e o escape do rotulo). A direcao das dependencias e
estritamente descendente, sem ciclo e sem import tardio novo.

## Superficie de compatibilidade

O bloco de reexportacao no fim do arquivo existe porque consumidores externos
importam nomes daqui: `app.py`, `core/dna_analysis.py`,
`tests/test_path_search.py`, `tests/test_mermaid_escape.py`,
`tests/test_characterization_mermaid.py`, `_reversa_sdd/parity/harness.py` e as
sondas do BUG-20260929-J6PQ. Enquanto eles nao forem migrados, o bloco fica.
"""

from __future__ import annotations

from .documentary_relationship import documentary_relationship, homonym_dossier, person_summary
from .family_navigation import (
    are_spouses,
    exclude_tail,
    find_person_by_name,
    get_parents,
    get_spouses,
    pick_spouse_for_couple,
    split_path_by_marriage,
)
from reporting.mermaid_render import (
    _LABEL_SEGURO,
    _mermaid_label,
    _mermaid_sid,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)
from .path_finding import MAX_DEPTH, MAX_HOPS, find_ancestral_path, find_indirect_path
from .gedcom_state import get_name, people, ref_id

# `are_spouses`, `get_parents`, `get_spouses`, `pick_spouse_for_couple`,
# `split_path_by_marriage`, `exclude_tail`, `MAX_DEPTH`, `_mermaid_sid`,
# `_LABEL_SEGURO`, `_mermaid_label` e `ref_id` nao sao usados por `path_search`.
# Eles estao aqui pela superficie de compatibilidade declarada em `__all__`.

AVISO_AFINIDADE = ("O caminho exibido passa por casamento/afinidade, e não por ancestral comum: "
                   "ele NÃO representa parentesco consanguíneo.")

# Teto de combinacoes testadas quando ha homonimos dos dois lados. Existe para que
# um nome muito comum (dezenas de registros) nao transforme a busca em varredura.
LIMITE_DE_CANDIDATOS = 5


def _candidatos(nome, ids_do_legado):
    """Todo registro que pode ser a pessoa consultada, sem escolher por ninguem.

    `find_person_by_name` compara com acento, entao "Jose Vicente de Souza" (sem
    acento, como vem do CSV) nao encontra "José Vicente de Souza". O dossie
    compara com `normalizar` (sem acento) e por isso recupera os registros que so
    diferem na acentuacao — que sao exatamente os homonimos que a regra manda
    NAO escolher em silencio.
    """
    dossie = homonym_dossier(nome)
    ids_exatos = [ficha["id"] for ficha in dossie["exact_matches"]]
    candidatos = list(dict.fromkeys(list(ids_do_legado) + ids_exatos))
    parecidos = [pid for pid in candidatos if pid not in ids_exatos]
    dossie["similar_matches"] = [person_summary(pid) for pid in parecidos[:5]]
    dossie["similar_count"] = len(parecidos)
    return dossie, candidatos


def _homonimos(person1_name, person2_name, p1_ids, p2_ids):
    """Dossie de ambiguidade dos dois nomes, ou {} quando cada um e unico.

    O rotulo e a contagem falam apenas do lado ambiguo: misturar os dois lados
    faria a tabela de homonimos listar a propria pessoa 1 como se fosse
    homonima da pessoa 2.
    """
    dossie1, _ = _candidatos(person1_name, p1_ids)
    dossie2, _ = _candidatos(person2_name, p2_ids)
    ambiguos = [(nome, dossie) for nome, dossie in
                ((person1_name, dossie1), (person2_name, dossie2)) if dossie["ambiguous"]]
    if not ambiguos and not dossie1["similar_count"] and not dossie2["similar_count"]:
        return {}
    if ambiguos:
        alvo = " / ".join(nome for nome, _ in ambiguos)
        contagem = sum(dossie["exact_count"] for _, dossie in ambiguos)
        fichas = [ficha for _, dossie in ambiguos for ficha in dossie["exact_matches"]]
        diferencas = [item for _, dossie in ambiguos for item in dossie["differences"]]
    else:
        alvo = f"{person1_name} / {person2_name}"
        contagem = dossie1["exact_count"] + dossie2["exact_count"]
        fichas = dossie1["exact_matches"] + dossie2["exact_matches"]
        diferencas = []
    return {
        "query": alvo,
        "ambiguous": bool(ambiguos),
        "exact_count": contagem,
        "person1": dossie1,
        "person2": dossie2,
        "exact_matches": fichas,
        "differences": diferencas,
    }


def path_search(person1_name: str, person2_name: str):
    """Executa o fluxo completo de busca de caminho.

    Retorna `(path_result, msg, success)`. `path_result` é dict com
    `person1_name`, `person2_name`, `text_path`, `mermaid_data`, `documentary`
    (parentesco documental) e `observations`.
    """
    person1_name = person1_name.strip()
    person2_name = person2_name.strip()

    p1_ids = find_person_by_name(person1_name)
    p2_ids = find_person_by_name(person2_name)
    if not p1_ids:
        return None, f"Pessoa 1 '{person1_name}' não encontrada.", False
    if not p2_ids:
        return None, f"Pessoa 2 '{person2_name}' não encontrada.", False

    homonimos = _homonimos(person1_name, person2_name, p1_ids, p2_ids)

    # Com homonimos, a escolha do registro deixa de ser silenciosa E deixa de ser
    # a primeira da lista: as combinacoes sao testadas e vence a primeira que
    # tiver caminho. Medido no GEDCOM real: "Jose Vicente de Souza" tem tres
    # registros (dois so diferem no acento) e so um tem pais — antes, a tela
    # respondia "nenhuma conexao" para uma conexao que o GEDCOM contem.
    _, candidatos1 = _candidatos(person1_name, p1_ids)
    _, candidatos2 = _candidatos(person2_name, p2_ids)
    cache = {}
    p1_id = p2_id = documental = None
    for cand1 in candidatos1[:LIMITE_DE_CANDIDATOS]:
        for cand2 in candidatos2[:LIMITE_DE_CANDIDATOS]:
            if (cand1, cand2) not in cache:
                cache[(cand1, cand2)] = documentary_relationship(cand1, cand2, homonyms=homonimos)
            candidato = cache[(cand1, cand2)]
            if (candidato.get("path") or {}).get("ids"):
                p1_id, p2_id, documental = cand1, cand2, candidato
                break
        if documental is not None:
            break

    if documental is None:
        p1_id, p2_id = p1_ids[0], p2_ids[0]
        documental = cache.get((p1_id, p2_id)) or documentary_relationship(p1_id, p2_id, homonyms=homonimos)

    caminho = (documental.get("path") or {}).get("ids")
    observacoes = [aviso["message"] for aviso in documental.get("warnings") or []]

    if caminho:
        nomes = (documental.get("path") or {}).get("names") or []
        mermaid_data = generate_mermaid_graph(caminho, p1_id, p2_id,
                                             (documental.get("common_ancestor") or {}).get("id"))
        msg = "Conexão direta encontrada (ancestral comum)."
    else:
        person_path = find_indirect_path(p1_id, p2_id, max_hops=MAX_HOPS)
        if not person_path:
            return (None,
                    f"Nenhuma conexão encontrada entre '{person1_name}' e '{person2_name}'.",
                    True)
        nomes = [get_name(people[n]) for n in person_path]
        mermaid_data = generate_mermaid_graph_indirect_bridge(p1_id, p2_id, person_path)
        msg = "Conexão indireta encontrada (via casamento/afinidade)."
        documental = dict(documental)
        documental["status"] = "affinity"
        documental["label"] = "Sem ancestral comum: conexão por afinidade (casamento)"
        documental["affinity_path"] = {"ids": person_path, "names": nomes}
        documental["warnings"] = list(documental.get("warnings") or []) + [
            {"code": "afinidade", "message": AVISO_AFINIDADE}]
        observacoes.append(AVISO_AFINIDADE)

    path_result = {
        "person1_name": person1_name,
        "person2_name": person2_name,
        "text_path": " → ".join(nomes),
        "mermaid_data": mermaid_data,
        "documentary": documental,
        "observations": observacoes,
    }
    return path_result, msg, True


# ---------------------------------------------------------------------------
# Superficie de compatibilidade (ver a nota no docstring do modulo).
# Reexporta o que era definido aqui antes da OPP-20260929-UXEF. Os nomes
# privados do render entram porque `tests/test_mermaid_escape.py` e as sondas do
# BUG-20260929-J6PQ os importam deste modulo.
# ---------------------------------------------------------------------------
__all__ = [
    "path_search",
    "find_person_by_name", "get_parents", "get_spouses", "are_spouses",
    "split_path_by_marriage", "pick_spouse_for_couple", "exclude_tail",
    "MAX_DEPTH", "MAX_HOPS", "find_indirect_path", "find_ancestral_path",
    "_mermaid_sid", "_LABEL_SEGURO", "_mermaid_label",
    "generate_mermaid_graph", "generate_mermaid_graph_indirect_bridge",
    "ref_id",
]

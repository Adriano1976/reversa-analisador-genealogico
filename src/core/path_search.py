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

## Superficie publica (OPP-20261006-ESKO, 2026-10-06)

Este modulo define `path_search` e declara so ele em `__all__`. Ate 2026-10-06 havia
aqui um bloco que reexportava 17 nomes de `family_navigation`, `path_finding`,
`reporting.mermaid_render` e `gedcom_state`, justificado por uma lista de
consumidores que a varredura desmentiu: `app.py` importa apenas `path_search`, e
`core/dna_analysis.py` nao importa nada deste modulo. Os consumidores reais eram
`tests/test_path_search.py`, `tests/test_mermaid_escape.py` e
`_reversa_sdd/parity/harness.py`, todos migrados para o modulo canonico.
"""

from __future__ import annotations

from .diagram_domain import resolvedor_de_diagrama
from .documentary_relationship import documentary_relationship, homonym_dossier, person_summary
from .family_navigation import find_person_by_name
from .path_finding import MAX_HOPS, find_indirect_path
from .registro import get_name




# Bloco de reexportacao removido pela OPP-20261006-ESKO. Os 13 nomes que ficavam
# aqui nao eram usados por `path_search` e existiam so pela superficie de
# compatibilidade; os consumidores passaram a importar do modulo canonico:
#
#   tests/test_path_search.py      -> family_navigation e path_finding
#   tests/test_mermaid_escape.py   -> reporting.mermaid_render
#   _reversa_sdd/parity/harness.py -> family_navigation e path_finding
#   app.py, core/dna_analysis.py   -> nunca consumiram esta superficie
#
# `__all__` passa a declarar so o que o modulo define.

AVISO_AFINIDADE = ("O caminho exibido passa por casamento/afinidade, e não por ancestral comum: "
                   "ele NÃO representa parentesco consanguíneo.")

# Teto de combinacoes testadas quando ha homonimos dos dois lados. Existe para que
# um nome muito comum (dezenas de registros) nao transforme a busca em varredura.
LIMITE_DE_CANDIDATOS = 5


def _candidatos(arvore, nome, ids_do_legado):
    """Todo registro que pode ser a pessoa consultada, sem escolher por ninguem.

    `find_person_by_name` compara com acento, entao "Jose Vicente de Souza" (sem
    acento, como vem do CSV) nao encontra "José Vicente de Souza". O dossie
    compara com `normalizar` (sem acento) e por isso recupera os registros que so
    diferem na acentuacao — que sao exatamente os homonimos que a regra manda
    NAO escolher em silencio.
    """
    dossie = homonym_dossier(arvore, nome)
    ids_exatos = [ficha["id"] for ficha in dossie["exact_matches"]]
    candidatos = list(dict.fromkeys(list(ids_do_legado) + ids_exatos))
    parecidos = [pid for pid in candidatos if pid not in ids_exatos]
    dossie["similar_matches"] = [person_summary(arvore, pid) for pid in parecidos[:5]]
    dossie["similar_count"] = len(parecidos)
    return dossie, candidatos


def _homonimos(arvore, person1_name, person2_name, p1_ids, p2_ids):
    """Dossie de ambiguidade dos dois nomes, ou {} quando cada um e unico.

    O rotulo e a contagem falam apenas do lado ambiguo: misturar os dois lados
    faria a tabela de homonimos listar a propria pessoa 1 como se fosse
    homonima da pessoa 2.
    """
    dossie1, _ = _candidatos(arvore, person1_name, p1_ids)
    dossie2, _ = _candidatos(arvore, person2_name, p2_ids)
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


def path_search(person1_name: str, person2_name: str, deps, arvore):
    """Executa o fluxo completo de busca de caminho.

    Retorna `(path_result, msg, success)`. `path_result` é dict com
    `person1_name`, `person2_name`, `text_path`, `mermaid_data`, `documentary`
    (parentesco documental) e `observations`.
    """
    person1_name = person1_name.strip()
    person2_name = person2_name.strip()

    p1_ids = find_person_by_name(arvore, person1_name)
    p2_ids = find_person_by_name(arvore, person2_name)
    if not p1_ids:
        return None, f"Pessoa 1 '{person1_name}' não encontrada.", False
    if not p2_ids:
        return None, f"Pessoa 2 '{person2_name}' não encontrada.", False

    homonimos = _homonimos(arvore, person1_name, person2_name, p1_ids, p2_ids)

    # Com homonimos, a escolha do registro deixa de ser silenciosa E deixa de ser
    # a primeira da lista: as combinacoes sao testadas e vence a primeira que
    # tiver caminho. Medido no GEDCOM real: "Jose Vicente de Souza" tem tres
    # registros (dois so diferem no acento) e so um tem pais — antes, a tela
    # respondia "nenhuma conexao" para uma conexao que o GEDCOM contem.
    _, candidatos1 = _candidatos(arvore, person1_name, p1_ids)
    _, candidatos2 = _candidatos(arvore, person2_name, p2_ids)
    cache = {}
    p1_id = p2_id = documental = None
    for cand1 in candidatos1[:LIMITE_DE_CANDIDATOS]:
        for cand2 in candidatos2[:LIMITE_DE_CANDIDATOS]:
            if (cand1, cand2) not in cache:
                cache[(cand1, cand2)] = documentary_relationship(arvore, cand1, cand2, homonyms=homonimos)
            candidato = cache[(cand1, cand2)]
            if (candidato.get("path") or {}).get("ids"):
                p1_id, p2_id, documental = cand1, cand2, candidato
                break
        if documental is not None:
            break

    if documental is None:
        p1_id, p2_id = p1_ids[0], p2_ids[0]
        documental = cache.get((p1_id, p2_id)) or documentary_relationship(arvore, p1_id, p2_id, homonyms=homonimos)

    caminho = (documental.get("path") or {}).get("ids")
    observacoes = [aviso["message"] for aviso in documental.get("warnings") or []]

    # A costura da OPP-20261006-ULVW: quem busca o dado de dominio e este lado,
    # e o renderizador recebe o resolvedor por parametro. Ver
    # `core/diagram_domain.py`.
    dominio = resolvedor_de_diagrama(arvore)

    if caminho:
        nomes = (documental.get("path") or {}).get("names") or []
        mermaid_data = deps.generate_mermaid(caminho, p1_id, p2_id,
                                             (documental.get("common_ancestor") or {}).get("id"),
                                             dominio)
        msg = "Conexão direta encontrada (ancestral comum)."
    else:
        person_path = find_indirect_path(arvore, p1_id, p2_id, max_hops=MAX_HOPS)
        if not person_path:
            return (None,
                    f"Nenhuma conexão encontrada entre '{person1_name}' e '{person2_name}'.",
                    True)
        nomes = [get_name(arvore[0][n]) for n in person_path]
        mermaid_data = deps.generate_mermaid_indirect(p1_id, p2_id, person_path, dominio)
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
# Superficie publica (OPP-20261006-ESKO).
#
# Ate 2026-10-06 este bloco reexportava 17 nomes que o modulo nao usa, e o
# docstring os justificava com consumidores que nao existiam. Varredura mostrou
# que `app.py` importa apenas `path_search` e que `core/dna_analysis.py` nao
# importa nada daqui. Os consumidores reais eram tres arquivos de teste e o
# harness de paridade, todos migrados para o modulo canonico.
# ---------------------------------------------------------------------------
__all__ = ["path_search"]

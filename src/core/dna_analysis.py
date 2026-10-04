"""Tarefa 04 - Analise de DNA (regra final: GEDCOM, DNA e confronto separados).

Este modulo passou a **orquestrar** tres etapas independentes, que antes estavam
misturadas em uma so:

1. **Parentesco documental** (`core.documentary_relationship`) — o que o GEDCOM
   afirma: caminho, ancestrais comuns, distancia geracional, parentesco, homonimos,
   caminhos multiplos, colapso de pedigree e a evidencia de cada salto. Nao le cM.
2. **Evidencia genetica** (`core.genetic_evidence`) — kit, fonte, cM, segmentos,
   maior segmento, SNPs, cromossomo e posicoes. Nao le o GEDCOM.
3. **Possibilidades e confronto** (`core.relationship_hypotheses` +
   `core.evidence_comparison`) — o cM vira uma LISTA de possibilidades pelo Shared
   cM Project 4.0, e o confronto devolve COMPATIVEL / POSSIVEL / CONFLITANTE /
   INCONCLUSIVO.

## Regra absoluta (nao regredir)

- O DNA **nao** altera o parentesco documental, e o cM **nao** e usado sozinho para
  afirmar parentesco.
- Nunca `if cm == faixa: parentesco = relacionamento_do_GEDCOM`, e nunca
  `if cm == 10.8: relacionamento = "primo de 4º grau"`.
- O rotulo "Relacionamento Provável (DNA)" foi removido: o que existe agora e
  "Possibilidades de parentesco pelo DNA", dentro da secao de evidencia genetica.

## Compatibilidade

`get_relationships_by_cm` e `SHARED_CM_DATA` continuam existindo e reexportados
(`core.cm_estimator`), porque `tests/test_dna_analysis.py` os exercita, mas o
fluxo e a interface **nao** os usam mais: eram faixas escritas a mao, sem fonte
verificavel, e estao marcadas como legado.
"""
from __future__ import annotations

from .cm_estimator import SHARED_CM_DATA, get_relationships_by_cm
from .documentary_relationship import documentary_relationship, homonym_dossier
from .evidence_comparison import compare
from .genetic_evidence import build_genetic_evidence, evidence_for
from .matching import build_ged_indexes, match_candidates
from .name_normalization import (
    drop_short_tokens,
    norm_name,
    soft_prefix_jaccard,
    split_name_pt,
    surname_core_tokens,
    surnames_set,
    token_prefixes,
    top_given_tokens,
)
from .relationship_hypotheses import hypotheses_for_evidence
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback
from reporting.mermaid_render import generate_mermaid_graph
from utils.text_cleaning import demojibake, strip_bad_utf
from .gedcom_state import get_name, people


def _montar_diagrama(documentary: dict, root_id: str, pid: str):
    """Mermaid do caminho DOCUMENTAL (ou None quando nao ha caminho)."""
    caminho = (documentary or {}).get("path") or {}
    if not caminho.get("ids"):
        return None
    ancestral = (documentary.get("common_ancestor") or {}).get("id")
    return generate_mermaid_graph(caminho["ids"], root_id, pid, ancestral)


def _observacoes(documentary, evidence, comparison, extra=None):
    """Secao 5 da tela: tudo que o operador precisa saber e nenhum veredito."""
    textos = []
    for aviso in (documentary or {}).get("warnings") or []:
        textos.append(aviso["message"])
    for aviso in (evidence or {}).get("warnings") or []:
        textos.append(aviso["message"])
    textos.extend((comparison or {}).get("observations") or [])
    for aviso in extra or []:
        textos.append(aviso)
    vistos, unicos = set(), []
    for texto in textos:
        if texto and texto not in vistos:
            vistos.add(texto)
            unicos.append(texto)
    return unicos


def dna_analysis(csv_path: str, root_name: str):
    """Executa o fluxo completo da analise de DNA.

    Retorna `(results_sorted, skipped, message)`. Cada resultado traz, lado a lado
    e sem misturar: `documentary` (GEDCOM), `genetic_evidence` (DNA),
    `hypotheses` (possibilidades) e `comparison` (confronto).
    """
    root_person_ids = [pid for pid, p in people.items() if root_name.lower() in get_name(p).lower()]
    if not root_person_ids:
        raise ValueError(f"Seu nome '{root_name}' não foi encontrado no GEDCOM.")
    root_id = root_person_ids[0]

    df = read_csv_with_fallback(csv_path)
    name_col, cm_col, match_id_col, match_email_col = detect_columns(df)
    if not name_col or not cm_col:
        raise ValueError("Colunas de Nome e cM não encontradas no CSV.")

    evidencias, avisos_da_evidencia = build_genetic_evidence(df)
    ged_index, surname_index, features = build_ged_indexes()

    raiz_ambigua = homonym_dossier(root_name)
    avisos_da_raiz = []
    if raiz_ambigua["ambiguous"]:
        avisos_da_raiz.append(
            f"O nome informado como raiz ('{root_name}') corresponde a {raiz_ambigua['exact_count']} "
            f"registros no GEDCOM ({', '.join(f['id'] for f in raiz_ambigua['exact_matches'])}). "
            "A análise usou o primeiro; confira se é a pessoa certa."
        )

    results_list = []
    skipped_matches = []
    documental_por_pessoa = {}
    dossie_por_nome = {}

    def _dossie(nome, candidatos):
        """Dossie de homonimos, uma vez por nome (a varredura custa ~35k nomes)."""
        if nome not in dossie_por_nome:
            dossie_por_nome[nome] = homonym_dossier(nome, similar_ids=candidatos)
        return dossie_por_nome[nome]

    for chave_nome, por_kit in evidencias.items():
        for chave_kit, kit in por_kit.items():
            # O matching continua recebendo o cM DO KIT (nunca a soma de kits
            # diferentes), preservando as decisões do fluxo anterior.
            candidate_pids, reason = match_candidates(
                kit["person_name_csv"], kit["total_cm"], ged_index, surname_index, features)

            if not candidate_pids:
                skipped_matches.append({
                    "csv_name": kit["person_name_csv"],
                    "kit": kit["kit"],
                    "cm": kit["total_cm"],
                    "motivo": reason or "não encontrado",
                })
                continue

            # O legado percorria TODOS os candidatos e ficava com o primeiro que
            # tivesse caminho. Isso e preservado — e e o que salva os casos de
            # registro duplicado em que so um dos homonimos tem pais no GEDCOM.
            # A escolha, porem, deixa de ser silenciosa: o dossie de homonimos
            # marca o resultado como identidade ambigua.
            documentais = []
            for candidato in candidate_pids:
                if candidato not in documental_por_pessoa:
                    documental_por_pessoa[candidato] = documentary_relationship(
                        root_id, candidato,
                        homonyms=_dossie(kit["person_name_csv"], candidate_pids))
                documentais.append((candidato, documental_por_pessoa[candidato]))
            pid, documentary = next(
                ((c, d) for c, d in documentais if (d.get("path") or {}).get("ids")),
                documentais[0])
            homonimos = documentary.get("homonyms") or {}

            evidence = evidence_for(por_kit, avisos=avisos_da_evidencia, kit_key=chave_kit)
            hypotheses = hypotheses_for_evidence(evidence)
            comparison = compare(documentary, hypotheses, evidence)

            nomes_do_caminho = (documentary.get("path") or {}).get("names") or []
            results_list.append({
                "match_name": get_name(people[pid]),
                "csv_name": kit["person_name_csv"],
                "cm": kit["total_cm"],
                "kit": kit["kit"],
                "text_path": " → ".join(nomes_do_caminho),
                "mermaid_data": _montar_diagrama(documentary, root_id, pid),
                "documentary": documentary,
                "genetic_evidence": evidence,
                "hypotheses": hypotheses,
                "comparison": comparison,
                "observations": _observacoes(documentary, evidence, comparison, avisos_da_raiz),
                "warnings": (documentary.get("warnings") or []) + (evidence.get("warnings") or []),
            })

    # Ordem de apresentacao (nao e ordem de confianca): primeiro o que tem
    # caminho documental ou identidade a esclarecer, depois o que so tem DNA.
    # Dentro de cada grupo, cM decrescente — a ordem que o fluxo sempre usou.
    # Medido em 2026-10 no GEDCOM real: 71 conexoes, das quais 64 sem caminho no
    # GEDCOM (antes eram descartadas em silencio por nao terem caminho). Ordenar
    # so por cM enterraria as 7 conexoes documentais no meio das 64.
    def _ordem(resultado):
        tem_caminho = bool((resultado["documentary"].get("path") or {}).get("ids"))
        return (0 if tem_caminho else 1, -(resultado.get("cm") or 0))

    results_sorted = sorted(results_list, key=_ordem)
    message = f"{len(results_sorted)} conexões encontradas. {len(skipped_matches)} descartadas."
    return results_sorted, skipped_matches, message


# ---------------------------------------------------------------------------
# Superficie de compatibilidade (ver a nota no docstring do modulo).
# Reexporta o que era definido aqui antes da separacao das tres etapas.
# ---------------------------------------------------------------------------
__all__ = [
    "dna_analysis", "get_relationships_by_cm", "SHARED_CM_DATA",
    "aggregate_matches", "detect_columns", "read_csv_with_fallback",
    "build_ged_indexes", "match_candidates",
    "norm_name", "split_name_pt", "surnames_set", "top_given_tokens",
    "token_prefixes", "drop_short_tokens", "surname_core_tokens",
    "soft_prefix_jaccard", "strip_bad_utf", "demojibake",
]

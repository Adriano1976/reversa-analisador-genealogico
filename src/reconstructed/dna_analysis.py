"""Tarefa 04 - Analise de DNA.

Cruza a arvore GEDCOM com um CSV de matches (ex.: GEDmatch). Agrega
segmentos duplicados por match (somando cM), faz matching difuso de nomes
com filtro anti-falso-positivo, calcula o caminho ancestral ate a pessoa-raiz
e preve o parentesco por faixa de cM. Renderiza resultados ordenados por cM
decrescente e lista os descartados para auditoria.

Comportamento identico ao legado, incluindo as decisoes documentadas:
- Limiares de score/given como literais nas regras A/B/C/D (92, 90, 86, ...).
- Relaxamento de Jaccard (0.5 -> 0.33) para cM>=150 e dado nao-generico.
- Regex de ID `[A-Z]{2}\\d{7}`.

## Layout (OPP-20260929-ZV52, OPP-20261003-RGKA)

Este modulo passou a orquestrar. As responsabilidades foram separadas em
`name_normalization`, `csv_ingest` e `matching`, e aqui ficam o fluxo principal
e o bloco de reexportacao.

A tabela de faixas de cM e a traducao de cM em parentesco sairam daqui na
`OPP-20261003-RGKA` e moram em `core/cm_estimator.py`, que declara no proprio
arquivo a origem da tabela. As duas continuam reexportadas abaixo.

## Superficie de compatibilidade

O bloco de reexportacao no fim do arquivo existe porque consumidores externos
importam nomes daqui: `app.py`, `tests/test_dna_analysis.py`,
`tests/test_characterization_matching.py` e `_reversa_sdd/parity/harness.py`.
Remover a reexportacao quebra esses consumidores. Enquanto eles nao forem
migrados para os modulos novos, o bloco fica.
"""
from __future__ import annotations

from .core.cm_estimator import SHARED_CM_DATA, get_relationships_by_cm
from .csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback
from .domain import demojibake, strip_bad_utf
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
from .path_finding import find_ancestral_path
from .mermaid_render import generate_mermaid_graph
from .gedcom_state import get_name, people


def dna_analysis(csv_path: str, root_name: str):
    """Executa o fluxo completo de análise de DNA.

    Retorna `(results_sorted, skipped, message)` ou lança exceção.
    `root_name` deve existir no GEDCOM.
    """
    root_person_ids = [pid for pid, p in people.items() if root_name.lower() in get_name(p).lower()]
    if not root_person_ids:
        raise ValueError(f"Seu nome '{root_name}' não foi encontrado no GEDCOM.")
    root_id = root_person_ids[0]

    df = read_csv_with_fallback(csv_path)
    name_col, cm_col, match_id_col, match_email_col = detect_columns(df)
    if not name_col or not cm_col:
        raise ValueError("Colunas de Nome e cM não encontradas no CSV.")
    aggregated = aggregate_matches(df, name_col, cm_col, match_id_col, match_email_col)

    ged_index, surname_index, features = build_ged_indexes()

    results_list = []
    skipped_matches = []

    for _, row in aggregated.iterrows():
        csv_name_raw = str(row[name_col]).strip()
        match_name = demojibake(csv_name_raw)
        cm_value = row[cm_col]

        candidate_pids, reason = match_candidates(match_name, cm_value, ged_index, surname_index, features)

        if not candidate_pids:
            skipped_matches.append({"csv_name": csv_name_raw, "motivo": reason or "não encontrado"})
            continue

        added = False
        for pid in candidate_pids:
            path, common_ancestor = find_ancestral_path(root_id, pid)
            if path:
                nomes = [get_name(people[p_id]) for p_id in path]
                probable_relationships = get_relationships_by_cm(cm_value)
                mermaid_data = generate_mermaid_graph(path, root_id, pid, common_ancestor)
                results_list.append({
                    "match_name": get_name(people[pid]),
                    "cm": cm_value,
                    "text_path": " → ".join(nomes),
                    "mermaid_data": mermaid_data,
                    "relationships": ", ".join(probable_relationships),
                    "csv_name": csv_name_raw,
                })
                added = True
                break
        if not added:
            skipped_matches.append({"csv_name": csv_name_raw, "motivo": "sem caminho subindo por pais (pais ausentes no GED?)"})

    results_sorted = sorted(results_list, key=lambda x: x.get("cm", 0), reverse=True)
    message = f"{len(results_sorted)} conexões encontradas. {len(skipped_matches)} descartadas."
    return results_sorted, skipped_matches, message


# ---------------------------------------------------------------------------
# Superficie de compatibilidade (ver a nota no docstring do modulo).
# Reexporta o que era definido aqui antes da OPP-20260929-ZV52.
# ---------------------------------------------------------------------------
__all__ = [
    "dna_analysis", "get_relationships_by_cm", "SHARED_CM_DATA",
    "aggregate_matches", "detect_columns", "read_csv_with_fallback",
    "build_ged_indexes", "match_candidates",
    "norm_name", "split_name_pt", "surnames_set", "top_given_tokens",
    "token_prefixes", "drop_short_tokens", "surname_core_tokens",
    "soft_prefix_jaccard", "strip_bad_utf", "demojibake",
]

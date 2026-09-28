
import json, os, sys

W = sys.argv[1]; GED = sys.argv[2]; OUT = sys.argv[3]
sys.path.insert(0, os.path.join(W, "analisador-genealogico"))
os.chdir(os.path.join(W, ".parity-run-cand"))

from reconstructed import upload as U
from reconstructed import path_search as P
from reconstructed import dna_analysis as D
from reconstructed import domain as DM

obs = {}
def safo(fn, *a, **k):
    try:
        return {"ok": True, "v": fn(*a, **k)}
    except Exception as e:
        return {"ok": False, "e": type(e).__name__}

names = U.load_gedcom_and_build_graph(GED)
obs["person_count"] = len(U.people)
obs["family_count"] = len(U.families)
obs["names"] = names
obs["graph"] = {"nodes": U.graph.number_of_nodes(), "edges": U.graph.number_of_edges()}
obs["child_to_family"] = {k: sorted(v) for k, v in sorted(U.child_to_family.items())}

ids = sorted(U.people.keys())
obs["get_name"] = {i: (U.get_name(U.people[i]) if U.get_name(U.people[i]) is not None else None) for i in ids}
obs["get_parents"] = {i: sorted(P.get_parents(i) or []) for i in ids}
obs["get_spouses"] = {i: sorted(P.get_spouses(i) or []) for i in ids}

obs["norm_name"] = {n: safo(D.norm_name, n) for n in names}
# ATENCAO — equivalente correto de `strip_bad_utf`:
#   O oraculo tem UMA funcao `strip_bad_utf` (L62-81) que faz o dicionario de fixes
#   de mojibake E a limpeza de nao-alfanumericos.
#   A reconstrucao DIVIDIU isso em duas:
#     - `dna_analysis.strip_bad_utf` (L74-90) = copia fiel do oraculo  <-- ESTE e o equivalente
#     - `domain.strip_bad_utf`    (L29-40) = outra coisa (so remove U+FFFD)
#     - `domain.demojibake`       (L43-57) = parte do trabalho, implementacao diferente
#   Comparar `domain.strip_bad_utf` com o oraculo gera FALSO POSITIVO de divergencia:
#   nao e o mesmo comportamento, e nem pretende ser. O probe correto e `norm_name`
#   (que usa a funcao certa internamente) + `D.strip_bad_utf` abaixo.
obs["strip_bad_utf"] = {n: safo(D.strip_bad_utf, n) for n in names}
obs["demojibake"] = {n: safo(D.demojibake, n) for n in names}
obs["split_name_pt"] = {n: safo(lambda x: [list(v) if isinstance(v, (set, tuple)) else v for v in D.split_name_pt(x)], n) for n in names}
obs["surnames_set"] = {n: safo(lambda x: sorted(D.surnames_set(x)), n) for n in names}
obs["top_given_tokens"] = {n: safo(lambda x: D.top_given_tokens(x), n) for n in names}
obs["token_prefixes"] = {n: safo(lambda x: sorted(D.token_prefixes(x or [])), n) for n in names}
obs["drop_short_tokens"] = {n: safo(lambda x: sorted(D.drop_short_tokens(x or [])), n) for n in names}
obs["surname_core_tokens"] = {n: safo(lambda x: D.surname_core_tokens(x), n) for n in names}

obs["cm"] = {}
for cm in json.loads(sys.argv[4]):
    obs["cm"][str(cm)] = safo(D.get_relationships_by_cm, cm)

obs["ancestral"] = {}
obs["indirect"] = {}
sample = ids[:40]
for a in sample:
    for b in sample:
        r = P.find_ancestral_path(a, b)
        obs["ancestral"][a + "|" + b] = [list(r[0]) if r[0] else None, r[1]]
        q = P.find_indirect_path(a, b)
        obs["indirect"][a + "|" + b] = list(q) if q else None

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(obs, fh, ensure_ascii=False, sort_keys=True)
print("CANDIDATO coletado: %d pessoas, %d familias" % (obs["person_count"], obs["family_count"]))

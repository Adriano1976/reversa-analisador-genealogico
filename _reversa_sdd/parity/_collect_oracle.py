
import importlib.util, json, os, shutil, sys

W = sys.argv[1]; GED = sys.argv[2]; OUT = sys.argv[3]
tmp = os.path.join(W, ".parity-run-oracle")
shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
local = os.path.join(tmp, "oracle.py")
shutil.copyfile(os.path.join(W, "_reversa_sdd", "oracle", "app_legacy_e43ca22.py"), local)
os.chdir(tmp)  # neutraliza os.makedirs("uploads"/"static") relativo do oraculo
spec = importlib.util.spec_from_file_location("oracle", local)
m = importlib.util.module_from_spec(spec); sys.modules["oracle"] = m
spec.loader.exec_module(m)

obs = {}
def safo(fn, *a, **k):
    try:
        return {"ok": True, "v": fn(*a, **k)}
    except Exception as e:
        return {"ok": False, "e": type(e).__name__}

names = m.load_gedcom_and_build_graph(GED)
obs["person_count"] = len(m.people)
obs["family_count"] = len(m.families)
obs["names"] = names
obs["graph"] = {"nodes": m.graph.number_of_nodes(), "edges": m.graph.number_of_edges()}
obs["child_to_family"] = {k: sorted(v) for k, v in sorted(m.child_to_family.items())}

ids = sorted(m.people.keys())
obs["get_name"] = {i: safo(m.get_name, m.people[i])["v"] if m.get_name(m.people[i]) is not None else None for i in ids}
obs["get_parents"] = {i: sorted(m.get_parents(i) or []) for i in ids}
obs["get_spouses"] = {i: sorted(m.get_spouses(i) or []) for i in ids}

obs["norm_name"] = {n: safo(m.norm_name, n) for n in names}
obs["strip_bad_utf"] = {n: safo(m.strip_bad_utf, n) for n in names}
obs["demojibake"] = {n: safo(m.demojibake, n) for n in names}
obs["split_name_pt"] = {n: safo(lambda x: [list(v) if isinstance(v, (set, tuple)) else v for v in m.split_name_pt(x)], n) for n in names}
obs["surnames_set"] = {n: safo(lambda x: sorted(m.surnames_set(x)), n) for n in names}
obs["top_given_tokens"] = {n: safo(lambda x: m.top_given_tokens(x), n) for n in names}
obs["token_prefixes"] = {n: safo(lambda x: sorted(m.token_prefixes(x or [])), n) for n in names}
obs["drop_short_tokens"] = {n: safo(lambda x: sorted(m.drop_short_tokens(x or [])), n) for n in names}
obs["surname_core_tokens"] = {n: safo(lambda x: m.surname_core_tokens(x), n) for n in names}

obs["cm"] = {}
for cm in json.loads(sys.argv[4]):
    obs["cm"][str(cm)] = safo(m.get_relationships_by_cm, cm)

obs["ancestral"] = {}
obs["indirect"] = {}
sample = ids[:int(os.environ.get("PARITY_SAMPLE", "40"))]
for a in sample:
    for b in sample:
        r = m.find_ancestral_path(a, b)
        obs["ancestral"][a + "|" + b] = [list(r[0]) if r[0] else None, r[1]]
        q = m.find_indirect_path(a, b)
        obs["indirect"][a + "|" + b] = list(q) if q else None

shutil.rmtree(tmp, ignore_errors=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(obs, fh, ensure_ascii=False, sort_keys=True)
print("ORACLE coletado: %d pessoas, %d familias" % (obs["person_count"], obs["family_count"]))

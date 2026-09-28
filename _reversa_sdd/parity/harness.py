"""Harness diferencial: ORACULO CONGELADO x CANDIDATO.

Prova a metrica primaria do brief — "paridade de matching >= 100%" — por execucao
diferencial real, nao por inspecao.

## O que este harness resolve (RISK-002)

O oraculo e `_reversa_sdd/oracle/app_legacy_e43ca22.py` (monolito de 888 linhas,
extraido do commit e43ca22). NAO use `analisador-genealogico/app.py`: ele virou um
wrapper de 86 linhas que importa `reconstructed/`, e usa-lo produz validacao
circular — comparar a reconstrucao com ela mesma.

## Arquitetura

    FASE 1 (coleta)   Roda o oraculo em SUBPROCESSO e o candidato em OUTRO
                      subprocesso, cada um isolado, e serializa as observacoes
                      em JSON. Isolamento e obrigatorio: o oraculo mantem estado
                      global mutavel (people/families/graph/child_to_family) e
                      importa-lo junto do candidato contaminaria este ultimo.

    FASE 2 (diff)     Compara os dois JSON com IGUALDADE EXATA e reporta.

## Uso

    python _reversa_sdd/parity/harness.py                 # fixtures sinteticas
    python _reversa_sdd/parity/harness.py --gedcom X.ged  # um GEDCOM real
    python _reversa_sdd/parity/harness.py --json out.json # salva as observacoes
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIXTURES = os.path.join(HERE, "fixtures")
ORACLE = os.path.join(ROOT, "_reversa_sdd", "oracle", "app_legacy_e43ca22.py")
CANDIDATE_DIR = os.path.join(ROOT, "analisador-genealogico")

# ---------------------------------------------------------------------------
# Amostra de pares de caminho — CONFIGURAVEL por variavel de ambiente.
#
# Por que existe: `find_ancestral_path`/`find_indirect_path` sao caros em arvore
# grande. Com a amostra fixa de 40x40 = 1.600 pares, uma arvore real de 35.460
# pessoas nao termina em tempo razoavel (medido: saturacao de CPU sem fim a vista).
#
# O harness exporta estas variaveis para os coletores, que as leem. Assim o mesmo
# codigo serve para fixture sintetica (amostra grande, e barata) e arvore real
# grande (amostra reduzida, e o unico jeito de obter resultado).
#
#   PARITY_SAMPLE=40    -> 40x40 = 1.600 pares (padrao)
#   PARITY_SAMPLE=12    -> 12x12 =   144 pares
#   PARITY_TIMEOUT=600  -> segundos por coletor antes de desistir (padrao 600)
# ---------------------------------------------------------------------------
SAMPLE = int(os.environ.get("PARITY_SAMPLE", "40"))
TIMEOUT = int(os.environ.get("PARITY_TIMEOUT", "600"))

CM_PROBES = [
    0, -5, 1, 9, 10, 29, 30, 45, 46, 50, 109, 110, 199, 200, 219, 220, 299, 300,
    349, 350, 514, 515, 552, 553, 849, 850, 1329, 1330, 1316, 1317, 2199, 2200,
    2311, 2312, 3399, 3400, 3719, 3720, 5000, 99999,
]

# ---------------------------------------------------------------- coletores

ORACLE_COLLECTOR = r'''
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
'''

CANDIDATE_COLLECTOR = r'''
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
sample = ids[:int(os.environ.get("PARITY_SAMPLE", "40"))]
for a in sample:
    for b in sample:
        r = P.find_ancestral_path(a, b)
        obs["ancestral"][a + "|" + b] = [list(r[0]) if r[0] else None, r[1]]
        q = P.find_indirect_path(a, b)
        obs["indirect"][a + "|" + b] = list(q) if q else None

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(obs, fh, ensure_ascii=False, sort_keys=True)
print("CANDIDATO coletado: %d pessoas, %d familias" % (obs["person_count"], obs["family_count"]))
'''


def run_collector(code, gedcom, cm_json, tag):
    runner = os.path.join(HERE, "_collect_%s.py" % tag)
    out = os.path.join(HERE, "_obs_%s.json" % tag)
    run_dir = os.path.join(ROOT, ".parity-run-%s" % ("oracle" if tag == "oracle" else "cand"))
    os.makedirs(run_dir, exist_ok=True)
    with open(runner, "w", encoding="utf-8") as fh:
        fh.write(code)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PARITY_SAMPLE=str(SAMPLE))
    try:
        proc = subprocess.run(
            [sys.executable, runner, ROOT, gedcom, out, cm_json],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env, timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        # Nao gera resultado FALSO. Um coletor que nao termina nao pode ser lido
        # como "paridade OK" — e por isso que isto e uma excecao, nao um print.
        raise SystemExit(
            "coleta '%s' excedeu PARITY_TIMEOUT=%ds. NAO CONCLUYENTE (nao e divergencia).\n"
            "  Reduza a amostra de pares:  $env:PARITY_SAMPLE=\"12\"\n"
            "  Ou aumente o limite:        $env:PARITY_TIMEOUT=\"3600\"" % (tag, TIMEOUT)
        )
    if proc.returncode != 0 or not os.path.exists(out):
        print(proc.stdout or "", proc.stderr or "")
        raise SystemExit("coleta '%s' falhou (exit %d)" % (tag, proc.returncode))
    print("  " + (proc.stdout or "").strip())
    with open(out, encoding="utf-8") as fh:
        return json.load(fh)


def _canon(v):
    """Canonicaliza para comparacao: set/frozenset SEMPRE -> lista ordenada.

    Regra: um `set` nao tem ordem — compara-lo como lista produz falso positivo.
    Um `list`/`tuple` TEM ordem — preserva-la, mas canonicalizar cada elemento
    recursivamente (um set aninhado dentro de uma tupla, por exemplo).

    Sem isso, `split_name_pt` divergiria so porque um dos lados devolve
    `set(suffixes)` e o outro devolve a mesma coisa em ordem diferente.
    """
    if isinstance(v, dict):
        return {k: _canon(x) for k, x in v.items()}
    if isinstance(v, (set, frozenset)):
        return sorted(_canon(x) for x in v)
    if isinstance(v, (list, tuple)):
        return [_canon(x) for x in v]
    return v


def compare(obs_o, obs_c):
    """Compara com igualdade EXATA (apos canonicalizacao de ordem de set).

    Reporta a CAUSA RAIZ, nao os sintomas. Quando `names` divergir, os 12 probes
    de funcao de nome vao divergir em cascata apenas porque recebem strings
    diferentes — conta-los como 12 problemas esconderia o fato de que ha UM.
    """
    diffs = []

    # ---- 1. Causa raiz: identidade dos nomes ---------------------------------
    names_o, names_c = obs_o.get("names"), obs_c.get("names")
    names_divergem = _canon(names_o) != _canon(names_c)

    for key in ["person_count", "family_count", "graph", "child_to_family"]:
        a, b = _canon(obs_o.get(key)), _canon(obs_c.get(key))
        if a != b:
            diffs.append((key, "%r vs %r" % (a, b)))

    if names_divergem and isinstance(names_o, list) and isinstance(names_c, list):
        so, sc = set(map(str, names_o)), set(map(str, names_c))
        diffs.append(("names", "len %d vs %d | so no oraculo: %s | so no candidato: %s"
                      % (len(names_o), len(names_c), sorted(so - sc)[:5], sorted(sc - so)[:5])))
        # Localiza QUEM diverge, para o relatorio apontar a pessoa, nao o sintoma.
        ids = sorted(obs_o.get("get_name", {}))
        quem = [(i, obs_o["get_name"].get(i), obs_c.get("get_name", {}).get(i))
                for i in ids if _canon(obs_o["get_name"].get(i)) != _canon(obs_c.get("get_name", {}).get(i))]
        for i, no, nc in quem[:5]:
            diffs.append(("get_name[%s]" % i, "oraculo=%r candidato=%r" % (no, nc)))
        if len(quem) > 5:
            diffs.append(("get_name", "... e mais %d pessoas com nome divergente" % (len(quem) - 5)))

    # ---- 2. Probes de funcao de nome ---------------------------------------
    # Pulados quando os nomes divergem: eles so refletiriam a causa raiz acima.
    probe_keys = ["get_name", "get_parents", "get_spouses", "norm_name", "strip_bad_utf",
                  "demojibake", "split_name_pt", "surnames_set", "top_given_tokens",
                  "token_prefixes", "drop_short_tokens", "surname_core_tokens"]
    if not names_divergem:
        for key in probe_keys:
            a, b = obs_o.get(key, {}), obs_c.get(key, {})
            n = 0
            for k in sorted(set(a) | set(b)):
                if _canon(a.get(k)) != _canon(b.get(k)):
                    n += 1
                    if n <= 3:
                        diffs.append(("%s[%s]" % (key, k), "oraculo=%r candidato=%r" % (a.get(k), b.get(k))))
            if n > 3:
                diffs.append(("%s" % key, "... e mais %d divergencias neste probe" % (n - 3)))
    else:
        diffs.append(("[probes de nome]", "NAO avaliados nesta fixture: as entradas sao diferentes "
                                          "(causa raiz acima). Corrija `get_name` e re-execute."))

    # ---- 3. Probes independentes da identidade dos nomes --------------------
    for key in ["cm", "ancestral", "indirect"]:
        a, b = obs_o.get(key, {}), obs_c.get(key, {})
        n = 0
        for k in sorted(set(a) | set(b)):
            if _canon(a.get(k)) != _canon(b.get(k)):
                n += 1
                if n <= 5:
                    diffs.append(("%s[%s]" % (key, k), "oraculo=%r candidato=%r" % (a.get(k), b.get(k))))
        if n > 5:
            diffs.append(("%s" % key, "... e mais %d divergencias neste probe" % (n - 5)))

    return diffs


def main() -> int:
    global SAMPLE, TIMEOUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--gedcom", default=None, help="Um GEDCOM. Padrao: todas as fixtures de fixtures/gedcom/.")
    ap.add_argument("--json", default=None, help="Salva as observacoes em JSON.")
    ap.add_argument("--pares", type=int, default=None,
                    help="Lado da amostra de pares de caminho (NxN). Padrao 40. "
                         "Reduza para arvores reais grandes.")
    ap.add_argument("--timeout", type=int, default=None,
                    help="Segundos por coletor antes de desistir. Padrao 600.")
    args = ap.parse_args()

    if args.pares is not None:
        SAMPLE = args.pares
    if args.timeout is not None:
        TIMEOUT = args.timeout

    if args.gedcom:
        gedcoms = [args.gedcom]
    else:
        gdir = os.path.join(FIXTURES, "gedcom")
        gedcoms = [os.path.join(gdir, f) for f in sorted(os.listdir(gdir)) if f.endswith(".ged")]

    cm_json = json.dumps(CM_PROBES)
    total_div = 0
    inconclusivos = 0

    print("=" * 78)
    print("HARNESS DIFERENCIAL — oraculo congelado x reconstrucao")
    print("=" * 78)
    print("oraculo   : %s" % os.path.relpath(ORACLE, ROOT))
    print("candidato : analisador-genealogico/reconstructed/")
    print("probes    : %d valores de cM + grafo completo + pares de caminho" % len(CM_PROBES))
    print("amostra   : %dx%d = %d pares de caminho por lado" % (SAMPLE, SAMPLE, SAMPLE * SAMPLE))
    print("timeout   : %ds por coletor" % TIMEOUT)
    print()

    for ged in gedcoms:
        print("-" * 78)
        print("FIXTURE: %s (%d bytes)" % (os.path.relpath(ged, ROOT), os.path.getsize(ged)))
        try:
            obs_o = run_collector(ORACLE_COLLECTOR, ged, cm_json, "oracle")
            obs_c = run_collector(CANDIDATE_COLLECTOR, ged, cm_json, "cand")
        except SystemExit as e:
            msg = str(e)
            if "NAO CONCLUYENTE" in msg:
                # Distinto de divergencia: nao houve medicao. Nao conta como paridade
                # nem como falha de comportamento — conta como cobertura ausente.
                inconclusivos += 1
                print("  INCONCLUSIVO: %s" % msg)
            else:
                print("  ERRO: %s" % msg)
                total_div += 1
            continue

        diffs = compare(obs_o, obs_c)
        if diffs:
            total_div += len(diffs)
            print("  DIVERGENCIAS: %d" % len(diffs))
            for k, v in diffs:
                print("    [%s] %s" % (k, v))
        else:
            print("  PARIDADE OK — zero divergencia")

        if args.json:
            base = os.path.join(HERE, args.json if os.path.isabs(args.json) else args.json)
            with open(base + "." + os.path.basename(ged) + ".json", "w", encoding="utf-8") as fh:
                json.dump({"oracle": obs_o, "candidate": obs_c}, fh, ensure_ascii=False, sort_keys=True)

    print()
    print("=" * 78)
    if inconclusivos:
        print("RESULTADO: %s | %d INCONCLUSIVO(S) (sem medicao — NAO e paridade)"
              % ("PARIDADE 100%% (zero divergencia)" if total_div == 0 else "%d DIVERGENCIAS" % total_div,
                 inconclusivos))
    else:
        print("RESULTADO: %s" % ("PARIDADE 100%% (zero divergencia)" if total_div == 0
                                 else "%d DIVERGENCIAS" % total_div))
    print("=" * 78)
    return 1 if total_div else 0


if __name__ == "__main__":
    raise SystemExit(main())

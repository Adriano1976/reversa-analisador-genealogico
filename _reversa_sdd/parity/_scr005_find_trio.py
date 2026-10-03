"""Descobre um trio deterministico (GEDCOM, CSV, root_name) para capturar o SCR-005.

## O que o SCR-005 exige

A rota `dna_analysis` do oraculo faz, em ordem (app_legacy_e43ca22.py:584-595):

1. `matches_csv` presente — senao renderiza "Por favor, carregue o arquivo CSV de matches.";
2. `find_person_by_name(root_name)` — precisa achar alguem, senao renderiza
   "Seu nome '<root>' nao foi encontrado no GEDCOM.";
3. so entao agrega os matches e monta a regiao de resultados.

`find_person_by_name` (L208-211) compara contra `get_name(person)`, que devolve o
formato `"Nome /Sobrenome/"` — com BARRAS. Entao o root_name mais seguro e o nome
exatamente nessa forma, nao o nome limpo do CSV.

## O que este script faz

Para cada GEDCOM real em `uploads/`, carrega e extrai os nomes formatados. Para cada CSV
de matches, le a coluna `Name`. Entao responde, por MEDICAO: quais nomes do CSV existem
literalmente no GEDCOM. Escolhe o candidato com mais linhas no CSV (regiao de resultados
mais rica = golden mais util) e reporta o trio pronto para a captura.

Nao escreve nada no legado. So le.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ORACLE = os.path.join(ROOT, "_reversa_sdd", "oracle", "app_legacy_e43ca22.py")
UPLOADS = os.path.join(ROOT, "src", "uploads")


def carregar_oraculo(tmp: str):
    local = os.path.join(tmp, "oracle.py")
    shutil.copyfile(ORACLE, local)
    os.chdir(tmp)
    spec = importlib.util.spec_from_file_location("oracle", local)
    m = importlib.util.module_from_spec(spec)
    sys.modules["oracle"] = m
    spec.loader.exec_module(m)
    return m


def nomes_do_gedcom(m, ged: str) -> list[str]:
    m.load_gedcom_and_build_graph(ged)
    return [m.get_name(p) for p in m.people.values()]


def nomes_do_csv(p: str) -> list[str]:
    for enc in ("utf-8", "latin-1"):
        try:
            with open(p, encoding=enc, newline="") as fh:
                r = csv.DictReader(fh, skipinitialspace=True)
                cols = [c.strip() for c in (r.fieldnames or [])]
                col = next((c for c in ("Name", "MatchedName", "Nome") if c in cols), None)
                if not col:
                    return []
                return [row[col].strip() for row in r if row.get(col)]
        except UnicodeDecodeError:
            continue
    return []


def main() -> int:
    tmp = os.path.join(ROOT, ".scr005-probe")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    m = carregar_oraculo(tmp)

    geds = sorted(f for f in os.listdir(UPLOADS) if f.lower().endswith(".ged"))
    csvs = sorted(f for f in os.listdir(UPLOADS) if f.lower().endswith(".csv"))
    print("=" * 78)
    print("PROCURA DE TRIO PARA O SCR-005")
    print("=" * 78)
    print("GEDCOMs: %d | CSVs: %d" % (len(geds), len(csvs)))
    print()

    candidatos: list[dict] = []
    for g in geds:
        gp = os.path.join(UPLOADS, g)
        try:
            nomes = nomes_do_gedcom(m, gp)
        except Exception as e:
            print("  %-42s ERRO ao carregar: %s" % (g, type(e).__name__))
            continue
        # Indice por nome formatado exato, para casamento exato.
        exatos = {n.lower() for n in nomes}
        print("  %-42s %6d pessoas" % (g, len(nomes)))
        for c in csvs:
            nomes_csv = nomes_do_csv(os.path.join(UPLOADS, c))
            if not nomes_csv:
                continue
            # Quantos nomes distintos do CSV casam EXATAMENTE com algum nome formatado.
            casam = [n for n in set(nomes_csv) if n.lower() in exatos]
            if casam:
                linhas = sum(1 for n in nomes_csv if n.lower() in exatos)
                candidatos.append({"gedcom": g, "csv": c, "root_name": casam[0],
                                   "pessoas": len(nomes), "linhas_csv": linhas,
                                   "outros": sorted(casam)})

    print()
    print("=" * 78)
    if not candidatos:
        print("NENHUM par GEDCOM+CSV casou por nome exato.")
        print("Fallback: findBySubstring aceita substring — investigar nomes parciais.")
        shutil.rmtree(tmp, ignore_errors=True)
        return 1
    candidatos.sort(key=lambda d: (-d["linhas_csv"], -d["pessoas"]))
    print("TRIOS VIAVEIS (ordenados por linhas de CSV que casam):")
    for d in candidatos[:10]:
        print("  GEDCOM %-34s CSV %-28s" % (d["gedcom"], d["csv"]))
        print("      root_name = %r" % d["root_name"])
        print("      %d linhas do CSV casam | %d pessoas no GEDCOM | %d nomes distintos"
              % (d["linhas_csv"], d["pessoas"], len(d["outros"])))
    melhor = candidatos[0]
    print()
    print("=" * 78)
    print("MELHOR TRIO:")
    print(json.dumps(melhor, ensure_ascii=False, indent=2))
    with open(os.path.join(ROOT, ".scr005-probe", "trio.json"), "w", encoding="utf-8") as fh:
        json.dump(melhor, fh, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

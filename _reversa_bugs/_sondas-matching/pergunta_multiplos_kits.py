"""Sonda da pergunta do operador: "para que serve a frase de multiplos kits?"

Mede, no arquivo REAL que produziu o print (`03f50d273442cef1__Famílias_Sergipanas.csv`):

1. quantas vezes a frase aparece na tela (o aviso e global, mas `evidence_for` o
   copia para dentro de CADA cartao);
2. quanto a frase representa do total da secao "5. Observacoes";
3. o numero que a frase existe para impedir: a soma de cM entre kits diferentes
   do mesmo nome, e o parentesco que essa soma faria acreditar;
4. o que cada camada ja diz sobre os cinco nomes envolvidos.

Nao altera nada. Escreve o dump completo em `_dump_multiplos_kits.json` para
reuso (a analise sobre a arvore de 35 mil pessoas leva minutos).

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\pergunta_multiplos_kits.py
"""

import collections
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.relationship_hypotheses import possible_relationships  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    anotar_profundidade,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

GED = os.path.join(RAIZ, "src", "uploads", "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(RAIZ, "src", "uploads", "03f50d273442cef1__Famílias_Sergipanas.csv")
DUMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_dump_multiplos_kits.json")
FRASE = "mais de um kit"
PARES = [("MW3062586", "QN1766036"), ("JX1969406", "UV3651699"), ("LY5102040", "LR4550033"),
         ("FX8497870", "WK9592536"), ("ZA5409607", "WE9804196")]


def relacoes(cm):
    if cm is None:
        return "(sem cM)"
    p = possible_relationships(cm)
    nomes = [x["name_pt"] for x in p["possible_relationships"]]
    return ", ".join(nomes[:3]) or "(nenhuma relação publicada)"


def main():
    arvore = carregar_arvore(GED)
    deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                        generate_mermaid_graph, generate_mermaid_graph_indirect_bridge,
                        anotar_profundidade)
    observacoes_do_arquivo = []
    res, descartados, msg = dna_analysis(CSV, "Adriano Santos", deps, arvore,
                                         observacoes_do_arquivo=observacoes_do_arquivo)
    print(f"analise: {msg}")

    with open(DUMP, "w", encoding="utf-8") as fh:
        json.dump({"msg": msg, "resultados": res, "descartados": descartados,
                   "observacoes_do_arquivo": observacoes_do_arquivo}, fh,
                  ensure_ascii=False, default=str)
    print(f"dump: {DUMP}")

    contagem = collections.Counter()
    for r in res:
        for o in r.get("observations") or []:
            contagem[o] += 1
    total_linhas = sum(contagem.values())
    linhas_kits = sum(n for o, n in contagem.items() if FRASE in o)

    print("\n" + "=" * 100)
    print("1 e 2. O QUE A SECAO 5 DE CADA CARTAO AINDA CARREGA (depois do adendo 017)")
    print("=" * 100)
    print(f"  cartoes .......................................... {len(res)}")
    print(f"  linhas de observacao DE CARTAO somadas ........... {total_linhas}")
    print(f"  dessas, a frase de multiplos kits ................. {linhas_kits}"
          f"  (antes: 710 de 1010 = 70,3%)")
    print(f"  avisos distintos de multiplos kits NO CARTAO ...... "
          f"{sum(1 for o in contagem if FRASE in o)}  (antes: 5)")
    print(f"  cartoes em que ela aparece ........................ "
          f"{sum(1 for r in res if any(FRASE in o for o in r.get('observations') or []))}"
          f" de {len(res)}  (antes: 142 de 142)")
    print()
    print(f"  NO BLOCO DO ARQUIVO, uma vez cada ................. {len(observacoes_do_arquivo)}")
    for o in observacoes_do_arquivo:
        print(f"     - {o[:150]}{'…' if len(o) > 150 else ''}")

    print("\n" + "=" * 100)
    print("3. O NUMERO QUE A FRASE IMPEDE (soma entre kits do MESMO nome)")
    print("=" * 100)
    df = read_csv_with_fallback(CSV)
    kit = df["Kit number"].astype(str).str.strip()
    for a, b in PARES:
        sub = df[kit.isin([a, b])]
        nomes = sorted(set(sub["Name"]))
        print(f"\n  nome: {', '.join(repr(n) for n in nomes)}")
        totais = {}
        for k in (a, b):
            linhas = df[kit == k]
            if linhas.empty:
                print(f"    kit {k:<11} (ausente)")
                continue
            totais[k] = float(linhas["cM"].sum())
            print(f"    kit {k:<11} {len(linhas)} segmento(s)  total {totais[k]:>6.1f} cM"
                  f"  -> {relacoes(totais[k])}")
        if len(totais) > 1:
            soma = round(sum(totais.values()), 2)
            print(f"    {'SOMA':<15} {soma:>6.1f} cM  -> {relacoes(soma)}   <<< acreditacao falsa")

    print("\n" + "=" * 100)
    print("4. O QUE AS OUTRAS CAMADAS JA DIZEM SOBRE ESSES NOMES")
    print("=" * 100)
    alvos = set()
    for a, b in PARES:
        alvos |= set(df[kit.isin([a, b])]["Name"])
    for r in res:
        if r.get("csv_name") in alvos:
            ident = r.get("identidade") or {}
            doc = r.get("documentary") or {}
            print(f"  {str(r.get('csv_name'))[:26]:<26} kit={str(r.get('kit')):<11} "
                  f"cm={str(r.get('cm')):<6} "
                  f"identidade={str(ident.get('status')):<12} "
                  f"documental={str(doc.get('status')):<10} "
                  f"confronto={r.get('confrontacao_efetiva')}")
    print("\n  status de identidade de TODOS os cartoes:",
          dict(collections.Counter(str((r.get('identidade') or {}).get('status')) for r in res)))


if __name__ == "__main__":
    main()

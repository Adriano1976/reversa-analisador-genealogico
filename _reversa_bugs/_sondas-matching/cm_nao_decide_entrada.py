"""Por que nomes com cM ALTO ficam fora do "Resultado da Analise"?

O cM decide a entrada na lista? Esta sonda roda a analise real e junta os dois lados —
cartoes e descartes — numa tabela unica ordenada por cM, para medir:

  1. quantos grupos (nome, kit) do CSV entraram e quantos foram descartados;
  2. quantos DESCARTADOS tem cM maior que o MENOR cM aceito, e maior que 154,5;
  3. qual e' o maior cM que ficou de fora;
  4. se a ordem de exibicao dos cartoes e' monotona em cM (ela NAO e': quem tem caminho
     documental vem primeiro, ver `_ordem` em `core/dna_analysis.py`).

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\cm_nao_decide_entrada.py <ged>
"""

import collections
import os
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    anotar_profundidade,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

CSV = os.path.join(R, "src", "uploads", "54f4887e89705735__Famílias_Sergipanas.csv")
RAIZ = "Adriano Santos"


def main():
    ged = sys.argv[1]
    arvore = carregar_arvore(ged)
    deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                        generate_mermaid_graph, generate_mermaid_graph_indirect_bridge,
                        anotar_profundidade)
    resultados, descartados, msg = dna_analysis(CSV, RAIZ, deps, arvore, observacoes_do_arquivo=[])

    print(f"arvore : {os.path.basename(ged)}  ({len(arvore[0])} pessoas)")
    print(f"mensagem: {msg}")
    print()

    entraram = [{"nome": r["csv_name"], "kit": r["kit"], "cm": r["cm"],
                 "tem_caminho": bool((r["documentary"].get("path") or {}).get("ids")),
                 "na_arvore": r["match_name"], "estado": r["confrontacao_efetiva"]}
                for r in resultados]
    fora = [{"nome": d["csv_name"], "kit": d["kit"], "cm": d["cm"], "motivo": d["motivo"]}
            for d in descartados]

    total = len(entraram) + len(fora)
    print(f"grupos (nome, kit) no CSV: {total}")
    print(f"  entraram no Resultado da Analise : {len(entraram)}")
    print(f"  foram para Matches descartados   : {len(fora)}")
    print()

    todos = ([dict(x, status="ENTROU") for x in entraram]
             + [dict(x, status="FORA") for x in fora])
    todos.sort(key=lambda x: -(x["cm"] or 0))

    cm_entrou = sorted((x["cm"] or 0) for x in entraram)
    cm_fora = sorted((x["cm"] or 0) for x in fora)
    print(f"cM dos que ENTRARAM : min={cm_entrou[0]}  mediana={cm_entrou[len(cm_entrou)//2]}  max={cm_entrou[-1]}")
    print(f"cM dos que FICARAM FORA: min={cm_fora[0]}  mediana={cm_fora[len(cm_fora)//2]}  max={cm_fora[-1]}")
    print()

    maior_fora = cm_fora[-1]
    acima_do_maior_aceito = [x for x in fora if (x["cm"] or 0) > cm_entrou[-1]]
    acima_154 = [x for x in fora if (x["cm"] or 0) >= 154.5]
    acima_mediana = [x for x in fora if (x["cm"] or 0) > cm_entrou[len(cm_entrou) // 2]]
    print("o cM nao e' o criterio de entrada:")
    print(f"  descartados com cM MAIOR que o maior cM aceito ({cm_entrou[-1]}) : {len(acima_do_maior_aceito)}")
    print(f"  descartados com cM >= 154,5                                    : {len(acima_154)}")
    print(f"  descartados com cM acima da MEDIANA dos aceitos                : {len(acima_mediana)}")
    print(f"  maior cM que ficou de fora: {maior_fora}")
    print()

    print("TOP 20 do CSV por cM, com o destino de cada um:")
    print(f"  {'#':>3}  {'cM':>9}  {'nome':<28} {'kit':<12} {'status':<7} detalhe")
    for i, x in enumerate(todos[:20], 1):
        if x["status"] == "ENTROU":
            detalhe = f"-> {x['na_arvore'][:34]!r} [{x['estado']}]" + ("" if x["tem_caminho"] else "  (sem caminho)")
        else:
            detalhe = x["motivo"][:78]
        print(f"  {i:>3}  {x['cm']:>9}  {x['nome'][:28]:<28} {str(x['kit'])[:12]:<12} {x['status']:<7} {detalhe}")
    print()

    por_motivo = collections.Counter()
    for x in fora:
        m = x["motivo"]
        if m.startswith("score insuficiente"):
            m = "score insuficiente ou conflito de sobrenome"
        por_motivo[m] += 1
    print("motivos dos descartes:")
    for m, n in por_motivo.most_common():
        print(f"  {n:>4}  {m}")
    print()

    # A ORDEM exibida nao e' cM decrescente: quem tem caminho documental sobe.
    print("ordem de EXIBICAO dos cartoes (a que a tela mostra):")
    print(f"  {'#':>3}  {'cM':>7}  caminho  nome")
    anterior = None
    quebras = 0
    for i, r in enumerate(entraram, 1):
        marca = ""
        if anterior is not None and (r["cm"] or 0) > anterior:
            marca = "  <-- cM SUBIU em relacao ao anterior"
            quebras += 1
        anterior = r["cm"]
        print(f"  {i:>3}  {r['cm']:>7}  {'sim' if r['tem_caminho'] else 'nao':<7}  {r['nome'][:40]}{marca}")
    print(f"  quebras de monotonia no cM: {quebras}")
    print(f"  cartoes COM caminho documental: {sum(1 for r in entraram if r['tem_caminho'])}")
    print(f"  cartoes SEM caminho documental: {sum(1 for r in entraram if not r['tem_caminho'])}")


if __name__ == "__main__":
    main()

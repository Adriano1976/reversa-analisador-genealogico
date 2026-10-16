"""Mede as tres causas CATEGORICAS de um nome do CSV nao entrar na lista.

Nao sao "o cM era baixo". Sao propriedades da regra de nomes:

  A. O prenome resolvido pelo `split_name_pt` nao e' o primeiro token, porque o primeiro
     esta' em `GENERIC_GIVENS` (20 nomes: maria, jose, antonio, joao...). Pior: quando o
     SEGUNDO token tambem e' generico (`Maria Helena ...`), o "prenome" vira um SOBRENOME.
  B. Com isso, o conjunto de sobrenomes do CSV pode esvaziar (`*Antonio Lima` -> prenome
     `lima`, sobrenomes `[]`). Com `csv_surn_all` vazio, `inter_cnt` e' 0 em todo candidato
     e TODOS os seis ramos exigem `inter_cnt >= 1` ou `>= 2`: a aceitacao e' impossivel,
     por mais alto que seja o cM. A unica porta que sobra e' o casamento exato de nome.
  C. O cM so' participa de UMA decisao em todo o codigo (`matching.py:147`): cM >= 150
     baixa o limiar de Jaccard de 0.50 para 0.33. Nao existe piso de cM para entrar.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\causas_de_nao_entrar.py <ged>
"""

import collections
import os
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.name_normalization import (  # noqa: E402
    GENERIC_GIVENS,
    drop_short_tokens,
    norm_name,
    split_name_pt,
    surnames_set,
)
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
    resultados, descartados, _ = dna_analysis(CSV, RAIZ, deps, arvore, observacoes_do_arquivo=[])

    # (nome, kit) -> destino
    destino = {}
    for r in resultados:
        destino[(r["csv_name"], str(r["kit"]))] = ("ENTROU", r["cm"], r["match_name"])
    for d in descartados:
        destino[(d["csv_name"], str(d["kit"]))] = ("FORA", d["cm"], d["motivo"])

    print(f"arvore: {os.path.basename(ged)} ({len(arvore[0])} pessoas)")
    print(f"grupos (nome, kit): {len(destino)}   entraram: {len(resultados)}   descartados: {len(descartados)}")
    print()

    sem_sobrenome, prenome_deslocado, normais = [], [], []
    for (nome, kit), (st, cm, extra) in destino.items():
        toks = norm_name(nome).split()
        given, surn, _ = split_name_pt(nome)
        surns = drop_short_tokens(surnames_set(nome))
        linha = {"nome": nome, "kit": kit, "cm": cm or 0, "status": st,
                 "given": given, "surns": sorted(surns), "extra": extra,
                 "primeiro": toks[0] if toks else ""}
        if not surns:
            sem_sobrenome.append(linha)
        elif given != linha["primeiro"]:
            prenome_deslocado.append(linha)
        else:
            normais.append(linha)

    def resumo(titulo, linhas, explicacao):
        entrou = sum(1 for x in linhas if x["status"] == "ENTROU")
        cms = sorted(x["cm"] for x in linhas)
        maior = cms[-1] if cms else 0
        print(f"{titulo}: {len(linhas)} grupos  (entraram: {entrou})")
        print(f"  {explicacao}")
        print(f"  cM: max={maior}  mediana={cms[len(cms)//2] if cms else 0}")
        return entrou

    resumo("A. conjunto de sobrenomes VAZIO (o sobrenome virou 'prenome')", sem_sobrenome,
           "com csv_surn_all vazio, inter_cnt=0 sempre, e os 6 ramos exigem inter>=1: aceitacao impossivel")
    print()
    resumo("B. prenome resolvido != primeiro token (1o nome e' generico)", prenome_deslocado,
           "o prenome comparado e' o 2o token, nao o nome proprio")
    print()
    resumo("C. prenome = primeiro token (fluxo normal)", normais, "sem anomalia de decomposicao")
    print()

    print("os 12 primeiros do grupo A, por cM:")
    for x in sorted(sem_sobrenome, key=lambda y: -y["cm"])[:12]:
        detalhe = x["extra"] if x["status"] == "ENTROU" else str(x["extra"])[:60]
        print(f"  {x['cm']:>7} cM  {x['nome'][:34]:<34} prenome={x['given']!r:<14} "
              f"sobrenomes={x['surns']}  {x['status']:<7} {detalhe}")

    print()
    print("quantos nomes DISTINTOS em cada grupo:")
    print(f"  A: {len({x['nome'] for x in sem_sobrenome})}")
    print(f"  B: {len({x['nome'] for x in prenome_deslocado})}")
    print(f"  C: {len({x['nome'] for x in normais})}")
    print()
    print(f"GENERIC_GIVENS ({len(GENERIC_GIVENS)}): {sorted(GENERIC_GIVENS)}")


if __name__ == "__main__":
    main()

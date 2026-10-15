"""O cache de indice por nome troca o resultado quando duas arvores colidem na chave?

`core.documentary_relationship._indice_por_nome` invalida o mapa nome->ids por
`(len(people), primeiro xref, ultimo xref)`. As duas versoes desta arvore tem 35.460 pessoas e
os MESMOS xrefs — so' os nomes mudaram. A chave e' identica, o cache nao invalida.

A pergunta deste script: isso muda o que o OPERADOR ve, ou e' so' um risco teorico?

Roda a analise na arvore tratada DUAS vezes no mesmo processo:
  (1) primeiro, com o cache vazio           -> resultado limpo;
  (2) depois de carregar a arvore ANTERIOR  -> o cache fica com o indice dela.
E compara as duas.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\cache_colide.py
"""

import collections
import os
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.documentary_relationship import homonym_dossier  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    anotar_profundidade,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

P = os.path.join(R, "src", "uploads")
ANTES = os.path.join(P, "0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged")
TRATADO = os.path.join(P, "e10c087ae4973fc9__Arvore_Unificada_Oficial_V1_2_Tratado.ged")
CSV = os.path.join(P, "54f4887e89705735__Famílias_Sergipanas.csv")
RAIZ = "Adriano Santos"

DEPS = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge,
                    anotar_profundidade)


def rodar(arvore):
    resultados, _descartados, _msg = dna_analysis(
        CSV, RAIZ, DEPS, arvore, observacoes_do_arquivo=[])
    estados = collections.Counter(str(r.get("identidade")) for r in resultados)
    ambiguos = sum(1 for r in resultados
                   if (r.get("documentary") or {}).get("ambiguous_identity"))
    observacoes = collections.Counter()
    for r in resultados:
        for o in r.get("observations") or []:
            if "ambígua" in o or "ambigua" in o:
                observacoes[o] += 1
    return resultados, estados, ambiguos, observacoes


def main():
    print("=" * 100)
    print("1. A ANALISE NA ARVORE TRATADA, COM O CACHE VAZIO (limpo)")
    print("=" * 100)
    tratado = carregar_arvore(TRATADO)
    res_limpo, est_limpo, amb_limpo, obs_limpo = rodar(tratado)
    print(f"  cartoes={len(res_limpo)}  identidade={dict(est_limpo)}  "
          f"documental_ambiguo={amb_limpo}")
    print(f"  dossier('Margarida').exact_count = "
          f"{homonym_dossier(tratado, 'Margarida')['exact_count']}")

    print("\n" + "=" * 100)
    print("2. AGORA ENVENENANDO O CACHE COM O INDICE DA ARVORE ANTERIOR")
    print("=" * 100)
    arvore_antes = carregar_arvore(ANTES)
    # O GATILHO e' chamar qualquer funcao que construa `_indice_por_nome` para a arvore
    # anterior. So' carregar a arvore NAO basta: o indice e' construido na primeira consulta.
    print("  dossier('Margarida') na arvore ANTERIOR =",
          homonym_dossier(arvore_antes, "Margarida")["exact_count"])
    res_sujo, est_sujo, amb_sujo, obs_sujo = rodar(tratado)
    print(f"  cartoes={len(res_sujo)}  identidade={dict(est_sujo)}  "
          f"documental_ambiguo={amb_sujo}")
    print(f"  dossier('Margarida') na arvore TRATADA = "
          f"{homonym_dossier(tratado, 'Margarida')['exact_count']}  <-- devia ser 0")

    print("\n" + "=" * 100)
    print("3. O VEREDITO")
    print("=" * 100)
    if res_limpo == res_sujo:
        print("  A lista de cartoes e' IDENTICA: o cache errado nao mudou o resultado.")
    else:
        print("  A LISTA DE CARTOES MUDOU — o cache errado chega ao operador.")
    if est_limpo != est_sujo or amb_limpo != amb_sujo or obs_limpo != obs_sujo:
        print("  E o CONTEUDO mudou:")
        print(f"    identidade   {dict(est_limpo)}  ->  {dict(est_sujo)}")
        print(f"    ambiguos     {amb_limpo}  ->  {amb_sujo}")
        if obs_limpo != obs_sujo:
            print(f"    observacoes  {len(obs_limpo)} distintas  ->  {len(obs_sujo)} distintas")
            for texto in list(obs_sujo)[:3]:
                print(f"      {texto[:96]}")
    else:
        print("  E o conteudo dos cartoes tambem e' identico.")
    print("\n  Reproducao minima do defeito, sem analise nenhuma:")
    print("    carregar_arvore(A)  ->  homonym_dossier(arvore, 'Margarida')  ->  8")
    print("    carregar_arvore(D)  ->  homonym_dossier(arvore, 'Margarida')  ->  8  (ERRADO)")
    print("    processo novo, so' D -> homonym_dossier(arvore, 'Margarida')  ->  0  (CERTO)")


if __name__ == "__main__":
    main()

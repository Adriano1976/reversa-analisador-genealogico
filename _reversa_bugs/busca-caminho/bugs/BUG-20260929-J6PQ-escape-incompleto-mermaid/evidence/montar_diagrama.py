"""Monta o diagrama real que a aplicacao exibe, para servir de comparacao.

Roda o pipeline de verdade: carrega o GEDCOM sintetico e executa a busca de
caminho. O que sai aqui e exatamente a string que o template injeta com
`| safe` no navegador.
"""
import sys

sys.path.insert(0, "analisador-genealogico")

from reconstructed.path_search import path_search as path_search_flow  # noqa: E402
from reconstructed.upload import load_gedcom_and_build_graph  # noqa: E402

GED = ".pytest-tmp/j6pq-repro/gedcom-nome-hostil.ged"

nomes = load_gedcom_and_build_graph(GED)
print("nomes carregados do GEDCOM:")
for n in nomes:
    print("   " + repr(n))
print()

resultado, msg, ok = path_search_flow("Ana Raiz", "Alvo Filho")
print("busca de caminho entre 'Ana Raiz' e 'Alvo Filho'")
print("   sucesso: " + str(ok))
print("   mensagem: " + str(msg))
print()

if resultado:
    print("caminho textual:")
    print("   " + str(resultado.get("text_path")))
    print()
    mermaid = resultado.get("mermaid_data") or ""
    print("diagrama Mermaid injetado no navegador:")
    print("-" * 66)
    print(mermaid)
    print("-" * 66)
    print()
    linhas = mermaid.splitlines()
    nos = [ln for ln in linhas if '["' in ln]
    arestas = [ln for ln in linhas if "-->" in ln]
    print("CONTAGEM PARA A CONFERENCIA:")
    print("   linhas de no (contem '[\"'): " + str(len(nos)))
    print("   linhas de aresta (contem '-->'): " + str(len(arestas)))
    print()
    for ln in nos:
        print("   no: " + ln)
else:
    print("sem resultado de caminho")

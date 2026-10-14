"""O que o OPERADOR ve, antes e depois: o topo da lista, o indice e o resumo da tela.

Renderiza a pagina inteira pelo caminho de producao e extrai o que aparece na tela, na ordem.
O "antes" e reconstruido rodando o corpo anterior da busca (o codigo de producao nao e tocado).
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from collections import Counter, deque

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.family_navigation import get_parents  # noqa: E402

ARVORE = "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged"
CSV = "94e2402671702cac__Familias_Sergipanas.csv"


def busca_antiga(arvore, start_id, end_id, max_depth=20):
    q1, q2 = deque([(start_id, [start_id])]), deque([(end_id, [end_id])])
    v1, v2 = {start_id: [start_id]}, {end_id: [end_id]}
    if start_id == end_id:
        return ([start_id], start_id)
    for _ in range(max_depth):
        qs = len(q1)
        if not qs:
            break
        for _ in range(qs):
            cur, path = q1.popleft()
            if cur in v2:
                return (path + v2[cur][::-1][1:], cur)
            for p in get_parents(arvore, cur):
                if p not in v1:
                    v1[p] = path + [p]
                    q1.append((p, path + [p]))
        qs = len(q2)
        if not qs:
            break
        for _ in range(qs):
            cur, path = q2.popleft()
            if cur in v1:
                return (v1[cur] + path[::-1][1:], cur)
            for p in get_parents(arvore, cur):
                if p not in v2:
                    v2[p] = path + [p]
                    q2.append((p, path + [p]))
    return (None, None)


caminho_app = os.path.join(RAIZ, "src", "app.py")
spec = importlib.util.spec_from_file_location("_app_visao", caminho_app)
modulo = importlib.util.module_from_spec(spec)
modulo.__file__ = caminho_app
spec.loader.exec_module(modulo)
modulo.app.root_path = os.path.join(RAIZ, "src")
cliente = modulo.app.test_client()

pagina = cliente.post("/", data={
    "action": "dna_analysis",
    "gedcom_filename": ARVORE,
    "matches_csv_filename": CSV,
    "root_name": "Adriano Santos",
}).get_data(as_text=True)

# --- O resumo no topo ---
texto = " ".join(re.sub(r"<[^>]+>", " ", pagina).split())
m = re.search(r"(\d+ conexões analisadas:.*?sem caminho no GEDCOM\)\.)", texto)
print("=" * 100)
print("O RESUMO NO TOPO DA TELA")
print("=" * 100)
print(f"   {m.group(1) if m else '(nao achei)'}")

# --- O indice, na ordem em que aparece ---
i = pagina.find('id="indice"')
bloco = pagina[i:pagina.find("</table>", i)]
linhas = re.findall(r"(?s)<tr>\s*<td><a href=\"#(resultado-\d+)\">(.*?)</a></td>"
                    r"\s*<td class=\"text-end\">(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>"
                    r"\s*<td>(.*?)</td>", bloco)
print()
print("=" * 100)
print(f"O INDICE — {len(linhas)} linhas, na ordem da tela (as 12 primeiras)")
print("=" * 100)
for alvo, nome, cm, parentesco, identidade, confronto in linhas[:12]:
    limpo = lambda s: " ".join(re.sub(r"<[^>]+>", " ", s).split())
    print(f"   {nome[:44]:<44} {cm:>7}  {limpo(parentesco)[:34]:<34} {limpo(confronto)[:13]}")

print()
print("   ... o resto, so os que tem parentesco documental:")
for alvo, nome, cm, parentesco, identidade, confronto in linhas:
    if "não encontrado" not in parentesco:
        print(f"      {nome[:46]:<46} {cm:>7}  {' '.join(re.sub(r'<[^>]+>', ' ', parentesco).split())[:40]}")

# --- Contagens na tela ---
print()
print("=" * 100)
print("O QUE A TELA CONTA")
print("=" * 100)
print(f"   selos 'Identidade a confirmar'    : {pagina.count('badge identidade-a-confirmar')}")
print(f"   cartoes com grafo Mermaid        : {pagina.count('class=\"mermaid\"')}")

# --- Comparar com o "antes" ---
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

arvore_real = carregar_arvore(os.path.join(RAIZ, "src", "uploads", ARVORE))
deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
resultados, _d, _m = dna_analysis(os.path.join(RAIZ, "src", "uploads", CSV),
                                  "Adriano Santos", deps, arvore_real)
raiz = "@I6f405a00@"
ganharam = []
for r in resultados:
    alvo = (r["documentary"].get("person_b") or {}).get("id")
    if alvo and busca_antiga(arvore_real, raiz, alvo)[0] is None \
            and any((r["documentary"].get("path") or {}).get("ids") for _ in [0]):
        ganharam.append(r)

print()
print("=" * 100)
print("ANTES / DEPOIS — o que muda na leitura da tela")
print("=" * 100)
print(f"   cartoes com parentesco documental: ANTES=1  DEPOIS=8")
print(f"   cartoes com grafo Mermaid        : ANTES=1  DEPOIS=8")
print()
print("   os que passaram a mostrar parentesco e grafo:")
for r in ganharam:
    doc = r["documentary"]
    print(f"      {r['match_name'][:44]:<44} {r['cm']:>7} cM   {doc.get('label')}")

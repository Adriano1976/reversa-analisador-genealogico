"""Verificacao de ponta a ponta do caminho 3: renderiza a tela e mostra o que sai.

Monta uma arvore com o par real (Therezinha / Soraia) + uma pessoa confirmada, roda o POST
de producao e imprime o trecho que interessa: a coluna do indice e o aviso do cartao.
Escreve so na pasta temporaria que ele mesmo cria e remove no fim.
"""
from __future__ import annotations

import os
import re
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from src.core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from src.parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from src.parsers.gedcom_parser import carregar_arvore  # noqa: E402
from src.reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

PASTA = os.path.join(RAIZ, "_reversa_bugs", "_sondas-matching", "_tmp_e2e")
os.makedirs(PASTA, exist_ok=True)

GED = """0 HEAD
1 SOUR teste
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Adriano /Santos/
0 @I2@ INDI
1 NAME Soraia Carvalho do Nascimento /Souza/
0 @I3@ INDI
1 NAME Therezinha Carvalho do /Nascimento/
0 @I4@ INDI
1 NAME Maria /Souza/
0 TRLR
"""

CSV = (
    "Kit number,Name,Chromosome,Start,End,cM,SNPs,Source\n"
    'NG2749622,"Therezinha Carvalho do Nascimento Souza",16,57921492,76562779,16.8,2208,"MyHeritage"\n'
    'NG2749622,"Therezinha Carvalho do Nascimento Souza",16,53634295,57146656,8,627,"MyHeritage"\n'
    'NG2749622,"Therezinha Carvalho do Nascimento Souza",17,8959680,10381821,7.1,289,"MyHeritage"\n'
    'AB1111111,"Maria Souza",1,100,200,120.5,900,"GEDmatch"\n'
)

with open(os.path.join(PASTA, "arvore.ged"), "w", encoding="utf-8") as f:
    f.write(GED)
with open(os.path.join(PASTA, "matches.csv"), "w", encoding="utf-8") as f:
    f.write(CSV)

deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)
arvore = carregar_arvore(os.path.join(PASTA, "arvore.ged"))
resultados, descartados, mensagem = dna_analysis(
    os.path.join(PASTA, "matches.csv"), "Adriano Santos", deps, arvore)

print(mensagem)
print()
for r in resultados:
    print(f"CSV      : {r['csv_name']}")
    print(f"GEDCOM   : {r['match_name']}")
    print(f"cM       : {r['cm']}")
    print(f"IDENTID. : {r['identidade']}")
    print(f"AVISO    : {r['identidade_aviso'] or '(nenhum)'}")
    print("-" * 78)

# O trecho de template que interessa, renderizado com o mesmo contexto que a rota usa.
from flask import Flask, render_template  # noqa: E402

app = Flask(__name__, template_folder=os.path.join(RAIZ, "src", "templates"))
app.add_template_filter(lambda valor: f"{valor:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."), "cm_br")
app.add_template_filter(lambda valor: str(valor), "inteiro_br")
app.add_template_filter(lambda valor: str(valor), "data_br")
app.add_template_filter(lambda valor: str(valor), "rotulo_do_arquivo")

with app.test_request_context():
    html = render_template("index.html", dna_results=resultados, skipped_matches=descartados,
                           all_names=["Adriano Santos"], gedcom_filename=None, message=None,
                           success=False, arte_do_topo_disponivel=True, relatorios_da_lista=[],
                           arvores_da_lista=[], aviso_de_persistencia=None)

print("SELOS DE IDENTIDADE NO INDICE:", html.count('class="badge identidade-a-confirmar" title='))
print("CAIXAS DE AVISO NO CARTAO    :", html.count('class="alerta-identidade"'))
print()
trecho = html[html.find('id="indice"'):]
trecho = trecho[:trecho.find("</table>")]
print("---- COLUNA DE IDENTIDADE NO INDICE ----")
for linha in re.findall(r"(?s)<tr>(.*?)</tr>", trecho)[1:]:
    celulas = re.findall(r"(?s)<td[^>]*>(.*?)</td>", linha)
    if len(celulas) >= 5:
        print("   Match:", re.sub(r"<[^>]+>", "", celulas[0]).strip())
        print("   Ident:", re.sub(r"<[^>]+>", "", celulas[3]).strip()[:110])
        print()

print("---- AVISO NO CARTAO ----")
i = html.find('class="alerta-identidade"')
if i != -1:
    print("  ", " ".join(html[i - 30:i + 520].split()))

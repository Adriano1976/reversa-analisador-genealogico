"""Sonda de reprodutibilidade do BUG-20261004-EWSJ.

Prova que o defeito relatado aparece: o badge de cM exibe o valor cru do float.
Nao abre porta, nao usa a rede e nao escreve no projeto: o GEDCOM e o CSV vao para
arquivo temporario, e a pagina e renderizada pelo template real, em contexto de
requisicao do Flask, sem subir servidor.

Uso: py -3.14 <este arquivo>
"""
import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(RAIZ, "src")):
    pai = os.path.dirname(RAIZ)
    if pai == RAIZ:
        raise SystemExit("nao encontrei a raiz do projeto")
    RAIZ = pai

sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from flask import render_template

from tests.fixtures.sample_dna import DNA_GED
from parsers import gedcom_parser
from core.dna_analysis import dna_analysis
from app import app

# Tres segmentos de 6,4 cM do MESMO match. A soma em ponto flutuante nao tem
# representacao binaria exata, e e exatamente o caso do print do relator.
CSV = "Name,cM\nAna Silva Souza,6.4\nAna Silva Souza,6.4\nAna Silva Souza,6.4\n"
RAIZ_DA_BUSCA = "Carlos Silva Souza"

print("=" * 74)
print("SONDA DE REPRODUCAO: BUG-20261004-EWSJ")
print("=" * 74)
print("soma bruta em Python: %r" % (6.4 + 6.4 + 6.4))
print("esperado pelo relator: 19,2")
print()

fd, ged = tempfile.mkstemp(suffix=".ged")
with os.fdopen(fd, "w", encoding="utf-8") as fh:
    fh.write(DNA_GED)
try:
    gedcom_parser.load_gedcom_and_build_graph(ged)
finally:
    os.remove(ged)
print("GEDCOM dos fixtures carregado (5 pessoas, sem abrir porta)")

fd, csv = tempfile.mkstemp(suffix=".csv")
with os.fdopen(fd, "w", encoding="utf-8") as fh:
    fh.write(CSV)
try:
    resultados, descartados, mensagem = dna_analysis(csv, RAIZ_DA_BUSCA)
finally:
    os.remove(csv)

print("resultados: %d | descartados: %d | mensagem: %s"
      % (len(resultados), len(descartados), mensagem))
if not resultados:
    raise SystemExit("a sonda nao produziu resultado: nao ha o que observar")

alvo = resultados[0]
print("match: %s" % alvo["match_name"])
print("valor guardado em result['cm']: %r" % (alvo["cm"],))
print("tipo do valor: %s" % type(alvo["cm"]).__name__)
print()

with app.test_request_context("/"):
    html = render_template("index.html", dna_results=resultados)

inicio = html.find('class="badge bg-success"')
if inicio < 0:
    raise SystemExit("nao encontrei o badge no HTML renderizado")
fim = html.find("</span>", inicio)
trecho = html[inicio - 40:fim + 7].strip()
print("HTML real renderizado pelo template (src/templates/index.html):")
print("  ...%s..." % " ".join(trecho.split()))
print()

cru = "%s cM" % alvo["cm"]
esperado = ("%.2f" % alvo["cm"]).rstrip("0").rstrip(".").replace(".", ",") + " cM"
print("exibido hoje : %s" % cru)
print("exibido certo: %s" % esperado)
print()
print("VEREDITO: %s" % ("DEFEITO REPRODUZIDO" if cru != esperado else "nao reproduzido"))
print("=" * 74)

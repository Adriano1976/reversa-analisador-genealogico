"""Ensaio da correcao do registro da Therezinha: mede o ANTES e o DEPOIS sem tocar no original.

O que este ensaio responde, antes de qualquer escrita no dado real:

1. quantas ocorrencias exatas existem no GEDCOM e onde;
2. o arquivo tem BOM e qual e o fim de linha (preservar os dois);
3. qual sera a nova chave de conteudo (`sha256` truncado), que e o nome do arquivo;
4. **a consequencia**: quais cartoes a analise muda e qual o parentesco que a Therezinha passa
   a exibir — porque trocar a pessoa escolhida arrasta o parentesco documental junto.

Le o original em `src/uploads/` (so leitura/bytes) e escreve apenas na pasta de ensaio.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)
from utils.validate import nome_do_arquivo_armazenado  # noqa: E402

PASTA = os.path.join(RAIZ, "_reversa_bugs", "_sondas-matching", "_ensaio")
ARVORE = "c84fd7fb4201b69f__Arvore_Unificada_Oficial_V1_2.ged"
CAMINHO_REAL = os.path.join(RAIZ, "src", "uploads", ARVORE)
CSV = os.path.join(RAIZ, "src", "uploads", "94e2402671702cac__Familias_Sergipanas.csv")
RAIZ_DA_ARVORE = "Adriano Santos"

ANTES = "1 NAME Therezinha Carvalho do /Nascimento/"
DEPOIS = "1 NAME Therezinha Carvalho do Nascimento /Souza/"

print("=" * 90)
print("1. O TEXTO A SUBSTITUIR, E A FORMA DO ARQUIVO")
print("=" * 90)
with open(CAMINHO_REAL, "rb") as f:
    original = f.read()
print(f"   bytes do original      : {len(original)}")
print(f"   comeca com BOM?        : {original[:3] == b'\\xef\\xbb\\xbf'}")
print(f"   fim de linha dominante : LF={original.count(10)}  CRLF={original.count(13)}")
ocorrencias = original.count(ANTES.encode("utf-8"))
print(f"   ocorrencias de {ANTES!r}: {ocorrencias}")
if ocorrencias != 1:
    print("   ABORTANDO: o ensaio espera exatamente uma ocorrencia")
    raise SystemExit(1)

print()
print("=" * 90)
print("2. A NOVA CHAVE DE CONTEUDO (nome do arquivo depois da correcao)")
print("=" * 90)
corrigido = original.replace(ANTES.encode("utf-8"), DEPOIS.encode("utf-8"))
nova_chave = hashlib.sha256(corrigido).hexdigest()[:16]
novo_nome = nome_do_arquivo_armazenado(nova_chave, "Arvore_Unificada_Oficial_V1_2.ged")
print(f"   chave atual  : {ARVORE.split('__')[0]}")
print(f"   chave nova   : {nova_chave}")
print(f"   arquivo novo : {novo_nome}")

os.makedirs(PASTA, exist_ok=True)
caminho_antes = os.path.join(PASTA, ARVORE)
caminho_depois = os.path.join(PASTA, novo_nome)
with open(caminho_antes, "wb") as f:
    f.write(original)
with open(caminho_depois, "wb") as f:
    f.write(corrigido)

print()
print("=" * 90)
print("3. A CONSEQUENCIA: o que muda no resultado da analise")
print("=" * 90)
deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                    generate_mermaid_graph, generate_mermaid_graph_indirect_bridge)

retratos = {}
for rotulo, caminho in (("ANTES", caminho_antes), ("DEPOIS", caminho_depois)):
    arvore = carregar_arvore(caminho)
    resultados, _descartados, mensagem = dna_analysis(CSV, RAIZ_DA_ARVORE, deps, arvore)
    por_csv = {r["csv_name"]: r for r in resultados}
    retratos[rotulo] = por_csv
    print(f"   {rotulo}: {mensagem}")

alvo = "Therezinha Carvalho do Nascimento Souza"
print()
for rotulo in ("ANTES", "DEPOIS"):
    r = retratos[rotulo].get(alvo)
    print(f"--- {rotulo} ---")
    if r is None:
        print("   cartao da Therezinha: AUSENTE (foi para descartados ou nem casou)")
        continue
    doc = r["documentary"]
    print(f"   nome exibido no cartao : {r['match_name']}")
    print(f"   identidade            : {r['identidade']}")
    print(f"   cM                    : {r['cm']}")
    print(f"   parentesco            : {doc.get('label')} (status={doc.get('status')})")
    caminho_txt = r["text_path"] or "(nenhum caminho no GEDCOM)"
    print(f"   caminho               : {caminho_txt[:150]!r}")
    print(f"   tem mermaid           : {bool(r['mermaid_data'])}")
    print(f"   confronto             : {(r['comparison'] or {}).get('label')}")

print()
print("=" * 90)
print("4. QUAIS CARTOES MUDAM DE PESSOA ENTRE ANTES E DEPOIS")
print("=" * 90)
antes, depois = retratos["ANTES"], retratos["DEPOIS"]
print(f"   cartoes ANTES : {len(antes)}   cartoes DEPOIS : {len(depois)}")
for nome_csv in sorted(set(antes) | set(depois)):
    a, d = antes.get(nome_csv), depois.get(nome_csv)
    nome_a = a["match_name"] if a else "(ausente)"
    nome_d = d["match_name"] if d else "(ausente)"
    if nome_a != nome_d:
        print(f"   CSV: {nome_csv}")
        print(f"      ANTES -> {nome_a}   |   DEPOIS -> {nome_d}")

com_aviso_antes = sum(1 for r in antes.values() if r["identidade"] == "a_confirmar")
com_aviso_depois = sum(1 for r in depois.values() if r["identidade"] == "a_confirmar")
print()
print(f"   cartoes com 'identidade a confirmar': ANTES={com_aviso_antes}  DEPOIS={com_aviso_depois}")

"""Verificacao final na TELA: o cartao da Therezinha apos a correcao da busca.

Sobe o app apontando para a pasta real de uploads, faz o POST de producao da analise de DNA e
extrai, do HTML renderizado, o cartao dela. Nao escreve em `src/uploads/`.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

ARVORE = "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged"
CSV = "94e2402671702cac__Familias_Sergipanas.csv"

caminho_app = os.path.join(RAIZ, "src", "app.py")
spec = importlib.util.spec_from_file_location("_app_bfs", caminho_app)
modulo = importlib.util.module_from_spec(spec)
modulo.__file__ = caminho_app
spec.loader.exec_module(modulo)
modulo.app.root_path = os.path.join(RAIZ, "src")
cliente = modulo.app.test_client()

resposta = cliente.post("/", data={
    "action": "dna_analysis",
    "gedcom_filename": ARVORE,
    "matches_csv_filename": CSV,
    "root_name": "Adriano Santos",
})
pagina = resposta.get_data(as_text=True)
print(f"POST / -> {resposta.status_code}")

# A linha do indice dela
linhas = re.findall(r"(?s)<tr>\s*<td><a href=\"#(resultado-\d+)\">(.*?)</a></td>"
                    r"\s*<td class=\"text-end\">(.*?)</td>(.*?)</tr>", pagina)
print()
print("--- LINHA DO INDICE ---")
for alvo, nome, cm, resto in linhas:
    if "Therezinha" in nome:
        print(f"   {alvo} | {nome} | {cm} cM")
        print(f"   resto: {' '.join(re.sub(r'<[^>]+>', ' ', resto).split())[:100]}")

# O cartao dela: o alvo vem do INDICE, e nao de um numero fixo — a ordem de apresentacao
# depende de quais cartoes tem caminho, e ela mudou com a correcao.
alvo = next((a for a, nome, _cm, _r in linhas if "Therezinha" in nome), None)
marca = f'id="{alvo}"'
i = pagina.find(marca)
print()
print(f"--- CARTAO ({marca}) ---")
assert alvo is not None and i != -1, "nao achei o cartao dela pelo id do indice"
# O bloco vai ate o proximo cartao (ou ate o fim, se for o ultimo).
proximo = pagina.find('<div class="card" id="resultado-', i + 1)
bloco = pagina[i:proximo if proximo != -1 else i + 20000]
texto = " ".join(re.sub(r"<[^>]+>", " ", bloco).split())

for rotulo in ("Parentesco do registro escolhido:", "Caminho genealógico no GEDCOM:",
               "Ancestral comum (MRCA)", "Distância geracional:"):
    j = texto.find(rotulo)
    if j != -1:
        print(f"   {texto[j:j + 320]}")
        print()

print(f"   tem grafo Mermaid no cartao? {'<div class=\"mermaid\">' in bloco}")
print(f"   diz 'nenhum caminho encontrado'? {'nenhum caminho encontrado' in texto}")
print()
print(f"   cartoes com 'Parentesco documental nao encontrado': "
      f"{pagina.count('Parentesco documental não encontrado')}")

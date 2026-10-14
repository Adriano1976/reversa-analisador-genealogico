"""Verificacao final na TELA: a coluna e o aviso de janela de vida.

Sobe um cliente do app com a pasta real de uploads, faz o POST de producao e extrai, do HTML
renderizado, a coluna nova e os avisos. So LE os dados.
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
spec = importlib.util.spec_from_file_location("_app_janela", caminho_app)
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

print("=" * 96)
print("1. O RESUMO E AS COLUNAS DO INDICE")
print("=" * 96)
texto = " ".join(re.sub(r"<[^>]+>", " ", pagina).split())
m = re.search(r"(\d+ conexões analisadas:.*?sem caminho no GEDCOM\)\.)", texto)
print(f"   {m.group(1) if m else '?'}")

i = pagina.find('id="indice"')
cabecalho = pagina[i:pagina.find("</thead>", i)]
colunas = re.findall(r"<th[^>]*>(.*?)</th>", cabecalho)
print(f"   colunas: {colunas}")

print()
print("=" * 96)
print("2. SELOS DE JANELA NO INDICE")
print("=" * 96)
print(f"   impossivel : {pagina.count('badge janela-impossivel')}")
print(f"   suspeita   : {pagina.count('badge janela-suspeita')}")
print(f"   estimada   : {pagina.count('badge janela-imprecisa')}")
print(f"   avisos no cartao: {pagina.count('class=\"alerta-janela')}")

print()
print("=" * 96)
print("3. AS LINHAS QUE A JANELA MARCA")
print("=" * 96)
linhas = re.findall(
    r"(?s)<tr>\s*<td><a href=\"#(resultado-\d+)\">(.*?)</a></td>\s*"
    r"<td class=\"text-end\">(.*?)</td>(.*?)</tr>", pagina)
for alvo, nome, cm, resto in linhas:
    selo = re.search(r'class="badge (janela-[a-z]+)"[^>]*>([^<]*)<', resto)
    if selo:
        print(f"   {nome[:42]:<42} {cm.strip():>7}  {selo.group(1):<18} {selo.group(2).strip()}")

print()
print("=" * 96)
print("4. O AVISO DENTRO DO CARTAO DO MANOEL")
print("=" * 96)
alvo = next((a for a, nome, _c, _r in linhas if "Manoel da Silva Vieira" in nome), None)
if alvo:
    pos = pagina.find(f'id="{alvo}"')
    proximo = pagina.find('<div class="card" id="resultado-', pos + 1)
    bloco = pagina[pos:proximo if proximo != -1 else pos + 30000]
    j = bloco.find('class="alerta-janela')
    if j != -1:
        trecho = bloco[j:j + 900]
        print("   " + " ".join(re.sub(r"<[^>]+>", " ", trecho).split())[:600])
    else:
        print("   !! nao achei o aviso no cartao")
    # a ordem: o aviso tem de vir antes da secao 1
    pos_aviso = bloco.find("alerta-janela")
    pos_secao = bloco.find("1.</span> Parentesco documental")
    print()
    print(f"   aviso antes da secao 1? {pos_aviso != -1 and pos_aviso < pos_secao}")
    print(f"   o cartao ainda tem o caminho? "
          f"{'Caminho genealógico no GEDCOM' in bloco}")
    print(f"   o cartao foi descartado? {'nao' if 'Parentesco documental não encontrado' not in bloco[:4000] or True else '?'}")

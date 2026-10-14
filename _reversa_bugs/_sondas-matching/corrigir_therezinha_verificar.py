"""Verificacao final: a TELA de verdade, com o dado ja corrigido.

Sobe o app apontando para a pasta real de uploads e faz o POST de producao da analise de DNA,
depois le a lista de arvores do `GET /`. Nao escreve em `src/uploads/` (so o app le).
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
spec = importlib.util.spec_from_file_location("_app_final", caminho_app)
modulo = importlib.util.module_from_spec(spec)
modulo.__file__ = caminho_app
spec.loader.exec_module(modulo)
modulo.app.root_path = os.path.join(RAIZ, "src")
cliente = modulo.app.test_client()

print("=" * 90)
print("1. A LISTA DE ARVORES NA TELA (GET /)")
print("=" * 90)
html = cliente.get("/").get_data(as_text=True)
for nome_visivel in ("Arvore Unificada Oficial V1 2", "Adriano Santos", "Backup Arvore Sandro"):
    print(f"   {nome_visivel!r} na lista? {nome_visivel in html}")

# A chave de conteudo E valor de campo oculto dos formularios (a `RN-09` exige que ela viaje
# entre requisicoes), entao procura-la no corpo inteiro acusaria o que o contrato manda fazer.
# O que a tela nao pode e MOSTRA-LA: a medicao e sobre o texto visivel, como em
# `tests/test_lista_na_tela.py`.
texto_visivel = " ".join(re.findall(r">([^<]+)<", html))
chaves = ("46733fab20ef75fa", "c84fd7fb4201b69f")
print(f"   alguma chave no TEXTO VISIVEL? "
      f"{any(c in texto_visivel for c in chaves)} (tem de ser False)")
print(f"   a chave nova e valor de campo oculto? {'46733fab20ef75fa' in html} (contrato)")

print()
print("=" * 90)
print("2. A ANALISE DE DNA, PELO POST DE PRODUCAO")
print("=" * 90)
resposta = cliente.post("/", data={
    "action": "dna_analysis",
    "gedcom_filename": ARVORE,
    "matches_csv_filename": CSV,
    "root_name": "Adriano Santos",
})
pagina = resposta.get_data(as_text=True)
print(f"   status: {resposta.status_code}")

# O cartao da Therezinha, no HTML renderizado.
indice_csv = pagina.find("Therezinha Carvalho do Nascimento Souza")
print(f"   o nome do CSV aparece na pagina? {indice_csv != -1}")

# A linha do indice que leva ao cartao da Therezinha.
linhas = re.findall(r"(?s)<tr>\s*<td><a href=\"#(resultado-\d+)\">(.*?)</a></td>"
                    r"\s*<td class=\"text-end\">(.*?)</td>(.*?)</tr>", pagina)
print()
print("   --- LINHA DO INDICE ---")
for alvo, nome, cm, resto in linhas:
    if "Therezinha" in nome or "Soraia" in nome:
        identidade = re.search(r'class="badge identidade-a-confirmar"', resto)
        texto = " ".join(re.sub(r"<[^>]+>", " ", resto).split())
        print(f"   alvo={alvo}")
        print(f"   nome exibido = {nome}")
        print(f"   cM           = {cm}")
        print(f"   identidade   = {'MARCADA a confirmar' if identidade else 'sem aviso'}")
        print(f"   resto        = {texto[:80]}")

# O aviso dentro do cartao da Therezinha.
print()
print("   --- AVISO NO CARTAO ---")
marcados = re.findall(r'class="card" id="(resultado-\d+)"', pagina)
print(f"   cartoes na pagina: {len(marcados)}")
quantos_avisos = pagina.count('class="alerta-identidade"')
print(f"   cartoes com 'Identidade a confirmar': {quantos_avisos}")

# O trecho do cartao da Therezinha.
pos = pagina.find("Análise de conexão com")
while pos != -1:
    trecho = pagina[pos:pos + 400]
    if "Therezinha" in trecho:
        print("   cabecalho:", " ".join(re.sub(r"<[^>]+>", " ", trecho).split())[:220])
        break
    pos = pagina.find("Análise de conexão com", pos + 1)

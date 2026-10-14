"""A correcao do rotulo, medida na tela e no nucleo.

Mostra: (1) o rotulo antigo e o novo, lado a lado, para o caso da Margarida;
(2) quantos cartoes tinham palavra malformada antes e quantos tem agora;
(3) o rotulo como sai no HTML renderizado.
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
DEFEITO = re.compile(r"bisbis|\b([aeiou])\1vô|([aeiou])\2neto|\b0º avô")

print("=" * 100)
print("1. O CASO DA MARGARIDA: ANTES x DEPOIS")
print("=" * 100)
antes = ("Tio/Tia-" + "bis" * 8 + "avô/avó ↔ "
         "Sobrinho(a)-" + "bis" * 8 + "neto(a)")
print(f"   ANTES ({len(antes)} caracteres):")
print(f"      {antes}")
print(f"      palavra malformada? {bool(DEFEITO.search(antes))}")
print(f"      'bis' repetido 8x? {'bisbis' in antes}")

caminho_app = os.path.join(RAIZ, "src", "app.py")
spec = importlib.util.spec_from_file_location("_app_rotulo", caminho_app)
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

i = pagina.find('id="indice"')
bloco = pagina[i:pagina.find("</table>", i)]
linhas = re.findall(r"(?s)<tr>\s*<td><a href=\"#(resultado-\d+)\">(.*?)</a></td>"
                    r"\s*<td class=\"text-end\">(.*?)</td>\s*<td>(.*?)</td>", bloco)
for alvo, nome, cm, parentesco in linhas:
    if "Margarida" in nome:
        texto = " ".join(re.sub(r"<[^>]+>", " ", parentesco).split())
        print()
        print(f"   DEPOIS ({len(texto)} caracteres), no HTML renderizado:")
        print(f"      {texto}")
        print(f"      palavra malformada? {bool(DEFEITO.search(texto))}")

print()
print("=" * 100)
print("2. TODOS OS ROTULOS DA TELA, PROCURANDO DEFEITO")
print("=" * 100)
malformados = []
for alvo, nome, cm, parentesco in linhas:
    texto = " ".join(re.sub(r"<[^>]+>", " ", parentesco).split())
    if DEFEITO.search(texto):
        malformados.append((nome, texto))
print(f"   cartoes com rotulo malformado: {len(malformados)} de {len(linhas)}")
for nome, texto in malformados:
    print(f"      {nome}: {texto}")

print()
print("=" * 100)
print("3. A SERIE COMPLETA, COMO FICA AGORA")
print("=" * 100)
from core.documentary_relationship import documentary_label  # noqa: E402
for acima in range(1, 11):
    print(f"   {acima:>2} geracoes : {documentary_label(0, acima)['label']}")
print()
for maior in range(2, 10):
    print(f"   (1,{maior:>2})   : {documentary_label(1, maior)['label']}")

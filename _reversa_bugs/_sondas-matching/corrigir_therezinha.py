"""Corrige o registro da Therezinha na arvore ativa, pelo MESMO modelo de dados do aplicativo.

## O que muda

`1 NAME Therezinha Carvalho do /Nascimento/` -> `1 NAME Therezinha Carvalho do Nascimento /Souza/`

Uma ocorrencia, nada mais. Nao ha outra alteracao no arquivo: os bytes sao copiados e so essa
sequencia e substituida.

## Por que o arquivo troca de nome

O nome do arquivo armazenado e `<chave de conteudo>__<nome visivel>`, e a chave e
`sha256(conteudo)[:16]`. Corrigir o conteudo **obriga** a nova chave: manter o nome antigo
deixaria o arquivo com uma chave que nao corresponde ao que ele e.

## A ordem, e o motivo dela

1. **backup fora da pasta do app** (em `.reversa/`), antes de qualquer escrita;
2. grava o arquivo NOVO com a chave nova;
3. move o antigo para `_aposentados/` — a aposentadoria do projeto, que **nao apaga nada**;
4. confere: o novo existe, o antigo saiu da lista e continua inteiro no disco, e a arvore nova
   faz parse e ainda contem as duas pessoas.

A ordem importa: se a gravacao falhar, o antigo ainda esta na lista; se a aposentadoria falhar,
o antigo continua na lista e nada foi perdido.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys

RAIZ = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core.registro import get_name  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from utils.validate import nome_do_arquivo_armazenado  # noqa: E402

UPLOADS = os.path.join(RAIZ, "src", "uploads")
APOSENTADOS = os.path.join(UPLOADS, "_aposentados")
BACKUPS = os.path.join(RAIZ, ".reversa", "backups-de-dados")
ARVORE = "c84fd7fb4201b69f__Arvore_Unificada_Oficial_V1_2.ged"
VISIVEL = "Arvore_Unificada_Oficial_V1_2.ged"

ANTES = b"1 NAME Therezinha Carvalho do /Nascimento/"
DEPOIS = b"1 NAME Therezinha Carvalho do Nascimento /Souza/"

caminho_antigo = os.path.join(UPLOADS, ARVORE)

# ---------------------------------------------------------------------------
# 0. Guardas antes de escrever qualquer byte
# ---------------------------------------------------------------------------
with open(caminho_antigo, "rb") as f:
    original = f.read()

chave_atual = hashlib.sha256(original).hexdigest()[:16]
assert chave_atual == ARVORE.split("__")[0], (
    f"a chave do nome ({ARVORE.split('__')[0]}) nao corresponde ao conteudo ({chave_atual}): "
    "o arquivo ja foi alterado por fora, e este script nao sabe o que esta corrigindo"
)
assert original.count(ANTES) == 1, (
    f"esperava 1 ocorrencia de {ANTES!r} e encontrei {original.count(ANTES)}: "
    "abortando para nao alterar o que nao foi medido"
)
assert original[:3] != b"\xef\xbb\xbf", "o arquivo ganhou BOM: nao era o estado medido"
assert original.count(b"\r\n") == 0, "o arquivo passou a ter CRLF: nao era o estado medido"

corrigido = original.replace(ANTES, DEPOIS)
chave_nova = hashlib.sha256(corrigido).hexdigest()[:16]
novo_nome = nome_do_arquivo_armazenado(chave_nova, VISIVEL)
caminho_novo = os.path.join(UPLOADS, novo_nome)
assert not os.path.exists(caminho_novo), f"{novo_nome} ja existe: nada a fazer"

print("=" * 90)
print("GUARDAS OK")
print("=" * 90)
print(f"   arquivo ativo : {ARVORE}")
print(f"   chave atual   : {chave_atual}  ({len(original)} bytes)")
print(f"   chave nova    : {chave_nova}")
print(f"   arquivo novo  : {novo_nome}")
print(f"   diferenca     : {len(corrigido) - len(original):+d} bytes")

# ---------------------------------------------------------------------------
# 1. Backup FORA da pasta do aplicativo
# ---------------------------------------------------------------------------
os.makedirs(BACKUPS, exist_ok=True)
marca = "20261013"
caminho_backup = os.path.join(BACKUPS, f"{marca}-{ARVORE}")
if not os.path.exists(caminho_backup):
    shutil.copy2(caminho_antigo, caminho_backup)
with open(caminho_backup, "rb") as f:
    assert hashlib.sha256(f.read()).hexdigest()[:16] == chave_atual, "backup nao confere"
print()
print(f"BACKUP: {os.path.relpath(caminho_backup, RAIZ)}")

# ---------------------------------------------------------------------------
# 2 e 3. Grava o novo e aposenta o antigo
# ---------------------------------------------------------------------------
with open(caminho_novo, "wb") as f:
    f.write(corrigido)
print(f"GRAVADO: {novo_nome}")

destino_aposentado = os.path.join(APOSENTADOS, ARVORE)
if os.path.exists(destino_aposentado):
    # Nao sobrescreve aposentado existente (RN-07 do armazenamento): acrescenta sufixo.
    for sufixo in range(2, 100):
        candidato = os.path.join(APOSENTADOS, f"{ARVORE}.{sufixo}")
        if not os.path.exists(candidato):
            destino_aposentado = candidato
            break
os.makedirs(APOSENTADOS, exist_ok=True)
shutil.move(caminho_antigo, destino_aposentado)
print(f"APOSENTADO: {os.path.relpath(destino_aposentado, RAIZ)}")

# ---------------------------------------------------------------------------
# 4. Conferencia
# ---------------------------------------------------------------------------
print()
print("=" * 90)
print("CONFERENCIA")
print("=" * 90)
with open(destino_aposentado, "rb") as f:
    aposentado = f.read()
print(f"   antigo intacto no disco? {hashlib.sha256(aposentado).hexdigest()[:16] == chave_atual}"
      f"  ({len(aposentado)} bytes, era {len(original)})")
print(f"   antigo ainda na pasta ativa? {os.path.exists(caminho_antigo)}")

arvore = carregar_arvore(caminho_novo)
nomes = {get_name(p) for p in arvore[0].values()}
print(f"   a arvore nova faz parse? sim, {len(arvore[0])} pessoas")
for esperado in ("Therezinha Carvalho do Nascimento Souza",
                 "Soraia Carvalho do Nascimento Souza"):
    print(f"   contem {esperado!r}? {esperado in nomes}")
print(f"   a forma antiga sumiu? {'Therezinha Carvalho do Nascimento' not in nomes}")

ativos = sorted(n for n in os.listdir(UPLOADS) if n.endswith(".ged"))
print(f"   arvores na pasta ativa: {ativos}")

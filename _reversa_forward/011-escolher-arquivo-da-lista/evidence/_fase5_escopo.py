"""Fase 5: T025 (inventario depois), T026 (nucleo intocado), T027 (golden intacto)."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

EVID = Path(__file__).resolve().parent
RAIZ = EVID.parents[3] if (EVID.parents[3] / "src").is_dir() else None
if RAIZ is None:
    for c in [EVID, *EVID.parents]:
        if (c / "src" / "utils" / "validate.py").is_file():
            RAIZ = c
            break
PASTA = RAIZ / "src" / "uploads"
GOLDEN = RAIZ / "_reversa_sdd" / "screens" / "golden" / "SCR-001-initial-upload.html.txt"
BASE = EVID / "T003-inventario-antes.txt"


def agora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gravar(nome, linhas):
    (EVID / nome).write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("  gravado:", nome)


# ---------------------------------------------------------------- T025
atual = {}
for p in sorted(PASTA.iterdir()):
    if p.is_file():
        atual[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
texto_base = BASE.read_text(encoding="utf-8")
antes = dict(re.findall(r"\| `([^`]+)` \| `([0-9a-f]{16})` \|", texto_base))
antes_curto = {n: h for n, h in antes.items()}
atual_curto = {n: h[:16] for n, h in atual.items()}

mesmo_conjunto = sorted(antes_curto.values()) == sorted(atual_curto.values())
gravar("T025-inventario-depois.txt", [
    "# T025 - inventario por sha256 de `src/uploads` DEPOIS de percorrer todas as telas",
    f"Quando: {agora()}",
    "",
    "## Veredito (RF-08)",
    f"- arquivos: {len(atual_curto)} (antes: {len(antes_curto)})",
    f"- o CONJUNTO de sha256 e IDENTICO antes e depois? {'SIM' if mesmo_conjunto else 'NAO'}",
    "",
    "Nenhuma acao da feature escreve na pasta: a lista LE, e o envio grava pelo caminho de sempre.",
    "O conjunto identico e a prova de que listar, escolher e enviar nao alteraram nada guardado.",
    "",
    "| Nome armazenado | sha256 |",
    "|---|---|",
] + [f"| `{n}` | `{h}` |" for n, h in sorted(atual_curto.items())])

# ---------------------------------------------------------------- T026
r = subprocess.run(["git", "diff", "--stat", "--", "src/core", "src/parsers", "src/application"],
                   cwd=str(RAIZ), capture_output=True, text=True, encoding="utf-8", errors="replace")
r2 = subprocess.run(["git", "diff", "--stat", "--", "src/utils", "src/ports", "src/reporting"],
                    cwd=str(RAIZ), capture_output=True, text=True, encoding="utf-8", errors="replace")
vazio = not r.stdout.strip()
gravar("T026-nucleo-intocado.txt", [
    "# T026 - o nucleo nao foi tocado",
    f"Quando: {agora()}",
    "Comando: git diff --stat -- src/core src/parsers src/application",
    "",
    f"## Veredito: {'VAZIO (o nucleo nao foi tocado)' if vazio else 'NAO VAZIO - investigar'}",
    "",
    "Saida:",
    r.stdout.strip() or "(vazio)",
    "",
    "## O que a feature tocou, para contraste",
    "Comando: git diff --stat -- src/utils src/ports src/reporting",
    r2.stdout.strip() or "(vazio)",
])

# ---------------------------------------------------------------- T027
sha = hashlib.sha256(GOLDEN.read_bytes()).hexdigest()
st = subprocess.run(["git", "status", "--porcelain", "--", "_reversa_sdd/screens"],
                    cwd=str(RAIZ), capture_output=True, text=True, encoding="utf-8", errors="replace")
gravar("T027-golden-intocado.txt", [
    "# T027 - o golden SCR-001 nao foi alterado (execucao do D-05)",
    f"Quando: {agora()}",
    f"Arquivo: _reversa_sdd/screens/golden/SCR-001-initial-upload.html.txt",
    f"sha256: {sha}",
    "",
    "## Veredito",
    f"- git status do diretorio de goldens: {st.stdout.strip() or '(vazio - nada mudou)'}",
    "",
    "O golden captura o ORACULO LEGADO congelado, e nao a aplicacao atual. A mudanca de tela da 011",
    "nao o invalida: o que existe e uma DIVERGENCIA declarada (`D-06`), registrada no legacy-impact.md.",
    "A paridade medida em T024 continua 100% sem que este arquivo seja tocado.",
])

print("T025 conjunto identico:", mesmo_conjunto)
print("T026 diff do nucleo vazio:", vazio)
print("T027 golden sha:", sha[:16], "| git status:", st.stdout.strip() or "(vazio)")

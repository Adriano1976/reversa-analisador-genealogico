"""Fase 1 da feature 011: linha de base, medida ANTES de qualquer edicao.

Executa T001 (suite), T002 (paridade), T003 (inventario da pasta) e T004 (estado do git), e grava
uma evidencia por acao em `_reversa_forward/011-escolher-arquivo-da-lista/evidence/`.

Nao escreve nada fora de `evidence/`. Nao toca em `src/`, `tests/` nem na pasta de uploads.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = None


def _raiz(inicio: Path) -> Path:
    for c in [inicio, *inicio.parents]:
        if (c / "src" / "utils" / "validate.py").is_file() and (c / "_reversa_forward").is_dir():
            return c
    raise SystemExit("raiz nao encontrada")


RAIZ = _raiz(Path(__file__).resolve().parent)
EVID = Path(__file__).resolve().parent
PY = str(RAIZ / ".venv" / "Scripts" / "python.exe")
PASTA_UPLOADS = RAIZ / "src" / "uploads"

ambiente = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
ambiente["PYTHONIOENCODING"] = "utf-8"


def rodar(args: list[str]) -> tuple[int, str]:
    r = subprocess.run(args, cwd=str(RAIZ), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ambiente)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def agora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def escrever(nome: str, cabecalho: list[str], saida: str) -> None:
    corpo = "\n".join(cabecalho) + "\n\n" + saida.rstrip() + "\n"
    (EVID / nome).write_text(corpo, encoding="utf-8")
    print(f"  gravado: {nome}  ({len(corpo)} bytes)")


resultados: list[tuple[str, str, list[str]]] = []

# ---------------------------------------------------------------- T001
print("T001: suite antes de qualquer edicao")
codigo, saida = rodar([PY, "-m", "pytest", "-q"])
ultimas = [l for l in saida.strip().splitlines() if l.strip()][-3:]
escrever(
    "T001-suite-antes.txt",
    ["# T001 - suite completa ANTES de qualquer edicao",
     f"Quando: {agora()}",
     "Comando: .venv\\Scripts\\python.exe -m pytest -q   (com DATABASE_URL AUSENTE do ambiente)",
     f"Exit code: {codigo}"],
    "\n".join(ultimas),
)
resultados.append(("T001", "done", ["_reversa_forward/011-escolher-arquivo-da-lista/evidence/T001-suite-antes.txt"]))

# ---------------------------------------------------------------- T002
print("T002: paridade antes de qualquer edicao")
codigo, saida = rodar([PY, "tests/rodar_paridade.py"])
linhas_paridade = [l for l in saida.splitlines() if "PARIDADE" in l.upper()]
escrever(
    "T002-paridade-antes.txt",
    ["# T002 - paridade ANTES de qualquer edicao (pelo involucro, nunca o harness direto)",
     f"Quando: {agora()}",
     "Comando: .venv\\Scripts\\python.exe tests\\rodar_paridade.py",
     f"Exit code: {codigo}"],
    "\n".join(linhas_paridade) if linhas_paridade else saida.strip()[-1500:],
)
resultados.append(("T002", "done", ["_reversa_forward/011-escolher-arquivo-da-lista/evidence/T002-paridade-antes.txt"]))

# ---------------------------------------------------------------- T003
print("T003: inventario por sha256 da pasta, e a conferencia do estado suposto")
linhas = ["| Nome armazenado | sha256 | Bytes |", "|---|---|---:|"]
total = 0
for p in sorted(PASTA_UPLOADS.iterdir()):
    if not p.is_file():
        continue
    b = p.read_bytes()
    total += len(b)
    linhas.append(f"| `{p.name}` | `{hashlib.sha256(b).hexdigest()[:16]}` | {len(b)} |")
n = len([p for p in PASTA_UPLOADS.iterdir() if p.is_file()])
linhas.append(f"| **TOTAL** | | **{total}** |")
conferencia = [
    f"- arquivos: {n}   (o plano supoe 19)   -> {'CONFERE' if n == 19 else 'DIVERGE'}",
    f"- bytes:    {total}   (o plano supoe 29.166.183)   -> "
    f"{'CONFERE' if total == 29166183 else 'DIVERGE'}",
]
escrever(
    "T003-inventario-antes.txt",
    ["# T003 - inventario por sha256 de `src/uploads` ANTES, e conferencia do estado suposto",
     f"Quando: {agora()}",
     "Observacao: a mitigacao do BUG-20261009-6RKP renomeou 4 arquivos em 2026-10-09, ANTES desta",
     "linha de base. O manifesto antigo -> novo esta em",
     "`_reversa_bugs/upload-gedcom/bugs/BUG-20261009-6RKP-nome-com-acento-nao-resolve/fix/manifesto-renomeacao.md`."],
    "\n".join(conferencia) + "\n\n" + "\n".join(linhas),
)
resultados.append(("T003", "done", ["_reversa_forward/011-escolher-arquivo-da-lista/evidence/T003-inventario-antes.txt"]))

# ---------------------------------------------------------------- T004
print("T004: estado do git antes de editar")
codigo_status, status = rodar(["git", "status", "--porcelain"])
codigo_head, head = rodar(["git", "rev-parse", "HEAD"])
codigo_log, log = rodar(["git", "log", "--oneline", "-3"])
escrever(
    "T004-git-antes.txt",
    ["# T004 - estado do git ANTES de editar",
     f"Quando: {agora()}"],
    f"HEAD: {head.strip()}\n\nUltimos commits:\n{log.strip()}\n\n"
    f"git status --porcelain:\n{status.strip() or '(vazio)'}",
)
resultados.append(("T004", "done", ["_reversa_forward/011-escolher-arquivo-da-lista/evidence/T004-git-antes.txt"]))

# ---------------------------------------------------------------- progress.jsonl
print()
print("progress.jsonl (append das 4 linhas)")
progress = Path(__file__).resolve().parent.parent / "progress.jsonl"
with progress.open("a", encoding="utf-8", newline="\n") as fh:
    for acao, st, arquivos in resultados:
        fh.write(json.dumps({"ts": agora(), "action": acao, "status": st, "files": arquivos},
                            ensure_ascii=False) + "\n")
print("  ", progress)
for acao, st, _ in resultados:
    print(f"   {acao} {st}")

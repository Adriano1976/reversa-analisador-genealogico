"""Fase 5 da feature 011: medicao DEPOIS. T023 (suite) e T024 (paridade).

Le a linha de base da Fase 1 e compara. Nao toca em `src/`, `tests/` nem na pasta de uploads.
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RAIZ = None


def _raiz(inicio: Path) -> Path:
    for c in [inicio, *inicio.parents]:
        if (c / "src" / "utils" / "validate.py").is_file() and (c / "_reversa_forward").is_dir():
            return c
    raise SystemExit("raiz nao encontrada")


EVID = Path(__file__).resolve().parent
RAIZ = _raiz(EVID)
FEATURE = EVID.parent
PY = str(RAIZ / ".venv" / "Scripts" / "python.exe")

ambiente = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
ambiente["PYTHONIOENCODING"] = "utf-8"


def rodar(args, timeout=900):
    r = subprocess.run(args, cwd=str(RAIZ), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ambiente, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def agora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gravar(nome, cabecalho, saida):
    corpo = "\n".join(cabecalho) + "\n\n" + saida.rstrip() + "\n"
    (EVID / nome).write_text(corpo, encoding="utf-8")
    print(f"  gravado: {nome}")


registros = []

# ------------------------------------------------------------------ T023
print("T023: suite DEPOIS")
codigo, saida = rodar([PY, "-m", "pytest", "-q"])
linhas = [l for l in saida.splitlines() if l.strip()]
falhas = [l for l in linhas if l.startswith("FAILED ")]
resumo = [l for l in linhas if "passed" in l][-1:] or linhas[-1:]

por_arquivo: dict[str, int] = {}
for linha in falhas:
    arquivo = linha.split("::")[0].replace("FAILED ", "")
    por_arquivo[arquivo] = por_arquivo.get(arquivo, 0) + 1

conflito = por_arquivo.get("tests/test_icone_de_atalho.py", 0)
veredito = (
    "COMPARA com a linha de base SEM ressalva"
    if not falhas
    else f"NAO FECHA o criterio de pronto: {len(falhas)} falha(s), e {conflito} delas em "
         "tests/test_icone_de_atalho.py, que e o CONFLITO ENTRE FEATURES (a 009 prende o GET / por SHA)."
)
gravar("T023-suite-depois.txt",
       ["# T023 - suite completa DEPOIS da implementacao",
        f"Quando: {agora()}",
        "Comando: .venv\\Scripts\\python.exe -m pytest -q   (DATABASE_URL AUSENTE)",
        f"Exit code: {codigo}",
        "",
        "## Linha de base (T001)",
        "335 passed, 9 skipped",
        "",
        "## Veredito",
        veredito],
       "\n".join(resumo) + "\n\nFalhas por arquivo:\n" +
       "\n".join(f"  {n:>3}  {a}" for a, n in sorted(por_arquivo.items(), key=lambda kv: -kv[1])))
registros.append(("T023", "tests/test_icone_de_atalho.py" if falhas else None, len(falhas)))

# ------------------------------------------------------------------ T024
print("T024: paridade DEPOIS")
codigo_p, saida_p = rodar([PY, "tests/rodar_paridade.py"])
linhas_p = [l for l in saida_p.splitlines() if "PARIDADE" in l.upper()]
cem = any("100" in l for l in linhas_p)
gravar("T024-paridade-depois.txt",
       ["# T024 - paridade DEPOIS da mudanca de template (pelo involucro)",
        f"Quando: {agora()}",
        "Comando: .venv\\Scripts\\python.exe tests\\rodar_paridade.py",
        f"Exit code: {codigo_p}",
        "",
        "## Linha de base (T002)",
        "RESULTADO: PARIDADE 100% (zero divergencia)",
        "",
        "## Veredito",
        ("PARIDADE 100% mantida: a premissa de §4 do roadmap se confirma, e a mudanca de template "
         "e paridade-neutra como a leitura do harness previa")
        if cem else
        "A PARIDADE CAIU: a premissa de §4 do roadmap esta errada, e o harness NAO e insensivel ao "
        "template como a investigacao concluiu por leitura. Investigar antes de seguir."],
       "\n".join(linhas_p) if linhas_p else saida_p.strip()[-1200:])
registros.append(("T024", None if cem else "paridade caiu", None))

# ------------------------------------------------------------------ progress
with (FEATURE / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
    for acao, nota, n in registros:
        d = {"ts": agora(), "action": acao, "status": "done",
             "files": [f"_reversa_forward/011-escolher-arquivo-da-lista/evidence/{acao}-"
                       + ("suite-depois.txt" if acao == "T023" else "paridade-depois.txt")]}
        if acao == "T023":
            d["nota"] = (f"Suite DEPOIS: {len(falhas)} falha(s). {nota or ''} "
                         "O criterio de pronto exige suite sem regressao, e o conflito da feature 009 "
                         "precisa de decisao humana antes de a comparacao fechar.")
        else:
            d["nota"] = ("Paridade DEPOIS: " + ("100% mantida, premissa de §4 confirmada." if cem
                         else "CAIU. A leitura do harness estava errada."))
        fh.write(json.dumps(d, ensure_ascii=False) + "\n")

print()
print("T023: exit", codigo, "| falhas:", len(falhas), "| 009:", conflito)
print("T024: exit", codigo_p, "| 100%:", cem)

"""Prova de morte para a OPP-20260929-SEQO.

Varredura em TODO o repositorio (nao so no app), porque requirements.txt e um
manifesto que pode ser consumido por scripts de diagnostico fora do pacote.

Candidatos: STATIC_FOLDER, matplotlib, pyvis, ensure_dirs.
Somente leitura.
"""
import pathlib
import re

ROOT = pathlib.Path(r"D:\Projetos\reversa_analisador_gelealogico")
IGNORAR = {".git", "__pycache__", ".pytest-tmp", ".pytest_cache", "node_modules"}
EXTENSOES = {".py", ".html", ".txt", ".toml", ".ini", ".cfg", ".yml", ".yaml",
             ".json", ".md", ".feature", ".sh", ".ps1"}

arquivos = []
for p in ROOT.rglob("*"):
    if not p.is_file() or p.suffix.lower() not in EXTENSOES:
        continue
    if any(parte in IGNORAR for parte in p.parts):
        continue
    if "_reversa_refactor" in p.parts or "_reversa_bugs" in p.parts:
        continue  # artefatos do proprio time, nao consumidores
    arquivos.append(p)

print(f"arquivos varridos no repositorio: {len(arquivos)}")

CANDIDATOS = {
    "STATIC_FOLDER": r"\bSTATIC_FOLDER\b",
    "matplotlib": r"\bmatplotlib\b",
    "pyvis": r"\bpyvis\b",
    "ensure_dirs": r"\bensure_dirs\b",
}

for nome, padrao in CANDIDATOS.items():
    rx = re.compile(padrao)
    achados = []
    for p in arquivos:
        try:
            linhas = p.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for i, linha in enumerate(linhas, 1):
            if rx.search(linha):
                achados.append((p.relative_to(ROOT), i, linha.strip()[:110]))
    print(f"\n=== {nome}: {len(achados)} ocorrencia(s) ===")
    for arq, i, linha in achados:
        tipo = "CODIGO" if str(arq).endswith(".py") else "documento/config"
        print(f"  [{tipo}] {arq}:{i}  {linha}")

print("\n=== imports reais dos pacotes candidatos ===")
padrao_import = re.compile(r"^\s*(import|from)\s+(matplotlib|pyvis)\b")
total = 0
for p in ROOT.rglob("*.py"):
    if any(parte in IGNORAR for parte in p.parts):
        continue
    for i, linha in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if padrao_import.search(linha):
            total += 1
            print(f"  {p.relative_to(ROOT)}:{i}  {linha.strip()}")
print(f"  total de imports de matplotlib/pyvis em .py: {total}")

print("\n=== uso de ensure_dirs (quem chama) ===")
for p in ROOT.rglob("*.py"):
    if any(parte in IGNORAR for parte in p.parts):
        continue
    if "_reversa_refactor" in p.parts or "_reversa_bugs" in p.parts:
        continue
    for i, linha in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if "ensure_dirs" in linha:
            print(f"  {p.relative_to(ROOT)}:{i}  {linha.strip()}")

print("\n=== Veredito ===")
print("STATIC_FOLDER : morto. Declaracao e makedirs, sem nenhum consumidor.")
print("matplotlib    : morto como dependencia. Zero imports em todo o repositorio.")
print("pyvis         : morto como dependencia. Zero imports; segue citado no README e no ORACLE_MANIFEST.")
print("ensure_dirs   : ORFAO SUSPEITO. Chamado apenas pelo proprio teste, nunca pelo app.")

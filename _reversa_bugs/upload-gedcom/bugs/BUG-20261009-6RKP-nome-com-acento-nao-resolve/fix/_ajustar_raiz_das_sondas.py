"""Torna as 3 sondas copiadas para `evidence/` do bug independentes da PROFUNDIDADE da pasta.

As sondas nasceram em `_reversa_forward/011-.../evidence/` e calculavam a raiz do repositorio por
`parents[3]`. Copiadas para `_reversa_bugs/upload-gedcom/bugs/BUG-.../evidence/`, que esta DUAS
pastas mais fundo, elas passam a apontar para o lugar errado e falham com
`ModuleNotFoundError: No module named 'utils'`.

Correcao: trocar o calculo por uma subida ate a raiz que tenha `src/utils/validate.py`.
Verificacao: rodar as tres depois, de dentro da pasta do bug.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parent.parent / "evidence"

PREAMBULO = '''def _raiz_do_repositorio(inicio):
    """Sobe ate a raiz que tenha `src/utils/validate.py` (contar `parents[N]` quebra ao mover o arquivo)."""
    import pathlib
    for candidato in [inicio, *inicio.parents]:
        if (candidato / "src" / "utils" / "validate.py").is_file():
            return candidato
    raise SystemExit("raiz do repositorio nao encontrada a partir de " + str(inicio))


'''

# Formas antigas do calculo da raiz, uma por sonda. O `.*$` no fim e obrigatorio: uma das sondas
# tem comentario depois do calculo, e ancorar o `$` logo apos o `]` nao casava.
PADROES = [
    (re.compile(r"^RAIZ = Path\(__file__\)\.resolve\(\)\.parents\[3\].*$", re.M),
     "RAIZ = _raiz_do_repositorio(Path(__file__).resolve().parent)"),
    (re.compile(r"^RAIZ = os\.path\.dirname\(os\.path\.dirname\(os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)\)\).*$",
                re.M),
     "RAIZ = _raiz_do_repositorio(Path(__file__).resolve().parent)"),
]

alvos = sorted(EVIDENCE.glob("_sonda_*.py"))
if not alvos:
    raise SystemExit("nenhuma sonda em " + str(EVIDENCE))

for caminho in alvos:
    texto = caminho.read_text(encoding="utf-8")
    original = texto
    for padrao, novo in PADROES:
        texto = padrao.sub(novo, texto)
    if texto == original:
        print(f"  SEM MUDANCA  {caminho.name} (padrao de RAIZ nao reconhecido?)")
        continue
    # Injeta o preambulo logo antes da linha de RAIZ, uma unica vez.
    if "_raiz_do_repositorio(inicio)" not in texto:
        texto = texto.replace("RAIZ = _raiz_do_repositorio(",
                              PREAMBULO + "RAIZ = _raiz_do_repositorio(", 1)
    # `os` pode nao ser mais usado; nao removo import, para nao quebrar o resto.
    caminho.write_text(texto, encoding="utf-8")
    print(f"  AJUSTADA     {caminho.name}")

print()
print("Rodando as tres de dentro da pasta do bug:")
for caminho in alvos:
    r = subprocess.run([sys.executable, str(caminho)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(EVIDENCE.parent))
    ultima = [l for l in (r.stdout or "").strip().splitlines() if l.strip()]
    veredito = ultima[-1] if ultima else "(sem saida)"
    print(f"  {caminho.name:<34} exit={r.returncode}  {veredito[:90]}")
    if r.returncode != 0:
        print("      stderr:", (r.stderr or "").strip().splitlines()[-1:])

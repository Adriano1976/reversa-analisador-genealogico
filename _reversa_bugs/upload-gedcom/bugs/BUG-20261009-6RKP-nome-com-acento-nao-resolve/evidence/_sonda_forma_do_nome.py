"""Sonda 3: quais arquivos REAIS da pasta canonica sao alcancaveis por referencia.

`ArmazenamentoEmDisco.resolver` recusa a referencia por `chave_recebida_e_valida`, cuja forma e
`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`. Mas `nome_visivel_seguro` PRESERVA acentos e espacos. Se as
duas coisas nao combinam, todo arquivo com acento ou espaco no nome fica armazenado sob um nome
que o proprio resolvedor recusa -- e a resposta ao operador e "nao existe mais", que e FALSA.

Somente leitura: nao escreve nada na pasta.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

def _raiz_do_repositorio(inicio):
    """Sobe ate a raiz que tenha `src/utils/validate.py` (contar `parents[N]` quebra ao mover o arquivo)."""
    import pathlib
    for candidato in [inicio, *inicio.parents]:
        if (candidato / "src" / "utils" / "validate.py").is_file():
            return candidato
    raise SystemExit("raiz do repositorio nao encontrada a partir de " + str(inicio))


RAIZ = _raiz_do_repositorio(Path(__file__).resolve().parent)
sys.path.insert(0, str(RAIZ / "src"))

from utils.validate import chave_recebida_e_valida  # noqa: E402

PASTA = RAIZ / "src" / "uploads"

aceitas: list[str] = []
recusadas: list[str] = []

for caminho in sorted(PASTA.iterdir()):
    if not caminho.is_file():
        continue
    nome = caminho.name
    if chave_recebida_e_valida(nome):
        aceitas.append(nome)
        print("ACEITA   " + nome)
    else:
        recusadas.append(nome)
        print("RECUSA   " + nome)

print()
print(f"total de arquivos: {len(aceitas) + len(recusadas)}")
print(f"aceitas por referencia: {len(aceitas)}")
print(f"RECUSADAS pelo proprio validador de forma: {len(recusadas)}")

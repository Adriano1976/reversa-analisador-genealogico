"""Renomeia os titulos da RODADA 2 para nao colidirem com os da rodada 1 (MD024).

Os dois artefatos ganharam uma segunda rodada com titulos homonimos dos da
primeira. O `markdownlint` do repositorio tem MD024 ligado (`siblings_only`), e
titulos repetidos no mesmo nivel sao erro. Este script renomeia APENAS a segunda
ocorrencia de cada titulo, deixando a rodada 1 intacta.

Rodar da raiz do projeto:

    python _reversa_forward/005-nucleo-puro-src/evidence/_ajustar_titulos_rodada2.py
"""
import io
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

# (caminho relativo, titulo antigo, titulo novo)
ALVOS = [
    ("_reversa_forward/005-nucleo-puro-src/legacy-impact.md",
     "## Histórico de alterações", "### Histórico de alterações (rodada 2)"),
    ("_reversa_forward/005-nucleo-puro-src/regression-watch.md",
     "## Observações", "### Observações (rodada 2)"),
    ("_reversa_forward/005-nucleo-puro-src/regression-watch.md",
     "## Histórico de alterações", "### Histórico de alterações (rodada 2)"),
]

for relativo, antigo, novo in ALVOS:
    caminho = os.path.join(RAIZ, relativo)
    with io.open(caminho, encoding="utf-8") as fh:
        linhas = fh.readlines()
    # A ultima ocorrencia e a da rodada 2: a rodada 1 vem primeiro no arquivo.
    indices = [i for i, linha in enumerate(linhas) if linha.rstrip("\n") == antigo]
    if not indices:
        print("  AUSENTE  %s -> %s" % (relativo, antigo))
        continue
    alvo = indices[-1]
    linhas[alvo] = novo + "\n"
    with io.open(caminho, "w", encoding="utf-8", newline="\n") as fh:
        fh.writelines(linhas)
    print("  ok  %s  linha %d: %s" % (relativo.split("/")[-1], alvo + 1, novo))

"""Verificacao do actions.md da feature 011: contagens e cadeia, medidas do arquivo."""
from __future__ import annotations

import re
from pathlib import Path

CAMINHO = Path(__file__).resolve().parents[1] / "actions.md"
texto = CAMINHO.read_text(encoding="utf-8")

print("arquivo:", CAMINHO)
print("bytes:", len(texto.encode("utf-8")))
print("linhas:", texto.count("\n") + (0 if texto.endswith("\n") else 1))
print("BOM:", texto.startswith("\ufeff"))

# Linhas de acao: terminam em "| [ ] |" ou "| [X] |" (sem crase) -- a convencao do detector.
linhas = texto.splitlines()
acoes = []
for linha in linhas:
    if re.search(r"\|\s*\[[ X]\]\s*\|\s*$", linha):
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(celulas) == 7:
            acoes.append(celulas)

ids = [c[0] for c in acoes]
print("acoes com status reconhecido pelo detector:", len(acoes))
print("IDs unicos:", len(set(ids)) == len(ids))

# Fases
fase_atual = None
por_fase = {}
for linha in linhas:
    m = re.match(r"^## (Fase \d.*)$", linha)
    if m:
        fase_atual = m.group(1)
        por_fase[fase_atual] = 0
    if fase_atual and re.search(r"\|\s*\[[ X]\]\s*\|\s*$", linha):
        por_fase[fase_atual] += 1
print("por fase:", por_fase)
print("soma das fases:", sum(por_fase.values()))

# Paralelismo
marcadas = [c[0] for c in acoes if c[3].strip("`") == "[//]"]
print("marcadas [//]:", len(marcadas))
print("  ", marcadas)

# Dependencias
deps = {}
for c in acoes:
    bruto = c[2].strip()
    deps[c[0]] = [] if bruto in ("-", "") else [d.strip() for d in bruto.split(",")]

desconhecidas = {d for lista in deps.values() for d in lista} - set(ids)
print("dependencias apontando para ID inexistente:", sorted(desconhecidas) or "nenhuma")

# Cadeia mais longa (por numero de ACOES no caminho)
profundidade = {}
caminho_ate = {}

def medir(t, pilha=()):
    if t in profundidade:
        return profundidade[t]
    if t in pilha:
        raise SystemExit("ciclo de dependencia em " + t)
    if not deps[t]:
        profundidade[t] = 1
        caminho_ate[t] = [t]
        return 1
    melhor = 0
    melhor_caminho = []
    for d in deps[t]:
        valor = medir(d, pilha + (t,))
        if valor > melhor:
            melhor = valor
            melhor_caminho = caminho_ate[d]
    profundidade[t] = melhor + 1
    caminho_ate[t] = melhor_caminho + [t]
    return profundidade[t]

for t in ids:
    medir(t)

maior = max(profundidade.values())
campeoes = [t for t in ids if profundidade[t] == maior]
print("maior cadeia (numero de acoes):", maior)
for t in campeoes:
    print("  ", t, "->", " -> ".join(caminho_ate[t]))

# Resumo declarado x medido
resumo = re.search(r"\|\s*Total de ações\s*\|\s*(\d+)\s*\|", texto)
paralelas = re.search(r"\|\s*Paralelizáveis[^|]*\|\s*(\d+)\s*\|", texto)
cadeia = re.search(r"\|\s*Maior cadeia de dependência\s*\|\s*(\d+)\s*\|", texto)
print("declarado total:", resumo.group(1) if resumo else "AUSENTE")
print("declarado paralelizaveis:", paralelas.group(1) if paralelas else "AUSENTE")
print("declarado maior cadeia:", cadeia.group(1) if cadeia else "AUSENTE")

# Alvo compartilhado entre marcadas [//]
alvos = {}
for c in acoes:
    if c[0] in marcadas:
        alvos.setdefault(c[4], []).append(c[0])
colisoes = {a: v for a, v in alvos.items() if len(v) > 1}
print("colisao de arquivo alvo entre [//]:", colisoes or "nenhuma")

# Dependencia entre duas marcadas [//]
pares = [
    (a, d) for a in marcadas for d in deps[a] if d in marcadas
]
print("dependencia entre [//] da MESMA fase (proibida):", end=" ")
fase_de = {}
fase_atual = None
for linha in linhas:
    m = re.match(r"^## (Fase \d.*)$", linha)
    if m:
        fase_atual = m.group(1)
    if fase_atual:
        for t in ids:
            if re.match(r"^\|\s*" + t + r"\s*\|", linha):
                fase_de[t] = fase_atual
mesma_fase = [(a, d) for a, d in pares if fase_de.get(a) == fase_de.get(d)]
print(mesma_fase or "nenhuma")
print("dependencia entre [//] de fases diferentes (permitida):", [p for p in pares if p not in mesma_fase] or "nenhuma")

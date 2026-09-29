"""Sonda de re-verificacao do BUG-20260929-J6PQ contra a arvore atual.

O bug foi registrado antes da OPP-20260929-TPSH, que unificou as duas copias
da funcao interna `lab`. Esta sonda mede se o defeito de escape sobreviveu.
"""
import sys

sys.path.insert(0, "analisador-genealogico")

from reconstructed.path_search import _mermaid_label as lab  # noqa: E402

HOSTIS = [
    ("colchete", "Joao [Silva]"),
    ("crase", "Maria `teste`"),
    ("palavra-chave subgraph", "Ana subgraph"),
    ("palavra-chave end", "Pedro end"),
    ("seta de aresta", "Luis --> Rita"),
    ("entidades ja cobertas", "A & B < C > D"),
    ("aspas", 'Jose "Zeca"'),
    ("quebra de linha", "Ana\r\nMaria"),
    ("dois pontos", "Ana: Maria"),
]

print("sonda de escape do rotulo Mermaid apos a TPSH")
print("=" * 62)
for nome, entrada in HOSTIS:
    saida = lab(entrada)
    neutro = saida == entrada
    marca = "PASSA INTACTO" if neutro else "neutralizado"
    print(f"{nome:24} {entrada!r:28} -> {saida!r:28} {marca}")

print()
print("veredito por caractere:")
for ch, rotulo in [("[", "abre colchete"), ("]", "fecha colchete"), ("`", "crase"),
                   ("-->", "seta de aresta"), (":", "dois pontos")]:
    s = lab(f"A{ch}B")
    print(f"  {rotulo:16} {'neutralizado' if ch not in s else 'PASSA INTACTO'}")

"""Mede o acoplamento do pacote reconstruido, por contagem de dependencias.

Le as importacoes com AST, separa o que e interno ao pacote do que e externo, e
conta:

  fan-out interno: de quantos modulos internos este modulo depende
  fan-in interno : de quantos modulos internos este modulo e dependido

Tambem lista, para um modulo alvo, quem o importa de fora do pacote (aplicacao,
testes, instrumentacao), que e a superficie de compatibilidade dele.

Uso: python medir-acoplamento.py [modulo-alvo]
Nao escreve nada; imprime o relatorio.
"""
from __future__ import annotations

import ast
import pathlib
import sys

PACOTE = pathlib.Path("src/reconstructed")
EXTERNOS = ["src/app.py"] + [str(p) for p in sorted(pathlib.Path("tests").glob("*.py"))] + \
           [str(p) for p in sorted(pathlib.Path("_reversa_sdd/parity").glob("*.py"))]


def importacoes(caminho):
    """Devolve (internos, externos) como conjuntos de nomes de modulo."""
    arvore = ast.parse(pathlib.Path(caminho).read_text(encoding="utf-8"))
    interno, externo = set(), set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom):
            if no.level and no.level > 0:
                alvo = no.module or ""
                interno.add(alvo.split(".")[0] if alvo else "")
            else:
                if (no.module or "").startswith("reconstructed"):
                    interno.add((no.module or "").replace("reconstructed.", "").split(".")[0])
                elif no.module:
                    externo.add(no.module.split(".")[0])
        elif isinstance(no, ast.Import):
            for alias in no.names:
                if alias.name.startswith("reconstructed"):
                    interno.add(alias.name.replace("reconstructed.", "").split(".")[0])
                else:
                    externo.add(alias.name.split(".")[0])
    interno.discard("")
    return interno, externo


def main():
    alvo = sys.argv[1] if len(sys.argv) > 1 else None
    modulos = sorted(p.stem for p in PACOTE.glob("*.py") if p.stem != "__init__")

    saida = {}
    for m in modulos:
        saida[m] = importacoes(PACOTE / (m + ".py"))

    fan_out = {m: len(v[0]) for m, v in saida.items()}
    fan_in = {m: 0 for m in modulos}
    for m, (interno, _) in saida.items():
        for dep in interno:
            if dep in fan_in:
                fan_in[dep] += 1

    print("Acoplamento interno do pacote reconstruido")
    print("%-24s %8s %8s   %s" % ("modulo", "fan-out", "fan-in", "depende de"))
    for m in modulos:
        deps = ", ".join(sorted(saida[m][0])) or "-"
        print("%-24s %8d %8d   %s" % (m, fan_out[m], fan_in[m], deps))

    print()
    print("total de arestas internas = %d" % sum(fan_out.values()))
    if alvo and alvo in saida:
        print()
        print("Alvo: %s" % alvo)
        print("  fan-out interno = %d (%s)" % (fan_out[alvo], ", ".join(sorted(saida[alvo][0])) or "-"))
        print("  fan-in interno  = %d" % fan_in[alvo])
        print("  dependencias externas = %s" % (", ".join(sorted(saida[alvo][1])) or "-"))
        print("  superficie de compatibilidade (quem importa de fora do pacote):")
        achou = False
        for caminho in EXTERNOS:
            p = pathlib.Path(caminho)
            if not p.exists():
                continue
            try:
                interno, _ = importacoes(p)
            except SyntaxError:
                continue
            if alvo in interno:
                print("    %s" % caminho.replace("\\", "/"))
                achou = True
        if not achou:
            print("    nenhuma")
    return 0


if __name__ == "__main__":
    sys.exit(main())

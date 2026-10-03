"""Mede a coesao do pacote reconstruido, por AST, antes e depois da RGKA.

Uso:
    py -3.14 medir-coesao.py --rotulo antes
    py -3.14 medir-coesao.py --rotulo depois

Grava before-after/coesao-<rotulo>.txt e imprime o mesmo conteudo.
Nao escreve nada fora desta pasta de transformacao.
"""
from __future__ import annotations

import argparse
import ast
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PACOTE = os.path.join(ROOT, "src", "reconstructed")

ALVO = ["SHARED_CM_DATA", "get_relationships_by_cm", "dna_analysis"]


def modulos():
    for raiz, dirs, arquivos in os.walk(PACOTE):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for nome in sorted(arquivos):
            if nome.endswith(".py"):
                caminho = os.path.join(raiz, nome)
                yield os.path.relpath(caminho, ROOT).replace("\\", "/"), caminho


def nome_do_pacote(rel):
    """src/reconstructed/core/x.py -> reconstructed.core"""
    partes = rel.split("/")[1:-1]
    return ".".join(partes)


def alvos_internos(arvore, rel):
    """Todos os alvos de import relativo, inclusive os que vivem dentro de funcao."""
    pacote = nome_do_pacote(rel)
    partes = pacote.split(".")
    fora = set()
    for no in ast.walk(arvore):
        if not isinstance(no, ast.ImportFrom) or not no.level:
            continue
        base = ".".join(partes[: len(partes) - (no.level - 1)]) if no.level > 1 else pacote
        if no.module:
            fora.add(base + "." + no.module)
        else:
            for alias in no.names:
                fora.add(base + "." + alias.name)
    return sorted(fora)


def retrato():
    linhas = []
    total_linhas = 0
    total_arestas = 0
    definicoes = {}
    donos = {}
    fan_out = {}

    for rel, caminho in modulos():
        with open(caminho, encoding="utf-8") as fh:
            fonte = fh.read()
        arvore = ast.parse(fonte)
        n = len(fonte.splitlines())
        total_linhas += n

        topos = []
        for no in arvore.body:
            if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                topos.append(no.name)
            elif isinstance(no, (ast.Assign, ast.AnnAssign)):
                alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
                for a in alvos:
                    if isinstance(a, ast.Name):
                        topos.append(a.id)
        definicoes[rel] = topos
        for nome in ALVO:
            if nome in topos:
                donos.setdefault(nome, []).append(rel)

        arestas = alvos_internos(arvore, rel)
        fan_out[rel] = arestas
        total_arestas += len(arestas)

        linhas.append("%-46s %5d linhas  fan-out interno %2d" % (rel, n, len(arestas)))

    return {
        "linhas": linhas,
        "total_linhas": total_linhas,
        "total_arestas": total_arestas,
        "definicoes": definicoes,
        "donos": donos,
        "fan_out": fan_out,
        "n_modulos": len(definicoes),
    }


def relatorio(r):
    out = []
    out.append("=" * 78)
    out.append("COESAO DO PACOTE reconstruido (medido por AST)")
    out.append("=" * 78)
    out.append("modulos: %d | linhas: %d | arestas internas: %d"
               % (r["n_modulos"], r["total_linhas"], r["total_arestas"]))
    out.append("")
    for linha in r["linhas"]:
        out.append("  " + linha)

    out.append("")
    out.append("-" * 78)
    out.append("QUEM DEFINE O CONHECIMENTO DE cM")
    out.append("-" * 78)
    for nome in ALVO:
        onde = r["donos"].get(nome, [])
        out.append("  %-24s %s" % (nome, ", ".join(onde) if onde else "(nao definido em lugar nenhum)"))

    out.append("")
    out.append("-" * 78)
    out.append("DEFINICOES DE TOPO DE src/reconstructed/dna_analysis.py")
    out.append("-" * 78)
    chave = "src/reconstructed/dna_analysis.py"
    topos = r["definicoes"].get(chave, [])
    out.append("  total: %d" % len(topos))
    for nome in sorted(topos):
        out.append("    " + nome)

    out.append("")
    out.append("-" * 78)
    out.append("FAN-OUT INTERNO DE src/reconstructed/dna_analysis.py")
    out.append("-" * 78)
    for alvo in r["fan_out"].get(chave, []):
        out.append("    " + alvo)

    out.append("=" * 78)
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rotulo", default="atual", help="nome do arquivo de saida")
    args = ap.parse_args()

    texto = relatorio(retrato())
    destino = os.path.join(HERE, "before-after", "coesao-%s.txt" % args.rotulo)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(texto + "\n")
    print(texto)
    print("\ngravado em %s" % os.path.relpath(destino, ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

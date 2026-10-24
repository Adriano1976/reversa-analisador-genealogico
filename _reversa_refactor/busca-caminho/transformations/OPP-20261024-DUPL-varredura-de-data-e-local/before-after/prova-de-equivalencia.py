"""Prova de equivalencia da OPP-20261024-DUPL.

Compara, funcao por funcao, a versao de HEAD (antes) com a versao importada do projeto
(depois), sobre a arvore real de 35 mil pessoas.

As tres funcoes alteradas nao foram tocadas antes nesta sessao, entao o texto de HEAD e a
versao "antes" fiel. As funcoes antigas sao extraidas por AST e executadas num espaco com
os helpers do modulo atual; assim o unico lado que difere e o que a transformacao mudou.

Uso:
  --controle-negativo   injeta uma diferenca proposital e exige que a prova a detecte
  (sem flag)            prova de verdade, contra o modulo do projeto
"""
from __future__ import annotations

import ast
import os
import pathlib
import random
import subprocess
import sys

RAIZ = str(pathlib.Path(__file__).resolve().parents[5])
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core import documentary_relationship as dr  # noqa: E402
from core.registro import ref_id  # noqa: E402
from parsers import gedcom_parser  # noqa: E402

GED = os.path.join(RAIZ, "src", "uploads", "0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged")
TAGS = ("BIRT", "DEAT", "BURI", "MARR", "ZZZZ")


def funcoes_do_head(nomes):
    texto = subprocess.run(
        ["git", "show", "HEAD:src/core/documentary_relationship.py"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    nos = [n for n in ast.parse(texto).body
           if isinstance(n, ast.FunctionDef) and n.name in nomes]
    faltando = set(nomes) - {n.name for n in nos}
    if faltando:
        raise SystemExit(f"funcoes ausentes do HEAD: {sorted(faltando)}")
    espaco = dict(vars(dr))
    exec(compile(ast.Module(body=nos, type_ignores=[]), "<head>", "exec"), espaco)
    return {n.name: espaco[n.name] for n in nos}


def comparar(rotulo, antiga, nova, casos):
    divergentes = []
    for args in casos:
        a = antiga(*args)
        b = nova(*args)
        if a != b:
            divergentes.append((args, a, b))
    print(f"  {rotulo:52} casos: {len(casos):6}  divergentes: {len(divergentes)}")
    for args, a, b in divergentes[:3]:
        resumo = [x for x in args if isinstance(x, (str, int))]
        print(f"      {resumo}\n        antes: {a!r}\n        depois: {b!r}")
    return len(divergentes)


def main() -> int:
    controle = "--controle-negativo" in sys.argv
    antigas = funcoes_do_head({"_data_de", "_local_de", "hop_evidence"})

    print(f"carregando {os.path.basename(GED)} ...")
    arvore = gedcom_parser.carregar_arvore(GED)
    people, families = arvore[0], arvore[1]
    print(f"pessoas: {len(people)} | familias: {len(families)}")

    novas = {
        "_data_de": dr._data_de,
        "_local_de": dr._local_de,
        "hop_evidence": dr.hop_evidence,
    }
    if controle:
        original_data_de = novas["_data_de"]

        def data_de_com_diferenca(people, pid, tag):
            valor = original_data_de(people, pid, tag)
            return valor.upper() if isinstance(valor, str) else valor

        novas["_data_de"] = data_de_com_diferenca

    ids = sorted(people)
    amostra = ids[:4000]
    print()
    print("=== equivalencia ===")

    total = 0

    casos_data = [(people, pid, tag) for pid in amostra for tag in TAGS]
    casos_data += [(people, "@I99999999@", tag) for tag in TAGS]
    total += comparar("_data_de (BIRT, DEAT, BURI, MARR, inexistente)",
                      antigas["_data_de"], novas["_data_de"], casos_data)

    casos_local = [(people, pid, tag) for pid in amostra for tag in TAGS]
    casos_local += [(people, "@I99999999@", tag) for tag in TAGS]
    total += comparar("_local_de (BIRT, DEAT, BURI, MARR, inexistente)",
                      antigas["_local_de"], novas["_local_de"], casos_local)

    arestas = []
    for fam in families.values():
        filhos = [ref_id(r.value) for r in fam.sub_records if r.tag == "CHIL"]
        pais = [ref_id(r.value) for r in fam.sub_records if r.tag in ("HUSB", "WIFE")]
        for filho in filhos:
            for pai in pais:
                if filho and pai:
                    arestas.append((arvore, filho, pai))
    sem_vinculo = [(arvore, ids[i], ids[(i * 7919) % len(ids)]) for i in range(0, len(ids), max(1, len(ids) // 300))]
    inexistentes = [(arvore, "@I99999999@", ids[0]), (arvore, ids[0], "@I99999999@")]
    total += comparar("hop_evidence (todas as arestas + pares sem vinculo)",
                      antigas["hop_evidence"], novas["hop_evidence"],
                      arestas + sem_vinculo + inexistentes)

    print()
    print(f"total de divergencias: {total}")
    if controle:
        if total == 0:
            print("CONTROLE NEGATIVO FALHOU: a prova nao detectou a diferenca injetada.")
            return 1
        print("CONTROLE NEGATIVO OK: a prova detectou a diferenca injetada.")
        return 0
    if total:
        print("EQUIVALENCIA REPROVADA")
        return 1
    print("EQUIVALENCIA PROVADA: mesma saida em todos os casos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

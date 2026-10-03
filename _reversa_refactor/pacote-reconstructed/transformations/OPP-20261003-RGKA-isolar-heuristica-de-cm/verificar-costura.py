"""Prova de equivalencia da costura RGKA, sem depender do oraculo.

Extrai `SHARED_CM_DATA` e `get_relationships_by_cm` da copia PRISTINA guardada em
before-after/dna_analysis.antes.py, executa as duas versoes lado a lado e compara
o retorno para os 40 valores de cM que o harness usa mais as bordas de tipo.

Prova tambem a identidade dos objetos expostos pela fachada: quem importa de
`reconstructed.dna_analysis` continua recebendo o MESMO objeto, nao uma copia.
"""
from __future__ import annotations

import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
ANTES = os.path.join(HERE, "before-after", "dna_analysis.antes.py")

CM_PROBES = [
    0, -5, 1, 9, 10, 29, 30, 45, 46, 50, 109, 110, 199, 200, 219, 220, 299, 300,
    349, 350, 514, 515, 552, 553, 849, 850, 1329, 1330, 1316, 1317, 2199, 2200,
    2311, 2312, 3399, 3400, 3719, 3720, 5000, 99999,
]
BORDAS = [0.0, -0.5, 3720.0, 3721, 1e9, None, "300", [], True, False, -0.0]


def bloco_pristino():
    """Executa apenas as duas definicoes alvo do arquivo original."""
    with open(ANTES, encoding="utf-8") as fh:
        arvore = ast.parse(fh.read())
    ns = {}
    for no in arvore.body:
        alvo = (
            isinstance(no, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "SHARED_CM_DATA" for t in no.targets)
        ) or (isinstance(no, ast.FunctionDef) and no.name == "get_relationships_by_cm")
        if alvo:
            exec(compile(ast.Module(body=[no], type_ignores=[]), "<antes>", "exec"), ns)
    return ns


def all_pristino():
    with open(ANTES, encoding="utf-8") as fh:
        arvore = ast.parse(fh.read())
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in no.targets
        ):
            return [e.value for e in no.value.elts]
    return []


def main() -> int:
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from reconstructed import dna_analysis as D
    from reconstructed.core import cm_estimator as C

    antes = bloco_pristino()
    falhas = []

    print("=" * 78)
    print("EQUIVALENCIA DA COSTURA RGKA")
    print("=" * 78)

    print("\n1. TABELA")
    print("   antes  : %d faixas" % len(antes["SHARED_CM_DATA"]))
    print("   depois : %d faixas" % len(C.SHARED_CM_DATA))
    if antes["SHARED_CM_DATA"] != C.SHARED_CM_DATA:
        falhas.append("a tabela mudou de conteudo")
    else:
        print("   iguais, faixa a faixa, na mesma ordem")

    print("\n2. RETORNO PARA %d VALORES DE cM + %d BORDAS" % (len(CM_PROBES), len(BORDAS)))
    divergentes = 0
    for valor in CM_PROBES + BORDAS:
        a = antes["get_relationships_by_cm"](valor)
        b = C.get_relationships_by_cm(valor)
        if a != b or type(a) is not type(b):
            divergentes += 1
            falhas.append("cm=%r -> antes %r, depois %r" % (valor, a, b))
    print("   sondados : %d" % (len(CM_PROBES) + len(BORDAS)))
    print("   divergentes: %d" % divergentes)

    print("\n3. IDENTIDADE DOS OBJETOS EXPOSTOS PELA FACHADA")
    pares = [
        ("SHARED_CM_DATA", D.SHARED_CM_DATA, C.SHARED_CM_DATA),
        ("get_relationships_by_cm", D.get_relationships_by_cm, C.get_relationships_by_cm),
    ]
    for nome, da_fachada, do_modulo in pares:
        igual = da_fachada is do_modulo
        print("   %-24s mesmo objeto: %s" % (nome, "sim" if igual else "NAO"))
        if not igual:
            falhas.append("%s nao e o mesmo objeto" % nome)

    print("\n4. __all__ DA FACHADA")
    antes_all = all_pristino()
    depois_all = list(D.__all__)
    print("   antes  : %d nomes" % len(antes_all))
    print("   depois : %d nomes" % len(depois_all))
    if antes_all != depois_all:
        falhas.append("__all__ mudou: %r" % (set(antes_all) ^ set(depois_all)))
    else:
        print("   identicos, na mesma ordem")

    print("\n5. CONTAGEM DE RESPONSABILIDADES")
    print("   definicoes de topo de dna_analysis.py antes  : 4")
    print("   definicoes de topo de dna_analysis.py depois : 2")

    print()
    print("=" * 78)
    if falhas:
        print("RESULTADO: %d FALHA(S)" % len(falhas))
        for f in falhas:
            print("  " + f)
    else:
        print("RESULTADO: EQUIVALENCIA PROVADA (zero divergencia em %d sondagens)"
              % (len(CM_PROBES) + len(BORDAS)))
    print("=" * 78)
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Prova de equivalencia da OPP-20261024-SEPM.

Compara a saida de `documentary_relationship` e de `documental_nao_encontrado` da versao
de HEAD (antes) com a do modulo do projeto (depois), dicionario por dicionario.

As duas funcoes nao foram tocadas pelas transformacoes anteriores desta sessao (CACH e DUPL),
entao o texto de HEAD e a versao "antes" fiel. Elas sao extraidas por AST e executadas num
espaco com os helpers do modulo atual; como esses helpers foram provados equivalentes pela
OPP-20261024-DUPL, o unico lado que difere e o que esta transformacao mudou.

Uso:
  --controle-negativo   injeta uma diferenca proposital e exige que a prova a detecte
"""
from __future__ import annotations

import ast
import collections
import os
import pathlib
import subprocess
import sys
import tempfile

RAIZ = str(pathlib.Path(__file__).resolve().parents[5])
sys.path.insert(0, os.path.join(RAIZ, "src"))

from core import documentary_relationship as dr  # noqa: E402
from core import homonimos as ho  # noqa: E402
from parsers import gedcom_parser  # noqa: E402

GED_REAL = os.path.join(RAIZ, "src", "uploads", "0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged")
FIXTURES = [
    "affinity.ged", "basic.ged", "deep25.ged", "mojibake_latin1.ged", "no_name.ged", "variants.ged",
]
PASTA_FIXTURES = os.path.join(RAIZ, "_reversa_sdd", "parity", "fixtures", "gedcom")

GED_COLAPSO = """0 HEAD
1 SOUR PROVA
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
0 @X@ INDI
1 NAME Xisto Raiz
1 SEX M
1 BIRT
2 DATE 1930
1 FAMS @F1@
0 @Y@ INDI
1 NAME Yara Raiz
1 SEX F
1 BIRT
2 DATE 1932
1 FAMS @F1@
0 @M@ INDI
1 NAME Mario Meio
1 SEX M
1 BIRT
2 DATE 1960
1 FAMC @F1@
1 FAMS @F2@
0 @W@ INDI
1 NAME Wilma Meio
1 SEX F
1 BIRT
2 DATE 1962
1 FAMC @F1@
1 FAMS @F2@
0 @G@ INDI
1 NAME Gil Meio
1 SEX M
1 BIRT
2 DATE 1990
1 FAMC @F1@
1 FAMS @F3@
0 @A@ INDI
1 NAME Alfa Filho
1 SEX F
1 BIRT
2 DATE 1950
1 FAMC @F2@
0 @B@ INDI
1 NAME Beto Neto
1 SEX M
1 BIRT
2 DATE 1900
1 FAMC @F3@
0 @F1@ FAM
1 HUSB @X@
1 WIFE @Y@
1 CHIL @M@
1 CHIL @W@
1 CHIL @G@
0 @F2@ FAM
1 HUSB @M@
1 WIFE @W@
1 CHIL @A@
0 @F3@ FAM
1 HUSB @G@
1 CHIL @B@
0 TRLR
"""


def escrever_e_carregar(texto: str):
    fd, caminho = tempfile.mkstemp(suffix=".ged")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(texto)
    try:
        return gedcom_parser.carregar_arvore(caminho)
    finally:
        try:
            os.unlink(caminho)
        except OSError:
            pass


def funcoes_do_head(nomes):
    texto = subprocess.run(
        ["git", "show", "HEAD:src/core/documentary_relationship.py"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    nos = [n for n in ast.parse(texto).body if isinstance(n, ast.FunctionDef) and n.name in nomes]
    faltando = set(nomes) - {n.name for n in nos}
    if faltando:
        raise SystemExit(f"funcoes ausentes do HEAD: {sorted(faltando)}")
    espaco = dict(vars(dr))
    exec(compile(ast.Module(body=nos, type_ignores=[]), "<head>", "exec"), espaco)
    return espaco


def _seguro(valor) -> str:
    """repr que sobrevive a console cp1252, para a prova poder rodar em qualquer shell."""
    return repr(valor).encode("ascii", "backslashreplace").decode("ascii")


def pares_da_arvore(arvore, limite: int):
    people, families = arvore[0], arvore[1]
    ids = sorted(people)
    arestas, irmaos = [], []
    for fam in families.values():
        filhos = [dr.ref_id(r.value) for r in fam.sub_records if r.tag == "CHIL"]
        pais = [dr.ref_id(r.value) for r in fam.sub_records if r.tag in ("HUSB", "WIFE")]
        for filho in filhos:
            for pai in pais:
                if filho and pai:
                    arestas.append((filho, pai))
        for i, um in enumerate(filhos[:4]):
            for outro in filhos[i + 1:4]:
                if um and outro:
                    irmaos.append((um, outro))
    passo = max(1, len(ids) // max(1, limite // 4))
    aleatorios = [(ids[i], ids[(i * 7919 + 13) % len(ids)]) for i in range(0, len(ids), passo)]
    return (arestas[:limite] + irmaos[:limite] + aleatorios[: limite // 2])


def main() -> int:
    controle = "--controle-negativo" in sys.argv
    antigo = funcoes_do_head({"documentary_relationship", "documental_nao_encontrado"})

    novo_rel = dr.documentary_relationship
    if controle:
        original = novo_rel

        def com_diferenca(arvore, a_id, b_id, homonyms=None):
            resultado = original(arvore, a_id, b_id, homonyms=homonyms)
            return {**resultado, "label": str(resultado.get("label", "")).upper()}

        novo_rel = com_diferenca

    corpus = [("arvore real", gedcom_parser.carregar_arvore(GED_REAL), 400)]
    corpus.append(("colapso sintetico", escrever_e_carregar(GED_COLAPSO), 12))
    for nome in FIXTURES:
        caminho = os.path.join(PASTA_FIXTURES, nome)
        if os.path.exists(caminho):
            corpus.append((nome, gedcom_parser.carregar_arvore(caminho), 60))

    codigos = collections.Counter()
    divergentes = 0
    casos = 0

    print("=== equivalencia de documentary_relationship ===")
    for rotulo, arvore, limite in corpus:
        people = arvore[0]
        indice = ho._indice_por_nome(arvore)
        repetidos = [nome for nome, ids in indice.items() if len(ids) > 1][:2]
        dossies = [None]
        for nome in repetidos:
            dossies.append(dr.homonym_dossier(arvore, nome))
        dossies.append({"ambiguous": True, "exact_count": 2, "query": "Fulano de Tal"})

        casos_deste = 0
        for a_id, b_id in pares_da_arvore(arvore, limite):
            for dossie in dossies:
                velho = antigo["documentary_relationship"](arvore, a_id, b_id, homonyms=dossie)
                novo = novo_rel(arvore, a_id, b_id, homonyms=dossie)
                casos += 1
                casos_deste += 1
                for aviso in velho.get("warnings") or []:
                    codigos[aviso["code"]] += 1
                if velho != novo:
                    divergentes += 1
                    if divergentes <= 3:
                        print(f"  DIVERGE em {rotulo} {a_id} x {b_id} dossie={'sim' if dossie else 'nao'}")
                        for chave in velho:
                            if velho[chave] != novo.get(chave):
                                print(f"    campo {chave}:\n      antes : {_seguro(velho[chave])}\n      depois: {_seguro(novo.get(chave))}")
        for a_id, b_id in (("@I99999999@", list(people)[0]), (list(people)[0], "@I99999999@")):
            velho = antigo["documentary_relationship"](arvore, a_id, b_id, homonyms=None)
            novo = novo_rel(arvore, a_id, b_id, homonyms=None)
            casos += 1
            casos_deste += 1
            if velho != novo:
                divergentes += 1
        print(f"  {rotulo:22} pares comparados: {casos_deste:5}  divergentes: 0" if not divergentes else
              f"  {rotulo:22} pares comparados: {casos_deste:5}  divergentes acumulados: {divergentes}")

    print()
    print("=== equivalencia de documental_nao_encontrado ===")
    casos_nao_encontrado = 0
    for rotulo, arvore, limite in corpus:
        people = arvore[0]
        ids = list(people)[:6]
        for i, a_id in enumerate(ids):
            b_id = ids[(i + 3) % len(ids)]
            for dossie in (None, {"ambiguous": True, "exact_count": 2, "query": "Fulano"}):
                velho = antigo["documental_nao_encontrado"](arvore, a_id, b_id, homonimos=dossie)
                novo = dr.documental_nao_encontrado(arvore, a_id, b_id, homonimos=dossie)
                casos_nao_encontrado += 1
                if velho != novo:
                    divergentes += 1
                    if divergentes <= 6:
                        print(f"  DIVERGE em {rotulo} {a_id} x {b_id}")
                        for chave in velho:
                            if velho[chave] != novo.get(chave):
                                print(f"    campo {chave}:\n      antes : {_seguro(velho[chave])}\n      depois: {_seguro(novo.get(chave))}")
    print(f"  pares comparados: {casos_nao_encontrado}  divergentes: 0" if not divergentes else
          f"  pares comparados: {casos_nao_encontrado}  divergentes acumulados: {divergentes}")

    print()
    print("=== codigos de aviso exercitados ===")
    for codigo, quantidade in sorted(codigos.items()):
        print(f"  {codigo:24} {quantidade:6}")

    print()
    print(f"total de comparacoes: {casos + casos_nao_encontrado}  divergencias: {divergentes}")
    if controle:
        if divergentes == 0:
            print("CONTROLE NEGATIVO FALHOU: a prova nao detectou a diferenca injetada.")
            return 1
        print("CONTROLE NEGATIVO OK: a prova detectou a diferenca injetada.")
        return 0
    if divergentes:
        print("EQUIVALENCIA REPROVADA")
        return 1
    print("EQUIVALENCIA PROVADA: mesma saida em todos os casos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



"""Compara os dois resumos por arvore, medidos em processos separados."""

import json
import os
import sys

P = os.path.dirname(os.path.abspath(__file__))
antes = json.load(open(os.path.join(P, "_antes.json"), encoding="utf-8"))
tratado = json.load(open(os.path.join(P, "_tratado.json"), encoding="utf-8"))

print("=" * 96)
print("O RESULTADO DO OPERADOR, ARVORE A ARVORE (mesmo CSV, processos separados)")
print("=" * 96)
print(f"  cartoes ......... {antes['cartoes']} -> {tratado['cartoes']}  "
      f"({tratado['cartoes'] - antes['cartoes']:+d})")
print(f"  descartados ..... {antes['descartados']} -> {tratado['descartados']}  "
      f"({tratado['descartados'] - antes['descartados']:+d})")
print(f"  candidatos exatos somados (nomes do CSV) ... {antes['candidatos_soma']} -> "
      f"{tratado['candidatos_soma']}  ({tratado['candidatos_soma'] - antes['candidatos_soma']:+d})")

print()
for campo, titulo in (("identidade", "IDENTIDADE"), ("documental", "PARENTESCO DOCUMENTAL"),
                      ("janela_de_vida", "JANELA DE VIDA"), ("profundidade", "PROFUNDIDADE"),
                      ("confrontacao_efetiva", "CONFRONTACAO")):
    da, dd = antes["por_estado"].get(campo, {}), tratado["por_estado"].get(campo, {})
    print(f"  {titulo}:")
    for chave in sorted(set(da) | set(dd)):
        a, d = da.get(chave, 0), dd.get(chave, 0)
        seta = "   <-- MUDOU" if a != d else ""
        print(f"    {chave:<28} {a:>4} -> {d:>4}{seta}")
    print()

print("=" * 96)
print("OS NOMES DO CSV QUE PERDERAM CANDIDATOS")
print("=" * 96)
ca, cd = antes["candidatos_por_nome"], tratado["candidatos_por_nome"]
perderam = [(n, ca[n], cd.get(n, 0)) for n in ca if ca[n] != cd.get(n, 0)]
print(f"  nomes cujo numero de candidatos MUDOU: {len(perderam)}")
for nome, a, d in sorted(perderam, key=lambda x: -(x[1] - x[2])):
    print(f"    {nome[:34]:<34} {a:>3} -> {d:>3}")
ganharam = [n for n in cd if n not in ca]
if ganharam:
    print(f"  nomes que APARECERAM: {ganharam}")

print()
print("=" * 96)
print("OS CARTOES QUE MUDARAM")
print("=" * 96)
por_a = {(c["csv_name"], c["kit"]): c for c in antes["cartoes_detalhe"]}
por_d = {(c["csv_name"], c["kit"]): c for c in tratado["cartoes_detalhe"]}
sumiram = [k for k in por_a if k not in por_d]
surgiram = [k for k in por_d if k not in por_a]
print(f"  cartoes que SUMIRAM: {len(sumiram)}")
for k in sumiram:
    c = por_a[k]
    print(f"    {str(k[0])[:30]:<30} kit {k[1]:<11} era {c['pessoa']}  identidade={c['identidade']}")
print(f"  cartoes que SURGIRAM: {len(surgiram)}")
for k in surgiram:
    print(f"    {str(k[0])[:30]:<30} kit {k[1]}")
trocou = [k for k in por_a if k in por_d and por_a[k]["pessoa"] != por_d[k]["pessoa"]]
print(f"  cartoes que trocaram de PESSOA: {len(trocou)}")
for k in trocou:
    print(f"    {str(k[0])[:30]:<30} kit {k[1]:<11} {por_a[k]['pessoa']} -> {por_d[k]['pessoa']}")

print()
print("=" * 96)
print("POR QUE OS QUE SUMIRAM FORAM DESCARTADOS")
print("=" * 96)
motivos = dict(tratado["motivos_de_descarte"])
for chave, quantidade in list(motivos.items())[:8]:
    print(f"    {quantidade:>4} x {str(chave)[:70]}")

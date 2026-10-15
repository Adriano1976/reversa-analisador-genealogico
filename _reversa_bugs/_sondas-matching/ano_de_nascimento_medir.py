"""Quanto um ANO DE NASCIMENTO da pessoa testada discriminaria — medido.

A pergunta do operador: se o CSV trouxesse o ano de nascimento da pessoa testada, a
precisao melhoraria?

A resposta NAO e' a mesma de "melhorar a janela de vida". A janela de vida pergunta se o
registro escolhido PODERIA ter doado DNA (idade <= 122). Um ano de nascimento na planilha
pergunta outra coisa, muito mais forte: se o registro da arvore E' a mesma pessoa que
testou. Mesma pessoa => mesmo ano de nascimento. E' igualdade, nao plausibilidade.

O que decide se isso vale e' uma coisa so': os candidatos de um nome ambiguo tem anos de
nascimento DIFERENTES entre si? Se tiverem, a coluna resolve o homonimo. Se forem iguais —
ou se faltarem —, a coluna nao compra nada.

Mede:
  A. os 11 homonimos do CSV: os anos de nascimento de cada candidato, e se (nome + ano)
     isola um registro;
  B. a arvore inteira: entre os nomes com mais de um registro, quantos ficam UNICOS quando
     se acrescenta o ano de nascimento — a alavancagem da coluna, medida no corpus;
  C. a cobertura: quantos registros tem ano, porque o filtro so' funciona onde o dado existe.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\ano_de_nascimento_medir.py
"""

import collections
import os
import re
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from core.documentary_relationship import homonym_dossier  # noqa: E402
from core.name_normalization import norm_name  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.csv_ingest import read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

GED = os.path.join(R, "src", "uploads", "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(R, "src", "uploads", "03f50d273442cef1__Famílias_Sergipanas.csv")


def ano_de_nascimento(arvore, pessoa_id):
    """O ano do BIRT/DATE, ou None. Tolera `ABT 1850`, `BEF 1900` e afins."""
    pessoa = arvore[0].get(pessoa_id)
    if pessoa is None:
        return None
    for registro in pessoa.sub_records:
        if registro.tag != "BIRT":
            continue
        for filho in registro.sub_records:
            if filho.tag == "DATE" and filho.value:
                achado = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", str(filho.value))
                if achado:
                    return int(achado.group(1))
    return None


def main():
    arvore = carregar_arvore(GED)
    pessoas = arvore[0]
    df = read_csv_with_fallback(CSV)

    print("=" * 100)
    print("A. OS 11 HOMONIMOS — os candidatos tem anos DIFERENTES entre si?")
    print("=" * 100)
    nomes = sorted({str(n) for n in df["Name"].dropna()})
    ambiguos = []
    for nome in nomes:
        fichas = homonym_dossier(arvore, nome)["exact_matches"]
        if len(fichas) > 1:
            ambiguos.append((nome, [f["id"] for f in fichas]))

    resolve = 0
    for nome, ids in sorted(ambiguos, key=lambda x: -len(x[1])):
        anos = [ano_de_nascimento(arvore, i) for i in ids]
        conhecidos = [a for a in anos if a]
        distintos = sorted(set(conhecidos))
        # (nome + ano) isola um registro? Só quando TODOS tem ano e todos os anos diferem.
        separa = len(conhecidos) == len(anos) and len(distintos) == len(anos) and len(anos) > 1
        resolve += 1 if separa else 0
        marca = "SEPARA" if separa else ("parcial" if len(distintos) > 1 else "NAO SEPARA")
        print(f"  {nome[:26]:<26} {len(anos)} cands  anos={str(anos):<34} {marca}")
    print(f"\n  >>> o ano separaria por completo: {resolve} de {len(ambiguos)}")
    sem_ano = sum(1 for _, ids in ambiguos
                  for i in ids if ano_de_nascimento(arvore, i) is None)
    total_cands = sum(len(ids) for _, ids in ambiguos)
    print(f"  candidatos SEM ano de nascimento na arvore: {sem_ano} de {total_cands}")

    print("\n" + "=" * 100)
    print("B. A ALAVANCAGEM NO CORPUS — (nome + ano) isola quantos registros?")
    print("=" * 100)
    por_nome = collections.defaultdict(list)
    for pessoa_id, pessoa in pessoas.items():
        chave = norm_name(get_name(pessoa))
        if chave:
            por_nome[chave].append(pessoa_id)

    repetidos = {n: ids for n, ids in por_nome.items() if len(ids) > 1}
    resolvidos = 0
    continua_ambiguo = 0
    sem_dado = 0
    for nome, ids in repetidos.items():
        anos = [ano_de_nascimento(arvore, i) for i in ids]
        conhecidos = [a for a in anos if a]
        if len(conhecidos) < len(anos):
            sem_dado += 1
            continue
        if len(set(conhecidos)) == len(anos):
            resolvidos += 1
        else:
            continua_ambiguo += 1
    print(f"  nomes com mais de um registro: {len(repetidos)}")
    print(f"    (nome + ano) ISOLA todos os registros ...... {resolvidos}")
    print(f"    continua ambiguo (anos repetidos) ......... {continua_ambiguo}")
    print(f"    nao da' para decidir (falta ano) .......... {sem_dado}")
    if repetidos:
        print(f"\n  >>> a coluna resolveria {resolvidos} de {len(repetidos)} nomes ambiguos "
              f"({100.0 * resolvidos / len(repetidos):.1f}%)")

    print("\n" + "=" * 100)
    print("C. COBERTURA — o filtro so' funciona onde o dado existe")
    print("=" * 100)
    total = len(pessoas)
    com_ano = sum(1 for i in pessoas if ano_de_nascimento(arvore, i) is not None)
    print(f"  pessoas com ano de nascimento na arvore: {com_ano} de {total} "
          f"({100.0 * com_ano / total:.1f}%)")
    print(f"  pessoas sem: {total - com_ano} ({100.0 * (total - com_ano) / total:.1f}%)")
    print("\n  E' esta a cobertura do lado da ARVORE. Do lado da PLANILHA seria 100% por")
    print("  construcao, se o campo viesse preenchido — mas o casamento exige os DOIS lados.")


if __name__ == "__main__":
    main()

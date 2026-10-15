"""Parte C da sonda, com o filtro de vazio CORRETO.

A coluna do CSV e' `object` com `NaN` de verdade, e o filtro por texto ('nan') nao os
pegava: a primeira medicao contou 1289 linhas "com Y Haplogroup" quando o preenchido real
e' 287. O numero errado inflava o teste de contradicao de 105 para o que ele e' de fato.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\haplogrupo_medir.py
"""

import collections
import os
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from core.documentary_relationship import homonym_dossier  # noqa: E402
from parsers.csv_ingest import read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

GED = os.path.join(R, "src", "uploads", "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(R, "src", "uploads", "03f50d273442cef1__Famílias_Sergipanas.csv")


def main():
    arvore = carregar_arvore(GED)
    df = read_csv_with_fallback(CSV)

    print("=" * 96)
    print("PREECHIMENTO REAL DAS COLUNAS IGNORADAS")
    print("=" * 96)
    for coluna in ("Y Haplogroup", "MT Haplogroup", "Overlap"):
        serie = df[coluna]
        vazios = int(serie.isna().sum())
        print(f"  {coluna:<16} preenchidos em {len(serie) - vazios:>5} de {len(serie)} linhas "
              f"({100.0 * (len(serie) - vazios) / len(serie):>5.1f}%)")

    print("\n" + "=" * 96)
    print("CONTRADICAO QUE O Y HAPLOGROUP PERMITIRIA — so' nas linhas em que ele EXISTE")
    print("=" * 96)
    com_y = df[df["Y Haplogroup"].notna()]
    print(f"  linhas com Y Haplogroup: {len(com_y)}")
    sexos = collections.Counter()
    contradicoes = []
    for _, linha in com_y.iterrows():
        nome = str(linha["Name"])
        for ficha in homonym_dossier(arvore, nome)["exact_matches"]:
            sexo = next((r.value for r in arvore[0][ficha["id"]].sub_records if r.tag == "SEX"), None)
            sexos[sexo] += 1
            if sexo == "F":
                contradicoes.append((nome, linha.get("Kit number"), linha["Y Haplogroup"]))
    print(f"  sexo dos registros alcancados por esses nomes: {dict(sexos)}")
    print(f"  CONTRADICOES (Y preenchido = testador homem x registro FEMININO): {len(contradicoes)}")
    for nome, kit, valor in contradicoes[:12]:
        print(f"    {nome[:32]:<32} kit {kit}  Y={valor!r}")
    if not contradicoes:
        print("    (nenhuma)")

    print("\n" + "=" * 96)
    print("O SINAL QUE O Y DA' E QUE A ARVORE NAO DA': separar por SOBRENOME paterno")
    print("=" * 96)
    # Um haplogrupo Y igual entre DOIS matches de sobrenomes diferentes e' evidencia de
    # ancestral paterno comum — coisa que o cM sozinho nao separa de endogamia.
    por_haplo = collections.defaultdict(set)
    for _, linha in com_y.iterrows():
        por_haplo[linha["Y Haplogroup"]].add(str(linha["Name"]).split()[-1])
    repetidos = {h: nomes for h, nomes in por_haplo.items()
                 if len([n for n in nomes if n]) > 1 and len(por_haplo[h]) > 1}
    print(f"  haplogrupos Y distintos entre {len(com_y)} linhas: {len(por_haplo)}")
    print(f"  haplogrupos que agrupam mais de um SOBRENOME: {len(repetidos)}")
    for haplo, nomes in list(repetidos.items())[:6]:
        print(f"    {haplo:<14} {sorted(nomes)[:6]}")


if __name__ == "__main__":
    main()

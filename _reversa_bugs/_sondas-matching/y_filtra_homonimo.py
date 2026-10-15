"""O Y haplogroup resolve algum dos 11 casos de homonimo? — medido, caso a caso.

A pergunta que decide a recomendacao. O raciocinio:

  linha com `Y Haplogroup` preenchido  =>  o TESTADOR e' homem.
  Se o nome do CSV casa com um registro FEMININO na arvore, ou a linha nao e' daquela
  pessoa, ou o registro escolhido esta' errado. Em qualquer dos casos, o candidato feminino
  esta' ELIMINADO — e isso e' um filtro de sexo que a planilha doa de graca, sem coluna nova.

Para cada nome com mais de um registro exato na arvore (os homonimos reais), mede quantos
candidatos o Y elimina. Se elimina zero em todos, o sinal nao serve para homonimo e a
recomendacao muda.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\y_filtra_homonimo.py
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


def sexo(arvore, pessoa_id):
    return next((r.value for r in arvore[0][pessoa_id].sub_records if r.tag == "SEX"), None)


def main():
    arvore = carregar_arvore(GED)
    df = read_csv_with_fallback(CSV)

    # Nomes com mais de um registro exato na arvore = os homonimos reais.
    nomes = sorted({str(n) for n in df["Name"].dropna()})
    ambiguos = []
    for nome in nomes:
        fichas = homonym_dossier(arvore, nome)["exact_matches"]
        if len(fichas) > 1:
            ambiguos.append((nome, fichas))

    print("=" * 100)
    print("OS 11 HOMONIMOS: o Y haplogroup elimina algum candidato?")
    print("=" * 100)
    print(f"{'nome':<26} {'Y?':<6} {'cands':>5} {'M':>4} {'F':>4} {'sem sexo':>8}  elimina")
    print("-" * 100)

    total_eliminados = 0
    casos_com_y = 0
    for nome, fichas in sorted(ambiguos, key=lambda x: -len(x[1])):
        linhas = df[df["Name"] == nome]
        y = linhas["Y Haplogroup"].dropna()
        tem_y = len(y) > 0
        contagem = collections.Counter(sexo(arvore, f["id"]) for f in fichas)
        elimina = contagem.get("F", 0) if tem_y else 0
        total_eliminados += elimina
        casos_com_y += 1 if tem_y else 0
        print(f"{nome[:26]:<26} {'sim' if tem_y else 'NAO':<6} {len(fichas):>5} "
              f"{contagem.get('M', 0):>4} {contagem.get('F', 0):>4} {contagem.get(None, 0):>8}  "
              f"{('-' + str(elimina)) if tem_y else '(nao se aplica)'}")

    print("-" * 100)
    print(f"  homonimos com Y haplogroup na planilha: {casos_com_y} de {len(ambiguos)}")
    print(f"  candidatos eliminados no total: {total_eliminados}")

    print("\n" + "=" * 100)
    print("O SINAL MAIS DIRETO: o Y revela o SEXO DO TESTADOR, e a arvore diz o do registro")
    print("=" * 100)
    com_y = df[df["Y Haplogroup"].notna()]
    sem_y = df[df["Y Haplogroup"].isna()]
    print(f"  linhas com Y (testador HOMEM por definicao): {len(com_y)}")
    print(f"  linhas sem Y: {len(sem_y)}  (mulher OU homem sem teste de Y — nao da' para separar)")

    # Quantos cartoes da analise tem carta na manga: nome ambiguo + Y preenchido.
    print("\n  Cruzando com a analise: quantos cartoes ficam com o sexo DEDUZIVEL?")
    kits_com_y = set(com_y["Kit number"])
    kits_sem_y = set(sem_y["Kit number"])
    print(f"    kits com Y preenchido: {len(kits_com_y)}")
    print(f"    kits sem Y: {len(kits_sem_y)}")

    print("\n" + "=" * 100)
    print("VEREDITO")
    print("=" * 100)
    if total_eliminados:
        print(f"  O Y elimina {total_eliminados} candidato(s) nos casos de homonimo. Serve.")
    else:
        print("  O Y NAO elimina candidato nenhum nos casos de homonimo deste arquivo.")
        print("  Motivo: os nomes ambiguos nao tem Y preenchido, ou os candidatos sao do")
        print("  mesmo sexo. Sem isso, o sinal nao ataca o problema que o operador apontou.")


if __name__ == "__main__":
    main()

"""Quanta precisao cada campo NOVO do formulario compraria — medido, nao opinado.

Duas perguntas do operador:
  1. que informacao do USUARIO falta ao lado de "2. Seu Nome (como esta no GEDCOM)";
  2. que informacao falta na planilha "1. Lista de Matches (CSV)".

Este script nao propoe nada: ele mede a alavancagem de cada candidato sobre os
arquivos reais, para que a proposta que sobreviver seja a que tem numero.

Mede:
  A. a escolha da RAIZ — quantos registros o nome do operador alcanca, qual deles o
     app pega, e o que muda no `ano_base` da janela de vida (o app ANCORA a
     verificacao de idade no nascimento da raiz);
  B. a PRESSAO DE HOMONIMOS nos nomes do CSV — quantos nomes tem mais de um registro
     exato na arvore, e quantos cartoes ficam em `a_confirmar`;
  C. o que a planilha JA TRAZ e o app IGNORA — `Y Haplogroup`, `MT Haplogroup` e
     `Overlap` —, com o teste de contradicao que o haplogrupo Y permitiria hoje:
     linha com Y haplogroup implica testador homem; se a pessoa casada na arvore for
     mulher, ha contradicao.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\campos_que_faltam.py
"""

import collections
import os
import sys

RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ_PROJETO)
sys.path.insert(0, os.path.join(RAIZ_PROJETO, "src"))

from core.documentary_relationship import homonym_dossier  # noqa: E402
from core.name_normalization import norm_name  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.csv_ingest import read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

GED = os.path.join(RAIZ_PROJETO, "src", "uploads",
                   "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(RAIZ_PROJETO, "src", "uploads",
                   "03f50d273442cef1__Famílias_Sergipanas.csv")
RAIZ = "Adriano Santos"


def nascimento(arvore, pessoa_id):
    from core.janela_de_vida import ano_de_referencia

    for registro in arvore[0][pessoa_id].sub_records:
        if registro.tag == "BIRT":
            for filho in registro.sub_records:
                if filho.tag == "DATE":
                    return filho.value, ano_de_referencia(2026, filho.value)
    return None, ano_de_referencia(2026, None)


def main():
    arvore = carregar_arvore(GED)
    print(f"arvore: {len(arvore[0])} pessoas")

    # ------------------------------------------------------------------ A
    print("\n" + "=" * 96)
    print("A. A ESCOLHA DA RAIZ — o app pega o PRIMEIRO que casa por substring")
    print("=" * 96)
    regra_do_app = [p for p, pessoa in arvore[0].items() if RAIZ.lower() in get_name(pessoa).lower()]
    print(f"  nome informado: {RAIZ!r}")
    print(f"  registros alcancados pela MESMA regra do app (`root_name in nome`): {len(regra_do_app)}")
    for posicao, pessoa_id in enumerate(regra_do_app[:12], 1):
        data, ano_base = nascimento(arvore, pessoa_id)
        marca = "  <<< o app usa ESTE" if posicao == 1 else ""
        print(f"    {posicao:>2}. {pessoa_id:<14} {get_name(arvore[0][pessoa_id])[:44]:<44} "
              f"nasc={str(data):<14} ano_base={ano_base}{marca}")
    if len(regra_do_app) > 12:
        print(f"    ... e mais {len(regra_do_app) - 12}")

    exatos = homonym_dossier(arvore, RAIZ)
    print(f"\n  registros com o nome EXATO (normalizado): {exatos['exact_count']}")
    anexos = [p for p, pessoa in arvore[0].items() if norm_name(get_name(pessoa)) == norm_name(RAIZ)]
    print(f"  registros com o nome exato pela normalizacao do app: {len(anexos)}")
    anos = sorted({nascimento(arvore, p)[1] for p in regra_do_app})
    print(f"  anos-base possiveis entre os alcancados: {anos}")
    if len(anos) > 1:
        print(f"  >>> a janela de vida muda de ancora conforme a raiz escolhida "
              f"({anos[0]} a {anos[-1]}): o erro de raiz NAO fica so' no aviso")

    # ------------------------------------------------------------------ B
    print("\n" + "=" * 96)
    print("B. PRESSAO DE HOMONIMOS NOS NOMES DO CSV")
    print("=" * 96)
    df = read_csv_with_fallback(CSV)
    nomes = sorted({str(n) for n in df["Name"].dropna()})
    print(f"  nomes distintos no CSV: {len(nomes)}")
    contagem = {}
    for nome in nomes:
        contagem[nome] = homonym_dossier(arvore, nome)["exact_count"]
    distribuicao = collections.Counter(contagem.values())
    for quantidade in sorted(distribuicao):
        rotulo = "1 registro exato" if quantidade == 1 else f"{quantidade} registros exatos"
        print(f"    {rotulo:<22} {distribuicao[quantidade]:>4} nome(s)")
    ambiguos = [n for n, c in contagem.items() if c > 1]
    sem_registro = [n for n, c in contagem.items() if c == 0]
    print(f"\n  nomes com mais de um registro exato (homonimo real): {len(ambiguos)}")
    for nome in sorted(ambiguos, key=lambda n: -contagem[n])[:12]:
        print(f"    {contagem[nome]:>3} x {nome!r}")
    print(f"  nomes sem NENHUM registro exato: {len(sem_registro)}")

    # ------------------------------------------------------------------ C
    print("\n" + "=" * 96)
    print("C. O QUE A PLANILHA JA TRAZ E O APP IGNORA")
    print("=" * 96)
    for coluna in ("Y Haplogroup", "MT Haplogroup", "Overlap"):
        if coluna not in df.columns:
            print(f"  {coluna:<16} AUSENTE neste CSV")
            continue
        valores = df[coluna].astype(str).str.strip()
        preenchidos = valores[~valores.str.lower().isin(("", "nan", "none", "-"))]
        distintos = preenchidos.nunique()
        print(f"  {coluna:<16} preenchidos em {len(preenchidos):>5} de {len(df)} linhas "
              f"({100.0 * len(preenchidos) / len(df):>5.1f}%), {distintos} valor(es) distinto(s)")
        if distintos and distintos <= 8:
            print(f"      valores: {sorted(preenchidos.unique())}")

    # O teste de contradicao que o Y Haplogroup permitiria HOJE, sem pedir nada novo.
    if "Y Haplogroup" in df.columns:
        y = df["Y Haplogroup"].astype(str).str.strip()
        tem_y = ~y.str.lower().isin(("", "nan", "none", "-"))
        sexos = collections.Counter()
        contradicoes = []
        for _, linha in df[tem_y].iterrows():
            nome = str(linha["Name"])
            candidatos = homonym_dossier(arvore, nome)["exact_matches"]
            for ficha in candidatos:
                sexo = next((r.value for r in arvore[0][ficha["id"]].sub_records
                             if r.tag == "SEX"), None)
                sexos[sexo] += 1
                if sexo == "F":
                    contradicoes.append((nome, linha.get("Kit number"), y[linha.name]))
        print(f"\n  linhas COM Y Haplogroup: {int(tem_y.sum())}")
        print(f"  sexo dos registros que esses nomes alcancam: {dict(sexos)}")
        print(f"  CONTRADICOES (linha com Y = testador homem, registro feminino): {len(contradicoes)}")
        for nome, kit, valor in contradicoes[:10]:
            print(f"    {nome[:34]:<34} kit {kit}  Y={valor!r}  -> registro FEMININO na arvore")
        if not contradicoes:
            print("    (nenhuma: neste arquivo o sinal nao separa nada)")


if __name__ == "__main__":
    main()

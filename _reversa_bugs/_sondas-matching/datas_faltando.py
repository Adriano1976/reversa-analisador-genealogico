"""Datas de nascimento faltando no GEDCOM — cobertura, tipos de falha e onde ela pesa.

A pergunta do operador: "o arquivo ainda tem datas de nascimento faltando?".

A contagem crua ("32,3% das pessoas") nao responde o que ele precisa saber. O GEDCOM tem
35 mil pessoas, a maioria ancestrais distantes que nao participam de nenhuma escolha. O que
decide se vale usar o ano de nascimento como sinal e' a cobertura ONDE A ESCOLHA ACONTECE:
nos registros que o app precisa comparar entre si.

Mede:
  A. identidade do arquivo (tamanho, mtime, sha256) — para saber se e' o mesmo que foi medido;
  B. cobertura crua, separando os TIPOS de falha (sem BIRT, BIRT sem DATE, data qualificada,
     intervalo, data ilegivel);
  C. cobertura nos lugares que decidem: a raiz, os registros escolhidos e os CANDIDATOS de
     cada homonimo;
  D. concentracao: a falta esta' nos ancestrais distantes ou nos contemporaneos?

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\datas_faltando.py
"""

import collections
import hashlib
import os
import re
import sys
import time

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from core.documentary_relationship import homonym_dossier  # noqa: E402
from core.name_normalization import norm_name  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.csv_ingest import read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

GED = os.path.join(R, "src", "uploads", "0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(R, "src", "uploads", "03f50d273442cef1__Famílias_Sergipanas.csv")

# Os qualificadores que o GEDCOM usa quando a data NAO e' exata. A lista e' a mesma que
# `core.janela_de_vida` trata; aqui ela serve para SEPARAR "sem data" de "data aproximada",
# que sao problemas diferentes.
QUALIFICADORES = ("ABT", "EST", "CAL", "BEF", "AFT", "CIRCA", "ABOUT", "APPROX")
ANO = re.compile(r"\b(1[0-9]{3}|20[0-9]{2}|[0-9]{3})\b")


def analisar_pessoa(pessoa):
    """Devolve (ano, tipo) — `tipo` diz POR QUE o ano existe ou falta."""
    registros_birt = [r for r in pessoa.sub_records if r.tag == "BIRT"]
    if not registros_birt:
        return None, "sem BIRT"
    datas = [f.value for r in registros_birt for f in r.sub_records
             if f.tag == "DATE" and f.value]
    if not datas:
        return None, "BIRT sem DATE"
    bruto = str(datas[0]).strip()
    achado = ANO.search(bruto.upper())
    if not achado:
        return None, "DATE ilegivel: " + bruto[:24]
    ano = int(achado.group(1))
    texto = bruto.upper()
    if "BET" in texto and "AND" in texto:
        return ano, "intervalo (BET ... AND)"
    if any(texto.startswith(q) or texto.startswith(q + " ") for q in QUALIFICADORES):
        return ano, "qualificada (ABT/EST/BEF/AFT...)"
    if len(datas) > 1:
        return ano, "mais de um DATE"
    return ano, "exata"


def main():
    print("=" * 100)
    print("A. IDENTIDADE DO ARQUIVO")
    print("=" * 100)
    info = os.stat(GED)
    with open(GED, "rb") as fh:
        resumo = hashlib.sha256(fh.read()).hexdigest()
    print(f"  caminho : {GED}")
    print(f"  bytes   : {info.st_size:,}".replace(",", "."))
    print(f"  mtime   : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info.st_mtime))}")
    print(f"  sha256  : {resumo}")
    print(f"  (a analise desta sessao leu um arquivo de 5.332.206 bytes)")

    arvore = carregar_arvore(GED)
    pessoas = arvore[0]
    print(f"\n  pessoas : {len(pessoas):,}".replace(",", "."))

    print("\n" + "=" * 100)
    print("B. COBERTURA CRUA, POR TIPO DE FALHA")
    print("=" * 100)
    tipos = collections.Counter()
    anos = {}
    for pessoa_id, pessoa in pessoas.items():
        ano, tipo = analisar_pessoa(pessoa)
        tipos[tipo.split(":")[0]] += 1
        anos[pessoa_id] = ano
    com_ano = sum(1 for a in anos.values() if a)
    print(f"  com ano : {com_ano:>7,}  ({100.0 * com_ano / len(pessoas):5.1f}%)".replace(",", "."))
    print(f"  sem ano : {len(pessoas) - com_ano:>7,}  ({100.0 * (len(pessoas) - com_ano) / len(pessoas):5.1f}%)".replace(",", "."))
    print()
    for tipo, quantidade in tipos.most_common():
        print(f"    {tipo:<34} {quantidade:>7,}".replace(",", "."))

    print("\n" + "=" * 100)
    print("C. COBERTURA ONDE A ESCOLHA ACONTECE")
    print("=" * 100)
    df = read_csv_with_fallback(CSV)
    nomes_csv = sorted({str(n) for n in df["Name"].dropna()})

    candidatos_total = 0
    candidatos_com_ano = 0
    nomes_com_2_ou_mais = 0
    nomes_com_2_ou_mais_e_anos = 0
    nomes_sem_nenhum_ano = []
    for nome in nomes_csv:
        fichas = homonym_dossier(arvore, nome)["exact_matches"]
        if len(fichas) < 2:
            continue
        nomes_com_2_ou_mais += 1
        anos_cands = [anos.get(f["id"]) for f in fichas]
        candidatos_total += len(anos_cands)
        com = [a for a in anos_cands if a]
        candidatos_com_ano += len(com)
        if len(com) == len(anos_cands):
            nomes_com_2_ou_mais_e_anos += 1
        elif not com:
            nomes_sem_nenhum_ano.append(nome)

    print(f"  nomes do CSV com 2+ registros exatos (homonimos): {nomes_com_2_ou_mais}")
    print(f"    ... com ano em TODOS os candidatos .......... {nomes_com_2_ou_mais_e_anos}")
    print(f"    ... sem ano em NENHUM candidato ............. {len(nomes_sem_nenhum_ano)}")
    if nomes_sem_nenhum_ano:
        for nome in nomes_sem_nenhum_ano[:10]:
            print(f"        {nome!r}")
    print(f"  candidatos (registros a comparar): {candidatos_total}")
    print(f"    com ano: {candidatos_com_ano} ({100.0 * candidatos_com_ano / max(candidatos_total, 1):.1f}%)")

    # A raiz.
    raiz = [p for p, pessoa in pessoas.items() if "adriano santos" in get_name(pessoa).lower()]
    for pessoa_id in raiz:
        print(f"\n  raiz {pessoa_id}: ano = {anos.get(pessoa_id)}")

    print("\n" + "=" * 100)
    print("D. CONCENTRACAO — a falta esta' nos distantes ou nos contemporaneos?")
    print("=" * 100)
    # Quem nao aparece como pai/mae de ninguem e' folha da arvore: ancestral distante ou
    # pessoa sem descendencia registrada. E' onde a data faz menos falta.
    tem_filho = set()
    for familia in arvore[1].values():
        # `sub_tag_value` RESOLVE a referencia e o arquivo ja' foi fechado por
        # `carregar_arvore` (ValueError: seek of closed file). O valor cru do registro basta.
        for registro in familia.sub_records:
            if registro.tag in ("HUSB", "WIFE") and registro.value:
                tem_filho.add(str(registro.value))
    faixas = collections.Counter()
    for pessoa_id in pessoas:
        ano = anos.get(pessoa_id)
        if ano is None:
            faixas["SEM ANO"] += 1
        elif ano < 1800:
            faixas["antes de 1800"] += 1
        elif ano < 1900:
            faixas["1800-1899"] += 1
        elif ano < 1950:
            faixas["1900-1949"] += 1
        else:
            faixas["1950 ou depois"] += 1
    for faixa in ("antes de 1800", "1800-1899", "1900-1949", "1950 ou depois", "SEM ANO"):
        quantidade = faixas[faixa]
        print(f"    {faixa:<18} {quantidade:>7,}  ({100.0 * quantidade / len(pessoas):5.1f}%)".replace(",", "."))

    sem_ano_com_filho = sum(1 for p in tem_filho if p in pessoas and anos.get(p) is None)
    com_ano_contemporaneo = sum(1 for p, a in anos.items() if a and a >= 1900)
    print(f"\n  pessoas SEM ano que SAO pai/mae de alguem (elo de cadeia): "
          f"{sem_ano_com_filho:,}".replace(",", "."))
    print(f"  pessoas nascidas de 1900 em diante (candidatas a quem doou DNA): "
          f"{com_ano_contemporaneo:,}".replace(",", "."))


if __name__ == "__main__":
    main()

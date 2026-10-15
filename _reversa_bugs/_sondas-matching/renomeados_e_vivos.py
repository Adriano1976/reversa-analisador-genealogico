"""Os 1.886 renomeados pelo tratamento sao pessoas vivas?

Relevante por dois motivos: (a) o sufixo `[Homônimo - Ixxx]` carrega o xref do registro, e se
ele caiu em gente viva, o arquivo publica um identificador de pessoa viva; (b) saber se o
tratamento mirou os vivos ou os ancestrais antigos diz para que ele serve.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\renomeados_e_vivos.py
"""

import collections
import os
import re
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from core.janela_de_vida import IDADE_IMPOSSIVEL, IDADE_SUSPEITA, ano_de_referencia  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

P = os.path.join(R, "src", "uploads")
ANTES = os.path.join(P, "0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged")
DEPOIS = os.path.join(P, "e10c087ae4973fc9__Arvore_Unificada_Oficial_V1_2_Tratado.ged")
ANO = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")


def ano_e_obito(pessoa):
    nascimento, obito = None, False
    for r in pessoa.sub_records:
        if r.tag == "DEAT":
            obito = True
        elif r.tag == "BIRT":
            for f in r.sub_records:
                if f.tag == "DATE" and f.value:
                    achado = ANO.search(str(f.value))
                    if achado:
                        nascimento = int(achado.group(1))
    return nascimento, obito


def main():
    antes = carregar_arvore(ANTES)
    depois = carregar_arvore(DEPOIS)
    ano_base = ano_de_referencia(2026, None)

    renomeados = [pid for pid in (set(antes[0]) & set(depois[0]))
                  if get_name(antes[0][pid]) != get_name(depois[0][pid])]
    print(f"renomeados: {len(renomeados)}")

    faixas = collections.Counter()
    for pid in renomeados:
        nascimento, obito = ano_e_obito(depois[0][pid])
        if obito:
            faixas["tem obito registrado"] += 1
        elif nascimento is None:
            faixas["sem obito e sem data"] += 1
        elif nascimento > ano_base - IDADE_SUSPEITA:
            faixas[f"VIVO plausivel (>{ano_base - IDADE_SUSPEITA})"] += 1
        elif nascimento > ano_base - IDADE_IMPOSSIVEL:
            faixas[f"VIVO possivel (>{ano_base - IDADE_IMPOSSIVEL})"] += 1
        else:
            faixas["antigo demais para estar vivo"] += 1
    print("\n  os renomeados, por situacao de vida:")
    for chave, quantidade in faixas.most_common():
        print(f"    {chave:<38} {quantidade:>6,}".replace(",", "."))

    vivos = sum(v for k, v in faixas.items() if k.startswith("VIVO"))
    print(f"\n  renomeados que PODEM estar vivos: {vivos:,}".replace(",", "."))

    # Todos os nomes do arquivo que carregam o sufixo.
    com_sufixo = [pid for pid, p in depois[0].items() if "[Homônimo" in (get_name(p) or "")]
    print(f"  registros com o sufixo `[Homônimo` no nome: {len(com_sufixo):,}".replace(",", "."))
    vivos_com_sufixo = 0
    for pid in com_sufixo:
        nascimento, obito = ano_e_obito(depois[0][pid])
        if not obito and (nascimento is None or nascimento > ano_base - IDADE_IMPOSSIVEL):
            vivos_com_sufixo += 1
    print(f"  deles, sem obito e sem impedimento de idade: {vivos_com_sufixo:,}".replace(",", "."))


if __name__ == "__main__":
    main()

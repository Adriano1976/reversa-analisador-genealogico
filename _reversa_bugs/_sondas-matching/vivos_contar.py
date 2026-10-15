"""Quantas pessoas VIVAS — sob cada definicao possivel, porque a definicao muda o numero.

O arquivo NAO tem marcador de vida nem de privacidade: nenhuma tag `RESN`, `_LIVING` ou
`_PRIVATE`. A unica coisa disponivel e' a AUSENCIA de `DEAT` — que sozinha superestima muito,
porque GEDCOM de pesquisa omite obito de ancestral antigo cujo obito se desconhece.

Entao "viva" tem de ser inferida pela combinacao de duas coisas: nao ter obito registrado, e
o nascimento permitir que a pessoa ainda esteja viva. As duas definicoes usam os MESMOS
limiares que o projeto ja' declara em `core.janela_de_vida`:

  IDADE_IMPOSSIVEL = 122  -> nascido antes de (ano_base - 122) nao pode estar vivo;
  IDADE_SUSPEITA   = 105  -> nascido antes de (ano_base - 105) e' improvavel.

E ha' uma terceira pista, mais forte que as duas: nome GENERICO (`Indivíduo`, `Living`). Nome
substituido e' a forma classica de anonimizar quem esta' vivo num GEDCOM publicado.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\vivos_contar.py
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

GED = os.path.join(R, "src", "uploads",
                   "e10c087ae4973fc9__Arvore_Unificada_Oficial_V1_2_Tratado.ged")
ANO = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
GENERICOS = ("indivíduo", "individuo", "living", "privado", "private", "?")


def perfil(pessoa):
    """(ano_de_nascimento, tem_obito, nome_limpo_sem_sufixo) de um registro."""
    nascimento = None
    obito = False
    for r in pessoa.sub_records:
        if r.tag == "DEAT":
            obito = True
        elif r.tag == "BIRT":
            for f in r.sub_records:
                if f.tag == "DATE" and f.value:
                    achado = ANO.search(str(f.value))
                    if achado:
                        nascimento = int(achado.group(1))
    nome = (get_name(pessoa) or "").strip()
    return nascimento, obito, nome.split("[")[0].strip()


def main():
    arvore = carregar_arvore(GED)
    pessoas = arvore[0]
    ano_base = ano_de_referencia(2026, None)
    limite_122 = ano_base - IDADE_IMPOSSIVEL
    limite_105 = ano_base - IDADE_SUSPEITA
    print(f"pessoas: {len(pessoas)}   ano_base={ano_base}   "
          f"limite 122 anos={limite_122}   limite 105 anos={limite_105}")

    perfis = {pid: perfil(p) for pid, p in pessoas.items()}

    sem_obito = [pid for pid, (_, obito, _) in perfis.items() if not obito]
    sem_obito_e_jovem = [pid for pid in sem_obito
                         if perfis[pid][0] and perfis[pid][0] > limite_122]
    sem_obito_e_plausivel = [pid for pid in sem_obito
                             if perfis[pid][0] and perfis[pid][0] > limite_105]
    sem_obito_sem_data = [pid for pid in sem_obito if perfis[pid][0] is None]
    genericos = [pid for pid, (_, _, nome) in perfis.items()
                 if nome.lower() in GENERICOS]
    genericos_sem_obito = [pid for pid in genericos if not perfis[pid][1]]

    def nomes(ids):
        return {perfis[pid][2].lower() for pid in ids if perfis[pid][2]}

    definicoes = [
        ("A. sem obito registrado (cru)", sem_obito),
        (f"B. sem obito e nascido depois de {limite_122} (<=122 anos)", sem_obito_e_jovem),
        (f"C. sem obito e nascido depois de {limite_105} (<=105 anos)", sem_obito_e_plausivel),
        ("D. sem obito e SEM data de nascimento (indecidivel)", sem_obito_sem_data),
        ("E. nome generico (Indivíduo/Living)", genericos),
        ("F. nome generico E sem obito", genericos_sem_obito),
    ]

    print("\n" + "=" * 96)
    print("QUANTAS PESSOAS VIVAS, SOB CADA DEFINICAO")
    print("=" * 96)
    print(f"  {'definicao':<52} {'pessoas':>8} {'nomes distintos':>16}")
    print("  " + "-" * 78)
    for titulo, ids in definicoes:
        print(f"  {titulo:<52} {len(ids):>8,} {len(nomes(ids)):>16,}".replace(",", "."))

    print("\n" + "=" * 96)
    print("O QUE AS PISTAS DIZEM JUNTAS")
    print("=" * 96)
    # Um nome generico sem obito e' o sinal mais forte de "vivo anonimizado".
    com_data = [pid for pid in genericos_sem_obito if perfis[pid][0]]
    sem_data = [pid for pid in genericos_sem_obito if not perfis[pid][0]]
    print(f"  nome generico E sem obito ....... {len(genericos_sem_obito):>6,}".replace(",", "."))
    print(f"     com data de nascimento ....... {len(com_data):>6,}".replace(",", "."))
    print(f"     sem data ..................... {len(sem_data):>6,}".replace(",", "."))
    if com_data:
        anos = sorted(perfis[pid][0] for pid in com_data)
        print(f"     anos: de {anos[0]} a {anos[-1]}")

    print("\n  nome generico COM obito (nao e' vivo, so' nome faltando): "
          f"{len(genericos) - len(genericos_sem_obito):,}".replace(",", "."))

    # A faixa B por ano, para ver se ha' um corte natural.
    faixas = collections.Counter()
    for pid in sem_obito:
        ano = perfis[pid][0]
        if ano is None:
            faixas["sem data"] += 1
        elif ano >= 1950:
            faixas["1950 ou depois"] += 1
        elif ano >= 1900:
            faixas["1900-1949"] += 1
        elif ano >= 1800:
            faixas["1800-1899"] += 1
        else:
            faixas["antes de 1800"] += 1
    print("\n  os SEM OBITO, por epoca de nascimento:")
    for faixa in ("antes de 1800", "1800-1899", "1900-1949", "1950 ou depois", "sem data"):
        print(f"    {faixa:<18} {faixas[faixa]:>7,}".replace(",", "."))


if __name__ == "__main__":
    main()

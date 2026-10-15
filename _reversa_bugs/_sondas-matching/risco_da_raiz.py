"""Quanto o campo "Seu Nome" arrisca, medido na arvore inteira.

O app escolhe a raiz com `root_name.lower() in nome.lower()` e fica com o PRIMEIRO. Nao ha
desambiguacao: quando o nome alcanca mais de um registro, a escolha e' silenciosa e o aviso
so' aparece depois. E a raiz nao e' detalhe — o nascimento dela e' a ancora do `ano_base`,
que decide a idade de todo cartao em `core.janela_de_vida`.

Mede:
  A. quantos nomes da arvore sao compartilhados por mais de um registro (o risco geral);
  B. o que aconteceria com o `ano_base` se a raiz fosse outra;
  C. se o operador desta arvore corre esse risco hoje.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\risco_da_raiz.py
"""

import collections
import os
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from core.name_normalization import norm_name  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402

GED = os.path.join(R, "src", "uploads", "46733fab20ef75fa__Arvore_Unificada_Oficial_V1_2.ged")


def main():
    arvore = carregar_arvore(GED)
    pessoas = arvore[0]
    print(f"arvore: {len(pessoas)} pessoas")

    print("\n" + "=" * 96)
    print("A. NOMES COMPARTILHADOS — o risco de a raiz ser escolhida errado")
    print("=" * 96)
    por_nome = collections.Counter()
    for pessoa in pessoas.values():
        chave = norm_name(get_name(pessoa))
        if chave:
            por_nome[chave] += 1
    distribuicao = collections.Counter(por_nome.values())
    for quantidade in sorted(distribuicao):
        pessoas_afetadas = quantidade * distribuicao[quantidade]
        print(f"  {quantidade:>3} registro(s) com o mesmo nome: {distribuicao[quantidade]:>6} nome(s)"
              f"   -> {pessoas_afetadas:>6} pessoas")
    ambiguos = sum(n for q, n in distribuicao.items() if q > 1)
    total_nomes = len(por_nome)
    print(f"\n  nomes ambíguos: {ambiguos} de {total_nomes} ({100.0 * ambiguos / total_nomes:.1f}%)")
    pior = por_nome.most_common(8)
    print("  os piores:")
    for nome, quantidade in pior:
        print(f"    {quantidade:>4} x {nome[:60]!r}")

    print("\n" + "=" * 96)
    print("B. SE A RAIZ FOSSE OUTRA, O `ano_base` MUDARIA — e com ele a idade de TODO cartao")
    print("=" * 96)
    from core.janela_de_vida import ano_de_referencia

    nascimentos = collections.Counter()
    sem_data = 0
    for pessoa in pessoas.values():
        data = None
        for registro in pessoa.sub_records:
            if registro.tag == "BIRT":
                for filho in registro.sub_records:
                    if filho.tag == "DATE":
                        data = filho.value
        if data:
            nascimentos[ano_de_referencia(2026, data)] += 1
        else:
            sem_data += 1
    print(f"  pessoas SEM data de nascimento: {sem_data} de {len(pessoas)}"
          f" ({100.0 * sem_data / len(pessoas):.1f}%)")
    print("  anos-base que a arvore produziria, por pessoa:")
    for ano, quantidade in sorted(nascimentos.items()):
        print(f"    ano_base {ano}: {quantidade} pessoa(s)")
    print(f"\n  >>> sao {len(nascimentos)} ancoras possiveis. Escolher o registro errado desloca a"
          f"\n      ancora e muda a janela de vida de cartoes que nada tem a ver com o erro.")

    print("\n" + "=" * 96)
    print("C. O OPERADOR DESTA ARVORE CORRE ESSE RISCO?")
    print("=" * 96)
    for nome in ("Adriano Santos",):
        alcancados = [p for p, pessoa in pessoas.items() if nome.lower() in get_name(pessoa).lower()]
        exatos = por_nome.get(norm_name(nome), 0)
        print(f"  {nome!r}: alcancados pela regra do app = {len(alcancados)}; nome exato = {exatos}")
        if len(alcancados) == 1:
            print("    -> HOJE nao ha risco: a escolha e' unica e o aviso nem aparece.")
            print("       O que falta nao e' um campo novo, e' a escolha ser VISIVEL.")


if __name__ == "__main__":
    main()

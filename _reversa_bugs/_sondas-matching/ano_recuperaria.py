"""Quantos cartoes o ano de nascimento RECUPERARIA — o numero que decide a recomendacao.

O ganho de uma coluna de ano de nascimento nao e' "escolher melhor entre homonimos" no
abstrato. E' isto: hoje o app escolhe UM candidato por desempate congelado e, se o escolhido
for antigo demais para ter doado DNA, o cartao inteiro vira "Parentesco documental nao
encontrado" (regra do adendo 016). Se OUTRO candidato do mesmo nome for plausivel, o cartao
foi jogado fora por causa do desempate — e nao por falta de dado na arvore.

Mede, cartao a cartao da analise real:
  - o ano de nascimento do registro ESCOLHIDO;
  - se ele e' plausivel para quem doou DNA (a mesma regra do app: nascido depois de
    `ano_base - IDADE_IMPOSSIVEL`);
  - se existe OUTRO candidato plausivel que o desempate nao escolheu.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\ano_recuperaria.py
"""

import collections
import os
import re
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from core.dna_analysis import Dependencias, dna_analysis  # noqa: E402
from core.documentary_relationship import homonym_dossier  # noqa: E402
from core.janela_de_vida import IDADE_IMPOSSIVEL, ano_de_referencia  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    anotar_profundidade,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

GED = os.path.join(R, "src", "uploads", "0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged")
CSV = os.path.join(R, "src", "uploads", "03f50d273442cef1__Famílias_Sergipanas.csv")


def ano_de_nascimento(arvore, pessoa_id):
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
    ano_base = ano_de_referencia(2026, None)
    limite = ano_base - IDADE_IMPOSSIVEL
    print(f"ano_base={ano_base}  limite de plausibilidade={limite} (nascido depois disto)")

    deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                        generate_mermaid_graph, generate_mermaid_graph_indirect_bridge,
                        anotar_profundidade)
    resultados, _descartados, _msg = dna_analysis(
        CSV, "Adriano Santos", deps, arvore, observacoes_do_arquivo=[])

    print(f"cartoes: {len(resultados)}\n")
    print("=" * 104)
    print("A ESCOLHA, CARTAO A CARTAO, E O QUE O DESEMPATE CUSTOU")
    print("=" * 104)

    sem_ano_escolhido = 0
    implausivel_sem_alternativa = 0
    recuperaveis = []
    sem_ano_travados = []
    for resultado in resultados:
        documento = resultado.get("documentary") or {}
        do_registro = resultado.get("documentary_do_registro") or documento
        pessoa_b = ((do_registro.get("person_b") or {}).get("id")
                    or ((documento.get("person_b") or {}).get("id")))
        nome_csv = resultado.get("csv_name")
        if not pessoa_b:
            continue
        ano_escolhido = ano_de_nascimento(arvore, pessoa_b)
        if ano_escolhido is None:
            sem_ano_escolhido += 1
            fichas = homonym_dossier(arvore, nome_csv)["exact_matches"]
            sem_ano_travados.append({
                "nome": nome_csv, "kit": resultado.get("kit"), "pessoa": pessoa_b,
                "candidatos": len(fichas),
                "candidatos_com_ano": sum(1 for f in fichas
                                          if ano_de_nascimento(arvore, f["id"])),
            })
            continue
        plausivel = ano_escolhido > limite
        if plausivel:
            continue
        # O escolhido e' antigo demais. Existe OUTRO candidato plausivel?
        alternativas = [f["id"] for f in homonym_dossier(arvore, nome_csv)["exact_matches"]
                        if f["id"] != pessoa_b]
        boas = [(i, ano_de_nascimento(arvore, i)) for i in alternativas]
        boas = [(i, a) for i, a in boas if a and a > limite]
        if boas:
            recuperaveis.append((nome_csv, resultado.get("kit"), ano_escolhido, boas))
        else:
            implausivel_sem_alternativa += 1

    print(f"  cartoes cujo registro escolhido NAO tem ano de nascimento .. {sem_ano_escolhido}")
    print(f"  cartoes com escolhido antigo demais e SEM alternativa boa .. {implausivel_sem_alternativa}")
    print(f"  cartoes RECUPERAVEIS (escolhido antigo, existe alternativa) . {len(recuperaveis)}")
    print()
    for nome, kit, ano_ruim, boas in recuperaveis:
        lista = ", ".join(f"{i}={a}" for i, a in boas)
        print(f"    {str(nome)[:30]:<30} kit {str(kit):<11} escolhido={ano_ruim}  "
              f"alternativa(s) plausivel(is): {lista}")

    print("\n" + "=" * 104)
    print("OS CARTOES TRAVADOS POR FALTA DE DATA — onde preencher o GEDCOM vale mais")
    print("=" * 104)
    for registro in sem_ano_travados:
        print(f"    {str(registro['nome'])[:30]:<30} kit {str(registro['kit']):<11} "
              f"registro {registro['pessoa']:<14} candidatos={registro['candidatos']} "
              f"com_ano={registro['candidatos_com_ano']}")

    print("\n" + "=" * 104)
    print("RESUMO")
    print("=" * 104)
    total_com_ano = sum(1 for r in resultados
                        if (r.get("documentary") or {}).get("person_b"))
    print(f"  cartoes com registro escolhido: {total_com_ano}")
    print(f"  recuperaveis por um ano de nascimento na planilha: {len(recuperaveis)}")
    if recuperaveis:
        nomes = {n for n, _, _, _ in recuperaveis}
        print(f"  nomes distintos envolvidos: {len(nomes)} -> {sorted(nomes)}")
    else:
        print("  nenhum: neste arquivo o desempate nao esta' jogando cartao bom fora.")


if __name__ == "__main__":
    main()

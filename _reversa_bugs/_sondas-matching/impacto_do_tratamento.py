"""O que o TRATAMENTO da arvore mudou, e o que isso muda no resultado do operador.

Compara a arvore anterior com a `..._Tratado.ged`, em tres camadas:

  1. ESTRUTURA — o que mudou registro a registro, casando por `xref` (que o tratamento
     preserva, porque edita registros em vez de recriar a arvore): nomes alterados, datas
     acrescentadas, registros novos ou removidos;
  2. HOMONIMOS — quantos nomes colidiam antes e colidem agora, e o que aconteceu com os
     nomes que o CSV realmente pedia;
  3. RESULTADO — a analise rodada nas DUAS arvores com o MESMO CSV, cartao a cartao, para
     dizer o que o operador ve diferente.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\impacto_do_tratamento.py
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
from core.identidade_do_match import conferir  # noqa: E402
from core.name_normalization import norm_name  # noqa: E402
from core.registro import get_name  # noqa: E402
from parsers.csv_ingest import aggregate_matches, detect_columns, read_csv_with_fallback  # noqa: E402
from parsers.gedcom_parser import carregar_arvore  # noqa: E402
from reporting.mermaid_render import (  # noqa: E402
    anotar_profundidade,
    generate_mermaid_graph,
    generate_mermaid_graph_indirect_bridge,
)

PASTA = os.path.join(R, "src", "uploads")
ANTES = os.path.join(PASTA, "0fa3699e246caae1__Arvore_Unificada_Oficial_V1_2.ged")
DEPOIS = os.path.join(PASTA, "e10c087ae4973fc9__Arvore_Unificada_Oficial_V1_2_Tratado.ged")
CSV = os.path.join(PASTA, "54f4887e89705735__Famílias_Sergipanas.csv")
RAIZ = "Adriano Santos"


def ano(arvore, pessoa_id):
    pessoa = arvore[0].get(pessoa_id)
    if pessoa is None:
        return None
    for registro in pessoa.sub_records:
        if registro.tag == "BIRT":
            for filho in registro.sub_records:
                if filho.tag == "DATE" and filho.value:
                    achado = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", str(filho.value))
                    if achado:
                        return int(achado.group(1))
    return None


def sexo(arvore, pessoa_id):
    pessoa = arvore[0].get(pessoa_id)
    if pessoa is None:
        return None
    return next((r.value for r in pessoa.sub_records if r.tag == "SEX"), None)


def metricas_da_arvore(arvore):
    pessoas = arvore[0]
    por_nome = collections.defaultdict(list)
    com_ano = 0
    for pessoa_id, pessoa in pessoas.items():
        chave = norm_name(get_name(pessoa))
        if chave:
            por_nome[chave].append(pessoa_id)
        if ano(arvore, pessoa_id):
            com_ano += 1
    ambiguos = {n: ids for n, ids in por_nome.items() if len(ids) > 1}
    return {
        "pessoas": len(pessoas),
        "nomes_distintos": len(por_nome),
        "ambiguos": len(ambiguos),
        "com_ano": com_ano,
        "por_nome": por_nome,
        "ambiguos_detalhe": ambiguos,
    }


def rodar(arvore, deps):
    resultados, descartados, _msg = dna_analysis(
        CSV, RAIZ, deps, arvore, observacoes_do_arquivo=[])
    return resultados, descartados


def main():
    print("=" * 100)
    print("A. IDENTIDADE DOS ARQUIVOS")
    print("=" * 100)
    for rotulo, caminho in (("antes  ", ANTES), ("tratado", DEPOIS)):
        info = os.stat(caminho)
        print(f"  {rotulo}: {info.st_size:>10,} bytes   {os.path.basename(caminho)}".replace(",", "."))

    arvore_antes = carregar_arvore(ANTES)
    arvore_depois = carregar_arvore(DEPOIS)

    print("\n" + "=" * 100)
    print("B. O QUE O TRATAMENTO MUDOU, REGISTRO A REGISTRO (casado por xref)")
    print("=" * 100)
    antes_ids = set(arvore_antes[0])
    depois_ids = set(arvore_depois[0])
    comuns = antes_ids & depois_ids
    print(f"  registros antes ....... {len(antes_ids):>7,}".replace(",", "."))
    print(f"  registros tratados .... {len(depois_ids):>7,}".replace(",", "."))
    print(f"  so' no tratado ........ {len(depois_ids - antes_ids):>7,}".replace(",", "."))
    print(f"  so' no anterior ....... {len(antes_ids - depois_ids):>7,}".replace(",", "."))

    renomeados, ganharam_data, perderam_data, mudaram_sexo = [], [], [], []
    for pessoa_id in comuns:
        nome_a = get_name(arvore_antes[0][pessoa_id])
        nome_d = get_name(arvore_depois[0][pessoa_id])
        if nome_a != nome_d:
            renomeados.append((pessoa_id, nome_a, nome_d))
        ano_a, ano_d = ano(arvore_antes, pessoa_id), ano(arvore_depois, pessoa_id)
        if ano_a is None and ano_d is not None:
            ganharam_data.append((pessoa_id, nome_d, ano_d))
        elif ano_a is not None and ano_d is None:
            perderam_data.append((pessoa_id, nome_d, ano_a))
        if sexo(arvore_antes, pessoa_id) != sexo(arvore_depois, pessoa_id):
            mudaram_sexo.append((pessoa_id, sexo(arvore_antes, pessoa_id),
                                 sexo(arvore_depois, pessoa_id)))
    print(f"\n  NOMES alterados ............ {len(renomeados):>6,}".replace(",", "."))
    print(f"  ganharam data de nascimento  {len(ganharam_data):>6,}".replace(",", "."))
    print(f"  perderam data .............. {len(perderam_data):>6,}".replace(",", "."))
    print(f"  sexo alterado .............. {len(mudaram_sexo):>6,}".replace(",", "."))

    if renomeados:
        print("\n  amostra dos nomes alterados (20 primeiros):")
        for pessoa_id, antes, depois in renomeados[:20]:
            print(f"    {pessoa_id:<14} {antes[:40]:<40} -> {depois[:40]}")

    print("\n" + "=" * 100)
    print("C. PRESSAO DE HOMONIMOS, ANTES E DEPOIS")
    print("=" * 100)
    ma, md = metricas_da_arvore(arvore_antes), metricas_da_arvore(arvore_depois)
    for rotulo, m in (("antes", ma), ("tratado", md)):
        pct = 100.0 * m["ambiguos"] / m["nomes_distintos"]
        cobertura = 100.0 * m["com_ano"] / m["pessoas"]
        print(f"  {rotulo:<8} pessoas={m['pessoas']:>7,}  nomes={m['nomes_distintos']:>7,}  "
              f"ambiguos={m['ambiguos']:>6,} ({pct:4.1f}%)  com ano={cobertura:4.1f}%".replace(",", "."))
    delta = md["ambiguos"] - ma["ambiguos"]
    print(f"\n  nomes ambiguos: {ma['ambiguos']} -> {md['ambiguos']}  ({delta:+d})")

    piores_antes = sorted(ma["ambiguos_detalhe"].items(), key=lambda x: -len(x[1]))[:8]
    print("\n  os piores ANTES, e o que viraram:")
    for nome, ids in piores_antes:
        depois = md["ambiguos_detalhe"].get(nome)
        agora = f"{len(depois)}" if depois else "RESOLVIDO (0 ou 1)"
        print(f"    {len(ids):>4} x {nome[:46]:<46} -> {agora}")

    print("\n" + "=" * 100)
    print("D. OS NOMES QUE O CSV PEDE")
    print("=" * 100)
    df = read_csv_with_fallback(CSV)
    nomes_csv = sorted({str(n) for n in df["Name"].dropna()})
    print(f"  nomes distintos no CSV: {len(nomes_csv)}")
    total_a = total_d = 0
    mudou = []
    for nome in nomes_csv:
        ca = len(homonym_dossier(arvore_antes, nome)["exact_matches"])
        cd = len(homonym_dossier(arvore_depois, nome)["exact_matches"])
        total_a += ca
        total_d += cd
        if ca != cd:
            mudou.append((nome, ca, cd))
    print(f"  candidatos exatos somados: {total_a} -> {total_d}  ({total_d - total_a:+d})")
    print(f"  nomes cujo numero de candidatos MUDOU: {len(mudou)}")
    for nome, ca, cd in mudou[:25]:
        marca = "RESOLVIDO" if cd <= 1 else ("piorou" if cd > ca else "melhorou")
        print(f"    {nome[:40]:<40} {ca} -> {cd}   {marca}")

    print("\n" + "=" * 100)
    print("E. RESULTADO DA ANALISE NAS DUAS ARVORES (mesmo CSV)")
    print("=" * 100)
    deps = Dependencias(read_csv_with_fallback, detect_columns, aggregate_matches,
                        generate_mermaid_graph, generate_mermaid_graph_indirect_bridge,
                        anotar_profundidade)
    res_a, desc_a = rodar(arvore_antes, deps)
    res_d, desc_d = rodar(arvore_depois, deps)
    print(f"  cartoes ........... {len(res_a)} -> {len(res_d)}")
    print(f"  descartados ....... {len(desc_a)} -> {len(desc_d)}")

    def distribuicao(resultados, campo, sub=None):
        contagem = collections.Counter()
        for r in resultados:
            valor = r.get(campo)
            if sub and isinstance(valor, dict):
                valor = valor.get(sub)
            contagem[str(valor)] += 1
        return contagem

    for rotulo, campo, sub in (("identidade", "identidade", None),
                               ("parentesco documental", "documentary", "status"),
                               ("janela de vida", "janela_de_vida", None),
                               ("profundidade", "profundidade", None),
                               ("confrontacao", "confrontacao_efetiva", None)):
        da = distribuicao(res_a, campo, sub)
        dd = distribuicao(res_d, campo, sub)
        print(f"\n  {rotulo}:")
        for chave in sorted(set(da) | set(dd)):
            seta = "  <-- MUDOU" if da.get(chave, 0) != dd.get(chave, 0) else ""
            print(f"    {chave:<28} {da.get(chave, 0):>4} -> {dd.get(chave, 0):>4}{seta}")

    print("\n  cartoes que MUDARAM de pessoa na arvore:")
    por_chave_a = {(r["csv_name"], str(r["kit"])): r for r in res_a}
    por_chave_d = {(r["csv_name"], str(r["kit"])): r for r in res_d}
    mudancas = 0
    for chave in sorted(set(por_chave_a) | set(por_chave_d)):
        ra, rd = por_chave_a.get(chave), por_chave_d.get(chave)
        if ra is None or rd is None:
            print(f"    {chave[0][:30]:<30} kit {chave[1]:<11} "
                  f"{'so no ANTES' if rd is None else 'so no TRATADO'}")
            mudancas += 1
            continue
        pessoa_a = ((ra.get("documentary") or {}).get("person_b") or {}).get("id")
        pessoa_d = ((rd.get("documentary") or {}).get("person_b") or {}).get("id")
        if pessoa_a != pessoa_d:
            print(f"    {chave[0][:30]:<30} kit {chave[1]:<11} {pessoa_a} -> {pessoa_d}")
            mudancas += 1
    if not mudancas:
        print("    (nenhum)")


if __name__ == "__main__":
    main()

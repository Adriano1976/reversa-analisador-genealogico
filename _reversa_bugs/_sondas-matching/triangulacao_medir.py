"""A alavanca que NAO exige coluna nova: as posicoes dos segmentos.

O CSV do GEDmatch traz `Chromosome`, `Start` e `End` por linha, e o app le essas tres
colunas — mas so' para EXIBIR. Nenhuma decisao de parentesco as usa.

Triangulacao e' o uso classico delas: tres ou mais kits que compartilham o MESMO trecho do
mesmo cromossomo descendem, com probabilidade alta, do mesmo ancestral — e isso e'
independente do nome. Um grupo triangulado cujos caminhos documentais apontam para
ancestrais DIFERENTES e' contradicao; um grupo cujos caminhos convergem e' corroboracao.

Esta sonda mede quanta materia-prima existe para isso no arquivo real. Ela NAO triangula de
verdade (isso exigiria a lista de matches de cada kit, e nao so' a do operador): ela conta
grupos candidatos — trechos com sobreposicao entre kits distintos.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\triangulacao_medir.py
"""

import collections
import os
import sys

R = r"D:\Projetos\reversa_analisador_gelealogico"
sys.path.insert(0, R)
sys.path.insert(0, os.path.join(R, "src"))

from parsers.csv_ingest import read_csv_with_fallback  # noqa: E402

CSV = os.path.join(R, "src", "uploads", "03f50d273442cef1__Famílias_Sergipanas.csv")

CM_MINIMO = 7.0


def main():
    df = read_csv_with_fallback(CSV)
    print(f"linhas: {len(df)}   kits distintos: {df['Kit number'].nunique()}")
    print(f"colunas: {list(df.columns)}")
    print()

    utilizaveis = df[(df["cM"] >= CM_MINIMO) & df["Start"].notna() & df["End"].notna()].copy()
    utilizaveis["Start"] = utilizaveis["Start"].astype(float)
    utilizaveis["End"] = utilizaveis["End"].astype(float)
    print(f"segmentos com >= {CM_MINIMO:g} cM e posicao: {len(utilizaveis)}")

    # Grupos candidatos: mesmo cromossomo e trechos que se sobrepoem, entre KITS DISTINTOS.
    grupos = []
    for cromossomo, bloco in utilizaveis.groupby("Chromosome"):
        linhas = bloco.sort_values("Start").to_dict("records")
        atual = None
        for linha in linhas:
            if atual is None or linha["Start"] > atual["fim"]:
                if atual and len(atual["kits"]) >= 3:
                    grupos.append(atual)
                atual = {"cromossomo": cromossomo, "inicio": linha["Start"],
                         "fim": linha["End"], "kits": {linha["Kit number"]},
                         "nomes": {linha["Name"]}}
            else:
                atual["fim"] = max(atual["fim"], linha["End"])
                atual["kits"].add(linha["Kit number"])
                atual["nomes"].add(linha["Name"])
        if atual and len(atual["kits"]) >= 3:
            grupos.append(atual)

    print("\n" + "=" * 96)
    print("GRUPOS CANDIDATOS A TRIANGULACAO (>= 3 kits no mesmo trecho do mesmo cromossomo)")
    print("=" * 96)
    print(f"  grupos: {len(grupos)}")
    if grupos:
        por_tamanho = collections.Counter(len(g["kits"]) for g in grupos)
        for tamanho in sorted(por_tamanho, reverse=True):
            print(f"    {tamanho:>3} kits: {por_tamanho[tamanho]} grupo(s)")
        kits_em_grupo = {k for g in grupos for k in g["kits"]}
        print(f"  kits envolvidos: {len(kits_em_grupo)} de {df['Kit number'].nunique()}")
        print("\n  os maiores:")
        for grupo in sorted(grupos, key=lambda g: -len(g["kits"]))[:6]:
            nomes = sorted(grupo["nomes"])
            print(f"    chr{grupo['cromossomo']:<3} {int(grupo['inicio']):>10}-{int(grupo['fim']):<10} "
                  f"{len(grupo['kits']):>2} kits, {len(nomes)} nome(s): {nomes[:4]}")

    print("\n" + "=" * 96)
    print("O QUE ISSO MUDARIA NO RESULTADO DE HOJE")
    print("=" * 96)
    print("  Hoje: cada kit e' julgado SOZINHO contra a arvore, pelo nome.")
    print("  Com triangulacao: os kits de um grupo teriam de apontar para o MESMO ancestral,")
    print("  e um grupo coeso cujos caminhos divergem e' contradicao que o nome nao revela —")
    print("  'Margarida' com 8 homonimos deixa de ser um sorteio e passa a ser uma pergunta")
    print("  com resposta: qual dos 8 explica o grupo inteiro?")


if __name__ == "__main__":
    main()

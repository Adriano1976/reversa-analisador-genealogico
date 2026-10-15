"""Remedicao da triangulacao: sobreposicao por POSICAO, e nao uniao em cadeia.

A primeira medicao agrupava por uniao: um segmento que encostava no anterior esticava o
grupo, e o intervalo final era a UNIAO. O maior "grupo" saiu com 40 Mb (chr16:46-86M), o
que denuncia o defeito — 40 Mb nao e' um segmento compartilhado, e' uma cadeia de segmentos
distintos que se tocam nas pontas. Um grupo assim nao sustenta "ancestral comum".

A medicao correta pergunta outra coisa: em cada POSICAO do cromossomo, quantos KITS
DISTINTOS cobrem aquele par de bases? Onde 3 ou mais cobrem, ha sobreposicao real — e nao
cadeia. E' a metrica que a triangulacao de verdade usa como ponto de partida.

Uso: .\\.venv\\Scripts\\python.exe _reversa_bugs\\_sondas-matching\\triangulacao_posicao.py
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
    utilizaveis = df[(df["cM"] >= CM_MINIMO) & df["Start"].notna() & df["End"].notna()].copy()
    utilizaveis["Start"] = utilizaveis["Start"].astype(float)
    utilizaveis["End"] = utilizaveis["End"].astype(float)
    print(f"segmentos com >= {CM_MINIMO:g} cM e posicao: {len(utilizaveis)}  "
          f"kits: {utilizaveis['Kit number'].nunique()}")

    profundidade_maxima = 0
    kits_em_regiao_funda = set()
    regioes = []

    for cromossomo, bloco in utilizaveis.groupby("Chromosome"):
        segmentos = list(zip(bloco["Kit number"], bloco["Start"], bloco["End"]))
        cortes = sorted({p for _, inicio, fim in segmentos for p in (inicio, fim)})
        ativos_por_intervalo = []
        for esquerda, direita in zip(cortes, cortes[1:]):
            meio = (esquerda + direita) / 2
            ativos = {kit for kit, inicio, fim in segmentos if inicio <= meio <= fim}
            ativos_por_intervalo.append((esquerda, direita, ativos))
            profundidade_maxima = max(profundidade_maxima, len(ativos))
            if len(ativos) >= 3:
                kits_em_regiao_funda |= ativos

        # Junta intervalos vizinhos que tenham 3+ kits, formando regioes contiguas.
        atual = None
        for esquerda, direita, ativos in ativos_por_intervalo:
            if len(ativos) < 3:
                if atual:
                    regioes.append(atual)
                    atual = None
                continue
            if atual is None:
                atual = {"cromossomo": cromossomo, "inicio": esquerda, "fim": direita,
                         "kits": set(ativos), "minimo": len(ativos)}
            else:
                atual["fim"] = direita
                atual["kits"] |= ativos
                atual["minimo"] = min(atual["minimo"], len(ativos))
        if atual:
            regioes.append(atual)

    print("\n" + "=" * 96)
    print("SOBREPOSICAO REAL — posicoes cobertas por 3 ou mais KITS DISTINTOS")
    print("=" * 96)
    print(f"  profundidade maxima em qualquer posicao: {profundidade_maxima} kits")
    print(f"  kits que participam de alguma posicao com >= 3: {len(kits_em_regiao_funda)} "
          f"de {utilizaveis['Kit number'].nunique()}")
    print(f"  regioes contiguas com >= 3 kits: {len(regioes)}")
    if not regioes:
        print("  (nenhuma)")
        return

    extensoes = sorted(((r["fim"] - r["inicio"], r) for r in regioes), reverse=True)
    print("\n  as 8 maiores, por EXTENSAO da regiao onde 3+ kits se sobrepoem:")
    for extensao, regiao in extensoes[:8]:
        print(f"    chr{regiao['cromossomo']:<3} {int(regiao['inicio']):>10}-{int(regiao['fim']):<10} "
              f"{extensao / 1e6:>6.2f} Mb   kits na regiao: {len(regiao['kits']):>3}   "
              f"minimo simultaneo: {regiao['minimo']}")

    total_mb = sum(e for e, _ in extensoes) / 1e6
    print(f"\n  soma da extensao de todas as regioes: {total_mb:.1f} Mb")
    print(f"  mediana da extensao: {sorted(e for e, _ in extensoes)[len(extensoes) // 2] / 1e6:.2f} Mb")

    print("\n" + "=" * 96)
    print("A COMPARACAO QUE IMPORTA")
    print("=" * 96)
    print(f"  medicao por UNIAO (artefato): 48 grupos, 265 kits, maior 'grupo' com 40 Mb")
    print(f"  medicao por POSICAO (esta):   {len(regioes)} regioes, {len(kits_em_regiao_funda)} kits, "
          f"maior regiao com {extensoes[0][0] / 1e6:.2f} Mb")
    print("  Um segmento compartilhado de verdade tem alguns Mb; 40 Mb e' uma cadeia.")


if __name__ == "__main__":
    main()

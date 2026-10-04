"""Possibilidades de parentesco a partir do cM observado.

Responsabilidade unica: traduzir um total de cM em **possibilidades** de
parentesco, usando a tabela publicada do Shared cM Project 4.0. Nunca devolve um
parentesco unico, nunca "confirma" nada e nunca le o GEDCOM.

## Regra do projeto

cM -> conjunto de possibilidades. O parentesco documental vem do GEDCOM
(`core.documentary_relationship`) e nao e tocado por este modulo. A comparacao
entre os dois mora em `core.evidence_comparison`.

## Fonte (Shared cM Project 4.0)

- Bettinger, B. T. *The Shared cM Project Version 4.0 (March 2020)*, PDF oficial:
  https://thegeneticgenealogist.com/wp-content/uploads/2020/03/Shared-cM-Project-Version-4.pdf
- DNA Painter, *Shared cM Project 4.0 tool*:
  https://dnapainter.com/tools/sharedcmv4
- Anuncio da versao: https://thegeneticgenealogist.com/2020/03/27/version-4-0-march-2020-update-to-the-shared-cm-project/
- 59.714 envios ate 08/07/2019; 55.418 usados nas 48 relacoes analisadas.

O que a fonte diz e o que ela **nao** diz, porque isso muda a leitura da tela:

- A coluna "Range" da fonte e, literalmente, "Range (low to high; 99th
  percentile)": 1% dos envios foi removido (0,5% em cada ponta) antes de reportar
  minimo e maximo. Nao e o intervalo observado completo.
- **A versao 4.0 nao publica mediana** para relacao nenhuma (so numero de envios,
  minimo, media, maximo e desvio padrao). Por isso `average` existe aqui e
  `median` nao.
- As distribuicoes **se sobrepoem**: a propria fonte registra que "o cM total nao
  pode ser utilizado para diferenciar meios-irmaos de tio/tia" (PDF, p.49).
- **Endogamia e colapso de pedigree aumentam** o cM compartilhado para o mesmo
  parentesco genealogico (PDF, p.1), e as estatisticas "nao atendem colapso de
  pedigree ou endogamia" (DNA Painter). O valor lido, portanto, e um teto otimista
  nesses casos.
- Para relacoes cujo minimo e 0 cM, **a media so considera quem compartilha DNA
  detectavel** (PDF, p.4). Nao e a media de todos os primos de 5º grau, e sim a
  dos que compartilham algo.
- A fonte **nao afirma** nada sobre "segmento abaixo de X cM e falso positivo".
  O limite `LIMITE_SEGMENTO_FRACO` de `core.genetic_evidence` e criterio do
  projeto, e a tela deve apresenta-lo como tal.
- Relacoes **nao publicadas** na 4.0 (nao invente numero para elas): 1C4R, 1C5R,
  1C6R, 3C2R, 2º bisavô/avó e 3º bisavô/avó. Faltam justamente as mais distantes,
  que e onde o caso real deste repositorio cai.
"""
from __future__ import annotations

SCP40_META = {
    "version": "4.0",
    "release": "março de 2020",
    "sample_size": 59714,
    "range_definition": "faixa (mínimo–máximo) após remoção de 1% dos envios (0,5% em cada ponta); "
                        "não é o intervalo observado completo",
    "sources": [
        "https://thegeneticgenealogist.com/wp-content/uploads/2020/03/Shared-cM-Project-Version-4.pdf",
        "https://dnapainter.com/tools/sharedcmv4",
    ],
}

# (chave interna, nome na fonte, nome em português, meioses, média, mínimo, máximo)
# `meioses` = número de saltos pai-filho entre as duas pessoas; é a grandeza que o
# cM mede. Relações diferentes com o mesmo número de meioses se sobrepõem — é por
# isso que a resposta é uma lista.
SCP40_ROWS = [
    ("PARENT_CHILD", "Parent/Child", "Pai/Mãe ↔ Filho(a)", 1, 3485, 3330, 3720),
    ("SIBLINGS", "Sibling", "Irmãos completos", 2, 2613, 1613, 3488),
    ("HALF_SIBLINGS", "Half Sibling", "Meios-irmãos", 2, 1759, 1160, 2436),
    ("GRANDPARENT", "Grandparent/Grandchild", "Avô/Avó ↔ Neto(a)", 2, 1754, 984, 2462),
    ("AUNT_UNCLE", "Aunt / Uncle", "Tio/Tia ↔ Sobrinho(a)", 3, 1741, 1201, 2282),
    ("DIRECT_3", "Great-Grandparent/Great-Grandchild", "Bisavô/Bisavó ↔ Bisneto(a)", 3, 887, 485, 1486),
    ("GREAT_AUNT_1", "Great-Aunt / Uncle", "Tio/Tia-avô/avó ↔ Sobrinho(a)-neto(a)", 4, 850, 330, 1467),
    ("GREAT_AUNT_2", "Great-Great-Aunt / Uncle", "Tio/Tia-bisavô/avó ↔ Sobrinho(a)-bisneto(a)", 5, 420, 186, 713),
    ("1C", "1C", "Primos de 1º grau", 2, 866, 396, 1397),
    ("1C1R", "1C1R", "Primos de 1º grau (1× removido)", 3, 433, 102, 980),
    ("1C2R", "1C2R", "Primos de 1º grau (2× removidos)", 4, 221, 33, 471),
    ("1C3R", "1C3R", "Primos de 1º grau (3× removidos)", 5, 117, 25, 238),
    ("2C", "2C", "Primos de 2º grau", 4, 229, 41, 592),
    ("2C1R", "2C1R", "Primos de 2º grau (1× removido)", 5, 122, 14, 353),
    ("2C2R", "2C2R", "Primos de 2º grau (2× removidos)", 6, 71, 0, 244),
    ("2C3R", "2C3R", "Primos de 2º grau (3× removidos)", 7, 51, 0, 154),
    ("3C", "3C", "Primos de 3º grau", 6, 73, 0, 234),
    ("3C1R", "3C1R", "Primos de 3º grau (1× removido)", 7, 48, 0, 192),
    ("4C", "4C", "Primos de 4º grau", 8, 35, 0, 139),
    ("4C1R", "4C1R", "Primos de 4º grau (1× removido)", 9, 28, 0, 126),
    ("5C", "5C", "Primos de 5º grau", 10, 25, 0, 117),
    ("5C1R", "5C1R", "Primos de 5º grau (1× removido)", 11, 21, 0, 80),
    ("6C", "6C", "Primos de 6º grau", 12, 18, 0, 71),
    ("7C", "7C", "Primos de 7º grau", 14, 14, 0, 57),
    ("8C", "8C", "Primos de 8º grau", 16, 11, 0, 42),
    ("HALF_1C", "Half 1C", "Meio-primos de 1º grau", 3, 449, 156, 979),
    ("HALF_2C", "Half 2C", "Meio-primos de 2º grau", 5, 120, 10, 325),
]

# Relações que a 4.0 não publica. A lista existe para que o confronto saiba
# dizer "não há faixa publicada" em vez de inventar uma.
SCP40_NOT_PUBLISHED = {
    "1C4R": "não analisada na versão 4.0",
    "1C5R": "não analisada na versão 4.0",
    "1C6R": "não analisada na versão 4.0",
    "3C2R": "não analisada na versão 4.0",
    "DIRECT_4": "2º bisavô/avó: não analisada na versão 4.0",
    "DIRECT_5": "3º bisavô/avó: não analisada na versão 4.0",
}


def row_for_key(key: str):
    """Linha publicada do Shared cM 4.0 para a chave canonica, ou None."""
    for chave, nome_en, nome_pt, meioses, media, baixo, alto in SCP40_ROWS:
        if chave == key:
            return {"key": chave, "name_en": nome_en, "name_pt": nome_pt, "meioses": meioses,
                    "average": media, "range_low": baixo, "range_high": alto}
    return None


def rows_by_meioses(meioses: int) -> list:
    """Todas as linhas publicadas com o mesmo numero de meioses."""
    return [row_for_key(c[0]) for c in SCP40_ROWS if c[3] == meioses]


def meioses_window(meioses: int):
    """Janela de compatibilidade para uma contagem de meioses, tirada da fonte.

    Usada quando a relacao exata **nao** foi publicada na 4.0 (caso de 1C6R):
    em vez de inventar numero, reunimos as relacoes publicadas com o MESMO numero
    de meioses e usamos a envoltoria das faixas delas. Sem relacao publicada
    naquele numero de meioses, nao ha janela — e o confronto fica inconclusivo.
    """
    linhas = rows_by_meioses(meioses)
    if not linhas:
        return None
    return {
        "meioses": meioses,
        "range_low": min(l["range_low"] for l in linhas),
        "range_high": max(l["range_high"] for l in linhas),
        "average": round(sum(l["average"] for l in linhas) / len(linhas)),
        "rows": [l["name_en"] for l in linhas],
    }


def _confianca(qtd: int, cm) -> tuple:
    """Confianca da lista, pelo criterio explicito do projeto (nao da fonte).

    Quanto mais relacoes publicadas contem o valor, menos o valor discrimina.
    A fonte do Shared cM nao define grau de confianca algum; isto e heuristica
    declarada, e a tela deve apresenta-la como tal.
    """
    if cm is None or cm <= 0:
        return "indeterminada", "Não há valor de cM válido para avaliar."
    if qtd == 0:
        return "indeterminada", "Nenhuma relação publicada na versão 4.0 cobre exatamente este valor."
    if qtd == 1:
        return "baixa", ("Apenas uma relação publicada cobre este valor — e ainda assim a fonte alerta "
                         "que as distribuições se sobrepõem.")
    if qtd <= 3:
        return "baixa", f"{qtd} relações publicadas cobrem este valor; o cM não distingue qual delas é a verdadeira."
    if qtd <= 6:
        return "muito baixa", f"{qtd} relações publicadas cobrem este valor: a sobreposição é ampla."
    return "muito baixa", f"{qtd} relações publicadas cobrem este valor — nesta faixa o cM praticamente não discrimina."


def possible_relationships(total_cm) -> dict:
    """Estrutura do contrato: total_cm + possibilidades + confianca + leitura.

    Devolve SEMPRE lista em `possible_relationships`, inclusive vazia, e nunca um
    unico parentesco afirmado como conclusao.
    """
    if total_cm is None:
        return {
            "total_cm": None,
            "possible_relationships": [],
            "confidence": "indeterminada",
            "interpretation": "Sem valor de cM utilizável: não é possível listar possibilidades.",
            "reference": SCP40_META,
        }

    cm = float(total_cm)
    candidatas = []
    for chave, nome_en, nome_pt, meioses, media, baixo, alto in SCP40_ROWS:
        if baixo <= cm <= alto:
            candidatas.append({
                "key": chave, "name_en": nome_en, "name_pt": nome_pt, "meioses": meioses,
                "average": media, "range_low": baixo, "range_high": alto,
            })
    candidatas.sort(key=lambda c: (abs(c["average"] - cm), c["name_en"]))

    confianca, explicacao = _confianca(len(candidatas), cm)
    if candidatas:
        leitura = (f"{len(candidatas)} relação(ões) publicada(s) na versão 4.0 do Shared cM Project "
                   f"admitem {cm:g} cM. Essas relações têm distribuições sobrepostas: o valor observado "
                   "não identifica qual delas é a verdadeira. Quanto mais distante a relação, maior a "
                   "cautela, porque a média das relações distantes só considera quem compartilha DNA "
                   "detectável.")
    else:
        leitura = (f"Nenhuma relação publicada na versão 4.0 cobre exatamente {cm:g} cM. Isso não "
                   "descarta parentesco: pode ser uma relação não analisada pela fonte ou um valor "
                   "afetado por agregação, endogamia ou limiar da empresa de teste.")

    return {
        "total_cm": cm,
        "possible_relationships": candidatas,
        "confidence": confianca,
        "confidence_note": explicacao,
        "interpretation": leitura,
        "reference": SCP40_META,
    }


def hypotheses_for_evidence(evidence: dict) -> list:
    """Uma lista de hipoteses por KIT — nunca uma hipotese sobre a soma de kits.

    Sem evidencia, devolve lista vazia: sem DNA nao ha possibilidade de parentesco
    pelo DNA a listar (e o confronto dira que e inconclusivo, nao que e compativel).
    """
    if not evidence or not evidence.get("available"):
        return []
    blocos = []
    for kit in evidence.get("kits", []):
        bloco = possible_relationships(kit.get("total_cm"))
        bloco["kit"] = kit.get("kit")
        bloco["segment_count"] = kit.get("segment_count")
        bloco["largest_segment_cm"] = kit.get("largest_segment_cm")
        blocos.append(bloco)
    return blocos


__all__ = [
    "SCP40_ROWS", "SCP40_META", "SCP40_NOT_PUBLISHED", "row_for_key", "rows_by_meioses",
    "meioses_window", "possible_relationships", "hypotheses_for_evidence",
]
